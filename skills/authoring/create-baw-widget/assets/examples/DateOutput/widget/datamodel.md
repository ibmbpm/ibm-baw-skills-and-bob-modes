## Business data

Date value as a Date object, ISO 8601 string, or timestamp (number)

## Configuration options

**format** (String)
- Custom date format string that uses tokens:
  - YYYY: 4-digit year (for example, 2025)
  - YY: 2-digit year (for example, 25)
  - MM: 2-digit month (01-12)
  - M: Month without leading zero (1-12)
  - DD: 2-digit day (01-31)
  - D: Day without leading zero (1-31)
  - HH: 2-digit hours (00-23)
  - H: Hours without leading zero (0-23)
  - mm: 2-digit minutes (00-59)
  - m: Minutes without leading zero (0-59)
  - ss: 2-digit seconds (00-59)
  - s: Seconds without leading zero (0-59)
- Default: "MM/DD/YYYY"
- Examples:
  - "DD/MM/YYYY" displays 22/12/2025
  - "YYYY-MM-DD" displays 2025-12-22
  - "MM/DD/YYYY HH:mm" displays 12/22/2025 14:30
  - "D/M/YY" displays 22/12/25

**locale** (String)
- Locale identifier for date formatting (future enhancement)
- Default: "en-US"
- Examples: "en-GB", "fr-FR", "de-DE"

**showTime** (Boolean)
- Whether to append the time to the date if the format does not already include it
- Default: false
- When true and the format does not include time tokens, the widget appends HH:mm

**timeZone** (String)
- Time zone identifier (future enhancement)
- Default: undefined (uses the browser's local time zone)
- Examples: "America/New_York", "Europe/London", "Asia/Tokyo"
