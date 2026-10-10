# Widget Testing Guide

This guide helps you test the Carbon-themed widgets in BAW Process Designer.

## Quick Start

1. **Open your Process App** in BAW Process Designer
2. **Create a new Coach** or open an existing one
3. **Add the widgets** you want to test from the palette
4. **Set up test data** using the script below

## Step-by-Step Instructions

### 1. Create Coach Variables

In your coach, create these variables (only create the ones for widgets you're testing):

| Variable Name | Type | Widget |
|--------------|------|--------|
| `breadcrumb` | BreadcrumbItem (List) | Breadcrumb |
| `dateoutput` | Date | DateOutput |
| `markdownviewer` | String | MarkdownViewer |
| `multiSelect` | String (List) | MultiSelect |
| `processcircle` | Integer | ProcessCircle |
| `progressbar` | ProgressData | ProgressBar |
| `tasksList` | String (List) | TasksList |
| `timeline` | TimelineEvent (List) | Timeline |

### 2. Add Widgets to Coach

Drag and drop the widgets from the palette onto your coach canvas.

### 3. Bind Variables to Widgets

For each widget:
1. Select the widget
2. Go to the **Data** tab
3. Bind the appropriate variable to the widget's data binding

### 4. Add Test Data Script

1. Click on the coach canvas (not on any widget)
2. Go to the **Behavior** section
3. Find the **Script** section
4. Copy the contents of [`test_widgets_sample_data.js`](../scripts/test_widgets_sample_data.js) and paste it into the Script field
5. Save your coach

### 5. Run and Test

1. Click **Run** to preview your coach
2. The widgets should now display with sample data
3. Test interactions and verify the Carbon theme styling

## Widget-Specific Test Data

### Breadcrumb
```javascript
tw.local.breadcrumb = [
    { "label": "Home", "status": "completed", "url": "#home" },
    { "label": "Products", "status": "current", "url": "#products" }
];
```

### DateOutput
```javascript
tw.local.dateoutput = new Date(); // Current date
```

### MarkdownViewer
```javascript
tw.local.markdownviewer = "# Title\n\nSome **bold** text.";
```

### MultiSelect
```javascript
// Selected values (data binding)
tw.local.multiSelect = [
    "life",
    "health",
    "disability"
];

// Available options (configuration option - set in widget properties)
tw.local.multiSelectOptions = {
    listAllItems: [
        {name: "Life Insurance", value: "life"},
        {name: "Health Insurance", value: "health"},
        {name: "Disability Insurance", value: "disability"},
        {name: "Auto Insurance", value: "auto"},
        {name: "Home Insurance", value: "home"},
        {name: "Travel Insurance", value: "travel"}
    ]
};
```

**Important:** In the MultiSelect widget's Configuration Options panel, bind the `options` property to `tw.local.multiSelectOptions`. The widget expects a list of objects with `name` and `value` properties (nameValuePair structure).

### ProcessCircle
```javascript
tw.local.processcircle = 75; // 75% complete
```

### ProgressBar
```javascript
tw.local.progressbar = {
    "percentage": 65,
    "status": "In Progress",
    "label": "Application Processing"
};
```

### TasksList
```javascript
tw.local.tasksList = [
    "Task 1",
    "Task 2",
    "Task 3"
];
```

### Timeline
```javascript
tw.local.timeline = [
    {
        "date": "2026-05-01",
        "title": "Event Title",
        "description": "Event description",
        "status": "completed",
        "metadata": "Additional info"
    }
];
```

## Carbon Theme Features to Test

### Colors
- **Primary Blue**: `#0f62fe` - Used for active states, links, primary actions
- **Success Green**: `#198038` - Used for completed states
- **Warning Yellow**: `#fdd13a` - Used for warning states
- **Error Red**: `#da1e28` - Used for error states

### Typography
- **Font Family**: IBM Plex Sans
- **Base Size**: 14px
- **Small Size**: 12px
- **Large Size**: 18px

### Interactive States
Test these interactions:
- ✅ Hover effects (should show subtle color changes)
- ✅ Click/active states
- ✅ Focus states (keyboard navigation)
- ✅ Disabled states

## Troubleshooting

### Widget Not Displaying
- Check that the variable is properly bound to the widget
- Verify the variable type matches the widget's expected type
- Check browser console for JavaScript errors

### Data Not Showing
- Ensure the script runs before the widgets render
- Check that variable names match exactly (case-sensitive)
- Verify the data structure matches the widget's expected format

### Styling Issues
- Clear browser cache
- Verify the toolkit was deployed successfully
- Check that you're using version 1.0.68 or later

## Testing Checklist

- [ ] Breadcrumb navigation works
- [ ] DateOutput displays correctly formatted date
- [ ] MarkdownViewer renders markdown properly
- [ ] MultiSelect allows selection
- [ ] ProcessCircle shows correct percentage
- [ ] ProgressBar displays with correct color based on percentage
- [ ] TasksList displays all items
- [ ] Timeline shows events in chronological order
- [ ] All widgets use Carbon theme colors
- [ ] All widgets use IBM Plex Sans font
- [ ] Hover states work correctly
- [ ] Responsive design works on mobile

## Next Steps

After testing:
1. Integrate widgets into your actual process flows
2. Connect to real business data
3. Customize widget options as needed
4. Add event handlers for user interactions

## Support

For issues or questions:
- Review [`CARBON_THEME_VARIABLES.md`](CARBON_THEME_VARIABLES.md)
- Examine widget README files in `widgets/[WidgetName]/README.md`

---
**Version**: 1.0.68  
**Last Updated**: 2026-05-06  
**Carbon Theme**: Fully integrated