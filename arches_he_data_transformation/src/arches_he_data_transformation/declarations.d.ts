// declare untyped modules that have been added to your project in `package.json`
// Module homepage on npmjs.com uses logos "TS" or "DT" to indicate if typed

import("@/arches/declarations.d.ts");

// gettext extractor keywords used in this app's frontend
// These are declared for TypeScript only; the extractor scans for usages.
declare function __(text: string): string;
declare function _n(singular: string, plural: string, count: number): string;
