"""Tests for configuration management."""

import os
from unittest.mock import patch

import pytest
from pydantic import ValidationError

from company_research_agent.core.config import EDINETConfig


class TestEDINETConfig:
    """Tests for EDINETConfig class."""

    def test_direct_initialization(self) -> None:
        """EDINETConfig should accept direct parameter values."""
        config = EDINETConfig(
            api_key="test-key-123",
            base_url="https://test.api.example.com",
            timeout_list=60,
            timeout_download=120,
        )
        assert config.api_key == "test-key-123"
        assert config.base_url == "https://test.api.example.com"
        assert config.timeout_list == 60
        assert config.timeout_download == 120

    def test_default_values(self) -> None:
        """EDINETConfig should have correct default values."""
        config = EDINETConfig(api_key="test-key")
        assert config.base_url == "https://api.edinet-fsa.go.jp/api/v2"
        assert config.timeout_list == 30
        assert config.timeout_download == 60

    def test_api_key_required(self) -> None:
        """EDINETConfig should require api_key."""
        with pytest.raises(ValidationError) as exc_info:
            EDINETConfig()  # type: ignore[call-arg]

        errors = exc_info.value.errors()
        assert any(
            error["loc"] == ("api_key",) or error["loc"] == ("EDINET_API_KEY",) for error in errors
        )

    def test_from_environment_variable(self) -> None:
        """EDINETConfig should read api_key from EDINET_API_KEY env var."""
        with patch.dict(os.environ, {"EDINET_API_KEY": "env-api-key"}):
            config = EDINETConfig()
            assert config.api_key == "env-api-key"

    def test_direct_value_over_env_var(self) -> None:
        """Direct api_key should override environment variable."""
        with patch.dict(os.environ, {"EDINET_API_KEY": "env-api-key"}):
            config = EDINETConfig(api_key="direct-api-key")
            assert config.api_key == "direct-api-key"

    def test_timeout_values_positive(self) -> None:
        """Timeout values should be positive integers."""
        config = EDINETConfig(
            api_key="test-key",
            timeout_list=1,
            timeout_download=1,
        )
        assert config.timeout_list == 1
        assert config.timeout_download == 1

    def test_base_url_can_be_customized(self) -> None:
        """base_url should be customizable for testing or staging."""
        config = EDINETConfig(
            api_key="test-key",
            base_url="http://localhost:8080/api/v2",
        )
        assert config.base_url == "http://localhost:8080/api/v2"

    def test_model_config_extra_ignore(self) -> None:
        """EDINETConfig should ignore extra fields."""
        # This tests that extra="ignore" is set in model_config
        config = EDINETConfig(
            api_key="test-key",
            unknown_field="should be ignored",  # type: ignore[call-arg]
        )
        assert config.api_key == "test-key"
        assert not hasattr(config, "unknown_field")
