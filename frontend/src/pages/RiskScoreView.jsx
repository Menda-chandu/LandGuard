import React, { useEffect, useState } from 'react';
import RiskScoreBadge from '../components/RiskScoreBadge';
import { getRiskAssessmentApi } from '../api/config';
import { mockRiskBreakdown } from '../data/mockData';

const ANOMALY_WEIGHTS = {
  OWNER_NAME_MISMATCH: 25,
  SURVEY_NUMBER_MISMATCH: 25,
  SURVEY_NOT_FOUND: 25,
  LAND_AREA_MISMATCH: 20,
  DUPLICATE_REGISTRATION_FLAGGED: 30,
  RAPID_OWNERSHIP_TRANSFER: 15,
  UNFOUND_SELLER_IN_HISTORY: 15,
  MISSING_HISTORICAL_TITLE_CHAIN: 15,
  INCOMPLETE_DOCUMENT_DATA: 10,
  SPATIAL_LOCATION_MISMATCH: 20,
  GIS_PARCEL_NOT_FOUND: 15,
  DOCUMENT_NOT_FOUND: 30
};

const DEFAULT_FALLBACK_ANOMALIES = [
  {
    anomaly_type: "OWNER_NAME_MISMATCH",
    title: "Ownership Identity Mismatch",
    severity: "High",
    points_added: 25,
    description: "Document claims ownership under an executant differing from official Revenue Registry."
  },
  {
    anomaly_type: "LAND_AREA_MISMATCH",
    title: "Land Area Inflation Anomaly",
    severity: "High",
    points_added: 20,
    description: "Document claims land extent exceeding the official Cadastral map parcel boundary."
  }
];

export default function RiskScoreView({ activeDocument, verificationResult }) {
  const [riskData, setRiskData] = useState(null);
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    const docId = activeDocument?.document_id || "DOC-2026-8901";
    setIsLoading(true);
    getRiskAssessmentApi(docId)
      .then((data) => {
        setRiskData(data);
        setIsLoading(false);
      })
      .catch((err) => {
        console.warn("Risk API notice:", err.message);
        setIsLoading(false);
      });
  }, [activeDocument]);

  const docId = activeDocument?.document_id || riskData?.document_id || "DOC-UNASSIGNED";

  // Derive breakdown from live risk data, shared verification result, or aligned fallback
  const breakdown = (riskData?.scoring_breakdown && riskData.scoring_breakdown.length > 0)
    ? riskData.scoring_breakdown
    : (verificationResult?.detected_anomalies && verificationResult.detected_anomalies.length > 0)
    ? verificationResult.detected_anomalies.map((a) => ({
        anomaly_type: a.type || a.title || "ANOMALY",
        title: a.title || a.type,
        severity: a.severity || "High",
        points_added: ANOMALY_WEIGHTS[a.type] || (a.severity === "Critical" ? 30 : a.severity === "High" ? 25 : 15),
        description: a.description || ""
      }))
    : activeDocument
    ? []
    : DEFAULT_FALLBACK_ANOMALIES;

  // Calculate score dynamically from breakdown weights instead of a disconnected static number
  const computedPointsSum = breakdown.reduce((sum, item) => sum + (Number(item.points_added) || 0), 0);
  const score = riskData?.risk_score != null ? riskData.risk_score : Math.min(computedPointsSum, 100);

  // Normalize risk level category for consistent UI threshold highlights
  const rawLevel = riskData?.risk_level || (score >= 80 ? 'CRITICAL' : score >= 60 ? 'HIGH' : score >= 30 ? 'MEDIUM' : 'LOW');
  const normalizedLevel = (rawLevel || '').toUpperCase().replace(' RISK', '').trim();

  const recommendation = riskData?.recommendation || (
    normalizedLevel === 'LOW' ? "No major inconsistency detected" :
    normalizedLevel === 'MEDIUM' ? "Manual review recommended" :
    normalizedLevel === 'HIGH' ? "Further verification required" :
    "Immediate detailed verification required"
  );

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h2 className="text-2xl font-extrabold text-white tracking-tight">Risk Score & Fraud Audit</h2>
        <p className="text-sm text-slate-400 mt-1">
          Explainable risk scoring breakdown for document ({docId}) calculated by summing weights of detected anomalies.
        </p>
      </div>

      {isLoading ? (
        <div className="p-12 bg-slate-900 border border-slate-800 rounded-xl text-center text-slate-400 text-sm animate-pulse">
          Computing explainable risk assessment score...
        </div>
      ) : (
        <>
          {/* Visual Risk Gauge & Status Banner */}
          <div className="grid grid-cols-1 md:grid-cols-12 gap-6">
            <div className="md:col-span-5">
              <RiskScoreBadge score={score} />
            </div>

            {/* Risk Categories Visual Meter */}
            <div className="md:col-span-7 bg-slate-900 border border-slate-800 rounded-xl p-6 flex flex-col justify-between space-y-4">
              <div>
                <h3 className="text-sm font-bold uppercase tracking-wider text-slate-300 mb-2">
                  Risk Level Category Thresholds
                </h3>
                <div className="grid grid-cols-4 gap-2">
                  <div className={`p-2.5 rounded-lg border text-center space-y-0.5 ${normalizedLevel === 'LOW' ? 'ring-2 ring-emerald-500 bg-emerald-950/60' : 'bg-slate-950 border-slate-800'}`}>
                    <span className="text-[11px] font-bold text-emerald-400 block">LOW</span>
                    <span className="text-sm font-black text-emerald-300">0 - 29</span>
                  </div>

                  <div className={`p-2.5 rounded-lg border text-center space-y-0.5 ${normalizedLevel === 'MEDIUM' ? 'ring-2 ring-amber-500 bg-amber-950/60' : 'bg-slate-950 border-slate-800'}`}>
                    <span className="text-[11px] font-bold text-amber-400 block">MEDIUM</span>
                    <span className="text-sm font-black text-amber-300">30 - 59</span>
                  </div>

                  <div className={`p-2.5 rounded-lg border text-center space-y-0.5 ${normalizedLevel === 'HIGH' ? 'ring-2 ring-rose-500 bg-rose-950/60' : 'bg-slate-950 border-slate-800'}`}>
                    <span className="text-[11px] font-bold text-rose-400 block">HIGH</span>
                    <span className="text-sm font-black text-rose-300">60 - 79</span>
                  </div>

                  <div className={`p-2.5 rounded-lg border text-center space-y-0.5 ${normalizedLevel === 'CRITICAL' ? 'ring-2 ring-purple-500 bg-purple-950/60' : 'bg-slate-950 border-slate-800'}`}>
                    <span className="text-[11px] font-bold text-purple-400 block">CRITICAL</span>
                    <span className="text-sm font-black text-purple-300">80 - 100</span>
                  </div>
                </div>
              </div>

              <div className="p-3 rounded-lg bg-slate-950 border border-slate-800 text-xs text-slate-300 flex items-center justify-between">
                <div>
                  <span className="font-bold text-blue-400 block">Verification Recommendation:</span>
                  <span className="text-sm font-bold text-white">{recommendation}</span>
                </div>
                <span className="text-xs font-mono font-bold px-3 py-1 bg-slate-800 rounded border border-slate-700 text-slate-300">
                  {score} / 100 Pts
                </span>
              </div>
            </div>
          </div>

          {/* Transparent Point Breakdown Table */}
          <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 space-y-4">
            <h3 className="text-base font-bold text-white">Transparent Anomaly Point Breakdown</h3>

            <div className="space-y-3">
              {breakdown.map((item, idx) => (
                <div key={idx} className="p-4 rounded-xl bg-slate-950 border border-slate-800 space-y-1">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <span className="text-sm font-bold text-white">{item.title || item.anomaly_type}</span>
                      <span className="text-xs font-bold px-2 py-0.5 rounded bg-rose-950 text-rose-400 border border-rose-800">
                        +{item.points_added} Points Added
                      </span>
                    </div>
                    <span className="text-xs text-slate-400 font-mono">{item.severity || 'High'} Severity</span>
                  </div>
                  <p className="text-xs text-slate-400 leading-relaxed pt-1">
                    {item.description}
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
