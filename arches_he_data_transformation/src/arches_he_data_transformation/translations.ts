// Frontend translatable strings for arches_he_data_transformation
// Use __() and _n() so vue-gettext-extract picks them up per gettext.config.js

export const heDataTransformationStrings = {
    // Example UI labels
    exportBranchExcelSummary: __("Export Branch Excel Summary"),
    importBranchExcelSummary: __("Import Branch Excel Summary"),
    exportTileExcel: __("Export Tile Excel"),
    importTileExcelSummary: __("Import Tile Excel Summary"),
    jsonLdArchive: __("JSON-LD Archive"),
    downloadExportedZipFile: __("Download Exported Zip File"),

    // Buttons and actions
    start: __("Start"),
    submit: __("Submit"),
    cancel: __("Cancel"),
    preview: __("Preview"),
    manage: __("Manage"),

    // Pluralized examples
    filesUploaded: (count: number) =>
        _n("file uploaded", "files uploaded", count),
    resourcesUpdated: (count: number) =>
        _n("Resource updated", "Resources updated", count),
};

// Usage example (not required):
// import { heDataTransformationStrings as t } from "./translations";
// console.log(t.exportBranchExcelSummary);
