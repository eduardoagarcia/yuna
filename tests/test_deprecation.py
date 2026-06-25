"""Tests for deprecation utilities."""

import warnings

import pytest

from yuna.deprecation import (
    DeprecationConfig,
    DeprecationError,
    DeprecationLevel,
    deprecated,
    deprecation_warning,
    get_deprecation_config,
)


def test_deprecation_config_creation() -> None:
    """Test deprecation config creation."""
    config = DeprecationConfig()

    assert config.enabled is True
    assert config.warnings_as_errors is False
    assert len(config._warned) == 0


def test_deprecation_config_should_warn_first_time() -> None:
    """Test should_warn returns True on first call."""
    config = DeprecationConfig()

    assert config.should_warn(identifier="test.function") is True


def test_deprecation_config_should_warn_second_time() -> None:
    """Test should_warn returns False on second call."""
    config = DeprecationConfig()
    config.should_warn(identifier="test.function")

    assert config.should_warn(identifier="test.function") is False


def test_deprecation_config_should_warn_disabled() -> None:
    """Test should_warn returns False when disabled."""
    config = DeprecationConfig()
    config.enabled = False

    assert config.should_warn(identifier="test.function") is False


def test_deprecation_config_reset() -> None:
    """Test reset clears warning tracking."""
    config = DeprecationConfig()
    config.should_warn(identifier="test.function")

    config.reset()

    assert config.should_warn(identifier="test.function") is True


def test_get_deprecation_config() -> None:
    """Test get_deprecation_config returns global config."""
    config1 = get_deprecation_config()
    config2 = get_deprecation_config()

    assert config1 is config2


def test_deprecation_warning_emits_warning() -> None:
    """Test deprecation_warning emits warning."""
    config = get_deprecation_config()
    config.reset()

    with warnings.catch_warnings(record=True) as warning_list:
        warnings.simplefilter(action="always")
        deprecation_warning(
            message="Function is deprecated",
            deprecated_in="3.1.0",
        )

    assert len(warning_list) == 1
    assert issubclass(warning_list[0].category, DeprecationWarning)
    assert "Function is deprecated" in str(warning_list[0].message)
    assert "deprecated in 3.1.0" in str(warning_list[0].message)


def test_deprecation_warning_with_removed_in() -> None:
    """Test deprecation_warning includes removal version."""
    config = get_deprecation_config()
    config.reset()

    with warnings.catch_warnings(record=True) as warning_list:
        warnings.simplefilter(action="always")
        deprecation_warning(
            message="Function is deprecated",
            deprecated_in="3.1.0",
            removed_in="4.0.0",
        )

    assert len(warning_list) == 1
    assert "will be removed in 4.0.0" in str(warning_list[0].message)


def test_deprecation_warning_with_migration_guide() -> None:
    """Test deprecation_warning includes migration guide."""
    config = get_deprecation_config()
    config.reset()

    with warnings.catch_warnings(record=True) as warning_list:
        warnings.simplefilter(action="always")
        deprecation_warning(
            message="Function is deprecated",
            deprecated_in="3.1.0",
            migration_guide="Use new_function() instead",
        )

    assert len(warning_list) == 1
    assert "Migration: Use new_function() instead" in str(warning_list[0].message)


def test_deprecation_warning_level_error() -> None:
    """Test deprecation_warning raises with ERROR level."""
    with pytest.raises(DeprecationError, match="Function is deprecated"):
        deprecation_warning(
            message="Function is deprecated",
            deprecated_in="3.1.0",
            level=DeprecationLevel.ERROR,
        )


def test_deprecation_warning_level_removed() -> None:
    """Test deprecation_warning raises with REMOVED level."""
    with pytest.raises(DeprecationError, match="Function is deprecated"):
        deprecation_warning(
            message="Function is deprecated",
            deprecated_in="3.1.0",
            level=DeprecationLevel.REMOVED,
        )


def test_deprecation_warning_warnings_as_errors() -> None:
    """Test deprecation_warning raises when warnings_as_errors enabled."""
    config = get_deprecation_config()
    config.warnings_as_errors = True
    config.reset()

    try:
        with pytest.raises(DeprecationError, match="Function is deprecated"):
            deprecation_warning(
                message="Function is deprecated",
                deprecated_in="3.1.0",
                level=DeprecationLevel.WARNING,
            )
    finally:
        config.warnings_as_errors = False


def test_deprecated_decorator_emits_warning() -> None:
    """Test deprecated decorator emits warning on first call."""
    config = get_deprecation_config()
    config.reset()

    @deprecated(deprecated_in="3.1.0")
    def old_function(x: int) -> int:
        return x * 2

    with warnings.catch_warnings(record=True) as warning_list:
        warnings.simplefilter(action="always")
        result = old_function(x=5)

    assert result == 10
    assert len(warning_list) == 1
    assert "old_function() is deprecated" in str(warning_list[0].message)


def test_deprecated_decorator_warns_once() -> None:
    """Test deprecated decorator warns only once."""
    config = get_deprecation_config()
    config.reset()

    @deprecated(deprecated_in="3.1.0")
    def old_function(x: int) -> int:
        return x * 2

    with warnings.catch_warnings(record=True) as warning_list:
        warnings.simplefilter(action="always")
        old_function(x=5)
        old_function(x=10)

    assert len(warning_list) == 1


def test_deprecated_decorator_with_reason() -> None:
    """Test deprecated decorator includes reason."""
    config = get_deprecation_config()
    config.reset()

    @deprecated(deprecated_in="3.1.0", reason="Use new_function() instead")
    def old_function(x: int) -> int:
        return x * 2

    with warnings.catch_warnings(record=True) as warning_list:
        warnings.simplefilter(action="always")
        old_function(x=5)

    assert len(warning_list) == 1
    assert "Use new_function() instead" in str(warning_list[0].message)


def test_deprecated_decorator_with_removed_in() -> None:
    """Test deprecated decorator includes removal version."""
    config = get_deprecation_config()
    config.reset()

    @deprecated(deprecated_in="3.1.0", removed_in="4.0.0")
    def old_function(x: int) -> int:
        return x * 2

    with warnings.catch_warnings(record=True) as warning_list:
        warnings.simplefilter(action="always")
        old_function(x=5)

    assert len(warning_list) == 1
    assert "will be removed in 4.0.0" in str(warning_list[0].message)


def test_deprecated_decorator_with_migration_guide() -> None:
    """Test deprecated decorator includes migration guide."""
    config = get_deprecation_config()
    config.reset()

    @deprecated(
        deprecated_in="3.1.0",
        migration_guide="Replace old_function(x) with new_function(x)",
    )
    def old_function(x: int) -> int:
        return x * 2

    with warnings.catch_warnings(record=True) as warning_list:
        warnings.simplefilter(action="always")
        old_function(x=5)

    assert len(warning_list) == 1
    assert "Replace old_function(x) with new_function(x)" in str(
        warning_list[0].message
    )


def test_deprecated_decorator_level_error() -> None:
    """Test deprecated decorator raises with ERROR level."""
    config = get_deprecation_config()
    config.reset()

    @deprecated(deprecated_in="3.1.0", level=DeprecationLevel.ERROR)
    def old_function(x: int) -> int:
        return x * 2

    with pytest.raises(DeprecationError, match="old_function\\(\\) is deprecated"):
        old_function(x=5)


def test_deprecated_decorator_level_removed() -> None:
    """Test deprecated decorator raises with REMOVED level."""
    config = get_deprecation_config()
    config.reset()

    @deprecated(deprecated_in="3.1.0", level=DeprecationLevel.REMOVED)
    def old_function(x: int) -> int:
        return x * 2

    with pytest.raises(DeprecationError, match="old_function\\(\\) is deprecated"):
        old_function(x=5)


def test_deprecated_decorator_preserves_function_name() -> None:
    """Test deprecated decorator preserves function name."""

    @deprecated(deprecated_in="3.1.0")
    def old_function(x: int) -> int:
        return x * 2

    assert old_function.__name__ == "old_function"


def test_deprecated_decorator_preserves_docstring() -> None:
    """Test deprecated decorator preserves docstring."""

    @deprecated(deprecated_in="3.1.0")
    def old_function(x: int) -> int:
        """Multiply x by 2."""
        return x * 2

    assert old_function.__doc__ == "Multiply x by 2."


def test_deprecated_decorator_when_disabled() -> None:
    """Test deprecated decorator does not warn when disabled."""
    config = get_deprecation_config()
    config.enabled = False
    config.reset()

    @deprecated(deprecated_in="3.1.0")
    def old_function(x: int) -> int:
        return x * 2

    try:
        with warnings.catch_warnings(record=True) as warning_list:
            warnings.simplefilter(action="always")
            result = old_function(x=5)

        assert result == 10
        assert len(warning_list) == 0
    finally:
        config.enabled = True


def test_deprecated_decorator_on_method() -> None:
    """Test deprecated decorator works on methods."""
    config = get_deprecation_config()
    config.reset()

    class MyClass:
        @deprecated(deprecated_in="3.1.0")
        def old_method(self, x: int) -> int:
            return x * 2

    instance = MyClass()

    with warnings.catch_warnings(record=True) as warning_list:
        warnings.simplefilter(action="always")
        result = instance.old_method(x=5)

    assert result == 10
    assert len(warning_list) == 1
    assert "old_method() is deprecated" in str(warning_list[0].message)


def test_multiple_deprecated_functions() -> None:
    """Test multiple deprecated functions track separately."""
    config = get_deprecation_config()
    config.reset()

    @deprecated(deprecated_in="3.1.0")
    def function_a(x: int) -> int:
        return x * 2

    @deprecated(deprecated_in="3.1.0")
    def function_b(x: int) -> int:
        return x * 3

    with warnings.catch_warnings(record=True) as warning_list:
        warnings.simplefilter(action="always")
        function_a(x=5)
        function_b(x=5)
        function_a(x=10)
        function_b(x=10)

    assert len(warning_list) == 2
