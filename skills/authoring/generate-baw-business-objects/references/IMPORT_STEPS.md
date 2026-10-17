# BAW WebPD — Business Objects import steps

Copy these steps verbatim into every response that includes a generated BO import file.

---

## How to import Business Objects into BAW WebPD

1. **Save the JSON file** to a location on your local machine.
2. **Open WebPD** for your target project.
3. **In the left navigation panel**, click **Data → Import business objects**.
4. **Select your saved JSON file** in the file picker and confirm.
5. **Verify the imported Business Objects** appear in the Business Objects list. BAW marks imported BOs as read-only. This is expected behavior.
6. **To update Business Objects later**, revise the JSON file (manually, or with the help of an AI assistant such as Bob) and re-import using the same steps. Re-importing overrides the existing definitions immediately.

> ⚠️ **Before re-importing a modified file:** removing or renaming any field will break every service, process, or coach that references that field — immediately upon import. Review all consumers of the affected Business Objects before proceeding.

---

## Alternative: toolkit TWX import

If Business Objects should live in a **reusable toolkit** so multiple process apps can reference them, Bob can generate a toolkit `.twx` file — either creating a brand-new one or updating an existing one. The resulting `.twx` lands in `output/twx/` inside the domain folder.

### How to import the toolkit TWX into BAW

Depending on your environment, import the generated toolkit `.twx` file using one of the following routes:

- **Workflow Center**: `Workflow Center → Toolkits → Import Toolkit`
- **Business Automation Studio**: `Business Automation Studio → Business automations → Toolkits → Import`

Once imported, add the toolkit as a dependency to any process app that needs these Business Objects. The types will then be available in Data Mapping and Coach Views.
