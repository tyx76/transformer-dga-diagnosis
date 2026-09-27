param(
    [Parameter(Mandatory=$true)][string]$Source,
    [Parameter(Mandatory=$true)][string]$Output
)

Add-Type -AssemblyName System.IO.Compression
Add-Type -AssemblyName System.IO.Compression.FileSystem

$utf8 = [Text.UTF8Encoding]::new($false)
$sourcePath = (Resolve-Path -LiteralPath $Source).Path
$outputPath = [IO.Path]::GetFullPath($Output)
$lines = [IO.File]::ReadAllLines($sourcePath, $utf8)
$doc = [Text.StringBuilder]::new()

function Xml-Escape([string]$text) {
    if ($null -eq $text) { return '' }
    return [Security.SecurityElement]::Escape($text)
}

function Clean-Inline([string]$text) {
    if ($null -eq $text) { return '' }
    $t = $text
    $t = $t -replace '\*\*([^*]+)\*\*', '$1'
    $t = $t -replace '__([^_]+)__', '$1'
    $t = $t -replace '`([^`]+)`', '$1'
    $t = $t -replace '\[([^\]]+)\]\([^\)]+\)', '$1'
    return $t
}

function Append-Paragraph([string]$text, [string]$style = 'Normal', [bool]$bold = $false) {
    $escaped = Xml-Escape (Clean-Inline $text)
    [void]$doc.Append('<w:p><w:pPr><w:pStyle w:val="' + $style + '"/></w:pPr><w:r>')
    if ($bold) { [void]$doc.Append('<w:rPr><w:b/></w:rPr>') }
    [void]$doc.Append('<w:t xml:space="preserve">' + $escaped + '</w:t></w:r></w:p>')
}

function Append-PageBreak() {
    [void]$doc.Append('<w:p><w:r><w:br w:type="page"/></w:r></w:p>')
}

function Split-Row([string]$row) {
    $t = $row.Trim()
    if ($t.StartsWith('|')) { $t = $t.Substring(1) }
    if ($t.EndsWith('|')) { $t = $t.Substring(0, $t.Length - 1) }
    return @($t -split '\|')
}

function Append-Table([string[]]$headers, [System.Collections.Generic.List[string[]]]$rows) {
    $cols = $headers.Count
    if ($cols -le 0) { return }
    $width = [int](9360 / $cols)
    [void]$doc.Append('<w:tbl><w:tblPr><w:tblStyle w:val="TableGrid"/><w:tblW w:w="0" w:type="auto"/><w:tblLayout w:type="fixed"/></w:tblPr><w:tblGrid>')
    for ($i = 0; $i -lt $cols; $i++) { [void]$doc.Append('<w:gridCol w:w="' + $width + '"/>') }
    [void]$doc.Append('</w:tblGrid>')
    [void]$doc.Append('<w:tr><w:trPr><w:cantSplit/></w:trPr>')
    foreach ($h in $headers) {
        [void]$doc.Append('<w:tc><w:tcPr><w:tcW w:w="' + $width + '" w:type="dxa"/><w:shd w:val="clear" w:color="auto" w:fill="0B5394"/><w:vAlign w:val="center"/></w:tcPr><w:p><w:pPr><w:pStyle w:val="TableHeader"/></w:pPr><w:r><w:t xml:space="preserve">' + (Xml-Escape (Clean-Inline $h)) + '</w:t></w:r></w:p></w:tc>')
    }
    [void]$doc.Append('</w:tr>')
    $rowIndex = 0
    foreach ($row in $rows) {
        $shade = if (($rowIndex % 2) -eq 0) { 'F2F7FB' } else { 'FFFFFF' }
        [void]$doc.Append('<w:tr><w:trPr><w:cantSplit/></w:trPr>')
        for ($c = 0; $c -lt $cols; $c++) {
            $value = ''
            if ($c -lt $row.Count) { $value = $row[$c] }
            [void]$doc.Append('<w:tc><w:tcPr><w:tcW w:w="' + $width + '" w:type="dxa"/><w:shd w:val="clear" w:color="auto" w:fill="' + $shade + '"/><w:vAlign w:val="center"/></w:tcPr><w:p><w:pPr><w:pStyle w:val="TableText"/></w:pPr><w:r><w:t xml:space="preserve">' + (Xml-Escape (Clean-Inline $value)) + '</w:t></w:r></w:p></w:tc>')
        }
        [void]$doc.Append('</w:tr>')
        $rowIndex++
    }
    [void]$doc.Append('</w:tbl>')
}$inCode = $false
$seenFirstSeparator = $false

for ($i = 0; $i -lt $lines.Count; $i++) {
    $line = $lines[$i]
    $trim = $line.Trim()

    if ($trim.StartsWith('```')) { $inCode = -not $inCode; continue }
    if ($inCode) { Append-Paragraph $line 'Code'; continue }

    if ($trim -match '^\|.*\|$' -and ($i + 1) -lt $lines.Count -and $lines[$i + 1] -match '^\s*\|?[\s:\-\|]+\|?\s*$') {
        $headers = Split-Row $line
        $rowList = [System.Collections.Generic.List[string[]]]::new()
        $i += 2
        while ($i -lt $lines.Count -and $lines[$i].Trim().StartsWith('|')) {
            $rowList.Add((Split-Row $lines[$i]))
            $i++
        }
        $i--
        Append-Table $headers $rowList
        continue
    }

    if ([string]::IsNullOrWhiteSpace($trim)) { continue }
    if ($trim -eq '---') {
        if (-not $seenFirstSeparator) { Append-PageBreak; $seenFirstSeparator = $true }
        continue
    }
    if ($trim.StartsWith('# ')) { Append-Paragraph $trim.Substring(2) 'Title'; continue }
    if ($trim.StartsWith('## 第二轮')) { Append-Paragraph $trim.Substring(3) 'Subtitle'; continue }
    if ($trim.StartsWith('#### ')) { Append-Paragraph $trim.Substring(5) 'Heading3'; continue }
    if ($trim.StartsWith('### ')) { Append-Paragraph $trim.Substring(4) 'Heading2'; continue }
    if ($trim.StartsWith('## ')) { Append-Paragraph $trim.Substring(3) 'Heading1'; continue }
    if ($trim.StartsWith('> ')) { Append-Paragraph $trim.Substring(2) 'Quote'; continue }
    if ($trim.StartsWith('推荐路线为：') -or $trim.StartsWith('本报告形成四项判断。') -or $trim.StartsWith('推荐采用') -or $trim.StartsWith('一句话收束：')) { Append-Paragraph $trim 'KeyPoint'; continue }
    if ($trim -match '^\d+\.\s+(.+)$') { Append-Paragraph $trim 'ListParagraph'; continue }
    if ($trim.StartsWith('- ')) { Append-Paragraph ('• ' + $trim.Substring(2)) 'ListParagraph'; continue }
    Append-Paragraph $trim 'Normal'
}

[void]$doc.Append('<w:sectPr><w:pgSz w:w="11906" w:h="16838"/><w:pgMar w:top="1440" w:right="1440" w:bottom="1440" w:left="1440" w:header="720" w:footer="720" w:gutter="0"/><w:cols w:space="720"/><w:docGrid w:type="lines" w:linePitch="360"/></w:sectPr>')
[void]$doc.Append('</w:body></w:document>')
$documentXml = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?><w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><w:body>' + $doc.ToString()

$stylesXml = @"
<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:styles xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
  <w:docDefaults>
    <w:rPrDefault><w:rPr><w:rFonts w:ascii="Microsoft YaHei" w:eastAsia="Microsoft YaHei" w:hAnsi="Microsoft YaHei"/><w:sz w:val="24"/><w:szCs w:val="24"/></w:rPr></w:rPrDefault>
    <w:pPrDefault><w:pPr><w:spacing w:after="160" w:line="360" w:lineRule="auto"/></w:pPr></w:pPrDefault>
  </w:docDefaults>
  <w:style w:type="paragraph" w:default="1" w:styleId="Normal"><w:name w:val="Normal"/><w:qFormat/><w:pPr><w:spacing w:after="160" w:line="360" w:lineRule="auto"/></w:pPr><w:rPr><w:sz w:val="24"/><w:szCs w:val="24"/></w:rPr></w:style>
  <w:style w:type="paragraph" w:styleId="Title"><w:name w:val="Title"/><w:basedOn w:val="Normal"/><w:next w:val="Subtitle"/><w:qFormat/><w:pPr><w:jc w:val="center"/><w:spacing w:before="2400" w:after="360"/></w:pPr><w:rPr><w:b/><w:color w:val="0B5394"/><w:sz w:val="64"/><w:szCs w:val="64"/></w:rPr></w:style>
  <w:style w:type="paragraph" w:styleId="Subtitle"><w:name w:val="Subtitle"/><w:basedOn w:val="Normal"/><w:next w:val="Normal"/><w:qFormat/><w:pPr><w:jc w:val="center"/><w:spacing w:before="120" w:after="720"/></w:pPr><w:rPr><w:b/><w:color w:val="2E75B6"/><w:sz w:val="32"/><w:szCs w:val="32"/></w:rPr></w:style>
  <w:style w:type="paragraph" w:styleId="Heading1"><w:name w:val="heading 1"/><w:basedOn w:val="Normal"/><w:next w:val="Normal"/><w:qFormat/><w:pPr><w:keepNext/><w:keepLines/><w:pBdr><w:bottom w:val="single" w:sz="12" w:space="6" w:color="0B5394"/></w:pBdr><w:spacing w:before="300" w:after="160"/><w:outlineLvl w:val="0"/></w:pPr><w:rPr><w:b/><w:color w:val="0B5394"/><w:sz w:val="40"/><w:szCs w:val="40"/></w:rPr></w:style>
  <w:style w:type="paragraph" w:styleId="Heading2"><w:name w:val="heading 2"/><w:basedOn w:val="Normal"/><w:next w:val="Normal"/><w:qFormat/><w:pPr><w:keepNext/><w:keepLines/><w:pBdr><w:left w:val="single" w:sz="18" w:space="6" w:color="2E75B6"/></w:pBdr><w:ind w:left="180"/><w:spacing w:before="300" w:after="140"/><w:outlineLvl w:val="1"/></w:pPr><w:rPr><w:b/><w:color w:val="2E75B6"/><w:sz w:val="30"/><w:szCs w:val="30"/></w:rPr></w:style>
  <w:style w:type="paragraph" w:styleId="Heading3"><w:name w:val="heading 3"/><w:basedOn w:val="Normal"/><w:next w:val="Normal"/><w:qFormat/><w:pPr><w:keepNext/><w:spacing w:before="240" w:after="100"/><w:outlineLvl w:val="2"/></w:pPr><w:rPr><w:b/><w:color w:val="404040"/><w:sz w:val="26"/><w:szCs w:val="26"/></w:rPr></w:style>
  <w:style w:type="paragraph" w:styleId="ListParagraph"><w:name w:val="List Paragraph"/><w:basedOn w:val="Normal"/><w:pPr><w:ind w:left="520" hanging="260"/><w:spacing w:after="80" w:line="340" w:lineRule="auto"/></w:pPr><w:rPr><w:sz w:val="24"/><w:szCs w:val="24"/></w:rPr></w:style>
  <w:style w:type="paragraph" w:styleId="Quote"><w:name w:val="Quote"/><w:basedOn w:val="Normal"/><w:pPr><w:pBdr><w:left w:val="single" w:sz="18" w:space="8" w:color="2E75B6"/></w:pBdr><w:shd w:val="clear" w:color="auto" w:fill="EAF3FB"/><w:ind w:left="280" w:right="200"/><w:spacing w:before="120" w:after="200"/></w:pPr><w:rPr><w:color w:val="1F4E79"/><w:sz w:val="22"/><w:szCs w:val="22"/></w:rPr></w:style>
  <w:style w:type="paragraph" w:styleId="KeyPoint"><w:name w:val="Key Point"/><w:basedOn w:val="Normal"/><w:pPr><w:pBdr><w:left w:val="single" w:sz="24" w:space="8" w:color="0B5394"/></w:pBdr><w:shd w:val="clear" w:color="auto" w:fill="D9EAF7"/><w:ind w:left="280" w:right="200"/><w:spacing w:before="160" w:after="220"/></w:pPr><w:rPr><w:b/><w:color w:val="1F4E79"/><w:sz w:val="24"/><w:szCs w:val="24"/></w:rPr></w:style>
  <w:style w:type="paragraph" w:styleId="Code"><w:name w:val="Code"/><w:basedOn w:val="Normal"/><w:pPr><w:shd w:val="clear" w:color="auto" w:fill="F5F5F5"/><w:spacing w:after="0" w:line="280" w:lineRule="auto"/></w:pPr><w:rPr><w:rFonts w:ascii="Consolas" w:eastAsia="Microsoft YaHei" w:hAnsi="Consolas"/><w:color w:val="333333"/><w:sz w:val="19"/><w:szCs w:val="19"/></w:rPr></w:style>
  <w:style w:type="paragraph" w:styleId="TableText"><w:name w:val="Table Text"/><w:basedOn w:val="Normal"/><w:pPr><w:spacing w:after="0" w:line="260" w:lineRule="auto"/></w:pPr><w:rPr><w:sz w:val="18"/><w:szCs w:val="18"/></w:rPr></w:style>
  <w:style w:type="paragraph" w:styleId="TableHeader"><w:name w:val="Table Header"/><w:basedOn w:val="TableText"/><w:pPr><w:jc w:val="center"/><w:spacing w:after="0" w:line="260" w:lineRule="auto"/></w:pPr><w:rPr><w:b/><w:color w:val="FFFFFF"/><w:sz w:val="18"/><w:szCs w:val="18"/></w:rPr></w:style>
  <w:style w:type="paragraph" w:styleId="Separator"><w:name w:val="Separator"/><w:basedOn w:val="Normal"/><w:pPr><w:jc w:val="center"/><w:spacing w:before="80" w:after="80"/></w:pPr><w:rPr><w:color w:val="999999"/></w:rPr></w:style>
  <w:style w:type="table" w:styleId="TableGrid"><w:name w:val="Table Grid"/><w:tblPr><w:tblBorders><w:top w:val="single" w:sz="4" w:color="D9E2F3"/><w:left w:val="single" w:sz="4" w:color="D9E2F3"/><w:bottom w:val="single" w:sz="4" w:color="D9E2F3"/><w:right w:val="single" w:sz="4" w:color="D9E2F3"/><w:insideH w:val="single" w:sz="4" w:color="D9E2F3"/><w:insideV w:val="single" w:sz="4" w:color="D9E2F3"/></w:tblBorders></w:tblPr></w:style>
</w:styles>
"@

$contentTypes = @"
<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="xml" ContentType="application/xml"/>
  <Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>
  <Override PartName="/word/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml"/>
  <Override PartName="/docProps/core.xml" ContentType="application/vnd.openxmlformats-package.core-properties+xml"/>
</Types>
"@
$rootRels = @"
<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>
  <Relationship Id="rId2" Type="http://schemas.openxmlformats.org/package/2006/relationships/metadata/core-properties" Target="docProps/core.xml"/>
</Relationships>
"@
$docRels = @"
<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>
</Relationships>
"@
$coreXml = @"
<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<cp:coreProperties xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties" xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:dcterms="http://purl.org/dc/terms/" xmlns:dcmitype="http://purl.org/dc/dcmitype/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
  <dc:title>面向油浸式电力变压器故障根因分析的知识增强大模型调研报告（第二轮）</dc:title>
  <dc:creator>田雨翔、熊伯睿</dc:creator>
  <dc:subject>考题八技术向调研报告</dc:subject>
  <dcterms:created xsi:type="dcterms:W3CDTF">2026-09-25T00:00:00Z</dcterms:created>
  <dcterms:modified xsi:type="dcterms:W3CDTF">2026-09-25T00:00:00Z</dcterms:modified>
</cp:coreProperties>
"@

if (Test-Path -LiteralPath $outputPath) { Remove-Item -LiteralPath $outputPath -Force }
$zip = [IO.Compression.ZipFile]::Open($outputPath, [IO.Compression.ZipArchiveMode]::Create)
function Add-ZipText([string]$entryName, [string]$content) {
    $entry = $zip.CreateEntry($entryName, [IO.Compression.CompressionLevel]::Optimal)
    $writer = [IO.StreamWriter]::new($entry.Open(), $utf8)
    try { $writer.Write($content) } finally { $writer.Dispose() }
}
Add-ZipText '[Content_Types].xml' $contentTypes
Add-ZipText '_rels/.rels' $rootRels
Add-ZipText 'word/document.xml' $documentXml
Add-ZipText 'word/styles.xml' $stylesXml
Add-ZipText 'word/_rels/document.xml.rels' $docRels
Add-ZipText 'docProps/core.xml' $coreXml
$zip.Dispose()
Write-Output $outputPath