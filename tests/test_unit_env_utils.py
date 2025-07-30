"""Unit tests for environment utility functions."""

from unittest.mock import patch

import pytest

from app.exceptions.env_missing_exception import MissingEnvironmentVariableError
from app.exceptions.env_wrong_format import EnvironmentVariableFormatError
from app.utils.env_util import get_env, get_env_bool, get_env_int


class TestEnvUtils:
    """Unit tests for environment utility functions."""

    def test_get_env_with_existing_variable(self) -> None:
        """Test getting an environment variable that exists."""
        with patch("os.getenv") as mock_getenv:
            mock_getenv.return_value = "test_value"

            result = get_env("TEST_VAR")

            mock_getenv.assert_called_once_with("TEST_VAR")
            assert result == "test_value"

    def test_get_env_with_missing_variable_should_raise(self) -> None:
        """Test that get_env raises an error when variable is missing."""
        with patch("os.getenv") as mock_getenv:
            mock_getenv.return_value = None

            with pytest.raises(MissingEnvironmentVariableError):
                get_env("MISSING_VAR")

    def test_get_env_int_with_valid_integer(self) -> None:
        """Test getting an environment variable as integer with valid value."""
        with patch("os.getenv") as mock_getenv:
            mock_getenv.return_value = "42"

            result = get_env_int("TEST_INT_VAR")

            mock_getenv.assert_called_once_with("TEST_INT_VAR")
            assert result == 42
            assert isinstance(result, int)

    def test_get_env_int_with_invalid_string_should_raise_error(self) -> None:
        """Test that get_env_int raises EnvironmentVariableFormatError for non-integer values."""
        with patch("os.getenv") as mock_getenv:
            mock_getenv.return_value = "not_a_number"

            with pytest.raises(EnvironmentVariableFormatError):
                get_env_int("INVALID_INT_VAR")

    def test_get_env_int_with_float_string_should_raise_error(self) -> None:
        """Test that get_env_int raises EnvironmentVariableFormatError for float strings."""
        with patch("os.getenv") as mock_getenv:
            mock_getenv.return_value = "42.5"

            with pytest.raises(EnvironmentVariableFormatError):
                get_env_int("FLOAT_VAR")

    def test_get_env_bool_with_true_variants(self) -> None:
        """Test get_env_bool with true-equivalent strings."""
        true_values = ["true", "TRUE", "1", "yes", "YeS"]
        for val in true_values:
            with patch("os.getenv") as mock_getenv:
                mock_getenv.return_value = val
                result = get_env_bool("BOOL_VAR")
                assert result is True

    def test_get_env_bool_with_false_variants(self) -> None:
        """Test get_env_bool with false-equivalent strings."""
        false_values = ["false", "FALSE", "0", "no", "No"]
        for val in false_values:
            with patch("os.getenv") as mock_getenv:
                mock_getenv.return_value = val
                result = get_env_bool("BOOL_VAR")
                assert result is False

    def test_get_env_bool_with_invalid_value_should_raise_error(self) -> None:
        """Test that get_env_bool raises error on unexpected boolean value."""
        with patch("os.getenv") as mock_getenv:
            mock_getenv.return_value = "not_bool"

            with pytest.raises(EnvironmentVariableFormatError):
                get_env_bool("INVALID_BOOL_VAR")

    def test_get_env_bool_with_missing_value_should_raise_error(self) -> None:
        """Test that get_env_bool raises MissingEnvironmentVariableError if variable is not set."""
        with patch("os.getenv") as mock_getenv:
            mock_getenv.return_value = None

            with pytest.raises(MissingEnvironmentVariableError):
                get_env_bool("MISSING_BOOL_VAR")
