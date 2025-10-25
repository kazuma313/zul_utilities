"""
Zul - CLI tool untuk membuat template proyek dan utilities
"""
__version__ = "0.1.0"

# Export utilities agar bisa diimport langsung
from zul.utilities import milvus_helper

__all__ = ["milvus_helper"]
