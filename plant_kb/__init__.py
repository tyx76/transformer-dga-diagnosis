"""Pure retrieval-only knowledge backend."""
from .api import exact_lookup, list_domains, search, stats

__all__ = ["list_domains", "search", "exact_lookup", "stats"]