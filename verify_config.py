#!/usr/bin/env python3
"""Verify Phase 1 configuration system implementation.

This script validates that the configuration system is properly implemented
and can be imported and used by the core modules.

Run with: python3 verify_config.py
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))


def test_imports():
    """Test that all config modules can be imported."""
    print("=" * 70)
    print("PHASE 1 VERIFICATION: Configuration System")
    print("=" * 70)
    print()

    print("1. Testing imports...")
    try:
        from document_consolidation.config import (
            Settings,
            TournamentSettings,
            IntegrationSettings,
            VerificationSettings,
            load_settings,
            get_settings,
            reset_settings,
            settings,
            setup_logging,
            get_logger,
        )
        print("   ✓ All imports successful")
        return True
    except ImportError as e:
        print(f"   ✗ Import failed: {e}")
        return False


def test_settings_creation():
    """Test settings object creation."""
    print("\n2. Testing settings creation...")
    try:
        from document_consolidation.config import Settings, TournamentSettings

        # Test default creation
        s = Settings()
        print(f"   ✓ Default settings created")
        print(f"     - Input directory: {s.input_directory}")
        print(f"     - Source folders: {len(s.source_folders)} folders")
        print(f"     - Log level: {s.log_level}")

        # Test custom creation
        s = Settings(
            tournament=TournamentSettings(
                completeness_weight=8.0,
                recency_weight=9.0,
            )
        )
        print(f"   ✓ Custom settings created")
        print(f"     - Completeness weight: {s.tournament.completeness_weight}")
        print(f"     - Recency weight: {s.tournament.recency_weight}")

        return True
    except Exception as e:
        print(f"   ✗ Settings creation failed: {e}")
        return False


def test_validation():
    """Test settings validation."""
    print("\n3. Testing validation...")
    try:
        from document_consolidation.config import TournamentSettings

        # Test valid values
        s = TournamentSettings(completeness_weight=10.0)
        print(f"   ✓ Valid weight accepted: {s.completeness_weight}")

        # Test invalid values
        try:
            s = TournamentSettings(completeness_weight=15.0)
            print(f"   ✗ Invalid weight should have been rejected")
            return False
        except ValueError as e:
            print(f"   ✓ Invalid weight rejected: {str(e)[:60]}...")

        return True
    except Exception as e:
        print(f"   ✗ Validation test failed: {e}")
        return False


def test_nested_settings():
    """Test nested settings access."""
    print("\n4. Testing nested settings...")
    try:
        from document_consolidation.config import Settings

        s = Settings()

        # Access nested settings
        total_weight = s.tournament.total_weight
        output_dir = s.integration.output_dir
        max_blanks = s.verification.max_consecutive_blank_lines

        print(f"   ✓ Tournament total weight: {total_weight}")
        print(f"   ✓ Integration output dir: {output_dir}")
        print(f"   ✓ Verification max blanks: {max_blanks}")

        return True
    except Exception as e:
        print(f"   ✗ Nested settings access failed: {e}")
        return False


def test_logger():
    """Test logger creation."""
    print("\n5. Testing logger...")
    try:
        from document_consolidation.config import get_logger

        logger = get_logger(__name__)
        print(f"   ✓ Logger created: {logger.name}")
        print(f"   ✓ Logger level: {logger.level}")

        return True
    except Exception as e:
        print(f"   ✗ Logger creation failed: {e}")
        return False


def test_integration_with_core():
    """Test that config integrates with core modules."""
    print("\n6. Testing integration with core modules...")
    try:
        # Import tournament module which uses config
        from document_consolidation.core import tournament

        print(f"   ✓ Tournament module imports config successfully")

        # Check that it can access settings
        from document_consolidation.config import settings
        print(f"   ✓ Settings accessible: input_dir={settings.input_directory.name}")

        return True
    except ImportError as e:
        print(f"   ✗ Core module integration failed: {e}")
        return False


def main():
    """Run all verification tests."""
    tests = [
        test_imports,
        test_settings_creation,
        test_validation,
        test_nested_settings,
        test_logger,
        test_integration_with_core,
    ]

    results = [test() for test in tests]

    print("\n" + "=" * 70)
    print("VERIFICATION SUMMARY")
    print("=" * 70)

    passed = sum(results)
    total = len(results)

    print(f"Tests passed: {passed}/{total}")

    if passed == total:
        print("\n✓ Phase 1 Configuration System: COMPLETE")
        print("\nThe configuration system is fully implemented and ready to use.")
        print("\nNext steps:")
        print("  1. Install dependencies: pip install pydantic pyyaml")
        print("  2. Run tests: pytest tests/integration/test_configuration.py")
        print("  3. Create config.yaml from config.example.yaml")
        print("  4. Proceed to Phase 2 (Core engine implementation)")
        return 0
    else:
        print(f"\n✗ {total - passed} test(s) failed")
        print("\nPlease review the errors above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
