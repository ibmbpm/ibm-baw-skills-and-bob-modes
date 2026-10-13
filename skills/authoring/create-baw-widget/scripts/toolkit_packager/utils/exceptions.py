"""
Custom exceptions for the BAW Toolkit Packager.
"""


class ToolkitPackagerError(Exception):
    """Base exception for all toolkit packager errors."""
    pass


class ConfigurationError(ToolkitPackagerError):
    """Raised when configuration is invalid or missing."""
    pass


class WidgetValidationError(ToolkitPackagerError):
    """Raised when widget validation fails."""
    
    def __init__(self, widget_name: str, errors: list):
        self.widget_name = widget_name
        self.errors = errors
        message = f"Widget '{widget_name}' validation failed:\n" + "\n".join(f"  - {e}" for e in errors)
        super().__init__(message)


class XMLGenerationError(ToolkitPackagerError):
    """Raised when XML generation fails."""
    pass


class PackagingError(ToolkitPackagerError):
    """Raised when TWX packaging fails."""
    pass


class FileNotFoundError(ToolkitPackagerError):
    """Raised when a required file is not found."""
    pass


class InvalidSchemaError(ToolkitPackagerError):
    """Raised when JSON schema is invalid."""
    pass

# Made with Bob
