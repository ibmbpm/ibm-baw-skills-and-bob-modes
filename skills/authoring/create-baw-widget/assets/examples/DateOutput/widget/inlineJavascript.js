// Get DOM elements — use querySelector scoped to this widget's root element
var container = this.context.element.querySelector(".dateoutput_maincontentbox");
var dateValueSpan = container.querySelector(".date-output-value");

// Get configuration options
var format = this.getOption("format") || "MM/DD/YYYY";
var locale = this.getOption("locale") || "en-US";
var showTime = this.getOption("showTime") || false;
var timeZone = this.getOption("timeZone") || undefined;

// Get the date data
var dateData = this.getData();

// Function to format date based on format string
function formatDate(date, formatString, locale, showTime, timeZone) {
    if (!date) {
        return "";
    }

    // Convert to Date object if it's a string or timestamp
    var dateObj;
    if (typeof date === 'string' || typeof date === 'number') {
        dateObj = new Date(date);
    } else if (date instanceof Date) {
        dateObj = date;
    } else {
        return "Invalid Date";
    }

    // Check if date is valid
    if (isNaN(dateObj.getTime())) {
        return "Invalid Date";
    }

    // Handle custom format strings
    var year = dateObj.getFullYear();
    var month = dateObj.getMonth() + 1;
    var day = dateObj.getDate();
    var hours = dateObj.getHours();
    var minutes = dateObj.getMinutes();
    var seconds = dateObj.getSeconds();

    // Pad with zeros
    var pad = function(num) {
        return num < 10 ? '0' + num : num;
    };

    // Replace format tokens
    var formatted = formatString
        .replace(/YYYY/g, year)
        .replace(/YY/g, String(year).slice(-2))
        .replace(/MM/g, pad(month))
        .replace(/M/g, month)
        .replace(/DD/g, pad(day))
        .replace(/D/g, day)
        .replace(/HH/g, pad(hours))
        .replace(/H/g, hours)
        .replace(/mm/g, pad(minutes))
        .replace(/m/g, minutes)
        .replace(/ss/g, pad(seconds))
        .replace(/s/g, seconds);

    // Add time if requested
    if (showTime && formatString.indexOf('H') === -1) {
        formatted += ' ' + pad(hours) + ':' + pad(minutes);
    }

    return formatted;
}

// Function to determine date class (past, today, future)
function getDateClass(date) {
    if (!date) return "";

    var dateObj = new Date(date);
    var today = new Date();
    today.setHours(0, 0, 0, 0);
    dateObj.setHours(0, 0, 0, 0);

    if (dateObj < today) {
        return "date-past";
    } else if (dateObj.getTime() === today.getTime()) {
        return "date-today";
    } else {
        return "date-future";
    }
}

// Format and display the date
var formattedDate = formatDate(dateData, format, locale, showTime, timeZone);
dateValueSpan.textContent = formattedDate;

// Add date class for styling
var dateClass = getDateClass(dateData);
if (dateClass) {
    container.className = "dateoutput_maincontentbox " + dateClass;
}

// Made with Bob
