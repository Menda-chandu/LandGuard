import React from 'react';

export default function RegistryRecord({ record, onViewMap, onUpload }) {
  return <div className="space-y-6">
    <div><h2 className="text-2xl font-extrabold text-white">Land Registry Record</h2><p className="text-sm text-slate-400 mt-2">Reference data from the imported synthetic dataset. Upload a deed to compare its contents with this registry.</p></div>
    <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
      {[
        ['Record ID', record.record_id], ['Registered owner', record.owner_name],
        ['Survey number', record.survey_number], ['Area (acres)', record.land_area_acres],
        ['Village / Mandal', `${record.village}, ${record.mandal}`], ['District / State', `${record.district}, ${record.state}`],
        ['Registration number', record.registration_number], ['Registration date', record.registration_date],
      ].map(([label, value]) => <div key={label} className="p-4 bg-slate-900 border border-slate-800 rounded-xl"><p className="text-xs text-slate-400">{label}</p><p className="text-base font-semibold text-white mt-2">{value ?? 'Not recorded'}</p></div>)}
    </div>
    <div className="flex flex-wrap gap-3"><button onClick={onViewMap} className="px-4 py-2 bg-slate-800 rounded-lg text-sm text-white">View parcel map</button><button onClick={onUpload} className="px-4 py-2 bg-blue-600 rounded-lg text-sm text-white">Upload deed for comparison</button></div>
    <section className="bg-slate-900 border border-slate-800 rounded-xl p-5"><h3 className="text-lg font-bold text-white">Recorded Ownership History</h3>
      {record.history_timeline.length === 0 ? <p className="text-sm text-slate-400 mt-3">No transfers recorded for this survey number.</p> : <ol className="divide-y divide-slate-800 mt-3">{record.history_timeline.map(item => <li key={item.history_id} className="py-3"><p className="text-white font-semibold">{item.owner_name}</p><p className="text-xs text-slate-400 mt-1">{item.transfer_date || 'Date not recorded'} · {item.transfer_type} · {item.history_id}</p></li>)}</ol>}
    </section>
  </div>;
}
