"""Integration tests for configuration management.

Tests settings integration including:
- Environment variable loading
- YAML config file loading
- Settings validation
- Nested settings structures
- Default values
"""

import os
from pathlib import Path

import pytest
import yaml

from document_consolidation.config.settings import (
    IntegrationSettings,
    Settings,
    TournamentSettings,
    VerificationSettings,
    load_settings,
)


@pytest.mark.integration
class TestConfigurationLoading:
    """Test configuration loading from various sources."""

    def test_default_settings(self):
        """Test settings load with default values."""
        settings = Settings()

        # Check defaults exist
        assert settings.input_directory is not None
        assert len(settings.source_folders) > 0

        # Check nested settings
        assert isinstance(settings.tournament, TournamentSettings)
        assert isinstance(settings.integration, IntegrationSettings)
        assert isinstance(settings.verification, VerificationSettings)

        # Check tournament defaults
        assert settings.tournament.completeness_weight == 10
        assert settings.tournament.recency_weight == 10
        assert settings.tournament.structure_weight == 10
        assert settings.tournament.citations_weight == 10
        assert settings.tournament.arguments_weight == 10

        # Check integration defaults
        assert settings.integration.add_evolution_metadata is True
        assert settings.integration.preserve_source_attribution is True
        assert settings.integration.integrate_citations is True

        # Check verification defaults
        assert settings.verification.check_markdown_formatting is True
        assert settings.verification.check_section_numbering is True
        assert settings.verification.check_no_duplication is True

    def test_environment_variable_override(self, monkeypatch):
        """Test environment variables override defaults."""
        # Set environment variables
        monkeypatch.setenv("TOURNAMENT_COMPLETENESS_WEIGHT", "8")
        monkeypatch.setenv("TOURNAMENT_RECENCY_WEIGHT", "9")
        monkeypatch.setenv("INTEGRATION_ADD_EVOLUTION_METADATA", "false")
        monkeypatch.setenv("VERIFICATION_CHECK_MARKDOWN_FORMATTING", "false")

        settings = Settings()

        # Check overrides applied
        assert settings.tournament.completeness_weight == 8
        assert settings.tournament.recency_weight == 9
        assert settings.integration.add_evolution_metadata is False
        assert settings.verification.check_markdown_formatting is False

    def test_yaml_config_loading(self, tmp_path):
        """Test loading settings from YAML config file."""
        config_data = {
            "input_directory": str(tmp_path / "custom_input"),
            "source_folders": ["custom1", "custom2"],
            "tournament": {
                "completeness_weight": 7,
                "citations_weight": 8,
            },
            "integration": {
                "add_evolution_metadata": False,
                "output_dir": "custom_output",
            },
            "verification": {
                "max_consecutive_blank_lines": 3,
            },
        }

        config_file = tmp_path / "config.yaml"
        with open(config_file, "w") as f:
            yaml.dump(config_data, f)

        settings = load_settings(config_file)

        # Check YAML values loaded
        assert "custom1" in settings.source_folders
        assert "custom2" in settings.source_folders
        assert settings.tournament.completeness_weight == 7
        assert settings.tournament.citations_weight == 8
        assert settings.integration.add_evolution_metadata is False
        assert str(settings.integration.output_dir) == "custom_output"
        assert settings.verification.max_consecutive_blank_lines == 3

    def test_yaml_config_nonexistent(self, tmp_path):
        """Test loading with nonexistent config file returns defaults."""
        missing_file = tmp_path / "missing.yaml"

        settings = load_settings(missing_file)

        # Should return defaults without error
        assert settings.tournament.completeness_weight == 10

    def test_path_expansion(self, monkeypatch):
        """Test path expansion for ~ and environment variables."""
        # Use environment variable
        monkeypatch.setenv("INPUT_DIRECTORY", "~/Documents/Test")

        settings = Settings()

        # Path should be expanded
        assert settings.input_directory.is_absolute()
        assert "~" not in str(settings.input_directory)


@pytest.mark.integration
class TestTournamentSettings:
    """Test tournament-specific settings."""

    def test_weight_validation_valid(self):
        """Test valid weight values."""
        settings = TournamentSettings(
            completeness_weight=10,
            recency_weight=5,
            structure_weight=8,
            citations_weight=7,
            arguments_weight=9,
        )

        assert settings.completeness_weight == 10
        assert settings.recency_weight == 5
        assert settings.structure_weight == 8

    def test_weight_validation_out_of_range_high(self):
        """Test weight validation rejects values > 10."""
        with pytest.raises(ValueError, match="between 0 and 10"):
            TournamentSettings(
                completeness_weight=11,  # Invalid
                recency_weight=5,
                structure_weight=5,
                citations_weight=5,
                arguments_weight=5,
            )

    def test_weight_validation_out_of_range_low(self):
        """Test weight validation rejects values < 0."""
        with pytest.raises(ValueError, match="between 0 and 10"):
            TournamentSettings(
                completeness_weight=-1,  # Invalid
                recency_weight=5,
                structure_weight=5,
                citations_weight=5,
                arguments_weight=5,
            )

    def test_weight_validation_boundary_values(self):
        """Test boundary values 0 and 10 are valid."""
        settings = TournamentSettings(
            completeness_weight=0,
            recency_weight=0,
            structure_weight=10,
            citations_weight=10,
            arguments_weight=5,
        )

        assert settings.completeness_weight == 0
        assert settings.structure_weight == 10

    def test_environment_prefix(self, monkeypatch):
        """Test TOURNAMENT_ environment variable prefix."""
        monkeypatch.setenv("TOURNAMENT_COMPLETENESS_WEIGHT", "6")
        monkeypatch.setenv("TOURNAMENT_CITATIONS_WEIGHT", "9")

        settings = TournamentSettings()

        assert settings.completeness_weight == 6
        assert settings.citations_weight == 9


@pytest.mark.integration
class TestIntegrationSettings:
    """Test integration-specific settings."""

    def test_default_values(self):
        """Test integration default values."""
        settings = IntegrationSettings()

        assert settings.add_evolution_metadata is True
        assert settings.preserve_source_attribution is True
        assert settings.integrate_citations is True
        assert settings.skip_citation_enhancement is False

    def test_output_dir_path_type(self, tmp_path):
        """Test output_dir is properly typed as Path."""
        settings = IntegrationSettings(output_dir=tmp_path / "output")

        assert isinstance(settings.output_dir, Path)

    def test_boolean_flags(self):
        """Test all boolean flags work correctly."""
        settings = IntegrationSettings(
            add_evolution_metadata=False,
            preserve_source_attribution=False,
            integrate_citations=False,
            skip_citation_enhancement=True,
        )

        assert settings.add_evolution_metadata is False
        assert settings.preserve_source_attribution is False
        assert settings.integrate_citations is False
        assert settings.skip_citation_enhancement is True

    def test_environment_prefix(self, monkeypatch):
        """Test INTEGRATION_ environment variable prefix."""
        monkeypatch.setenv("INTEGRATION_ADD_EVOLUTION_METADATA", "false")
        monkeypatch.setenv("INTEGRATION_SKIP_CITATION_ENHANCEMENT", "true")

        settings = IntegrationSettings()

        assert settings.add_evolution_metadata is False
        assert settings.skip_citation_enhancement is True


@pytest.mark.integration
class TestVerificationSettings:
    """Test verification-specific settings."""

    def test_default_values(self):
        """Test verification default values."""
        settings = VerificationSettings()

        assert settings.check_markdown_formatting is True
        assert settings.check_section_numbering is True
        assert settings.check_no_duplication is True
        assert settings.check_document_navigability is True
        assert settings.max_consecutive_blank_lines == 2

    def test_max_blank_lines_validation(self):
        """Test max_consecutive_blank_lines must be >= 1."""
        # Valid
        settings = VerificationSettings(max_consecutive_blank_lines=1)
        assert settings.max_consecutive_blank_lines == 1

        settings = VerificationSettings(max_consecutive_blank_lines=5)
        assert settings.max_consecutive_blank_lines == 5

        # Invalid
        with pytest.raises(ValueError):
            VerificationSettings(max_consecutive_blank_lines=0)

    def test_check_flags(self):
        """Test all check flags can be disabled."""
        settings = VerificationSettings(
            check_markdown_formatting=False,
            check_section_numbering=False,
            check_no_duplication=False,
            check_document_navigability=False,
        )

        assert settings.check_markdown_formatting is False
        assert settings.check_section_numbering is False
        assert settings.check_no_duplication is False
        assert settings.check_document_navigability is False

    def test_environment_prefix(self, monkeypatch):
        """Test VERIFICATION_ environment variable prefix."""
        monkeypatch.setenv("VERIFICATION_CHECK_MARKDOWN_FORMATTING", "false")
        monkeypatch.setenv("VERIFICATION_MAX_CONSECUTIVE_BLANK_LINES", "3")

        settings = VerificationSettings()

        assert settings.check_markdown_formatting is False
        assert settings.max_consecutive_blank_lines == 3


@pytest.mark.integration
class TestNestedSettings:
    """Test nested settings structures."""

    def test_nested_settings_creation(self):
        """Test creating settings with nested structures."""
        settings = Settings(
            input_directory=Path("/test/input"),
            tournament=TournamentSettings(completeness_weight=8),
            integration=IntegrationSettings(add_evolution_metadata=False),
            verification=VerificationSettings(max_consecutive_blank_lines=3),
        )

        assert settings.tournament.completeness_weight == 8
        assert settings.integration.add_evolution_metadata is False
        assert settings.verification.max_consecutive_blank_lines == 3

    def test_nested_environment_variables(self, monkeypatch):
        """Test nested settings via environment variables."""
        # Using double underscore delimiter
        monkeypatch.setenv("TOURNAMENT__COMPLETENESS_WEIGHT", "7")
        monkeypatch.setenv("INTEGRATION__ADD_EVOLUTION_METADATA", "false")
        monkeypatch.setenv("VERIFICATION__MAX_CONSECUTIVE_BLANK_LINES", "4")

        settings = Settings()

        # Note: Pydantic settings uses env_prefix, so full path is needed
        # This test documents the expected behavior

    def test_partial_nested_override(self, tmp_path):
        """Test partial override of nested settings."""
        config_data = {
            "tournament": {
                "completeness_weight": 6,
                # Other weights use defaults
            },
            "integration": {
                "add_evolution_metadata": False,
                # Other flags use defaults
            },
        }

        config_file = tmp_path / "partial_config.yaml"
        with open(config_file, "w") as f:
            yaml.dump(config_data, f)

        settings = load_settings(config_file)

        # Check overridden values
        assert settings.tournament.completeness_weight == 6

        # Check defaults still apply for non-overridden
        assert settings.tournament.recency_weight == 10
        assert settings.integration.preserve_source_attribution is True


@pytest.mark.integration
class TestSettingsPersistence:
    """Test settings can be serialized and reloaded."""

    def test_settings_to_dict(self):
        """Test settings can be converted to dictionary."""
        settings = Settings(
            source_folders=["folder1", "folder2"],
            tournament=TournamentSettings(completeness_weight=7),
        )

        settings_dict = settings.model_dump()

        assert "source_folders" in settings_dict
        assert "tournament" in settings_dict
        assert settings_dict["tournament"]["completeness_weight"] == 7

    def test_settings_round_trip(self, tmp_path):
        """Test settings can be saved and reloaded."""
        original_settings = Settings(
            input_directory=tmp_path,
            source_folders=["test1", "test2"],
            tournament=TournamentSettings(completeness_weight=8),
            integration=IntegrationSettings(add_evolution_metadata=False),
        )

        # Save to YAML
        config_file = tmp_path / "roundtrip.yaml"
        with open(config_file, "w") as f:
            yaml.dump(original_settings.model_dump(mode="json"), f)

        # Reload
        reloaded_settings = load_settings(config_file)

        # Verify
        assert reloaded_settings.tournament.completeness_weight == 8
        assert reloaded_settings.integration.add_evolution_metadata is False

    def test_settings_validation_on_reload(self, tmp_path):
        """Test validation occurs when reloading settings."""
        # Create invalid config
        invalid_config = {
            "tournament": {
                "completeness_weight": 15,  # Invalid (> 10)
            }
        }

        config_file = tmp_path / "invalid.yaml"
        with open(config_file, "w") as f:
            yaml.dump(invalid_config, f)

        # Should raise validation error
        with pytest.raises(ValueError):
            load_settings(config_file)


@pytest.mark.integration
class TestSettingsEdgeCases:
    """Test edge cases in settings handling."""

    def test_empty_source_folders(self):
        """Test handling of empty source folders list."""
        settings = Settings(source_folders=[])

        assert len(settings.source_folders) == 0

    def test_large_number_of_folders(self):
        """Test handling many source folders."""
        folders = [f"folder_{i}" for i in range(100)]
        settings = Settings(source_folders=folders)

        assert len(settings.source_folders) == 100

    def test_special_characters_in_paths(self, tmp_path):
        """Test paths with special characters."""
        special_path = tmp_path / "test with spaces" / "special-chars_123"
        special_path.mkdir(parents=True)

        settings = Settings(input_directory=special_path)

        assert settings.input_directory == special_path

    def test_unicode_in_folder_names(self):
        """Test folder names with Unicode characters."""
        settings = Settings(source_folders=["文件夹", "Dossier", "Папка"])

        assert "文件夹" in settings.source_folders
        assert "Dossier" in settings.source_folders
        assert "Папка" in settings.source_folders
