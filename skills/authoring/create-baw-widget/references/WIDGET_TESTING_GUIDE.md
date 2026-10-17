# Widget testing guide

This guide helps you test the Carbon-themed widgets in BAW Process Designer.

## Quick start

1. Open your process app in BAW Process Designer.
2. Create a new coach or open an existing one.
3. Add the widgets you want to test from the palette.
4. Set up test data using the script in step 4 of the instructions.

## Step-by-step instructions

### 1. Create coach variables

In your coach, create these variables. Create only the variables for the widgets you are testing.

| Variable name | Type | Widget |
|--------------|------|--------|
| `breadcrumb` | BreadcrumbItem (List) | Breadcrumb |
| `dateoutput` | Date | DateOutput |
| `markdownviewer` | String | MarkdownViewer |
| `multiSelect` | String (List) | MultiSelect |
| `processcircle` | Integer | ProcessCircle |
| `progressbar` | ProgressData | ProgressBar |
| `tasksList` | String (List) | TasksList |
| `timeline` | TimelineEvent (List) | Timeline |

### 2. Add widgets to the coach

Drag the widgets from the palette onto your coach canvas.

### 3. Bind variables to widgets

For each widget:

1. Select the widget.
2. Go to the **Data** tab.
3. Bind the appropriate variable to the widget's data binding.

### 4. Add the test data script

Use this script in a test environment only. Remove it from the coach before you promote the process app to production.

1. Click the coach canvas (not any widget).
2. Go to the **Behavior** section.
3. Find the **Script** section.
4. Copy the contents of [`test_widgets_sample_data.js`](../scripts/test_widgets_sample_data.js) and paste them into the Script field.
5. Save your coach.

### 5. Run and test

1. Click **Run** to preview your coach.
2. Confirm that the widgets display the sample data.
3. Test interactions and verify the Carbon theme styling.

## Widget-specific test data

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

## Carbon theme features to test

### Colors

- **Primary blue**: `#0f62fe`. Active states, links, and primary actions use this color.
- **Success green**: `#198038`. Completed states use this color.
- **Warning yellow**: `#fdd13a`. Warning states use this color.
- **Error red**: `#da1e28`. Error states use this color.

### Typography

- **Font family**: IBM Plex Sans
- **Base size**: 14px
- **Small size**: 12px
- **Large size**: 18px

### Interactive states

Test these interactions:

- Hover effects (subtle color changes)
- Click and active states
- Focus states (keyboard navigation)
- Disabled states

## Troubleshooting

### Widget not displaying

- Check that you bound the variable to the widget.
- Verify that the variable type matches the type that the widget expects.
- Check the browser console for JavaScript errors.

### Data not showing

- Ensure the script runs before the widgets render.
- Check that variable names match exactly (names are case-sensitive).
- Verify that the data structure matches the format that the widget expects.

### Styling issues

- Clear the browser cache.
- Verify that the toolkit imported successfully.
- Check that you imported the latest packaged toolkit version.

## Testing checklist

- [ ] Breadcrumb navigation works
- [ ] DateOutput displays a correctly formatted date
- [ ] MarkdownViewer renders markdown properly
- [ ] MultiSelect allows selection
- [ ] ProcessCircle shows the correct percentage
- [ ] ProgressBar displays the correct color for the percentage
- [ ] TasksList displays all items
- [ ] Timeline shows events in chronological order
- [ ] All widgets use Carbon theme colors
- [ ] All widgets use the IBM Plex Sans font
- [ ] Hover states work correctly
- [ ] Responsive design works on mobile

## Next steps

After testing:

1. Integrate the widgets into your process flows.
2. Connect the widgets to real business data.
3. Customize widget options as needed.
4. Add event handlers for user interactions.

## Support

For issues or questions:

- Review [`CARBON_THEME_VARIABLES.md`](CARBON_THEME_VARIABLES.md).
- Review the `datamodel.md` file in each widget folder (`widgets/<WidgetName>/widget/datamodel.md`).
