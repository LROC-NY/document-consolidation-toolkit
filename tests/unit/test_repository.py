"""Unit tests for FileSystemRepository.

Tests file system storage operations including:
- Finding documents
- Reading documents
- Writing documents
- Document existence checks
- Getting document stats
- Directory operations
"""

from pathlib import Path

import pytest

from document_consolidation.models.document import DocumentMetadata
from document_consolidation.storage.filesystem_repository import FileSystemRepository


class TestFileSystemRepository:
    """Test FileSystemRepository implementation."""

    def test_repository_initialization_default_encoding(self):
        """Test repository initializes with default encoding."""
        repo = FileSystemRepository()

        assert repo.encoding == "utf-8"

    def test_repository_initialization_custom_encoding(self):
        """Test repository initializes with custom encoding."""
        repo = FileSystemRepository(encoding="latin-1")

        assert repo.encoding == "latin-1"

    def test_find_documents_basic(self, tmp_path: Path):
        """Test finding documents in directory."""
        # Create test files
        (tmp_path / "doc1.md").write_text("# Document 1")
        (tmp_path / "doc2.md").write_text("# Document 2")
        (tmp_path / "readme.txt").write_text("Not markdown")

        repo = FileSystemRepository()
        documents = repo.find_documents(tmp_path, "*.md")

        assert len(documents) == 2
        assert all(isinstance(doc, DocumentMetadata) for doc in documents)
        assert all(doc.path.suffix == ".md" for doc in documents)

    def test_find_documents_with_metadata(self, tmp_path: Path):
        """Test found documents have correct metadata."""
        content = "# Test Document\n\nSome content here."
        filepath = tmp_path / "test.md"
        filepath.write_text(content)

        repo = FileSystemRepository()
        documents = repo.find_documents(tmp_path, "*.md")

        assert len(documents) == 1
        doc = documents[0]

        assert doc.path == filepath
        assert doc.folder == tmp_path.name
        assert doc.content == content
        assert doc.line_count == 3
        assert doc.modified_time > 0
        assert doc.hash is not None
        assert len(doc.hash) == 64  # SHA256 hash length

    def test_find_documents_empty_directory(self, tmp_path: Path):
        """Test finding documents in empty directory."""
        repo = FileSystemRepository()
        documents = repo.find_documents(tmp_path, "*.md")

        assert len(documents) == 0

    def test_find_documents_directory_not_found(self, tmp_path: Path):
        """Test finding documents raises when directory doesn't exist."""
        missing_path = tmp_path / "nonexistent"

        repo = FileSystemRepository()

        with pytest.raises(FileNotFoundError, match="Base path not found"):
            repo.find_documents(missing_path, "*.md")

    def test_find_documents_path_is_file(self, tmp_path: Path):
        """Test finding documents raises when path is a file."""
        filepath = tmp_path / "file.md"
        filepath.write_text("# File")

        repo = FileSystemRepository()

        with pytest.raises(ValueError, match="not a directory"):
            repo.find_documents(filepath, "*.md")

    def test_find_documents_pattern_matching(self, tmp_path: Path):
        """Test different glob patterns."""
        (tmp_path / "doc1.md").write_text("# Doc 1")
        (tmp_path / "doc2.md").write_text("# Doc 2")
        (tmp_path / "notes.txt").write_text("Notes")
        (tmp_path / "file.pdf").write_text("PDF")

        repo = FileSystemRepository()

        # Test *.md pattern
        md_docs = repo.find_documents(tmp_path, "*.md")
        assert len(md_docs) == 2

        # Test *.txt pattern
        txt_docs = repo.find_documents(tmp_path, "*.txt")
        assert len(txt_docs) == 1

        # Test * pattern (all files)
        all_docs = repo.find_documents(tmp_path, "*")
        assert len(all_docs) == 4

    def test_find_documents_skips_unreadable(self, tmp_path: Path):
        """Test finding documents skips files that can't be read."""
        # Create readable file
        (tmp_path / "readable.md").write_text("# Readable")

        # Create file with bad encoding
        bad_file = tmp_path / "bad.md"
        bad_file.write_bytes(b"\xff\xfe Invalid UTF-8")

        repo = FileSystemRepository()
        documents = repo.find_documents(tmp_path, "*.md")

        # Should only find the readable one
        assert len(documents) == 1
        assert documents[0].path.name == "readable.md"

    def test_read_document_success(self, tmp_path: Path):
        """Test reading document content."""
        content = "# Test Document\n\nThis is the content."
        filepath = tmp_path / "doc.md"
        filepath.write_text(content)

        repo = FileSystemRepository()
        read_content = repo.read_document(filepath)

        assert read_content == content

    def test_read_document_not_found(self, tmp_path: Path):
        """Test reading nonexistent document raises."""
        missing_path = tmp_path / "missing.md"

        repo = FileSystemRepository()

        with pytest.raises(FileNotFoundError, match="Document not found"):
            repo.read_document(missing_path)

    def test_read_document_invalid_encoding(self, tmp_path: Path):
        """Test reading document with invalid encoding raises."""
        filepath = tmp_path / "bad.md"
        filepath.write_bytes(b"\xff\xfe Invalid UTF-8")

        repo = FileSystemRepository()

        with pytest.raises(UnicodeDecodeError):
            repo.read_document(filepath)

    def test_write_document_success(self, tmp_path: Path):
        """Test writing document content."""
        content = "# New Document\n\nContent to write."
        filepath = tmp_path / "new.md"

        repo = FileSystemRepository()
        repo.write_document(filepath, content)

        assert filepath.exists()
        assert filepath.read_text() == content

    def test_write_document_creates_parent_directory(self, tmp_path: Path):
        """Test writing document creates parent directories."""
        content = "# Document"
        filepath = tmp_path / "subdir" / "nested" / "doc.md"

        repo = FileSystemRepository()
        repo.write_document(filepath, content)

        assert filepath.exists()
        assert filepath.read_text() == content
        assert filepath.parent.exists()

    def test_write_document_overwrites_existing(self, tmp_path: Path):
        """Test writing document overwrites existing file."""
        filepath = tmp_path / "doc.md"
        filepath.write_text("# Original")

        new_content = "# Updated Content"

        repo = FileSystemRepository()
        repo.write_document(filepath, new_content)

        assert filepath.read_text() == new_content

    def test_document_exists_true(self, tmp_path: Path):
        """Test document_exists returns True for existing file."""
        filepath = tmp_path / "doc.md"
        filepath.write_text("# Document")

        repo = FileSystemRepository()

        assert repo.document_exists(filepath) is True

    def test_document_exists_false(self, tmp_path: Path):
        """Test document_exists returns False for nonexistent file."""
        filepath = tmp_path / "missing.md"

        repo = FileSystemRepository()

        assert repo.document_exists(filepath) is False

    def test_document_exists_directory(self, tmp_path: Path):
        """Test document_exists returns False for directory."""
        dirpath = tmp_path / "directory"
        dirpath.mkdir()

        repo = FileSystemRepository()

        assert repo.document_exists(dirpath) is False

    def test_get_document_stats_success(self, tmp_path: Path):
        """Test getting document statistics."""
        content = "# Document\nContent"
        filepath = tmp_path / "doc.md"
        filepath.write_text(content)

        repo = FileSystemRepository()
        stats = repo.get_document_stats(filepath)

        assert "size" in stats
        assert "modified_time" in stats
        assert "created_time" in stats
        assert "is_file" in stats
        assert "is_dir" in stats

        assert stats["size"] > 0
        assert stats["modified_time"] > 0
        assert stats["is_file"] is True
        assert stats["is_dir"] is False

    def test_get_document_stats_not_found(self, tmp_path: Path):
        """Test getting stats for nonexistent document raises."""
        missing_path = tmp_path / "missing.md"

        repo = FileSystemRepository()

        with pytest.raises(FileNotFoundError, match="Document not found"):
            repo.get_document_stats(missing_path)

    def test_create_directory_success(self, tmp_path: Path):
        """Test creating directory."""
        dirpath = tmp_path / "new_directory"

        repo = FileSystemRepository()
        repo.create_directory(dirpath)

        assert dirpath.exists()
        assert dirpath.is_dir()

    def test_create_directory_nested(self, tmp_path: Path):
        """Test creating nested directories."""
        dirpath = tmp_path / "level1" / "level2" / "level3"

        repo = FileSystemRepository()
        repo.create_directory(dirpath)

        assert dirpath.exists()
        assert dirpath.is_dir()
        assert (tmp_path / "level1").exists()
        assert (tmp_path / "level1" / "level2").exists()

    def test_create_directory_already_exists(self, tmp_path: Path):
        """Test creating directory that already exists."""
        dirpath = tmp_path / "existing"
        dirpath.mkdir()

        repo = FileSystemRepository()
        repo.create_directory(dirpath)  # Should not raise

        assert dirpath.exists()

    def test_list_folders_success(self, tmp_path: Path):
        """Test listing folders in directory."""
        # Create folders and files
        (tmp_path / "folder1").mkdir()
        (tmp_path / "folder2").mkdir()
        (tmp_path / "folder3").mkdir()
        (tmp_path / "file.txt").write_text("Not a folder")

        repo = FileSystemRepository()
        folders = repo.list_folders(tmp_path)

        assert len(folders) == 3
        assert "folder1" in folders
        assert "folder2" in folders
        assert "folder3" in folders
        assert "file.txt" not in folders

    def test_list_folders_empty_directory(self, tmp_path: Path):
        """Test listing folders in empty directory."""
        repo = FileSystemRepository()
        folders = repo.list_folders(tmp_path)

        assert len(folders) == 0

    def test_list_folders_only_files(self, tmp_path: Path):
        """Test listing folders when directory only has files."""
        (tmp_path / "file1.txt").write_text("File 1")
        (tmp_path / "file2.txt").write_text("File 2")

        repo = FileSystemRepository()
        folders = repo.list_folders(tmp_path)

        assert len(folders) == 0

    def test_list_folders_not_found(self, tmp_path: Path):
        """Test listing folders raises when directory doesn't exist."""
        missing_path = tmp_path / "nonexistent"

        repo = FileSystemRepository()

        with pytest.raises(FileNotFoundError, match="Base path not found"):
            repo.list_folders(missing_path)

    def test_list_folders_path_is_file(self, tmp_path: Path):
        """Test listing folders raises when path is a file."""
        filepath = tmp_path / "file.txt"
        filepath.write_text("File")

        repo = FileSystemRepository()

        with pytest.raises(ValueError, match="not a directory"):
            repo.list_folders(filepath)

    def test_content_hash_consistency(self, tmp_path: Path):
        """Test content hash is consistent for same content."""
        content = "# Document\nSame content"
        filepath1 = tmp_path / "doc1.md"
        filepath2 = tmp_path / "doc2.md"

        filepath1.write_text(content)
        filepath2.write_text(content)

        repo = FileSystemRepository()
        docs = repo.find_documents(tmp_path, "*.md")

        assert len(docs) == 2
        # Same content should produce same hash
        assert docs[0].hash == docs[1].hash

    def test_content_hash_different_content(self, tmp_path: Path):
        """Test content hash differs for different content."""
        filepath1 = tmp_path / "doc1.md"
        filepath2 = tmp_path / "doc2.md"

        filepath1.write_text("# Document 1")
        filepath2.write_text("# Document 2")

        repo = FileSystemRepository()
        docs = repo.find_documents(tmp_path, "*.md")

        assert len(docs) == 2
        # Different content should produce different hashes
        assert docs[0].hash != docs[1].hash

    def test_line_count_calculation(self, tmp_path: Path):
        """Test line count is calculated correctly."""
        content = "Line 1\nLine 2\nLine 3\n"
        filepath = tmp_path / "doc.md"
        filepath.write_text(content)

        repo = FileSystemRepository()
        docs = repo.find_documents(tmp_path, "*.md")

        assert len(docs) == 1
        assert docs[0].line_count == 4  # 3 newlines + 1 = 4 lines

    def test_custom_encoding(self, tmp_path: Path):
        """Test repository works with custom encoding."""
        # Create file with Latin-1 encoding
        filepath = tmp_path / "latin1.txt"
        content = "Héllo Wörld"
        filepath.write_text(content, encoding="latin-1")

        repo = FileSystemRepository(encoding="latin-1")
        read_content = repo.read_document(filepath)

        assert read_content == content

    def test_unicode_content(self, tmp_path: Path):
        """Test repository handles Unicode content correctly."""
        content = "# Document\n\n中文测试\nEmoji: 🚀\nÄöüß"
        filepath = tmp_path / "unicode.md"
        filepath.write_text(content, encoding="utf-8")

        repo = FileSystemRepository()
        read_content = repo.read_document(filepath)

        assert read_content == content

    def test_large_file_handling(self, tmp_path: Path):
        """Test repository handles large files."""
        # Create large content (1000 lines)
        content = "\n".join([f"Line {i}" for i in range(1000)])
        filepath = tmp_path / "large.md"
        filepath.write_text(content)

        repo = FileSystemRepository()
        docs = repo.find_documents(tmp_path, "*.md")

        assert len(docs) == 1
        assert docs[0].line_count == 1000
        assert len(docs[0].content) > 5000  # Should be fairly large
