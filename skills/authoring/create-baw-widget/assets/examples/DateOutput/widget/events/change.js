var _this = this;

// Get DOM elements — use querySelector scoped to this widget's root element
var container = _this.context.element.querySelector(".dateoutput_maincontentbox");
var dateValueSpan = container.querySelector(".date-output-value");

// Get configuration options
var format = _this.getOption("format") || "MM/DD/YYYY";
var showTime = _this.getOption("showTime") || false;

// Get the updated date data
var dateData = _this.getData();

// Pad with zeros helper
var pad = function(num) {
    return num < 10 ? '0' + num : num;
};

// Format the date
function formatDate(date, formatString, showTime) {
    if (!date) return "";

    var dateObj = (typeof date === 'string' || typeof date === 'number') ? new Date(date) : date;
    if (isNaN(dateObj.getTime())) return "Invalid Date";

    var year    = dateObj.getFullYear();
    var month   = dateObj.getMonth() + 1;
    var day     = dateObj.getDate();
    var hours   = dateObj.getHours();
    var minutes = dateObj.getMinutes();
    var seconds = dateObj.getSeconds();

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

    if (showTime && formatString.indexOf('H') === -1) {
        formatted += ' ' + pad(hours) + ':' + pad(minutes);
    }
    return formatted;
}

// Update the display
dateValueSpan.textContent = formatDate(dateData, format, showTime);
