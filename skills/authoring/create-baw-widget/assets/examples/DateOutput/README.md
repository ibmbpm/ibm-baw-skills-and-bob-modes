# DateOutput Widget

An IBM Business Automation Workflow (BAW) custom view widget that displays date values in customizable string formats with visual styling based on date context (past, today, future).

## Overview

The DateOutput widget provides a flexible way to display dates in IBM BAW applications. It features:

- **Customizable date format** with token-based formatting (similar to moment.js)
- **Multiple input types** - accepts Date objects, ISO 8601 strings, or timestamps
- **Visual date context** - automatic color-coding for past, today, and future dates
- **Time support** - optional time display with configurable formats
- **Locale support** - prepared for internationalization
- **Clean styling** - modern, responsive design with hover effects

## Visual Representation

The widget displays as a styled text element with contextual coloring:

```
┌─────────────────────┐
│   12/22/2025        │  ← Formatted date string
└─────────────────────┘
```

### Color-Coded States

The widget automatically changes background color based on the date context:

| Date Context | Color | Background | Meaning |
|--------------|-------|------------|---------|
| Past dates   | 🟠 Orange | #fff3e0 | Dates before today |
| Today        | 🟢 Green  | #e8f5e9 | Current date |
| Future dates | 🔵 Blue   | #e3f2fd | Dates after today |

## Configuration Options

The widget accepts the following configuration options:

| Option | Type | Description | Default | Example |
|--------|------|-------------|---------|---------|
| `format` | String | Date format string using tokens | `"MM/DD/YYYY"` | `"DD/MM/YYYY"`, `"YYYY-MM-DD HH:mm"` |
| `locale` | String | Locale identifier (future enhancement) | `"en-US"` | `"en-GB"`, `"fr-FR"` |
| `showTime` | Boolean | Append time if not in format | `false` | `true` |
| `timeZone` | String | Time zone identifier (future enhancement) | `undefined` | `"America/New_York"` |

### Format Tokens

The `format` option supports the following tokens:

| Token | Description | Example Output |
|-------|-------------|----------------|
| `YYYY` | 4-digit year | 2025 |
| `YY` | 2-digit year | 25 |
| `MM` | 2-digit month (01-12) | 12 |
| `M` | Month without leading zero (1-12) | 12 |
| `DD` | 2-digit day (01-31) | 22 |
| `D` | Day without leading zero (1-31) | 22 |
| `HH` | 2-digit hours (00-23) | 14 |
| `H` | Hours without leading zero (0-23) | 14 |
| `mm` | 2-digit minutes (00-59) | 30 |
| `m` | Minutes without leading zero (0-59) | 30 |
| `ss` | 2-digit seconds (00-59) | 45 |
| `s` | Seconds without leading zero (0-59) | 45 |

## Business Data

### Input Data

- **Type**: Date object, ISO 8601 string, or timestamp (number)
- **Description**: The date value to be formatted and displayed
- **Examples**:
  - Date object: `new Date(2025, 11, 22)`
  - ISO string: `"2025-12-22T14:30:00Z"`
  - Timestamp: `1734876600000`

### Format Examples

| Format String | Input Date | Output |
|--------------|------------|--------|
| `"MM/DD/YYYY"` | 2025-12-22 | 12/22/2025 |
| `"DD/MM/YYYY"` | 2025-12-22 | 22/12/2025 |
| `"YYYY-MM-DD"` | 2025-12-22 | 2025-12-22 |
| `"D/M/YY"` | 2025-12-22 | 22/12/25 |
| `"MM/DD/YYYY HH:mm"` | 2025-12-22 14:30 | 12/22/2025 14:30 |
| `"DD-MM-YYYY HH:mm:ss"` | 2025-12-22 14:30:45 | 22-12-2025 14:30:45 |

## File Structure

```
DateOutput/
├── README.md                          # This file
├── widget/                            # Widget implementation files
│   ├── Layout.html                    # HTML structure and DOM elements
│   ├── InlineCSS.css                  # Styling and visual design
│   ├── inlineJavascript.js            # Initialization and formatting logic
│   ├── datamodel.md                   # Data model documentation
│   └── eventHandler.md                # Event handler documentation
└── AdvancePreview/                    # Preview mode implementation
    ├── DateOutput.html                # Preview styles
    └── DateOutputSnippet.js           # Preview generation logic
```

## Component Files

### Layout.html
Defines the HTML structure of the date output display:
```html
<div name="DateOutputContainer" class="date-output-container">
    <span name="DateOutputValue" class="date-output-value"></span>
</div>
```

### InlineCSS.css
Contains the styling for the widget:
- Base container styling with padding and borders
- Text styling for the date value
- Hover effects for interactivity
- Contextual color classes (past, today, future)

### inlineJavascript.js
Handles initialization and date formatting:
- Retrieves configuration options
- Formats date based on custom format string
- Determines date context (past/today/future)
- Updates DOM with formatted date and styling

### eventHandler.md
Documents the `change` event handler that updates the date display when the bound data changes.

### datamodel.md
Documents the business data structure and configuration options.

## Usage Examples

### Example 1: Basic Date Display

```javascript
// Business data: orderDate = new Date(2025, 11, 22)
// Configuration:
format: "MM/DD/YYYY"

// Result: Displays "12/22/2025"
```

### Example 2: European Date Format

```javascript
// Business data: deliveryDate = "2025-12-22"
// Configuration:
format: "DD/MM/YYYY"

// Result: Displays "22/12/2025"
```

### Example 3: Date with Time

```javascript
// Business data: appointmentTime = "2025-12-22T14:30:00Z"
// Configuration:
format: "MM/DD/YYYY HH:mm"

// Result: Displays "12/22/2025 14:30"
```

### Example 4: ISO Format

```javascript
// Business data: createdDate = new Date()
// Configuration:
format: "YYYY-MM-DD"

// Result: Displays "2025-12-22"
```

### Example 5: Compact Format

```javascript
// Business data: dueDate = 1734876600000
// Configuration:
format: "D/M/YY"

// Result: Displays "22/12/25"
```

### Example 6: Full Date and Time

```javascript
// Business data: timestamp = new Date()
// Configuration:
format: "DD-MM-YYYY HH:mm:ss"

// Result: Displays "22-12-2025 14:30:45"
```

## Technical Details

### Date Parsing

The widget accepts three types of date input:
1. **Date objects**: Native JavaScript Date instances
2. **ISO 8601 strings**: Standard date strings (e.g., "2025-12-22T14:30:00Z")
3. **Timestamps**: Numeric milliseconds since Unix epoch

All inputs are converted to Date objects for processing.

### Format Processing

The formatting engine:
1. Parses the input date into components (year, month, day, etc.)
2. Replaces format tokens with corresponding values
3. Applies zero-padding where specified (MM vs M, DD vs D, etc.)
4. Optionally appends time if `showTime` is enabled

### Date Context Detection

The widget determines date context by:
1. Normalizing both input date and current date to midnight (00:00:00)
2. Comparing timestamps to determine if date is past, today, or future
3. Applying appropriate CSS class for visual styling

### Error Handling

- Invalid dates display "Invalid Date"
- Null or undefined dates display empty string
- Malformed date strings are caught and handled gracefully

## Browser Compatibility

The widget uses standard JavaScript Date API and CSS3 features:
- ES5 JavaScript
- CSS3 for styling and transitions
- No external dependencies

**Recommended browsers**: Chrome 60+, Firefox 55+, Safari 11+, Edge 79+

## Integration with IBM BAW

This widget is designed to be used as a custom Coach View in IBM Business Automation Workflow. To integrate:

1. Import the widget into your Process App or Toolkit
2. Add it to a Coach or Coach View
3. Bind the business data to a Date variable or string
4. Configure the format option to match your desired output
5. The widget will automatically update when the bound data changes

## Styling Customization

You can customize the widget appearance by modifying the CSS classes:

- `.date-output-container`: Main container styling
- `.date-output-value`: Text styling
- `.date-past`: Past date styling
- `.date-today`: Today's date styling
- `.date-future`: Future date styling

## Future Enhancements

Planned features for future versions:
- Full locale support with Intl.DateTimeFormat
- Time zone conversion support
- Relative date display (e.g., "2 days ago", "in 3 hours")
- Custom date range validation
- Accessibility improvements with ARIA labels

## License

```
Licensed Materials - Property of IBM
5725-C95
(C) Copyright IBM Corporation
```

---

**Version**: 1.0  
**Last Updated**: 2025  
**IBM BAW Compatibility**: IBM Business Automation Workflow v18.0+