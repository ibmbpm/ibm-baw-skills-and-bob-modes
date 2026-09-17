# BAW WebPD — Business Objects import steps

Copy these steps verbatim into every response that includes a generated BO import file.

---

## How to import Business Objects into BAW WebPD

1. **Save the JSON file** to a location on your local machine.
2. **Open WebPD** for your target project.
3. **In the left navigation panel**, click **Data → Import business objects**.
4. **Select your saved JSON file** in the file picker and confirm.
5. **Verify the imported Business Objects** appear in the Business Objects list. Imported BOs are marked read-only — this is expected behavior by design.
6. **To update Business Objects later**, revise the JSON file (manually, or with the help of an AI assistant such as Bob) and re-import using the same steps. Re-importing overrides the existing definitions immediately.

> ⚠️ **Before re-importing a modified file:** removing or renaming any field will break every service, process, or coach that references that field — immediately upon import. Review all consumers of the affected Business Objects before proceeding.
