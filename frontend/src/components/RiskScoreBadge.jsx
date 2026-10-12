import React from 'react';

export default function RiskScoreBadge({ score, size = "md" }) {
  let level = "LOW";
  let colorClass = "text-emerald-400 bg-emerald-950/60 border-emerald-800";
  let barColor = "bg-emerald-500";

  if (score >= 80) {
    level = "CRITICAL";
    colorClass = "text-purple-400 bg-purple-950/60 border-purple-800";
    barColor = "bg-purple-500";
  } else if (score >= 60) {
    level = "HIGH";
    colorClass = "text-rose-400 bg-rose-950/60 border-rose-800";
    barColor = "bg-rose-500";
  } else if (score >= 30) {
    level = "MEDIUM";
    colorClass = "text-amber-400 bg-amber-950/60 border-amber-800";
    barColor = "bg-amber-500";
  }

  if (size === "sm") {
    return (
      <div className={`inline-flex items-center gap-2 px-2.5 py-1 rounded-md border font-medium text-xs ${colorClass}`}>
        <span className="font-bold">{score}%</span>
        <span>•</span>
        <span>{level}</span>
      </div>
    );
  }

  return (
    <div className={`p-4 rounded-xl border ${colorClass} flex flex-col gap-2`}>
      <div className="flex items-center justify-between">
        <span className="text-xs uppercase tracking-wider font-semibold opacity-80">Fraud Risk Index</span>
        <span className="text-sm font-bold px-2 py-0.5 rounded bg-slate-900/60 border border-slate-700">{level}</span>
      </div>
      <div className="flex items-baseline gap-2">
        <span className="text-3xl font-black">{score}</span>
        <span className="text-xs opacity-75">/ 100 Risk Points</span>
      </div>
      {/* Progress meter */}
      <div className="w-full bg-slate-800/80 rounded-full h-2 overflow-hidden mt-1">
        <div 
          className={`h-full ${barColor} transition-all duration-500 rounded-full`}
          style={{ width: `${score}%` }}
        />
      </div>
      <div className="flex justify-between text-[10px] text-slate-400 font-medium pt-1">
        <span className="text-emerald-400">0 - 29 LOW</span>
        <span className="text-amber-400">30 - 59 MEDIUM</span>
        <span className="text-rose-400">60 - 79 HIGH</span>
        <span className="text-purple-400">80 - 100 CRITICAL</span>
      </div>
    </div>
  );
}
