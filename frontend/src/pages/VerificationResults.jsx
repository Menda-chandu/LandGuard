import React, { useEffect, useState } from 'react';
import StatusBadge from '../components/StatusBadge';
import EvidenceChecks from '../components/EvidenceChecks';
import { getVerificationApi } from '../api/config';

export default function VerificationResults({ activeDocument, verificationResult, onVerificationComplete, onNavigate }) {
  const [verData, setVerData] = useState(verificationResult);
  const [isLoading, setIsLoading] = useState(false);

  const [error, setError] = useState(null);
  useEffect(() => {
    let cancelled = false;
    setError(null);
    if (verificationResult?.document_id === activeDocument?.document_id) {
      setVerData(verificationResult);
      return;
    }
    setVerData(null);
    setIsLoading(true);
    getVerificationApi(activeDocument.document_id)
      .then(data => {
        if (cancelled) return;
        setVerData(data);
        onVerificationComplete?.(data);
        setIsLoading(false);
      })
      .catch(err => { if (!cancelled) { setError(err.message); setIsLoading(false); } });
    return () => { cancelled = true; };
  }, [activeDocument, verificationResult, onVerificationComplete]);

  if (error) return <div role="alert" className="p-6 rounded-xl bg-rose-950 text-rose-200">{error}</div>;
  const docId = activeDocument.document_id;
  const verStatus = verData?.verification_status || 'PENDING';
  const matchedRec = verData?.matched_land_record || {};
  const fieldMatches = verData?.field_matches || {};
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
            Automated cross-matching of deed attributes against the imported synthetic land registry ({docId}).
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

      {isLoading ? (
        <div className="p-12 bg-slate-900 border border-slate-800 rounded-xl text-center text-slate-400 text-sm animate-pulse">
          Cross-matching deed details against land registry database...
        </div>
      ) : (
        <>
          <EvidenceChecks documentId={docId} checks={verData?.evidence_checks} onVerified={result => { setVerData(result); onVerificationComplete?.(result); }} />
          {/* Key Attributes Summary Bar */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="p-4 bg-slate-900 border border-slate-800 rounded-xl">
              <span className="text-[11px] font-bold uppercase text-slate-500 block">Owner Name Match</span>
              <span className="text-base font-bold text-white mt-1 block">
                {fieldMatches.owner_match ? "Matched" : "Mismatch"}
              </span>
              <span className={`text-xs font-medium ${fieldMatches.owner_match ? 'text-emerald-400' : 'text-rose-400'}`}>
                Registry: {matchedRec.owner_name || 'No matching record'}
              </span>
            </div>

            <div className="p-4 bg-slate-900 border border-slate-800 rounded-xl">
              <span className="text-[11px] font-bold uppercase text-slate-500 block">Survey Number</span>
              <span className="text-base font-bold text-blue-300 font-mono mt-1 block">
                {matchedRec.survey_number || 'Not matched'}
              </span>
              <span className="text-xs text-slate-400 font-medium">{fieldMatches.survey_number_match ? "Survey matched" : "Survey not matched"}</span>
            </div>

            <div className="p-4 bg-slate-900 border border-slate-800 rounded-xl">
              <span className="text-[11px] font-bold uppercase text-slate-500 block">Registered Land Area</span>
              <span className="text-base font-bold text-white mt-1 block">
                {matchedRec.land_area_acres == null ? 'Not matched' : `${matchedRec.land_area_acres} Acres`}
              </span>
              <span className={`text-xs font-medium ${fieldMatches.land_area_match ? 'text-emerald-400' : 'text-rose-400'}`}>
                {fieldMatches.land_area_match ? "Area Matched" : "Area Discrepancy"}
              </span>
            </div>

            <div className="p-4 bg-slate-900 border border-slate-800 rounded-xl">
              <span className="text-[11px] font-bold uppercase text-slate-500 block">Location & District</span>
              <span className="text-base font-bold text-white mt-1 block truncate">
                {matchedRec.village || 'Not matched'}{matchedRec.district ? `, ${matchedRec.district}` : ''}
              </span>
              <span className="text-xs text-slate-400 font-medium">{fieldMatches.spatial_match ? "Parcel location matched" : "Parcel location not matched"}</span>
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
