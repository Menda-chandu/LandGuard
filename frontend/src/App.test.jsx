import React from 'react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { cleanup, render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import App from './App';
import GisMap from './pages/GisMap';
import RiskScoreView from './pages/RiskScoreView';
import VerificationResults from './pages/VerificationResults';
import OwnershipHistory from './pages/OwnershipHistory';
import EvidenceChecks from './components/EvidenceChecks';

const api = vi.hoisted(() => Object.fromEntries([
  'getDashboardApi', 'searchRecordsApi', 'getRegistryRecordApi', 'getDocumentApi',
  'getDocumentNlpApi', 'getVerificationApi', 'getRiskAssessmentApi', 'getOwnershipHistoryApi',
  'getGisParcelsApi', 'getSampleDocumentsApi', 'getSampleDocumentApi', 'uploadDocumentApi', 'setDocumentBoundaryApi',
].map(name => [name, vi.fn()])));
vi.mock('./api/config', () => api);
const map = vi.hoisted(() => ({ invalidateSize: vi.fn(), fitBounds: vi.fn(), flyTo: vi.fn() }));
vi.mock('react-leaflet', async () => {
  const { forwardRef } = await import('react');
  return {
  MapContainer: ({ children }) => <div>{children}</div>,
  TileLayer: () => null, GeoJSON: forwardRef(() => null), Polygon: () => null,
  ScaleControl: () => null, Tooltip: () => null, useMap: () => map,
  };
});

const registry = {
  record_id: 'SYN-REC-001', survey_number: 'SYN-101/A', owner_name: 'Kalyan Varma Dantuluri',
  land_area_acres: 2.2, village: 'Narsingi', mandal: 'Gandipet', district: 'Ranga Reddy',
  state: 'Telangana', history_timeline: [],
};
const feature = (survey, owner) => ({ type: 'Feature', properties: {
  survey_number: survey, owner_name: owner, land_area_acres: 2, village: 'Narsingi',
  mandal: 'Gandipet', district: 'Ranga Reddy', state: 'Telangana', risk_level: 'LOW', conflict_status: 'Clean',
}, geometry: { type: 'Polygon', coordinates: [[[78, 17], [78.1, 17], [78.1, 17.1], [78, 17]]] } });

beforeEach(() => {
  vi.resetAllMocks();
  api.getDashboardApi.mockResolvedValue({ stats: {}, registry_preview: [], recent_documents: [] });
  api.searchRecordsApi.mockResolvedValue({ results: [{ ...registry, type: 'land_record' }] });
  api.getRegistryRecordApi.mockResolvedValue(registry);
  api.getDocumentApi.mockResolvedValue({});
  api.getGisParcelsApi.mockResolvedValue({ type: 'FeatureCollection', features: [feature('FIRST/A', 'First Owner'), feature('TARGET/B', 'Target Owner')] });
});
afterEach(cleanup);

describe('document evidence controls', () => {
  it('shows unavailable checks and attaches the supplied GeoJSON to the actual document', async () => {
    const user = userEvent.setup();
    const onVerified = vi.fn();
    const geometry = feature('TARGET/B', 'Target Owner').geometry;
    const response = { document_id: 'DOC-BOUNDARY', evidence_checks: { boundary_geometry: { status: 'MATCH' } } };
    api.setDocumentBoundaryApi.mockResolvedValue(response);
    render(<EvidenceChecks documentId="DOC-BOUNDARY" checks={{ registration_number: { status: 'REFERENCE_UNAVAILABLE' } }} onVerified={onVerified} />);
    expect(screen.getByText('reference unavailable')).toBeTruthy();
    const file = new File([JSON.stringify(geometry)], 'claim.geojson', { type: 'application/geo+json' });
    Object.defineProperty(file, 'text', { value: async () => JSON.stringify(geometry) });
    await user.upload(screen.getByLabelText('Attach claimed parcel boundary'), file);
    await waitFor(() => expect(onVerified).toHaveBeenCalledWith(response));
    expect(api.setDocumentBoundaryApi).toHaveBeenCalledWith('DOC-BOUNDARY', geometry);
  });

  it('shows rejected boundary validation without changing the verification result', async () => {
    const user = userEvent.setup();
    const onVerified = vi.fn();
    api.setDocumentBoundaryApi.mockRejectedValue(new Error('Boundary is self-intersecting.'));
    render(<EvidenceChecks documentId="DOC-1" onVerified={onVerified} />);
    const file = new File(['{}'], 'bad.geojson', { type: 'application/geo+json' });
    Object.defineProperty(file, 'text', { value: async () => '{}' });
    await user.upload(screen.getByLabelText('Attach claimed parcel boundary'), file);
    expect(await screen.findByRole('alert')).toHaveProperty('textContent', 'Boundary is self-intersecting.');
    expect(onVerified).not.toHaveBeenCalled();
  });
});

describe('registry and document navigation', () => {
  it('opens a searched reference record without inventing OCR or an upload', async () => {
    const user = userEvent.setup();
    render(<App />);
    await user.type(screen.getByPlaceholderText('Search Survey No. / Owner...'), 'SYN-REC-001');
    await user.click(await screen.findByRole('button', { name: /Survey SYN-101\/A SYN-REC-001/ }));
    expect(await screen.findByRole('heading', { name: 'Land Registry Record' })).toBeTruthy();
    expect(screen.queryByText(/OCR Confidence/)).toBeNull();
    expect(api.getDocumentNlpApi).not.toHaveBeenCalled();
    expect(api.getVerificationApi).not.toHaveBeenCalled();
    expect(api.uploadDocumentApi).not.toHaveBeenCalled();
  });

  it('requires an uploaded document before showing verification or risk', async () => {
    const user = userEvent.setup();
    render(<App />);
    await user.click(screen.getByRole('button', { name: 'Verification Results', exact: true }));
    expect(screen.getByRole('heading', { name: 'Select an uploaded document' })).toBeTruthy();
    await user.click(screen.getByRole('button', { name: 'Risk Score & Audit', exact: true }));
    expect(screen.getByRole('heading', { name: 'Select an uploaded document' })).toBeTruthy();
    expect(api.getVerificationApi).not.toHaveBeenCalled();
    expect(api.getRiskAssessmentApi).not.toHaveBeenCalled();
  });

  it('shows an API error instead of presenting a fabricated low risk result', async () => {
    api.getRiskAssessmentApi.mockRejectedValue(new Error('Backend unavailable'));
    render(<RiskScoreView activeDocument={{ document_id: 'DOC-1' }} />);
    expect(await screen.findByRole('alert')).toHaveProperty('textContent', 'Backend unavailable');
    expect(screen.queryByText('No major inconsistency detected')).toBeNull();
    expect(screen.queryByText('LOW')).toBeNull();
  });

  it('shows verification failures instead of leaving a pending report', async () => {
    api.getVerificationApi.mockRejectedValue(new Error('Verification unavailable'));
    render(<VerificationResults activeDocument={{ document_id: 'DOC-1' }} />);
    expect(await screen.findByRole('alert')).toHaveProperty('textContent', 'Verification unavailable');
    expect(screen.queryByText('PENDING')).toBeNull();
  });

  it('distinguishes an ownership request failure from an empty history', async () => {
    api.getOwnershipHistoryApi.mockRejectedValue(new Error('History unavailable'));
    render(<OwnershipHistory activeDocument={{ document_id: 'DOC-1' }} />);
    expect(await screen.findByRole('alert')).toHaveProperty('textContent', 'History unavailable');
    expect(screen.queryByText('No Historical Title Chain Records Found')).toBeNull();
  });
});

describe('parcel selection', () => {
  it('does not classify clean synthetic title labels as disputed parcels', async () => {
    const user = userEvent.setup();
    const clean = feature('TARGET/B', 'Target Owner');
    clean.properties.conflict_status = 'Clean Synthetic Title';
    api.getGisParcelsApi.mockResolvedValue({ type: 'FeatureCollection', features: [clean] });
    render(<GisMap />);
    await waitFor(() => expect(screen.getByTitle('Target Owner')).toBeTruthy());
    await user.click(screen.getByRole('button', { name: 'DISPUTED', exact: true }));
    expect(screen.getByText('No matching parcels found')).toBeTruthy();
  });
  it('follows the uploaded NLP survey and updates when another document is selected', async () => {
    const view = render(<GisMap activeDocument={{ extracted_nlp_fields: { survey_number: 'TARGET/B' } }} />);
    await waitFor(() => expect(screen.getByTitle('Target Owner')).toBeTruthy());
    view.rerender(<GisMap activeDocument={{ extracted_nlp_fields: { survey_number: 'FIRST/A' } }} />);
    await waitFor(() => expect(screen.getByTitle('First Owner')).toBeTruthy());
  });

  it('does not substitute an unrelated parcel when the survey is unmapped', async () => {
    render(<GisMap activeDocument={{ extracted_nlp_fields: { survey_number: 'MISSING/Z' } }} />);
    expect(await screen.findByRole('status')).toHaveProperty('textContent', 'No mapped parcel found for survey MISSING/Z. Select another parcel to explore the map.');
    expect(screen.queryByTitle('First Owner')).toBeNull();
    expect(screen.queryByTitle('Target Owner')).toBeNull();
  });
});
