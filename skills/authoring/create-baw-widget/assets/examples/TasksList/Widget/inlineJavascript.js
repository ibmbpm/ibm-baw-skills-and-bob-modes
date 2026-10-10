var _this = this;

function renderTasks(tasks) {
    var container = _this.context.element.querySelector(".taskslist_maincontentbox");
    var listDiv = container.querySelector(".taskslist-container");
    listDiv.innerHTML = "";

    if (!tasks || tasks.length === 0) {
        listDiv.innerHTML = "<p style='padding: 16px; text-align: center; color: #525252;'>No tasks available.</p>";
        return;
    }

    // Create widget wrapper
    var widgetDiv = document.createElement("div");
    widgetDiv.className = "task-widget";

    // Create header
    var headerDiv = document.createElement("div");
    headerDiv.className = "task-header";
    var headerTitle = document.createElement("h3");
    headerTitle.textContent = "Tasks";
    headerDiv.appendChild(headerTitle);
    widgetDiv.appendChild(headerDiv);

    // Create table
    var table = document.createElement("table");
    table.className = "task-table";

    // Create table header
    var thead = document.createElement("thead");
    var headerRow = document.createElement("tr");

    var thIcon = document.createElement("th");
    thIcon.className = "task-icon-cell";
    thIcon.textContent = "";
    headerRow.appendChild(thIcon);

    var thLabel = document.createElement("th");
    thLabel.className = "task-label-cell";
    thLabel.textContent = "Task";
    headerRow.appendChild(thLabel);

    var thStatus = document.createElement("th");
    thStatus.className = "task-status-cell";
    thStatus.textContent = "Status";
    headerRow.appendChild(thStatus);

    thead.appendChild(headerRow);
    table.appendChild(thead);

    // Create table body
    var tbody = document.createElement("tbody");

    tasks.forEach(function(task) {
        var row = document.createElement("tr");

        // Icon cell
        var iconCell = document.createElement("td");
        iconCell.className = "task-icon-cell";
        var iconSpan = document.createElement("span");
        iconSpan.className = "task-icon";
        iconSpan.innerHTML = getStatusIcon(task.status);
        iconCell.appendChild(iconSpan);
        row.appendChild(iconCell);

        // Label cell
        var labelCell = document.createElement("td");
        labelCell.className = "task-label-cell";
        labelCell.textContent = task.label;
        row.appendChild(labelCell);

        // Status cell
        var statusCell = document.createElement("td");
        statusCell.className = "task-status-cell";
        var statusBadge = document.createElement("span");
        statusBadge.className = "task-status-badge " + task.status.toLowerCase();
        statusBadge.textContent = task.status;
        statusCell.appendChild(statusBadge);
        row.appendChild(statusCell);

        tbody.appendChild(row);
    });

    table.appendChild(tbody);
    widgetDiv.appendChild(table);
    listDiv.appendChild(widgetDiv);
}

function getStatusIcon(status) {
    if (status === "Complete") {
        return '<svg width="20" height="20" viewBox="0 0 20 20" fill="#198038"><path d="M8 13l-4-4 1.4-1.4L8 10.2l6.6-6.6L16 5z"/></svg>';
    } else if (status === "Pending") {
        return '<svg width="20" height="20" viewBox="0 0 20 20" fill="#525252"><circle cx="10" cy="10" r="8" fill="none" stroke="currentColor" stroke-width="2"/></svg>';
    } else if (status === "Processing") {
        return '<svg width="20" height="20" viewBox="0 0 20 20" class="spinner" fill="#0043ce"><path d="M10 2v3a5 5 0 110 10v3a8 8 0 000-16z"/></svg>';
    } else if (status === "Failed") {
        return '<svg width="20" height="20" viewBox="0 0 20 20" fill="#da1e28"><path d="M10 2a8 8 0 100 16 8 8 0 000-16zm1 9H9V5h2v6zM9 13h2v2H9v-2z"/></svg>';
    }
    return '';
}

// Initial render
renderTasks(_this.getData().items);

// Made with Bob
