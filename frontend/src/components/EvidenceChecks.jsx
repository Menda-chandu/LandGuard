import React, { useState } from 'react';
import { setDocumentBoundaryApi } from '../api/config';

const label = status => (status || 'NOT_CHECKED').replaceAll('_', ' ').toLowerCase();

export default function EvidenceChecks({ documentId, checks = {}, onVerified }) {
  const [error, setError] = useState(null);
  const [busy, setBusy] = useState(false);
  const geometry = checks.boundary_geometry || {};
  const attachBoundary = async event => {
    const file = event.target.files?.[0];
    if (!file) return;
    setError(null);
    setBusy(true);
    try {
      if (file.size > 1024 * 1024) throw new Error('Boundary file must be smaller than 1 MB.');
      const data = JSON.parse(await file.text());
      const result = await setDocumentBoundaryApi(documentId, data);
      onVerified(result);
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
      event.target.value = '';
    }
  };
  return <section className="bg-slate-900 border border-slate-800 rounded-xl p-6 space-y-4">
    <h3 className="text-base font-bold text-white">Registration, duplicates & boundary evidence</h3>
    <p className="text-xs text-slate-400">A missing claim or reference is not a successful check. Results apply to the imported synthetic records.</p>
    <div className="grid sm:grid-cols-2 gap-3">
      {['registration_number', 'registration_date', 'duplicate_document'].map(key => <div key={key} className="p-3 bg-slate-950 rounded-lg text-sm text-slate-200">
        <strong className="block capitalize">{key.replaceAll('_', ' ')}</strong>
        <span className="capitalize">{label(checks[key]?.status)}</span>
        {checks[key]?.expected && <p className="text-xs text-slate-400 mt-1">Reference: {checks[key].expected} · Document: {checks[key].found || 'Not provided'}</p>}
        {checks[key]?.matches?.map(match => <p className="text-xs text-amber-300" key={match.document_id}>{match.document_id}: {label(match.evidence)}</p>)}
      </div>)}
      <div className="p-3 bg-slate-950 rounded-lg text-sm text-slate-200"><strong className="block">Boundary geometry</strong><span className="capitalize">{label(geometry.status)}</span>
        {geometry.difference_percent != null && <p className="text-xs text-slate-400 mt-1">Difference: {geometry.difference_percent}% · Outside reference: {geometry.outside_area_acres} acres · Missing: {geometry.missing_area_acres} acres</p>}
        {geometry.overlapping_parcels?.map(overlap => <p key={overlap.survey_number} className="text-xs text-rose-300">Overlap with {overlap.survey_number}: {overlap.overlap_acres} acres</p>)}
        {geometry.unchecked_reference_parcels?.length > 0 && <p className="text-xs text-amber-300">Invalid reference geometry prevented overlap checks for: {geometry.unchecked_reference_parcels.join(', ')}</p>}
      </div>
    </div>
    <div className="grid sm:grid-cols-4 gap-2 text-xs text-slate-300">
      {['north', 'south', 'east', 'west'].map(direction => <div key={direction}><strong className="capitalize">{direction}: </strong>{label(checks.boundary_descriptions?.[direction]?.status)}</div>)}
    </div>
    <label className="block text-sm font-semibold text-blue-300">Attach claimed parcel boundary (GeoJSON)
      <input aria-label="Attach claimed parcel boundary" disabled={busy} type="file" accept=".geojson,.json,application/geo+json,application/json" onChange={attachBoundary} className="block text-xs text-slate-300 mt-2" />
    </label>
    <p className="text-xs text-slate-400">Use a surveyed Polygon or MultiPolygon with longitude/latitude coordinates. Attaching it reruns verification and updates the map. Geometry areas are calculated separately from registry acreage.</p>
    {busy && <p role="status" className="text-sm text-blue-200">Comparing parcel geometry…</p>}
    {error && <p role="alert" className="text-sm text-rose-300">{error}</p>}
  </section>;
}
