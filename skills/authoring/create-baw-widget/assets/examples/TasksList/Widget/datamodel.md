## Business data

The widget expects an array of task items. Each item must be an object with the following structure:

```javascript
[
    {
        "label": "String",
        "status": "String"
    }
]
```

### Status values

The `status` field accepts the following values (case-sensitive):

- Complete: Task successfully completed (green badge with checkmark icon)
- Pending: Task waiting to start (gray badge with circle icon)
- Processing: Task currently in progress (blue badge with spinner icon)
- Failed: Task encountered an error (red badge with error icon)

### Example data

```javascript
[
    { "label": "Validate customer request", "status": "Complete" },
    { "label": "Approve budget allocation", "status": "Pending" },
    { "label": "Generate compliance report", "status": "Processing" },
    { "label": "Submit final documentation", "status": "Failed" }
]
```

### Visual presentation

The widget displays tasks in a table format with:
- Status icons in the first column for quick visual identification
- Task labels in the middle column with proper alignment
- Status badges in the right column with color-coded styling
- Hover effects for better interactivity
- Carbon Design System styling for consistency
