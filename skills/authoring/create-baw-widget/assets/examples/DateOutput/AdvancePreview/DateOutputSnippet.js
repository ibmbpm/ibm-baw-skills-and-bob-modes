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

                this.context.coachViewData.containingDiv = containingDiv;

                // Form group
                var formGroupDiv = domConstruct.create("div", null, containingDiv);
                domClass.add(formGroupDiv, "form-group");
                this.context.coachViewData.formGroupDiv = formGroupDiv;

                // Label
                var label = domConstruct.create("span", null, formGroupDiv);
                domClass.add(label, "control-label");
                label.appendChild(document.createTextNode(labelText));
                this.context.coachViewData.label = label;

                // Input container
                var inputDiv = domConstruct.create("div", null, formGroupDiv);
                domClass.add(inputDiv, "input");
                this.context.coachViewData.inputDiv = inputDiv;

                // Generate preview date output
                this.generateSampleData(domConstruct, domAttr, domClass);

                callback();
            }));
        }));
    },

    getLabelDomElement: function () {
        return this.context.coachViewData.label;
    },

    generateSampleData: function (domConstruct, domAttr, domClass) {
        // Example date value - current date
        var currentDate = new Date();
        
        // Format the date based on default format (MM/DD/YYYY)
        var month = currentDate.getMonth() + 1;
        var day = currentDate.getDate();
        var year = currentDate.getFullYear();
        
        var pad = function(num) {
            return num < 10 ? '0' + num : num;
        };
        
        var formattedDate = pad(month) + '/' + pad(day) + '/' + year;

        // Create container div
        var container = domConstruct.create("div", null, this.context.coachViewData.inputDiv);
        domClass.add(container, "date-output-container");
        domClass.add(container, "date-today"); // Since we're using current date

        // Create value span
        var valueSpan = domConstruct.create("span", null, container);
        domClass.add(valueSpan, "date-output-value");
        valueSpan.textContent = formattedDate;
    },

    propertyChanged: function (propertyName, propertyValue) {
        // Handle format option changes in preview
        if (propertyName === "format" && this.context.coachViewData.inputDiv) {
            // Clear existing content
            this.context.coachViewData.inputDiv.innerHTML = "";
            
            // Regenerate with new format
            require([
                "dojo/dom-construct",
                "dojo/dom-attr",
                "dojo/dom-class"
            ], this.lang.hitch(this, function (domConstruct, domAttr, domClass) {
                this.generateSampleData(domConstruct, domAttr, domClass);
            }));
        }
    },

    modelChanged: function (propertyName, propertyValue) {
        // Not required for preview
    }
};

// Made with Bob
