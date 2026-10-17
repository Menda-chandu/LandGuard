import React from 'react';

export default function DocumentRequired({ onUpload }) {
  return <div className="p-8 bg-slate-900 border border-slate-800 rounded-xl space-y-4">
    <h2 className="text-xl font-bold text-white">Select an uploaded document</h2>
    <p className="text-sm text-slate-400">Open a saved document from the dashboard, or upload a deed to view its analysis, verification, risk score, and ownership history.</p>
    <button onClick={onUpload} className="px-4 py-2 bg-blue-600 text-white text-sm rounded-lg">Upload a document</button>
  </div>;
}
