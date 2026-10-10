# Carbon Theme Variables Reference

This document provides a reference for using Carbon Design System theme variables in BAW Coach widgets.

## How to Use Carbon Theme Variables in Widgets

BAW Coach widgets use inline CSS that gets compiled with the Carbon.less theme file. To use theme variables:

1. Reference variables using LESS syntax: `@variable-name`
2. The variables will be resolved at compile time by BAW
3. Use comments to document which theme variables are being referenced

## Key Carbon Theme Variables

### Colors

#### Primary Colors
- `@bpm-color-primary: #0f62fe` - Primary blue color
- `@bpm-color-primary-light: #c9deff` - Light blue
- `@bpm-color-primary-dark: #0353E9` - Dark blue
- `@bpm-color-primary-darker: #061f80` - Darker blue

#### Semantic Colors
- `@bpm-color-success: #198038` - Success green
- `@bpm-color-success-light: #56d679` - Light green
- `@bpm-color-success-dark: #10642a` - Dark green

- `@bpm-color-warning: #fdd13a` - Warning yellow
- `@bpm-color-warning-light: #feeeb8` - Light yellow
- `@bpm-color-warning-dark: #cfa102` - Dark yellow

- `@bpm-color-alert: #da1e28` - Alert/Error red
- `@bpm-color-alert-light: #fcd0d3` - Light red
- `@bpm-color-alert-dark: #ba1b23` - Dark red

- `@bpm-color-info: #6ccaff` - Info blue
- `@bpm-color-info-light: #b3e6ff` - Light info blue
- `@bpm-color-info-dark: #0072c3` - Dark info blue

#### Neutral Colors
- `@bpm-neutral-darkest: #3d3d3d`
- `@bpm-neutral-darker: #171717`
- `@bpm-neutral-dark: #3c4646`
- `@bpm-neutral: #565656`
- `@bpm-neutral-light: #8c8c8c`
- `@bpm-neutral-lighter: #dcdcdc`
- `@bpm-neutral-lightest: #f3f3f3`

#### Text Colors
- `@bpm-text-color: #161616` - Primary text color (Carbon Gray 100)
- `@bpm-text-alternate-color: #fff` - Alternate text (white)
- `@bpm-text-color-negative: @bpm-neutral-lightest` - Negative/disabled text

#### Background Colors
- `@bpm-body-bg: #fff` - Main background (white)
- `@bpm-fill-normal: #fff` - Normal fill
- `@bpm-fill-darker: #565656` - Darker fill

#### Border Colors
- `@bpm-border-normal: lighten(@bpm-neutral, 2%)` - Normal border color

#### Link Colors
- `@bpm-link-text-color: #0f62fe` - Default link
- `@bpm-link-text-color-hover: #0043ce` - Hover link
- `@bpm-link-text-color-visited: #8a3ffc` - Visited link
- `@bpm-link-text-color-active: #161616` - Active link
- `@bpm-link-text-color-disabled: #c6c6c6` - Disabled link

### Typography

#### Font Families
- `@bpm-font-family-sans-serif: "IBM Plex Sans", "Helvetica Neue", Helvetica, Arial, sans-serif`
- `@bpm-font-family-serif: Georgia, "Times New Roman", Times, serif`
- `@bpm-font-family-monospace: "Courier New", Courier, monospace`
- `@bpm-font-family-base: @bpm-font-family-sans-serif`

#### Font Sizes
- `@bpm-font-size-base: 14px` - Base font size (body text)
- `@bpm-font-size-xsmall: round(@bpm-font-size-base/1.4)` - 10px
- `@bpm-font-size-small: round(@bpm-font-size-base/1.16)` - 12px
- `@bpm-font-size-large: round(@bpm-font-size-base*1.285)` - 18px
- `@bpm-font-size-xlarge: round(@bpm-font-size-base * 1.72)` - 24px
- `@bpm-font-size-xxlarge: round(@bpm-font-size-base * 2.3)` - 32px
- `@bpm-font-size-xxxlarge: round(@bpm-font-size-base * 3.85)` - 54px

#### Heading Sizes
- `@bpm-font-size-h1: round(@bpm-font-size-h2*1.25)`
- `@bpm-font-size-h2: round(@bpm-font-size-h3*1.25)`
- `@bpm-font-size-h3: round(@bpm-font-size-h4*1.25)`
- `@bpm-font-size-h4: @bpm-font-size-large` - 18px
- `@bpm-font-size-h5: @bpm-font-size-base` - 14px
- `@bpm-font-size-h6: @bpm-font-size-small` - 12px

#### Font Weights
- `@bpm-font-weight-normal: 400` - Regular
- `@bpm-font-weight-slim: @bpm-font-weight-normal * 0.75` - 300 (Light)
- `@bpm-font-weight-semibold: @bpm-font-weight-normal * 1.5` - 600 (Semibold)
- `@bpm-font-weight-bold: @bpm-font-weight-normal * 1.75` - 700 (Bold)

### Spacing & Layout

#### Padding
- `@bpm-main-body-padding: 0`

### Component-Specific Variables

#### Buttons
- `@bpm-btn-height-xsmall: 28px`
- `@bpm-btn-height-large: 48px`
- `@bpm-secondary-action-color-base: #0353e9`
- `@bpm-btn-alternate-hover-border: #054ada`
- `@bpm-btn-alternate-hover-color: @bpm-body-bg`

#### Inputs
- `@bpm-hover-border-bottom: @bpm-secondary-action-color-base`
- `@bpm-input-hover-border-bottom: @bpm-hover-border-bottom`

#### Checkboxes
- `@bpm-checkbox-bg: @bpm-body-bg`
- `@bpm-checkbox-border: @bpm-text-color`
- `@bpm-checkbox-border-width: 2px`
- `@bpm-checkbox-hover-bg: @bpm-body-bg`
- `@bpm-checkbox-hover-border: @bpm-secondary-action-color-base`
- `@bpm-checkbox-checked-bg: @bpm-text-color`
- `@bpm-checkbox-checked-border: @bpm-secondary-action-color-base`
- `@bpm-checkbox-checked-color: #fff`
- `@bpm-checkbox-height: 18px`
- `@bpm-checkbox-font-size: 15px`
- `@bpm-checkbox-border-radius: 0px`
- `@bpm-checkbox-box-size: 16px`
- `@bpm-checkbox-disabled-bg: #c6c6c6`
- `@bpm-checkbox-disabled-color: #fff`

#### Radio Buttons
- `@bpm-radio-bg: @bpm-body-bg`
- `@bpm-radio-color: @bpm-text-color`
- `@bpm-radio-border: @bpm-text-color`
- `@bpm-radio-hover-bg: @bpm-secondary-action-color-base`
- `@bpm-radio-hover-border: @bpm-text-color`
- `@bpm-radio-checked-bg: @bpm-body-bg`
- `@bpm-radio-checked-border: @bpm-text-color`
- `@bpm-radio-outer-circle-size: 18px`
- `@bpm-radio-inner-circle-size: 8px`

#### Tabs
- `@bpm-tabs-font-weight: bold`
- `@bpm-tabs-inactive-hover-color: @bpm-secondary-action-color-base`
- `@bpm-tabs-navbar-bg: @bpm-body-bg`
- `@bpm-tabs-active-border-bottom: @bpm-secondary-action-color-base`

#### Tables
- `@bpm-table-item-hover-bg: #F0F4F4`
- `@bpm-table-header-hover-border-bottom: @bpm-hover-border-bottom`

## Common Color Mappings

When updating widgets, use these mappings:

| Hardcoded Value | Carbon Variable | Usage |
|----------------|-----------------|-------|
| `#0f62fe` | `@bpm-color-primary` | Primary blue |
| `#0353E9` | `@bpm-color-primary-dark` | Dark blue |
| `#0043ce` | `@bpm-link-text-color-hover` | Hover blue |
| `#161616` | `@bpm-text-color` | Primary text |
| `#525252` | Gray 70 | Secondary text |
| `#8d8d8d` | Gray 50 | Tertiary text |
| `#c6c6c6` | Gray 30 | Disabled |
| `#e0e0e0` | Gray 20 | Borders |
| `#f4f4f4` | Gray 10 | Light backgrounds |
| `#ffffff` | `@bpm-body-bg` | White background |
| `#da1e28` | `@bpm-color-alert` | Error red |
| `#ba1b23` | `@bpm-color-alert-dark` | Dark red |
| `#198038` | `@bpm-color-success` | Success green |
| `#24a148` | Success green 50 | Medium green |
| `#fdd13a` | `@bpm-color-warning` | Warning yellow |
| `#f1c21b` | Warning yellow 50 | Medium yellow |
| `14px` | `@bpm-font-size-base` | Base font size |
| `12px` | `@bpm-font-size-small` | Small font size |
| `18px` | `@bpm-font-size-large` | Large font size |
| `'IBM Plex Sans'` | `@bpm-font-family-sans-serif` | Font family |

## Example: Before and After

### Before (Hardcoded)
```css
.widget-title {
    font-size: 14px;
    font-weight: 600;
    color: #161616;
    font-family: 'IBM Plex Sans', Arial, sans-serif;
}

.widget-primary {
    background-color: #0f62fe;
    border-color: #0353E9;
}
```

### After (Correct — hardcoded values with variable names as comments)
```css
/* ⚠️  InlineCSS.css is plain CSS — LESS variables do NOT work here.
   Use hardcoded hex/px values and document the corresponding theme variable in a comment. */
.widget-title {
    font-size: 14px; /* @bpm-font-size-base */
    font-weight: 600; /* @bpm-font-weight-semibold */
    color: #161616; /* @bpm-text-color */
    font-family: 'IBM Plex Sans', 'Helvetica Neue', Helvetica, Arial, sans-serif; /* @bpm-font-family-sans-serif */
}

.widget-primary {
    background-color: #0f62fe; /* @bpm-color-primary */
    border-color: #0353E9; /* @bpm-color-primary-dark */
}
```

### Wrong (LESS variables — will silently produce no styling)
```css
/* ❌ Do NOT use LESS variable syntax in InlineCSS.css */
.widget-title {
    font-size: @bpm-font-size-base;       /* ❌ not valid CSS */
    font-weight: @bpm-font-weight-semibold; /* ❌ not valid CSS */
    color: @bpm-text-color;               /* ❌ not valid CSS */
    font-family: @bpm-font-family-sans-serif; /* ❌ not valid CSS */
}
```

## Why hardcoded values + comments

BAW does **not** run LESS preprocessing on `InlineCSS.css` widget files. Using `@bpm-*` variable syntax directly produces invalid CSS that the browser silently ignores — the widget renders with no styling and no error message. The correct pattern is always: literal value in the property, variable name in a `/* comment */`.

## Notes

- Widget CSS (`InlineCSS.css`) is plain CSS — no LESS preprocessing
- Widget CSS is scoped to prevent conflicts between widgets
- Always test widgets after writing or updating CSS
- Document which theme variables the hardcoded values correspond to

<!-- Made with Bob -->