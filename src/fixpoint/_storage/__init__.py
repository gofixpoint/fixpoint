"""
This module contains the storage protocol and the implementation for the Supabase storage backend.
"""

from .protocol import SupportsStorage
from .supabase import SupabaseStorage

__all__ = ["SupportsStorage", "SupabaseStorage"]
