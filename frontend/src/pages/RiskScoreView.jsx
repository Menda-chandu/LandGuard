import React, { useEffect, useState } from 'react';
import RiskScoreBadge from '../components/RiskScoreBadge';
import { getRiskAssessmentApi } from '../api/config';

export default function RiskScoreView({ activeDocument }) {
  const [riskData, setRiskData] = useState(null);
  const [isLoading, setIsLoading] = useState(false);

  const [error, setError] = useState(null);
  useEffect(() => {
    let cancelled = false;
    setRiskData(null);
    setError(null);
    setIsLoading(true);
    getRiskAssessmentApi(activeDocument.document_id)
      .then(data => { if (!cancelled) { setRiskData(data); setIsLoading(false); } })
      .catch(err => { if (!cancelled) { setError(err.message); setIsLoading(false); } });
    return () => { cancelled = true; };
  }, [activeDocument]);
  if (error) return <div role="alert" className="p-6 rounded-xl bg-rose-950 text-rose-200">{error}</div>;
  const docId = activeDocument.document_id;
  const breakdown = riskData?.scoring_breakdown || [];
  const score = riskData?.risk_score;
  const normalizedLevel = riskData?.risk_level;
  const recommendation = riskData?.recommendation;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h2 className="text-2xl font-extrabold text-white tracking-tight">Risk Score & Fraud Audit</h2>
        <p className="text-sm text-slate-400 mt-1">
          Explainable risk scoring breakdown for document ({docId}) calculated by summing weights of detected anomalies.
        </p>
      </div>

      {isLoading || !riskData ? (
        <div className="p-12 bg-slate-900 border border-slate-800 rounded-xl text-center text-slate-400 text-sm animate-pulse">
          Computing explainable risk assessment score...
        </div>
      ) : (
        <>
          <div className="p-4 rounded-xl bg-slate-900 border border-slate-800 text-sm text-slate-300 space-y-2">
            <h3 className="font-bold text-white">AI anomaly assessment</h3>
            {riskData.ml_assessment?.status === 'ASSESSED' ? <>
              <p>Isolation Forest trained on {riskData.ml_assessment.training_records} imported reference records. Outlier percentile: {riskData.ml_assessment.outlier_percentile}. Added risk points: {riskData.ml_assessment.risk_points}.</p>
              {riskData.ml_assessment.explanation?.map(item => <p className="text-xs" key={item.feature}>{item.feature}: {item.document_value} (reference median {item.reference_median})</p>)}
              <p className="text-xs text-amber-200">{riskData.ml_assessment.limitation}</p>
            </> : <p>Insufficient reference data for the AI model. The displayed score uses explainable verification rules.</p>}
            <p className="text-xs text-slate-400">This score reflects available evidence. Review Verification Results for unchecked fields.</p>
          </div>
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
