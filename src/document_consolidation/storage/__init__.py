"""Storage layer for document persistence."""

from document_consolidation.storage.document_repository import DocumentRepository
from document_consolidation.storage.filesystem_repository import FileSystemRepository

__all__ = [
    "DocumentRepository",
    "FileSystemRepository",
]
