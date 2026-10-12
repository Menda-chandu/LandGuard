import React from 'react';
import StatusBadge from '../components/StatusBadge';
import RiskScoreBadge from '../components/RiskScoreBadge';
import { mockStats, mockRecentRecords } from '../data/mockData';

export default function Dashboard({ onNavigate }) {
  return (
    <div className="space-y-6">
      {/* Hero Banner / Header */}
      <div className="p-6 rounded-2xl bg-gradient-to-r from-slate-900 via-blue-950 to-slate-900 border border-blue-900/40 relative overflow-hidden shadow-xl">
        <div className="relative z-10 flex flex-col md:flex-row justify-between md:items-center gap-4">
          <div>
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-blue-900/50 border border-blue-700/50 text-blue-300 text-xs font-semibold mb-3">
              <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
              </svg>
              <span>Automated Land Revenue Intelligence</span>
            </div>
            <h2 className="text-2xl md:text-3xl font-extrabold text-white tracking-tight">
              LandGuard Portal
            </h2>
            <p className="text-slate-300 text-sm max-w-2xl mt-1">
              AI-Powered Land Record Validation and Fraud Detection System. Automated OCR deed extraction, revenue registry verification, anomaly detection, and GIS spatial mapping.
            </p>
          </div>

          <button
            onClick={() => onNavigate('upload')}
            className="flex items-center justify-center gap-2 bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 text-white font-semibold text-sm px-5 py-3 rounded-xl shadow-lg shadow-blue-950/60 transition-all shrink-0"
          >
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12" />
            </svg>
            <span>Upload Document to Verify</span>
          </button>
        </div>
      </div>

      {/* Synthetic Demonstration Notice */}
      <div className="p-4 rounded-xl bg-amber-950/30 border border-amber-800/50 text-amber-200/90 text-xs flex items-start gap-3 shadow-sm">
        <span className="text-lg leading-none mt-0.5">⚠️</span>
        <div className="space-y-0.5">
          <p className="font-bold text-amber-300">Synthetic / Demonstration Dataset Notice</p>
          <p className="text-slate-300">
            All 100 test scenarios, survey numbers, parcel boundaries, ownership histories, and anomaly flags displayed in this portal are <strong>synthetically generated demo data</strong>. The computed risk scores and validation results demonstrate the AI fraud-detection pipeline and <strong>do not represent official government records or certification</strong>.
          </p>
        </div>
      </div>

      {/* Stats Summary Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Total Documents */}
        <div className="p-5 rounded-xl bg-slate-900 border border-slate-800 flex flex-col justify-between space-y-3 shadow-md">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold uppercase text-slate-400">Total Checked</span>
            <div className="p-2 rounded-lg bg-blue-950 text-blue-400 border border-blue-800">
              <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
            </div>
          </div>
          <div>
            <div className="text-3xl font-black text-white">{mockStats.totalChecked.toLocaleString()}</div>
            <p className="text-xs text-slate-400 mt-1">Processed across districts</p>
          </div>
        </div>

        {/* Verified Records */}
        <div className="p-5 rounded-xl bg-slate-900 border border-slate-800 flex flex-col justify-between space-y-3 shadow-md">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold uppercase text-slate-400">Verified Records</span>
            <div className="p-2 rounded-lg bg-emerald-950 text-emerald-400 border border-emerald-800">
              <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
          </div>
          <div>
            <div className="text-3xl font-black text-emerald-400">{mockStats.verifiedRecords.toLocaleString()}</div>
            <p className="text-xs text-emerald-500/80 mt-1">88.9% Clean title rate</p>
          </div>
        </div>

        {/* Suspicious Records */}
        <div className="p-5 rounded-xl bg-slate-900 border border-slate-800 flex flex-col justify-between space-y-3 shadow-md">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold uppercase text-slate-400">Suspicious Flags</span>
            <div className="p-2 rounded-lg bg-rose-950 text-rose-400 border border-rose-800">
              <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
              </svg>
            </div>
          </div>
          <div>
            <div className="text-3xl font-black text-rose-400">{mockStats.suspiciousRecords.toLocaleString()}</div>
            <p className="text-xs text-rose-500/80 mt-1">Flagged for revenue audit</p>
          </div>
        </div>

        {/* Average Risk Score */}
        <div className="p-5 rounded-xl bg-slate-900 border border-slate-800 flex flex-col justify-between space-y-3 shadow-md">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold uppercase text-slate-400">Avg Risk Index</span>
            <div className="p-2 rounded-lg bg-amber-950 text-amber-400 border border-amber-800">
              <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
              </svg>
            </div>
          </div>
          <div>
            <div className="text-3xl font-black text-amber-400">{mockStats.averageRiskScore} <span className="text-base font-normal text-slate-400">/ 100</span></div>
            <p className="text-xs text-emerald-400 mt-1">Overall Low System Risk</p>
          </div>
        </div>
      </div>

      {/* Recent Verification Results Table */}
      <div className="bg-slate-900 rounded-xl border border-slate-800 overflow-hidden shadow-lg">
        <div className="p-5 border-b border-slate-800 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div>
            <h3 className="text-lg font-bold text-white">Recent Verification Results</h3>
            <p className="text-xs text-slate-400">Latest land title deeds processed by AI OCR & Validation Engine</p>
          </div>
          <button 
            onClick={() => onNavigate('verification')}
            className="text-xs font-semibold text-blue-400 hover:text-blue-300 flex items-center gap-1"
          >
            <span>View Full Verification Log</span>
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
            </svg>
          </button>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs md:text-sm">
            <thead className="bg-slate-950/80 text-slate-400 text-xs uppercase tracking-wider border-b border-slate-800">
              <tr>
                <th className="p-4">Document ID / File</th>
                <th className="p-4">Survey No.</th>
                <th className="p-4">Claimed Owner</th>
                <th className="p-4">District</th>
                <th className="p-4">Status</th>
                <th className="p-4">Risk Score</th>
                <th className="p-4 text-right">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 font-medium text-slate-300">
              {mockRecentRecords.map((record) => (
                <tr key={record.id} className="hover:bg-slate-800/40 transition-colors">
                  <td className="p-4">
                    <div className="font-semibold text-white">{record.id}</div>
                    <div className="text-xs text-slate-500 font-mono">{record.documentName}</div>
                  </td>
                  <td className="p-4">
                    <span className="font-mono text-xs font-bold px-2 py-1 rounded bg-slate-800 border border-slate-700 text-blue-300">
                      {record.surveyNumber}
                    </span>
                  </td>
                  <td className="p-4">{record.ownerName}</td>
                  <td className="p-4 text-slate-400">{record.district}</td>
                  <td className="p-4">
                    <StatusBadge status={record.status} />
                  </td>
                  <td className="p-4">
                    <RiskScoreBadge score={record.riskScore} size="sm" />
                  </td>
                  <td className="p-4 text-right">
                    <button
                      onClick={() => onNavigate('verification')}
                      className="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-blue-600 hover:text-white text-slate-300 text-xs font-medium border border-slate-700 transition-colors"
                    >
                      View Report
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
