import React, { useEffect, useState } from 'react';
import { getDocumentNlpApi } from '../api/config';

export default function DocumentAnalysis({ activeDocument, onProceedToResults }) {
  const [nlpData, setNlpData] = useState(null);
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    if (activeDocument && activeDocument.document_id) {
      setIsLoading(true);
      getDocumentNlpApi(activeDocument.document_id)
        .then((data) => {
          setNlpData(data);
          setIsLoading(false);
        })
        .catch((err) => {
          console.warn("NLP API notice:", err.message);
          setIsLoading(false);
        });
    }
  }, [activeDocument]);

  const docId = activeDocument?.document_id || "DOC-UNASSIGNED";
  const ocrText = activeDocument?.extracted_text || nlpData?.extracted_text || "[No OCR text available. Please upload a document to run extraction.]";
  const ocrConfidence = activeDocument?.ocr_confidence_score ?? 0.0;

  const fields = nlpData?.extracted_attributes || activeDocument?.extracted_nlp_fields || {};
  const nlpConfidence = nlpData?.nlp_confidence_score ?? activeDocument?.nlp_confidence_score ?? (fields.owner_name ? 85.0 : 0.0);
  const locationText = nlpData?.location_summary || activeDocument?.location_summary || ([fields.village, fields.mandal, fields.district, fields.state].filter(Boolean).join(", ") || "Not detected in document");

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <h2 className="text-2xl font-extrabold text-white tracking-tight">Document Analysis</h2>
            <span className="px-2.5 py-0.5 rounded text-xs font-bold bg-blue-950 text-blue-400 border border-blue-800">
              OCR & NLP Extracted
            </span>
          </div>
          <p className="text-sm text-slate-400 mt-1">
            Extracted text entities, OCR confidence scores, and structured metadata from uploaded deed ({docId}).
          </p>
        </div>

        <button
          onClick={onProceedToResults}
          className="flex items-center gap-2 px-5 py-2.5 bg-blue-600 hover:bg-blue-500 text-white font-semibold text-xs md:text-sm rounded-xl transition-all shadow-md"
        >
          <span>View Verification Results</span>
          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14 5l7 7m0 0l-7 7m7-7H3" />
          </svg>
        </button>
      </div>

      {/* Grid: Document Scan Viewer vs Extracted Entities */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Column: OCR Document Text Scan */}
        <div className="lg:col-span-5 bg-slate-900 border border-slate-800 rounded-xl p-5 flex flex-col space-y-4">
          <div className="flex items-center justify-between border-b border-slate-800 pb-3">
            <span className="text-xs font-bold uppercase text-slate-300">OCR Extracted Document Scan</span>
            <span className="text-[11px] font-mono text-slate-500">Document ID: {docId}</span>
          </div>

          <div className="bg-slate-950 border border-slate-800 rounded-lg p-5 flex flex-col space-y-3 font-mono text-slate-300 text-xs shadow-inner min-h-[380px] relative overflow-hidden">
            <div className="absolute top-2 right-2 px-2 py-1 bg-emerald-950 text-emerald-400 border border-emerald-800 rounded text-[10px] font-sans font-bold">
              OCR Confidence: {ocrConfidence}%
            </div>

            <div className="whitespace-pre-wrap leading-relaxed text-[11px] text-slate-300 font-mono pt-4 max-h-[500px] overflow-y-auto">
              {ocrText}
            </div>
          </div>
        </div>

        {/* Right Column: Extracted Entities Table */}
        <div className="lg:col-span-7 bg-slate-900 border border-slate-800 rounded-xl p-5 space-y-4">
          <div className="flex items-center justify-between border-b border-slate-800 pb-3">
            <div>
              <h3 className="text-sm font-bold text-white">Extracted Text Entities (Universal NLP Engine)</h3>
              <div className="flex items-center gap-2 mt-1">
                <span className="text-[11px] font-semibold text-blue-400">
                  Type: {fields.document_type || nlpData?.document_type || "General Land Record"}
                </span>
                {activeDocument?.pages_count > 1 && (
                  <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-slate-800 text-slate-300 border border-slate-700">
                    {activeDocument.pages_count} Pages
                  </span>
                )}
              </div>
            </div>
            <div className="text-right">
              <span className="text-xs text-blue-400 font-semibold block">
                NLP Confidence: {nlpConfidence}%
              </span>
              {(nlpData?.requires_review || activeDocument?.requires_review) && (
                <span className="text-[10px] text-amber-400 font-medium">
                  Review Recommended
                </span>
              )}
            </div>
          </div>

          {isLoading ? (
            <div className="p-8 text-center text-xs text-slate-400 animate-pulse">
              Extracting document fields...
            </div>
          ) : (
            <div className="space-y-3">
              <div className="p-3 bg-slate-950 rounded-lg border border-slate-800 flex justify-between items-center">
                <div>
                  <span className="text-[11px] font-semibold text-slate-500 uppercase block">Extracted Owner / Executant Name</span>
                  <span className="text-sm font-bold text-white">{fields.owner_name || "Not detected in document"}</span>
                  {(fields.seller_name || fields.buyer_name) && (
                    <div className="text-[10px] text-slate-400 mt-0.5">
                      {fields.seller_name && <span>Vendor: {fields.seller_name} </span>}
                      {fields.buyer_name && <span>| Vendee: {fields.buyer_name}</span>}
                    </div>
                  )}
                </div>
                <span className={`text-xs font-semibold px-2 py-0.5 rounded ${
                  fields.owner_name 
                    ? 'bg-emerald-950 text-emerald-400 border border-emerald-800' 
                    : 'bg-slate-800 text-slate-400 border border-slate-700'
                }`}>
                  {fields.owner_name ? 'Extracted' : 'Not Detected'}
                </span>
              </div>

              <div className="p-3 bg-slate-950 rounded-lg border border-slate-800 flex justify-between items-center">
                <div>
                  <span className="text-[11px] font-semibold text-slate-500 uppercase block">Survey / Sub-division No.</span>
                  <span className="text-sm font-bold text-white font-mono">{fields.survey_number || "Not detected in document"}</span>
                </div>
                <span className={`text-xs font-semibold px-2 py-0.5 rounded ${
                  fields.survey_number 
                    ? 'bg-emerald-950 text-emerald-400 border border-emerald-800' 
                    : 'bg-slate-800 text-slate-400 border border-slate-700'
                }`}>
                  {fields.survey_number ? 'Extracted' : 'Not Detected'}
                </span>
              </div>

              <div className="p-3 bg-slate-950 rounded-lg border border-slate-800 flex justify-between items-center">
                <div>
                  <span className="text-[11px] font-semibold text-slate-500 uppercase block">Claimed Land Extent</span>
                  <div className="flex items-center gap-2">
                    <span className="text-sm font-bold text-white">
                      {fields.land_area_raw || (fields.land_area_acres ? `${fields.land_area_acres} Acres` : "Not detected in document")}
                    </span>
                    {fields.land_area_raw && fields.land_area_normalized_acres && !fields.land_area_raw.toLowerCase().includes("acre") && (
                      <span className="text-xs font-mono text-blue-400 bg-blue-950/60 px-1.5 py-0.5 rounded border border-blue-900/50">
                        {fields.land_area_normalized_acres} Acres normalized
                      </span>
                    )}
                  </div>
                </div>
                <span className={`text-xs font-semibold px-2 py-0.5 rounded ${
                  fields.land_area_raw || fields.land_area_acres 
                    ? 'bg-emerald-950 text-emerald-400 border border-emerald-800' 
                    : 'bg-slate-800 text-slate-400 border border-slate-700'
                }`}>
                  {fields.land_area_raw || fields.land_area_acres ? 'Extracted' : 'Not Detected'}
                </span>
              </div>

              <div className="p-3 bg-slate-950 rounded-lg border border-slate-800 flex justify-between items-center">
                <div>
                  <span className="text-[11px] font-semibold text-slate-500 uppercase block">Jurisdiction & Location</span>
                  <span className="text-sm font-bold text-white">{locationText}</span>
                </div>
                <span className={`text-xs font-semibold px-2 py-0.5 rounded ${
                  locationText !== "Not detected in document"
                    ? 'bg-emerald-950 text-emerald-400 border border-emerald-800' 
                    : 'bg-slate-800 text-slate-400 border border-slate-700'
                }`}>
                  {locationText !== "Not detected in document" ? 'Extracted' : 'Not Detected'}
                </span>
              </div>

              <div className="p-3 bg-slate-950 rounded-lg border border-slate-800 flex justify-between items-center">
                <div>
                  <span className="text-[11px] font-semibold text-slate-500 uppercase block">Document Type & Registration</span>
                  <span className="text-sm font-bold text-slate-300">
                    {fields.document_type || "Instrument"} {fields.registration_date ? `(${fields.registration_date})` : ""}
                  </span>
                  {fields.encumbrance_status && (
                    <span className="text-xs text-emerald-400 block font-semibold mt-0.5">
                      Status: {fields.encumbrance_status}
                    </span>
                  )}
                </div>
                <span className="text-xs font-semibold px-2 py-0.5 rounded bg-blue-950 text-blue-400 border border-blue-800">
                  {fields.registration_number ? fields.registration_number : 'Instrument Recorded'}
                </span>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
