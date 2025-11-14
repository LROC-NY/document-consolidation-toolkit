"""Abstract repository interface for document storage operations.

Defines the contract for document storage implementations.
Supports dependency injection and testing with mock repositories.
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, List, Optional

from document_consolidation.models.document import DocumentMetadata


class DocumentRepository(ABC):
    """Abstract base class for document storage operations."""

    @abstractmethod
    def find_documents(
        self, base_path: Path, pattern: str = "*.md"
    ) -> List[DocumentMetadata]:
        """Find all documents matching pattern in base path.

        Args:
            base_path: Directory to search
            pattern: Glob pattern for files (default: *.md)

        Returns:
            List of DocumentMetadata objects

        Raises:
            FileNotFoundError: If base_path does not exist
            PermissionError: If base_path is not accessible
        """
        pass

    @abstractmethod
    def read_document(self, filepath: Path) -> str:
        """Read document content from file.

        Args:
            filepath: Path to document file

        Returns:
            Document content as string

        Raises:
            FileNotFoundError: If file does not exist
            PermissionError: If file is not readable
            UnicodeDecodeError: If file encoding is invalid
        """
        pass

    @abstractmethod
    def write_document(self, filepath: Path, content: str) -> None:
        """Write document content to file.

        Args:
            filepath: Path to output file
            content: Document content to write

        Raises:
            PermissionError: If file is not writable
            OSError: If directory does not exist
        """
        pass

    @abstractmethod
    def document_exists(self, filepath: Path) -> bool:
        """Check if document exists.

        Args:
            filepath: Path to check

        Returns:
            True if document exists, False otherwise
        """
        pass

    @abstractmethod
    def get_document_stats(self, filepath: Path) -> Dict[str, any]:
        """Get document statistics.

        Args:
            filepath: Path to document

        Returns:
            Dictionary with stats (size, modified_time, etc.)

        Raises:
            FileNotFoundError: If file does not exist
        """
        pass

    @abstractmethod
    def create_directory(self, dirpath: Path) -> None:
        """Create directory if it doesn't exist.

        Args:
            dirpath: Directory path to create

        Raises:
            PermissionError: If directory cannot be created
        """
        pass

    @abstractmethod
    def list_folders(self, base_path: Path) -> List[str]:
        """List all folders in base path.

        Args:
            base_path: Directory to list

        Returns:
            List of folder names

        Raises:
            FileNotFoundError: If base_path does not exist
            PermissionError: If base_path is not accessible
        """
        pass
