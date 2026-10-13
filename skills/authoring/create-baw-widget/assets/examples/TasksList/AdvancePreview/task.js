/*
 * #BEGIN COPYRIGHT
 *
 * Licensed Materials - Property of IBM
 * 5725-C95
 * (C) Copyright IBM Corporation
 *
 * #END COPYRIGHT
 */

var mixObject = {

    createPreview: function (containingDiv, labelText, callback) {
        var previewLayerUri = this.context.getManagedAssetUrl(
            "BPMExt-Controls.preview.js",
            this.context.assetType_WEB,
            "SYSBPMUI"
        );

        require([previewLayerUri], this.lang.hitch(this, function () {
            require([
                "dojo/dom-construct",
                "dojo/dom-class",
                "dojo/dom-attr",
                "bpmui/preview/BPMExt-Core-Designer"
            ], this.lang.hitch(this, function (domConstruct, domClass, domAttr, bpmext) {

                bpmext.uidesign.css.ensureGlyphsLoaded(this);
                bpmext.uidesign.css.ensureSparkUIClass(containingDiv);

                // Save references
                this.context.coachViewData.containingDiv = containingDiv;

                // Main form group
                var formGroupDiv = domConstruct.create("div", null, containingDiv);
                domClass.add(formGroupDiv, "form-group");
                this.context.coachViewData.formGroupDiv = formGroupDiv;

                // Label
                var labelNode = domConstruct.create("span", null, formGroupDiv);
                domClass.add(labelNode, "control-label");
                labelNode.appendChild(document.createTextNode(labelText));
                this.context.coachViewData.label = labelNode;

                // Input container
                var inputDiv = domConstruct.create("div", null, formGroupDiv);
                domClass.add(inputDiv, "input");
                domAttr.set(inputDiv, "role", "list");
                this.context.coachViewData.inputDiv = inputDiv;

                // Generate sample preview data
                this.generateSampleData(domConstruct, domClass);

                callback();
            }));
        }));
    },

    getLabelDomElement: function () {
        return this.context.coachViewData.label;
    },

    generateSampleData: function (domConstruct, domClass) {

        var tasks = [
            { label: "Validate customer request", status: "Complete" },
            { label: "Approve budget allocation", status: "Pending" },
            { label: "Generate compliance report", status: "Processing" },
            { label: "Submit final documentation", status: "Failed" }
        ];

        // Create widget container
        var widgetDiv = domConstruct.create("div", null, this.context.coachViewData.inputDiv);
        domClass.add(widgetDiv, "task-widget");

        // Create header
        var headerDiv = domConstruct.create("div", null, widgetDiv);
        domClass.add(headerDiv, "task-header");
        var headerTitle = domConstruct.create("h3", null, headerDiv);
        headerTitle.appendChild(document.createTextNode("Tasks"));

        // Create table
        var table = domConstruct.create("table", null, widgetDiv);
        domClass.add(table, "task-table");

        // Create table header
        var thead = domConstruct.create("thead", null, table);
        var headerRow = domConstruct.create("tr", null, thead);
        
        var thIcon = domConstruct.create("th", null, headerRow);
        domClass.add(thIcon, "task-icon-cell");
        thIcon.appendChild(document.createTextNode(""));
        
        var thLabel = domConstruct.create("th", null, headerRow);
        domClass.add(thLabel, "task-label-cell");
        thLabel.appendChild(document.createTextNode("Task"));
        
        var thStatus = domConstruct.create("th", null, headerRow);
        domClass.add(thStatus, "task-status-cell");
        thStatus.appendChild(document.createTextNode("Status"));

        // Create table body
        var tbody = domConstruct.create("tbody", null, table);
        this.context.coachViewData.tbody = tbody;

        // Add task rows
        for (var i = 0; i < tasks.length; i++) {
            this._createTaskRow(domConstruct, domClass, tasks[i], tbody);
        }
    },

    _createTaskRow: function (domConstruct, domClass, task, tbody) {

        var row = domConstruct.create("tr", null, tbody);

        // Icon cell
        var iconCell = domConstruct.create("td", null, row);
        domClass.add(iconCell, "task-icon-cell");
        var iconSpan = domConstruct.create("span", null, iconCell);
        domClass.add(iconSpan, "task-icon");
        iconSpan.innerHTML = this._getStatusIcon(task.status);

        // Label cell
        var labelCell = domConstruct.create("td", null, row);
        domClass.add(labelCell, "task-label-cell");
        labelCell.appendChild(document.createTextNode(task.label));

        // Status cell
        var statusCell = domConstruct.create("td", null, row);
        domClass.add(statusCell, "task-status-cell");
        var statusBadge = domConstruct.create("span", null, statusCell);
        domClass.add(statusBadge, "task-status-badge");
        domClass.add(statusBadge, task.status.toLowerCase());
        statusBadge.appendChild(document.createTextNode(task.status));
    },

    _getStatusIcon: function (status) {

        if (status === "Complete") {
            return '<svg width="16" height="16" fill="#1ba348"><path d="M6 10l-3-3 1-1 2 2 5-5 1 1z"/></svg>';
        }

        if (status === "Pending") {
            return '<svg width="16" height="16" fill="#777"><circle cx="8" cy="8" r="7"/></svg>';
        }

        if (status === "Failed") {
            return '<svg width="16" height="16" fill="#d32f2f"><path d="M8 1a7 7 0 100 14A7 7 0 008 1zm1 8H7V4h2v5zM7 11h2v2H7z"/></svg>';
        }

        return '';
    },

    propertyChanged: function (propertyName, propertyValue) {
        // No dynamic properties for this simple preview
    },

    modelChanged: function (propertyName, propertyValue) {
        // Not needed for preview-only widget
    }
};
