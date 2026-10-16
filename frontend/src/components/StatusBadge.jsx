import React from 'react';

export default function StatusBadge({ status }) {
  let badgeClass = "bg-slate-700 text-slate-300 border-slate-600";
  let dotClass = "bg-slate-400";

  switch (status?.toLowerCase()) {
    case 'verified':
      badgeClass = "bg-emerald-950/80 text-emerald-300 border-emerald-800/80";
      dotClass = "bg-emerald-400";
      break;
    case 'suspicious':
    case 'flagged suspicious':
      badgeClass = "bg-rose-950/80 text-rose-300 border-rose-800/80";
      dotClass = "bg-rose-400";
      break;
    case 'review needed':
    case 'warning':
      badgeClass = "bg-amber-950/80 text-amber-300 border-amber-800/80";
      dotClass = "bg-amber-400";
      break;
    case 'active encumbrance':
      badgeClass = "bg-purple-950/80 text-purple-300 border-purple-800/80";
      dotClass = "bg-purple-400";
      break;
    case 'reference_not_found':
    case 'reference not found':
      badgeClass = "bg-blue-950/80 text-blue-300 border-blue-800/80";
      dotClass = "bg-blue-400";
      break;
    case 'unverified':
    case 'inconclusive':
      badgeClass = "bg-slate-800 text-slate-300 border-slate-700";
      dotClass = "bg-slate-400";
      break;
    default:
      break;
  }

  return (
    <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 text-xs font-semibold rounded-full border ${badgeClass}`}>
      <span className={`w-1.5 h-1.5 rounded-full ${dotClass}`}></span>
      {status}
    </span>
  );
}
