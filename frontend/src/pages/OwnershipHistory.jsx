import React, { useEffect, useState } from 'react';
import StatusBadge from '../components/StatusBadge';
import { getOwnershipHistoryApi } from '../api/config';
import { mockOwnershipTimeline } from '../data/mockData';

export default function OwnershipHistory({ activeDocument }) {
  const [historyData, setHistoryData] = useState(null);
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    const docId = activeDocument?.document_id || "DOC-2026-8901";
    setIsLoading(true);
    getOwnershipHistoryApi(docId)
      .then((data) => {
        setHistoryData(data);
        setIsLoading(false);
      })
      .catch((err) => {
        console.warn("History API notice:", err.message);
        setIsLoading(false);
      });
  }, [activeDocument]);

  const surveyNo = historyData?.survey_number || activeDocument?.extracted_nlp_fields?.survey_number || "402/B";

  const timelineItems = (historyData?.history_timeline && historyData.history_timeline.length > 0)
    ? historyData.history_timeline.map((h, idx) => ({
        year: h.transfer_date ? h.transfer_date.split('-')[0] : "2023",
        date: h.transfer_date || "2023-04-10",
        event: h.transfer_type || "Sale Deed",
        parties: `Registered Owner: ${h.owner_name}`,
        surveyNo: h.survey_number,
        area: "Registered Parcel",
        documentRef: h.history_id,
        status: h.transfer_type.includes("Duplicate") || h.transfer_type.includes("Rapid") ? "Flagged Suspicious" : "Verified"
      }))
    : mockOwnershipTimeline;

  return (
    <div className="space-y-6 max-w-5xl mx-auto">
      {/* Header */}
      <div>
        <div className="flex items-center gap-2">
          <h2 className="text-2xl font-extrabold text-white tracking-tight">Ownership History Chain</h2>
          <span className="px-2.5 py-0.5 rounded text-xs font-mono font-bold bg-blue-950 text-blue-300 border border-blue-800">
            Survey No. {surveyNo}
          </span>
        </div>
        <p className="text-sm text-slate-400 mt-1">
          Historical title chain timeline tracking land transfers, mutations, encumbrances, and grants from PostgreSQL ownership_history.
        </p>
      </div>

      {isLoading ? (
        <div className="p-12 bg-slate-900 border border-slate-800 rounded-xl text-center text-slate-400 text-sm animate-pulse">
          Fetching historical title chain records...
        </div>
      ) : (
        /* Timeline View */
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 md:p-8 relative shadow-xl">
          <div className="space-y-8 relative before:absolute before:inset-0 before:left-4 md:before:left-1/2 before:-translate-x-px before:h-full before:w-0.5 before:bg-slate-800">
            {timelineItems.map((item, idx) => {
              const isFlagged = item.status.includes('Flagged') || item.status.includes('Encumbrance');

              return (
                <div key={idx} className="relative flex flex-col md:flex-row items-start md:items-center group">
                  {/* Timeline Dot */}
                  <div className={`absolute left-4 md:left-1/2 -translate-x-1/2 w-8 h-8 rounded-full border-4 flex items-center justify-center font-bold text-xs shadow-md z-10 transition-all ${
                    isFlagged 
                      ? 'bg-rose-950 border-rose-500 text-rose-300 ring-4 ring-rose-950' 
                      : 'bg-emerald-950 border-emerald-500 text-emerald-300 ring-4 ring-slate-900'
                  }`}>
                    {idx + 1}
                  </div>

                  {/* Left Card */}
                  <div className={`w-full md:w-1/2 pl-12 md:pl-0 ${idx % 2 === 0 ? 'md:pr-10 md:text-right' : 'md:order-2 md:pl-10 text-left'}`}>
                    <div className={`p-5 rounded-xl border transition-all ${
                      isFlagged 
                        ? 'bg-rose-950/30 border-rose-900/60 hover:border-rose-700' 
                        : 'bg-slate-950 border-slate-800 hover:border-slate-700'
                    }`}>
                      <div className="flex items-center justify-between gap-2 mb-2">
                        <span className="text-xs font-mono font-bold text-blue-400">{item.date}</span>
                        <StatusBadge status={item.status} />
                      </div>

                      <h3 className="text-base font-bold text-white mb-1">{item.event}</h3>
                      <p className="text-xs font-medium text-slate-300">{item.parties}</p>

                      <div className="mt-3 pt-3 border-t border-slate-800/80 grid grid-cols-2 gap-2 text-[11px]">
                        <div>
                          <span className="text-slate-500 block font-semibold">Survey Sub-division</span>
                          <span className="text-slate-200 font-mono">{item.surveyNo || surveyNo}</span>
                        </div>
                        <div>
                          <span className="text-slate-500 block font-semibold">Transfer Record ID</span>
                          <span className="text-slate-300 font-mono truncate">{item.documentRef}</span>
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* Empty Spacer */}
                  <div className={`hidden md:block w-1/2 ${idx % 2 === 0 ? 'order-2 pl-10' : 'pr-10 text-right'}`}>
                    <div className="text-xs font-bold text-slate-500 uppercase tracking-widest px-2">
                      {item.year} Transfer Record
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}
