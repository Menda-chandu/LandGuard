import React, { useEffect, useState } from 'react';
import StatusBadge from '../components/StatusBadge';
import RiskScoreBadge from '../components/RiskScoreBadge';
import { getVerificationApi } from '../api/config';
import { mockSelectedRecord } from '../data/mockData';

export default function VerificationResults({ activeDocument, verificationResult, onVerificationComplete, onNavigate }) {
  const [verData, setVerData] = useState(verificationResult);
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    if (verificationResult) {
      setVerData(verificationResult);
      return;
    }

    const docId = activeDocument?.document_id || "DOC-2026-8901";
    setIsLoading(true);
    getVerificationApi(docId)
      .then((data) => {
        setVerData(data);
        if (onVerificationComplete) {
          onVerificationComplete(data);
        }
        setIsLoading(false);
      })
      .catch((err) => {
        console.warn("Verification API notice:", err.message);
        setIsLoading(false);
      });
  }, [activeDocument, verificationResult, onVerificationComplete]);

  const docId = activeDocument?.document_id || verData?.document_id || "DOC-UNASSIGNED";
  const verStatus = verData?.verification_status || (activeDocument ? "PENDING" : "UNVERIFIED");
  const isReferenceNotFound = verStatus === "REFERENCE_NOT_FOUND" || verData?.reference_status === "NO_MATCHING_REFERENCE";

  const matchedRec = verData?.matched_land_record || {
    owner_name: activeDocument ? (isReferenceNotFound ? "Unindexed in Demo Layer" : "Checking registry...") : "No Record",
    survey_number: activeDocument?.extracted_nlp_fields?.survey_number || "N/A",
    land_area_acres: activeDocument?.extracted_nlp_fields?.land_area_acres || 0.0,
    village: activeDocument?.extracted_nlp_fields?.village || "N/A",
    district: activeDocument?.extracted_nlp_fields?.district || "N/A"
  };

  const fieldMatches = verData?.field_matches || {
    owner_match: false,
    survey_number_match: false,
    land_area_match: false
  };

  const detectedAnomalies = verData?.detected_anomalies || [];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <h2 className="text-2xl font-extrabold text-white tracking-tight">Verification Results</h2>
            <StatusBadge status={verStatus} />
          </div>
          <p className="text-sm text-slate-400 mt-1">
            Automated cross-matching of deed attributes against official Government Land Revenue Registry databases ({docId}).
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button 
            onClick={() => onNavigate('risk')}
            className="px-4 py-2 bg-rose-600 hover:bg-rose-500 text-white font-semibold text-xs md:text-sm rounded-lg transition-all shadow-md"
          >
            View Risk Score Audit
          </button>
        </div>
      </div>

      {/* Informational banner when parcel is not in synthetic demonstration registry */}
      {isReferenceNotFound && (
        <div className="p-4 rounded-xl bg-blue-950/40 border border-blue-800 text-blue-200 text-xs flex items-start gap-3 shadow-md">
          <span className="text-lg">ℹ️</span>
          <div>
            <strong className="block text-sm text-blue-300 font-bold mb-1">
              No Matching Reference Record Available in Demo Dataset (Synthetic Registry)
            </strong>
            <p className="text-slate-300 leading-relaxed">
              The survey number extracted from this document is not currently indexed in the synthetic demonstration database.
              This represents an unindexed parcel in the prototype layer, not fraud, title invalidity, or fake ownership.
            </p>
          </div>
        </div>
      )}

      {isLoading ? (
        <div className="p-12 bg-slate-900 border border-slate-800 rounded-xl text-center text-slate-400 text-sm animate-pulse">
          Cross-matching deed details against land registry database...
        </div>
      ) : (
        <>
          {/* Key Attributes Summary Bar */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="p-4 bg-slate-900 border border-slate-800 rounded-xl">
              <span className="text-[11px] font-bold uppercase text-slate-500 block">Owner Name Match</span>
              <span className="text-base font-bold text-white mt-1 block">
                {isReferenceNotFound ? "Unindexed" : fieldMatches.owner_match ? "Matched" : "Mismatch"}
              </span>
              <span className={`text-xs font-medium ${isReferenceNotFound ? 'text-blue-400' : fieldMatches.owner_match ? 'text-emerald-400' : 'text-rose-400'}`}>
                Govt: {matchedRec.owner_name}
              </span>
            </div>

            <div className="p-4 bg-slate-900 border border-slate-800 rounded-xl">
              <span className="text-[11px] font-bold uppercase text-slate-500 block">Survey Number</span>
              <span className="text-base font-bold text-blue-300 font-mono mt-1 block">
                {matchedRec.survey_number}
              </span>
              <span className={`text-xs font-medium ${isReferenceNotFound ? 'text-blue-400' : fieldMatches.survey_number_match ? 'text-emerald-400' : 'text-amber-400'}`}>
                {isReferenceNotFound ? "Not in Demo Layer" : fieldMatches.survey_number_match ? "Cadastral Matched" : "Unmatched"}
              </span>
            </div>

            <div className="p-4 bg-slate-900 border border-slate-800 rounded-xl">
              <span className="text-[11px] font-bold uppercase text-slate-500 block">Registered Land Area</span>
              <span className="text-base font-bold text-white mt-1 block">
                {isReferenceNotFound ? "N/A" : `${matchedRec.land_area_acres} Acres`}
              </span>
              <span className={`text-xs font-medium ${isReferenceNotFound ? 'text-slate-400' : fieldMatches.land_area_match ? 'text-emerald-400' : 'text-rose-400'}`}>
                {isReferenceNotFound ? "No baseline" : fieldMatches.land_area_match ? "Area Matched" : "Area Discrepancy"}
              </span>
            </div>

            <div className="p-4 bg-slate-900 border border-slate-800 rounded-xl">
              <span className="text-[11px] font-bold uppercase text-slate-500 block">Location & District</span>
              <span className="text-base font-bold text-white mt-1 block truncate">
                {matchedRec.village !== "N/A" ? `${matchedRec.village}, ${matchedRec.district}` : "Not Specified"}
              </span>
              <span className="text-xs text-slate-400 font-medium">
                {fieldMatches.spatial_match ? "GIS Boundary Verified" : "Cadastral Layer"}
              </span>
            </div>
          </div>

          {/* Explanation of Detected Issues Box */}
          <div className="bg-slate-900 border border-rose-900/50 rounded-xl p-6 space-y-4 shadow-lg">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="p-2.5 rounded-lg bg-rose-950 text-rose-400 border border-rose-800">
                  <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                  </svg>
                </div>
                <div>
                  <h3 className="text-lg font-extrabold text-white">Explanation of Detected Issues & Anomalies</h3>
                  <p className="text-xs text-rose-300">
                    Rule verification engine flagged {detectedAnomalies.length} anomaly issues.
                  </p>
                </div>
              </div>
            </div>

            <div className="space-y-3 pt-2">
              {detectedAnomalies.map((issue, idx) => (
                <div key={idx} className="p-4 rounded-lg bg-slate-950 border border-slate-800 space-y-1">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <span className="font-bold text-sm text-white">{idx + 1}. {issue.title || issue.type}</span>
                      <span className={`text-[10px] uppercase font-extrabold px-2 py-0.5 rounded ${
                        issue.severity === 'Critical' ? 'bg-rose-950 text-rose-300 border border-rose-800' :
                        issue.severity === 'High' ? 'bg-rose-950/80 text-rose-400 border border-rose-900' :
                        'bg-amber-950 text-amber-300 border border-amber-800'
                      }`}>
                        {issue.severity || 'High'} Priority
                      </span>
                    </div>
                  </div>

                  {issue.expected && (
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-2 text-xs pt-1">
                      <div className="p-2 rounded bg-slate-900 border border-slate-800 text-slate-300">
                        <span className="text-[10px] text-slate-500 uppercase font-bold block">Expected (Government Record)</span>
                        {issue.expected}
                      </div>
                      <div className="p-2 rounded bg-slate-900 border border-slate-800 text-slate-300">
                        <span className="text-[10px] text-slate-500 uppercase font-bold block">Found (Uploaded Document)</span>
                        {issue.found}
                      </div>
                    </div>
                  )}

                  <p className="text-xs text-slate-300 leading-relaxed pt-1">
                    {issue.description}
                  </p>
                </div>
              ))}
            </div>
          </div>
        </>
      )}
    </div>
  );
}
