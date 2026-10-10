"""
Widget validator for checking widget structure and files.
"""

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

from ..core import REQUIRED_WIDGET_FILES, OPTIONAL_WIDGET_FILES
from ..models import Widget
from ..utils import get_logger, WidgetValidationError

logger = get_logger(__name__)


@dataclass
class ValidationResult:
    """Result of widget validation."""
    widget_name: str
    is_valid: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    info: List[str] = field(default_factory=list)
    
    def add_error(self, message: str):
        """Add an error message."""
        self.errors.append(message)
        self.is_valid = False
    
    def add_warning(self, message: str):
        """Add a warning message."""
        self.warnings.append(message)
    
    def add_info(self, message: str):
        """Add an info message."""
        self.info.append(message)
    
    def has_errors(self) -> bool:
        """Check if validation has errors."""
        return len(self.errors) > 0
    
    def has_warnings(self) -> bool:
        """Check if validation has warnings."""
        return len(self.warnings) > 0
    
    def get_summary(self) -> str:
        """Get validation summary."""
        status = "✓ VALID" if self.is_valid else "✗ INVALID"
        parts = [f"{status}: {self.widget_name}"]
        
        if self.errors:
            parts.append(f"  Errors: {len(self.errors)}")
        if self.warnings:
            parts.append(f"  Warnings: {len(self.warnings)}")
        
        return " | ".join(parts)
    
    def __repr__(self) -> str:
        """String representation."""
        return self.get_summary()


def check_required_files(widget: Widget) -> List[str]:
    """
    Check if widget has all required files.
    
    Args:
        widget: Widget to check
        
    Returns:
        List of missing file names
    """
    missing = []
    
    for required_file in REQUIRED_WIDGET_FILES:
        if required_file not in widget.files:
            missing.append(required_file)
        elif not widget.files[required_file].exists():
            missing.append(f"{required_file} (path exists but file not found)")
    
    return missing


def check_json_schema(widget: Widget) -> Optional[str]:
    """
    Validate config.json file.
    
    Args:
        widget: Widget to check
        
    Returns:
        Error message if invalid, None if valid
    """
    try:
        config = widget.get_config()
        
        if not config:
            return "config.json not found or empty"
        
        # Validate required fields in config.json
        if 'name' not in config:
            return "config.json missing required 'name' field"
        
        if 'description' not in config:
            return "config.json missing required 'description' field"
        
        if 'bindingType' not in config:
            return "config.json missing required 'bindingType' field"
        
        if 'configOptions' not in config:
            return "config.json missing required 'configOptions' field"
        
        return None
        
    except FileNotFoundError:
        return "config.json file not found"
    except json.JSONDecodeError as e:
        return f"Invalid JSON in config.json: {str(e)}"
    except Exception as e:
        return f"Error reading config.json: {str(e)}"


def check_html_file(widget: Widget) -> Optional[str]:
    """
    Basic validation of HTML layout file.
    
    Args:
        widget: Widget to check
        
    Returns:
        Error message if invalid, None if valid
    """
    try:
        html = widget.get_layout_html()
        
        if not html or html.strip() == "":
            return "Layout.html is empty"
        
        # Basic HTML check - should have some tags
        if '<' not in html or '>' not in html:
            return "Layout.html does not appear to contain HTML"
        
        return None
        
    except FileNotFoundError:
        return "Layout.html not found"
    except Exception as e:
        return f"Error reading Layout.html: {str(e)}"


def check_css_file(widget: Widget) -> Optional[str]:
    """
    Basic validation of CSS file.
    
    Args:
        widget: Widget to check
        
    Returns:
        Error message if invalid, None if valid
    """
    try:
        css = widget.get_inline_css()
        
        # CSS can be empty, just check if readable
        if css is None:
            return "InlineCSS.css could not be read"
        
        return None
        
    except FileNotFoundError:
        return "InlineCSS.css not found"
    except Exception as e:
        return f"Error reading InlineCSS.css: {str(e)}"


def check_js_file(widget: Widget) -> Optional[str]:
    """
    Basic validation of JavaScript file.
    
    Args:
        widget: Widget to check
        
    Returns:
        Error message if invalid, None if valid
    """
    try:
        js = widget.get_inline_js()
        
        # JavaScript can be empty, just check if readable
        if js is None:
            return "inlineJavascript.js could not be read"
        
        return None
        
    except FileNotFoundError:
        return "inlineJavascript.js not found"
    except Exception as e:
        return f"Error reading inlineJavascript.js: {str(e)}"


def validate_widget(widget: Widget, strict: bool = False) -> ValidationResult:
    """
    Validate a widget's structure and files.
    
    Args:
        widget: Widget to validate
        strict: If True, warnings become errors
        
    Returns:
        ValidationResult with validation details
    """
    result = ValidationResult(widget_name=widget.name, is_valid=True)
    
    logger.debug(f"Validating widget: {widget.name}")
    
    # Check required files
    missing_files = check_required_files(widget)
    if missing_files:
        for missing in missing_files:
            result.add_error(f"Missing required file: {missing}")
    
    # Validate JSON schema
    json_error = check_json_schema(widget)
    if json_error:
        if strict:
            result.add_error(f"JSON schema error: {json_error}")
        else:
            result.add_warning(f"JSON schema issue: {json_error}")
    
    # Validate HTML
    html_error = check_html_file(widget)
    if html_error:
        result.add_error(f"HTML error: {html_error}")
    
    # Validate CSS
    css_error = check_css_file(widget)
    if css_error:
        result.add_error(f"CSS error: {css_error}")
    
    # Validate JavaScript
    js_error = check_js_file(widget)
    if js_error:
        result.add_error(f"JavaScript error: {js_error}")
    
    # Check for optional files
    for optional_file in OPTIONAL_WIDGET_FILES:
        if optional_file not in widget.files:
            result.add_info(f"Optional file not present: {optional_file}")
    
    # Check for preview files
    if not widget.has_preview_files():
        result.add_warning("No preview files found in AdvancePreview directory")
    else:
        result.add_info("Preview files found")
    
    # Log result
    if result.is_valid:
        logger.info(f"✓ Widget '{widget.name}' is valid")
    else:
        logger.warning(f"✗ Widget '{widget.name}' has validation errors")
        for error in result.errors:
            logger.warning(f"  - {error}")
    
    return result


def validate_widgets(widgets: List[Widget], strict: bool = False) -> List[ValidationResult]:
    """
    Validate multiple widgets.
    
    Args:
        widgets: List of widgets to validate
        strict: If True, warnings become errors
        
    Returns:
        List of ValidationResult objects
    """
    results = []
    
    logger.info(f"Validating {len(widgets)} widgets...")
    
    for widget in widgets:
        result = validate_widget(widget, strict)
        results.append(result)
    
    # Summary
    valid_count = sum(1 for r in results if r.is_valid)
    invalid_count = len(results) - valid_count
    
    logger.info(f"Validation complete: {valid_count} valid, {invalid_count} invalid")
    
    return results


def get_validation_summary(results: List[ValidationResult]) -> dict:
    """
    Get summary statistics from validation results.
    
    Args:
        results: List of validation results
        
    Returns:
        Dictionary with summary statistics
    """
    return {
        'total': len(results),
        'valid': sum(1 for r in results if r.is_valid),
        'invalid': sum(1 for r in results if not r.is_valid),
        'with_warnings': sum(1 for r in results if r.has_warnings()),
        'with_errors': sum(1 for r in results if r.has_errors()),
    }

# Made with Bob
