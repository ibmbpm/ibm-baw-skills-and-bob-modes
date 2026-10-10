## Business Data
    
    Date value as a Date object, ISO 8601 string, or timestamp (number)

## Configuration Options

**format** (String)
- Custom date format string using tokens:
  - YYYY: 4-digit year (e.g., 2025)
  - YY: 2-digit year (e.g., 25)
  - MM: 2-digit month (e.g., 01-12)
  - M: Month without leading zero (e.g., 1-12)
  - DD: 2-digit day (e.g., 01-31)
  - D: Day without leading zero (e.g., 1-31)
  - HH: 2-digit hours (e.g., 00-23)
  - H: Hours without leading zero (e.g., 0-23)
  - mm: 2-digit minutes (e.g., 00-59)
  - m: Minutes without leading zero (e.g., 0-59)
  - ss: 2-digit seconds (e.g., 00-59)
  - s: Seconds without leading zero (e.g., 0-59)
- Default: "MM/DD/YYYY"
- Examples:
  - "DD/MM/YYYY" → 22/12/2025
  - "YYYY-MM-DD" → 2025-12-22
  - "MM/DD/YYYY HH:mm" → 12/22/2025 14:30
  - "D/M/YY" → 22/12/25

**locale** (String)
- Locale identifier for date formatting (future enhancement)
- Default: "en-US"
- Examples: "en-GB", "fr-FR", "de-DE"

**showTime** (Boolean)
- Whether to append time to the date if not already in format
- Default: false
- When true and format doesn't include time tokens, appends HH:mm

**timeZone** (String)
- Time zone identifier (future enhancement)
- Default: undefined (uses browser's local time zone)
- Examples: "America/New_York", "Europe/London", "Asia/Tokyo"