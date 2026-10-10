/**
 * BAW Widget Test Data Script
 * Use this script in BAW Coach to initialize test data for all custom widgets
 * Copy and paste into the Script section of your coach
 */

// ============================================================================
// BREADCRUMB WIDGET TEST DATA
// ============================================================================
tw.local.breadcrumb = [
    {
        "label": "Home",
        "status": "completed",
        "url": "#home"
    },
    {
        "label": "Products",
        "status": "completed",
        "url": "#products"
    },
    {
        "label": "Insurance",
        "status": "current",
        "url": "#insurance"
    },
    {
        "label": "Application",
        "status": "pending",
        "url": "#application"
    }
];



// ============================================================================
// CAROUSEL WIDGET TEST DATA
// ============================================================================
tw.local.carousel = [
    {
        "icon": "data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='%234589ff'><path d='M12 2L2 7v10c0 5.55 3.84 10.74 9 12 5.16-1.26 9-6.45 9-12V7l-10-5zm0 18c-3.86-.93-7-5.43-7-10V8.3l7-3.11 7 3.11V10c0 4.57-3.14 9.07-7 10z'/><path d='M10.5 13.5l-2-2-1.41 1.41L10.5 16.5l6-6-1.41-1.41z'/></svg>",
        "title": "Security",
        "description": "Enterprise-grade security with end-to-end encryption, multi-factor authentication, and compliance with industry standards.",
        "id": "security-feature"
    },
    {
        "icon": "data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='%234589ff'><path d='M19 3H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zm0 16H5V5h14v14z'/><path d='M7 10h2v7H7zm4-3h2v10h-2zm4 6h2v4h-2z'/></svg>",
        "title": "Analytics",
        "description": "Comprehensive analytics dashboard with real-time insights, custom reports, and data visualization tools.",
        "id": "analytics-feature"
    },
    {
        "icon": "data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='%234589ff'><path d='M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 18c-4.41 0-8-3.59-8-8s3.59-8 8-8 8 3.59 8 8-3.59 8-8 8z'/><path d='M12.5 7H11v6l5.25 3.15.75-1.23-4.5-2.67z'/></svg>",
        "title": "Performance",
        "description": "Lightning-fast performance with optimized code, efficient caching, and scalable infrastructure.",
        "id": "performance-feature"
    },
    {
        "icon": "data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='%234589ff'><path d='M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z'/></svg>",
        "title": "Reliability",
        "description": "99.9% uptime guarantee with automated backups, disaster recovery, and 24/7 monitoring.",
        "id": "reliability-feature"
    },
    {
        "icon": "data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='%234589ff'><path d='M16 11c1.66 0 2.99-1.34 2.99-3S17.66 5 16 5c-1.66 0-3 1.34-3 3s1.34 3 3 3zm-8 0c1.66 0 2.99-1.34 2.99-3S9.66 5 8 5C6.34 5 5 6.34 5 8s1.34 3 3 3zm0 2c-2.33 0-7 1.17-7 3.5V19h14v-2.5c0-2.33-4.67-3.5-7-3.5zm8 0c-.29 0-.62.02-.97.05 1.16.84 1.97 1.97 1.97 3.45V19h6v-2.5c0-2.33-4.67-3.5-7-3.5z'/></svg>",
        "title": "Collaboration",
        "description": "Seamless team collaboration with real-time updates, shared workspaces, and integrated communication tools.",
        "id": "collaboration-feature"
    },
    {
        "icon": "data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='%234589ff'><path d='M19.35 10.04C18.67 6.59 15.64 4 12 4c-1.48 0-2.85.43-4.01 1.17l1.46 1.46C10.21 6.23 11.08 6 12 6c3.04 0 5.5 2.46 5.5 5.5v.5H19c1.66 0 3 1.34 3 3 0 1.13-.64 2.11-1.56 2.62l1.45 1.45C23.16 18.16 24 16.68 24 15c0-2.64-2.05-4.78-4.65-4.96zM3 5.27l2.75 2.74C2.56 8.15 0 10.77 0 14c0 3.31 2.69 6 6 6h11.73l2 2L21 20.73 4.27 4 3 5.27zM7.73 10l8 8H6c-2.21 0-4-1.79-4-4s1.79-4 4-4h1.73z'/></svg>",
        "title": "Cloud Integration",
        "description": "Seamless integration with major cloud providers including AWS, Azure, and Google Cloud Platform.",
        "id": "cloud-feature"
    }
];


// ============================================================================
// DATE OUTPUT WIDGET TEST DATA
// ============================================================================
tw.local.dateoutput = new Date(); // Current date
// Or use specific date:
// tw.local.dateoutput = new Date("2026-05-06");

// ============================================================================
// MARKDOWN VIEWER WIDGET TEST DATA
// ============================================================================
tw.local.markdownviewer = `# Insurance Application Guide

## Overview
Welcome to the **Life Insurance Application** process.

### Required Documents
- Valid ID
- Proof of income
- Medical records

### Steps
1. Fill out application form
2. Submit required documents
3. Complete medical examination
4. Wait for underwriting decision

> **Note**: Processing typically takes 2-4 weeks.

For more information, visit our [website](https://example.com).
`;

// ============================================================================
// MULTISELECT WIDGET TEST DATA
// ============================================================================
// Selected values (data binding) - array of strings matching option values
tw.local.multiSelect = [
    "life",
    "health",
    "disability"
];

// MultiSelect options (configuration option - set in widget properties)
// This should be configured as a Business Object list in the widget's Configuration Options
// The widget expects objects with 'name' and 'value' properties (nameValuePair structure)
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

// ============================================================================
// PROCESS CIRCLE WIDGET TEST DATA
// ============================================================================
tw.local.processcircle = 75; // 75% complete

// ============================================================================
// PROGRESS BAR WIDGET TEST DATA
// ============================================================================
tw.local.progressbar = {
    "percentage": 65,
    "status": "In Progress",
    "label": "Application Processing"
};

// ============================================================================
// TASKS LIST WIDGET TEST DATA
// ============================================================================
tw.local.tasksList = [
    {
        "label": "Complete application form",
        "status": "complete"
    },
    {
        "label": "Upload identification documents",
        "status": "complete"
    },
    {
        "label": "Schedule medical examination",
        "status": "processing"
    },
    {
        "label": "Review policy terms",
        "status": "pending"
    },
    {
        "label": "Sign final documents",
        "status": "pending"
    }
];

// ============================================================================
// TIMELINE WIDGET TEST DATA
// Demonstrates all status types: completed, current, pending, error, warning
// ============================================================================
tw.local.timeline = [
    {
        "date": "2026-05-01",
        "title": "Application Submitted",
        "description": "Your life insurance application has been received and is being reviewed.",
        "status": "completed",
        "metadata": "Submitted by: John Doe"
    },
    {
        "date": "2026-05-02",
        "title": "Document Verification",
        "description": "All required documents have been verified and approved.",
        "status": "completed",
        "metadata": "Verified by: Jane Smith"
    },
    {
        "date": "2026-05-03",
        "title": "Medical Examination",
        "description": "Medical examination scheduled and completed successfully.",
        "status": "completed",
        "metadata": "Examiner: Dr. Johnson"
    },
    {
        "date": "2026-05-04",
        "title": "Background Check",
        "description": "Minor discrepancy found in employment history - requires clarification.",
        "status": "warning",
        "metadata": "Action required: Contact HR department"
    },
    {
        "date": "2026-05-05",
        "title": "Credit Check Failed",
        "description": "Credit check returned an error - unable to verify financial information.",
        "status": "error",
        "metadata": "Error code: CR-401 - Please resubmit documents"
    },
    {
        "date": "2026-05-06",
        "title": "Underwriting Review",
        "description": "Application is currently under review by our underwriting team.",
        "status": "current",
        "metadata": "Assigned to: Underwriting Team A"
    },
    {
        "date": "2026-05-10",
        "title": "Policy Approval",
        "description": "Awaiting final approval and policy generation.",
        "status": "pending",
        "metadata": "Expected completion date"
    },
    {
        "date": "2026-05-12",
        "title": "Policy Issuance",
        "description": "Policy documents will be generated and sent to you.",
        "status": "pending",
        "metadata": "Delivery method: Email"
    }
];

// ============================================================================
// ALTERNATIVE TEST DATA SETS
// ============================================================================

// Stepper Widget - If you have a stepper widget
/*
tw.local.stepper = [
    {
        "label": "Personal Information",
        "description": "Enter your basic details",
        "status": "completed"
    },
    {
        "label": "Medical History",
        "description": "Provide medical information",
        "status": "completed"
    },
    {
        "label": "Coverage Selection",
        "description": "Choose your coverage options",
        "status": "current"
    },
    {
        "label": "Beneficiaries",
        "description": "Add beneficiary information",
        "status": "pending"
    },
    {
        "label": "Review & Submit",
        "description": "Review and submit application",
        "status": "pending"
    }
];
*/

// ============================================================================
// USAGE INSTRUCTIONS
// ============================================================================
/*
1. Copy this entire script
2. In BAW Process Designer, open your coach
3. Go to the "Variables" section and create the following variables:
   - breadcrumb (BreadcrumbItem List)
   - carousel (CarouselCard List)
   - dateoutput (Date)
   - markdownviewer (String)
   - multiSelect (String List)
   - processcircle (Integer)
   - progressbar (ProgressData)
   - tasksList (TaskItem List)
   - timeline (TimelineEvent List)

4. Go to the "Script" section
5. Paste this script
6. Save and run your coach

The widgets will now display with sample data!
*/

console.log("✅ Widget test data initialized successfully!");
console.log("📊 Breadcrumb items:", tw.local.breadcrumb ? tw.local.breadcrumb.length : 0);
console.log("🎠 Carousel cards:", tw.local.carousel ? tw.local.carousel.length : 0);
console.log("📅 Date output:", tw.local.dateoutput);
console.log("📝 Markdown length:", tw.local.markdownviewer ? tw.local.markdownviewer.length : 0);
console.log("☑️  Multi-select items:", tw.local.multiSelect ? tw.local.multiSelect.length : 0);
console.log("⭕ Process circle:", tw.local.processcircle + "%");
console.log("📊 Progress bar:", tw.local.progressbar ? tw.local.progressbar.percentage + "%" : "N/A");
console.log("✅ Tasks:", tw.local.tasksList ? tw.local.tasksList.length : 0);
console.log("⏱️  Timeline events:", tw.local.timeline ? tw.local.timeline.length : 0);

// Made with Bob
