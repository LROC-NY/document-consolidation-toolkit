"""Entry point for python -m document_consolidation.

Allows the package to be run as a module:
    python -m document_consolidation [command] [options]

Example:
    python -m document_consolidation full --config config.yaml
    python -m document_consolidation tournament --verbose
    python -m document_consolidation --help
"""

from document_consolidation.cli import main

if __name__ == "__main__":
    main()
