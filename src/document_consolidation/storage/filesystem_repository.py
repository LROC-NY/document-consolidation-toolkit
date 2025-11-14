"""File system implementation of document repository.

Concrete implementation using local file system operations.
"""

import hashlib
from pathlib import Path
from typing import Dict, List

from document_consolidation.config import get_logger
from document_consolidation.models.document import DocumentMetadata
from document_consolidation.storage.document_repository import DocumentRepository

logger = get_logger(__name__)


class FileSystemRepository(DocumentRepository):
    """File system-based document storage implementation."""

    def __init__(self, encoding: str = "utf-8"):
        """Initialize repository.

        Args:
            encoding: File encoding (default: utf-8)
        """
        self.encoding = encoding

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
        if not base_path.exists():
            logger.error("Base path not found", extra={"path": str(base_path)})
            raise FileNotFoundError(f"Base path not found: {base_path}")

        if not base_path.is_dir():
            logger.error("Path is not a directory", extra={"path": str(base_path)})
            raise ValueError(f"Path is not a directory: {base_path}")

        documents: List[DocumentMetadata] = []

        try:
            for filepath in base_path.glob(pattern):
                if filepath.is_file():
                    try:
                        content = self.read_document(filepath)
                        line_count = content.count("\n") + 1
                        modified_time = filepath.stat().st_mtime

                        # Calculate content hash
                        content_hash = hashlib.sha256(
                            content.encode(self.encoding)
                        ).hexdigest()

                        documents.append(
                            DocumentMetadata(
                                path=filepath,
                                folder=base_path.name,
                                content=content,
                                line_count=line_count,
                                modified_time=modified_time,
                                hash=content_hash,
                            )
                        )

                        logger.debug(
                            "Found document",
                            extra={
                                "path": str(filepath),
                                "lines": line_count,
                                "size": len(content),
                            },
                        )

                    except Exception as e:
                        logger.warning(
                            "Failed to read document",
                            extra={"path": str(filepath), "error": str(e)},
                        )
                        continue

        except PermissionError as e:
            logger.error(
                "Permission denied accessing directory",
                extra={"path": str(base_path), "error": str(e)},
            )
            raise

        logger.info(
            "Document search complete",
            extra={"path": str(base_path), "found": len(documents)},
        )

        return documents

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
        if not filepath.exists():
            logger.error("Document not found", extra={"path": str(filepath)})
            raise FileNotFoundError(f"Document not found: {filepath}")

        try:
            with open(filepath, "r", encoding=self.encoding) as f:
                content = f.read()

            logger.debug(
                "Document read successfully",
                extra={"path": str(filepath), "size": len(content)},
            )

            return content

        except UnicodeDecodeError as e:
            logger.error(
                "Invalid file encoding",
                extra={"path": str(filepath), "encoding": self.encoding, "error": str(e)},
            )
            raise

        except PermissionError as e:
            logger.error(
                "Permission denied reading file",
                extra={"path": str(filepath), "error": str(e)},
            )
            raise

    def write_document(self, filepath: Path, content: str) -> None:
        """Write document content to file.

        Args:
            filepath: Path to output file
            content: Document content to write

        Raises:
            PermissionError: If file is not writable
            OSError: If directory does not exist
        """
        # Ensure parent directory exists
        filepath.parent.mkdir(parents=True, exist_ok=True)

        try:
            with open(filepath, "w", encoding=self.encoding) as f:
                f.write(content)

            logger.info(
                "Document written successfully",
                extra={"path": str(filepath), "size": len(content)},
            )

        except PermissionError as e:
            logger.error(
                "Permission denied writing file",
                extra={"path": str(filepath), "error": str(e)},
            )
            raise

        except OSError as e:
            logger.error(
                "OS error writing file",
                extra={"path": str(filepath), "error": str(e)},
            )
            raise

    def document_exists(self, filepath: Path) -> bool:
        """Check if document exists.

        Args:
            filepath: Path to check

        Returns:
            True if document exists, False otherwise
        """
        exists = filepath.exists() and filepath.is_file()

        logger.debug(
            "Document existence check",
            extra={"path": str(filepath), "exists": exists},
        )

        return exists

    def get_document_stats(self, filepath: Path) -> Dict[str, any]:
        """Get document statistics.

        Args:
            filepath: Path to document

        Returns:
            Dictionary with stats (size, modified_time, etc.)

        Raises:
            FileNotFoundError: If file does not exist
        """
        if not filepath.exists():
            logger.error("Document not found for stats", extra={"path": str(filepath)})
            raise FileNotFoundError(f"Document not found: {filepath}")

        try:
            stat = filepath.stat()
            stats = {
                "size": stat.st_size,
                "modified_time": stat.st_mtime,
                "created_time": stat.st_ctime,
                "is_file": filepath.is_file(),
                "is_dir": filepath.is_dir(),
            }

            logger.debug("Retrieved document stats", extra={"path": str(filepath)})

            return stats

        except OSError as e:
            logger.error(
                "Failed to get document stats",
                extra={"path": str(filepath), "error": str(e)},
            )
            raise

    def create_directory(self, dirpath: Path) -> None:
        """Create directory if it doesn't exist.

        Args:
            dirpath: Directory path to create

        Raises:
            PermissionError: If directory cannot be created
        """
        try:
            dirpath.mkdir(parents=True, exist_ok=True)

            logger.info("Directory created", extra={"path": str(dirpath)})

        except PermissionError as e:
            logger.error(
                "Permission denied creating directory",
                extra={"path": str(dirpath), "error": str(e)},
            )
            raise

        except OSError as e:
            logger.error(
                "OS error creating directory",
                extra={"path": str(dirpath), "error": str(e)},
            )
            raise

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
        if not base_path.exists():
            logger.error("Base path not found", extra={"path": str(base_path)})
            raise FileNotFoundError(f"Base path not found: {base_path}")

        if not base_path.is_dir():
            logger.error("Path is not a directory", extra={"path": str(base_path)})
            raise ValueError(f"Path is not a directory: {base_path}")

        try:
            folders = [
                item.name for item in base_path.iterdir() if item.is_dir()
            ]

            logger.info(
                "Listed folders",
                extra={"path": str(base_path), "count": len(folders)},
            )

            return folders

        except PermissionError as e:
            logger.error(
                "Permission denied listing folders",
                extra={"path": str(base_path), "error": str(e)},
            )
            raise
