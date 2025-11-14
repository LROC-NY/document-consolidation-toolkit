"""Document Consolidation Toolkit.

A production-ready document consolidation system using tournament-based ranking
to transform scattered document versions into comprehensive master documents.

Key Features:
- Tournament-based ranking with 5 evaluation criteria
- Intelligent content extraction and integration
- Multiple interfaces: CLI, REST API, Web UI
- Database support with SQLAlchemy
- Comprehensive testing and type safety

Example Usage:
    >>> from document_consolidation import DocumentTournament
    >>> tournament = DocumentTournament(input_dirs=["folder1", "folder2"])
    >>> results = tournament.run()
"""

__version__ = "0.1.0"
__author__ = "LROC"
__email__ = "lroc@callcabrera.com"

# Expose main classes at package level (will be implemented in Phase 2)
# from document_consolidation.core.tournament import DocumentTournament
# from document_consolidation.core.extractor import ContentExtractor
# from document_consolidation.core.integrator import Integrator
# from document_consolidation.core.verifier import DocumentVerifier

__all__ = [
    "__version__",
    "__author__",
    "__email__",
    # "DocumentTournament",
    # "ContentExtractor",
    # "Integrator",
    # "DocumentVerifier",
]
