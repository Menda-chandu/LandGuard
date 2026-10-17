import React, { useCallback, useEffect, useState } from 'react';
import { Database, FileText, History, MapPin, RefreshCw, Upload } from 'lucide-react';
import StatusBadge from '../components/StatusBadge';
import RiskScoreBadge from '../components/RiskScoreBadge';
import { getDashboardApi, getDocumentApi, getDocumentNlpApi } from '../api/config';

export default function Dashboard({ onNavigate, onSelectDocument }) {
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(true);
  const [openingDocument, setOpeningDocument] = useState(null);
  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try { setData(await getDashboardApi()); }
    catch (err) { setData(null); setError(err.message); }
    finally { setLoading(false); }
  }, []);
  useEffect(() => { load(); }, [load]);

  const openDocument = async (documentId) => {
    setOpeningDocument(documentId);
    try {
      const [doc, nlp] = await Promise.all([getDocumentApi(documentId), getDocumentNlpApi(documentId)]);
      onSelectDocument({ ...doc, extracted_nlp_fields: nlp.extracted_attributes,
        extracted_fields: nlp.extracted_attributes, nlp_confidence_score: nlp.nlp_confidence_score });
    } catch (err) { setError(err.message); }
    finally { setOpeningDocument(null); }
  };
  const stats = data?.stats;
  const cards = [
    ['Land records', stats?.land_records, 'Registry entries loaded from the dataset', Database],
    ['Ownership history', stats?.ownership_history, 'Recorded title transfers', History],
    ['Mapped parcels', stats?.parcels, 'Boundaries from the dataset GeoJSON', MapPin],
    ['Uploaded documents', stats?.uploaded_documents, 'Files saved by this application', FileText],
  ];
  return (
    <div className="space-y-6">
      <div className="p-6 rounded-2xl bg-gradient-to-r from-slate-900 via-blue-950 to-slate-900 border border-blue-900/40 flex flex-col md:flex-row justify-between gap-4">
        <div>
          <span className="text-xs font-semibold text-blue-300">Imported synthetic dataset</span>
          <h2 className="text-2xl md:text-3xl font-extrabold text-white mt-2">LandGuard Portal</h2>
          <p className="text-sm text-slate-300 mt-2 max-w-2xl">Browse the loaded land records and parcel boundaries, then upload a deed to compare its details with the registry.</p>
          <p className="text-xs text-slate-400 mt-3">{data ? 'Connected to the local database' : loading ? 'Connecting to the database…' : 'Database unavailable'}</p>
        </div>
        <div className="flex items-center gap-3 shrink-0">
          <button onClick={load} disabled={loading} aria-label="Refresh dashboard" className="p-3 rounded-xl bg-slate-800 border border-slate-700 text-slate-300 disabled:opacity-50"><RefreshCw size={18} className={loading ? 'animate-spin' : ''} /></button>
          <button onClick={() => onNavigate('upload')} className="flex items-center gap-2 bg-blue-600 hover:bg-blue-500 text-white font-semibold text-sm px-5 py-3 rounded-xl"><Upload size={18} />Upload Document to Verify</button>
        </div>
      </div>
      {error && <div role="alert" className="p-4 rounded-xl bg-rose-950/50 border border-rose-800 text-sm text-rose-200">{error}</div>}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {cards.map(([label, value, description, Icon]) => (
          <div key={label} className="p-5 rounded-xl bg-slate-900 border border-slate-800 space-y-3">
            <div className="flex justify-between items-center"><span className="text-xs font-semibold uppercase text-slate-400">{label}</span><Icon size={20} className="text-blue-400" /></div>
            <div className="text-3xl font-black text-white">{value == null ? '—' : value.toLocaleString()}</div>
            <p className="text-xs text-slate-400">{description}</p>
          </div>
        ))}
      </div>
      <div className="p-4 rounded-xl bg-amber-950/30 border border-amber-800/50 text-xs text-amber-200">All imported records and document fixtures are synthetic. Verification results are calculated only after a document is checked; importing registry records does not verify them.</div>
      <section className="bg-slate-900 rounded-xl border border-slate-800 overflow-hidden">
        <div className="p-5 border-b border-slate-800">
          <h3 className="text-lg font-bold text-white">Loaded Land Registry</h3>
          <p className="text-xs text-slate-400 mt-1">Showing {data?.registry_preview.length ?? 0} of {stats?.land_records ?? '—'} records. Search by owner, survey number, or record ID using the search bar.</p>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs md:text-sm">
            <thead className="bg-slate-950/80 text-slate-400 uppercase text-xs"><tr>{['Record ID', 'Survey No.', 'Registered Owner', 'Area (acres)', 'Village', 'District'].map(label => <th key={label} className="p-4">{label}</th>)}</tr></thead>
            <tbody className="divide-y divide-slate-800 text-slate-300">
              {data?.registry_preview.map(record => <tr key={record.record_id} className="hover:bg-slate-800/40">
                <td className="p-4 font-mono text-blue-300">{record.record_id}</td><td className="p-4 font-mono">{record.survey_number}</td><td className="p-4 text-white">{record.owner_name || 'Not recorded'}</td><td className="p-4">{record.land_area_acres}</td><td className="p-4">{record.village}</td><td className="p-4">{record.district}</td>
              </tr>)}
              {data && data.registry_preview.length === 0 && <tr><td colSpan={6} className="p-6 text-slate-400">No land records loaded.</td></tr>}
            </tbody>
          </table>
        </div>
      </section>
      <section className="bg-slate-900 rounded-xl border border-slate-800 overflow-hidden">
        <div className="p-5 border-b border-slate-800">
          <h3 className="text-lg font-bold text-white">Recent Uploaded Documents</h3>
          <p className="text-xs text-slate-400 mt-1">{stats?.checked_documents ?? '—'} checked · {stats?.verified_documents ?? '—'} verified · {stats?.suspicious_documents ?? '—'} suspicious · Average assessed risk: {stats?.average_risk_score == null ? 'not assessed' : `${stats.average_risk_score}/100`}</p>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs md:text-sm">
            <thead className="bg-slate-950/80 text-slate-400 uppercase text-xs"><tr>{['Document', 'Survey No.', 'Claimed Owner', 'Verification', 'Risk Score', 'Action'].map(label => <th key={label} className="p-4">{label}</th>)}</tr></thead>
            <tbody className="divide-y divide-slate-800 text-slate-300">
              {data?.recent_documents.map(doc => <tr key={doc.document_id} className="hover:bg-slate-800/40">
                <td className="p-4"><div className="font-semibold text-white">{doc.filename}</div><div className="text-xs text-slate-500 font-mono mt-1">{doc.document_id}</div></td>
                <td className="p-4 font-mono">{doc.survey_number || 'Not extracted'}</td><td className="p-4">{doc.owner_name || 'Not extracted'}</td>
                <td className="p-4"><StatusBadge status={doc.verification_status.replaceAll('_', ' ')} /></td>
                <td className="p-4">{doc.risk_score == null ? 'Not assessed' : <RiskScoreBadge score={doc.risk_score} size="sm" />}</td>
                <td className="p-4"><button onClick={() => openDocument(doc.document_id)} disabled={openingDocument !== null} className="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-blue-600 text-white text-xs border border-slate-700 disabled:opacity-50">{openingDocument === doc.document_id ? 'Opening…' : 'View Report'}</button></td>
              </tr>)}
              {data && data.recent_documents.length === 0 && <tr><td colSpan={6} className="p-6 text-slate-400">No documents uploaded yet. Choose a dataset sample or upload a deed to begin.</td></tr>}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
}
