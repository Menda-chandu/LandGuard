import React, { useEffect, useState, useRef, useMemo } from 'react';
import { MapContainer, TileLayer, GeoJSON, ScaleControl, useMap } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import { getGisParcelsApi, getDocumentApi } from '../api/config';
import { fallbackGeoJson } from '../data/parcelsGeoJson';
import {
  MapPin,
  Layers,
  Search,
  X,
  AlertTriangle,
  CheckCircle2,
  Info,
  RotateCcw,
  Compass,
  Wifi,
  WifiOff,
  Crosshair
} from 'lucide-react';

const isDisputedParcel = properties => Boolean(properties.conflict_status && !/^clean\b/i.test(properties.conflict_status));

// Subcomponent to handle programmatic map pan/zoom animations
function MapController({ targetBounds, resetKey, defaultCenter, defaultZoom }) {
  const map = useMap();

  useEffect(() => {
    // Invalidate size on mount to ensure full container rendering
    const timer = setTimeout(() => {
      map.invalidateSize();
    }, 250);
    return () => clearTimeout(timer);
  }, [map]);

  useEffect(() => {
    if (targetBounds && typeof targetBounds.isValid === 'function' && targetBounds.isValid()) {
      map.fitBounds(targetBounds, { padding: [60, 60], maxZoom: 16 });
    }
  }, [targetBounds, map]);

  useEffect(() => {
    if (resetKey > 0) {
      map.flyTo(defaultCenter, defaultZoom, { duration: 1.2 });
    }
  }, [resetKey, defaultCenter, defaultZoom, map]);

  return null;
}

export default function GisMap({ activeDocument, surveyNumber }) {
  // Use fallback bundled synthetic GeoJSON as instant baseline data
  const [geoData, setGeoData] = useState(fallbackGeoJson);
  const [selectedParcel, setSelectedParcel] = useState(null);
  const [selectedFeature, setSelectedFeature] = useState(null);
  const [activeLayer, setActiveLayer] = useState('cadastral'); // 'cadastral' | 'satellite' | 'encumbrance'
  const [searchQuery, setSearchQuery] = useState('');
  const [riskFilter, setRiskFilter] = useState('ALL'); // 'ALL' | 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL' | 'DISPUTED'
  const [resetKey, setResetKey] = useState(0);
  const [apiSource, setApiSource] = useState('local'); // 'live' | 'local'
  const [isLoading, setIsLoading] = useState(false);
  const [claimedGeometry, setClaimedGeometry] = useState(null);

  const geoJsonRef = useRef(null);

  // Default coordinate center: Ranga Reddy / Hyderabad cadastral cluster
  const defaultCenter = [17.405, 78.355];
  const defaultZoom = 12;

  // Load live GIS parcels from backend if available, keeping fallback resilient
  useEffect(() => {
    setIsLoading(true);
    getGisParcelsApi()
      .then((data) => {
        if (data && data.features && data.features.length > 0) {
          setGeoData(data);
          setApiSource('live');
        } else {
          setGeoData(fallbackGeoJson);
          setApiSource('local');
        }
        setIsLoading(false);
      })
      .catch((err) => {
        console.warn("GIS Backend API notice (using bundled synthetic GeoJSON fallback):", err.message);
        setGeoData(fallbackGeoJson);
        setApiSource('local');
        setIsLoading(false);
      });
  }, []);

  // Features list
  const allFeatures = useMemo(() => geoData?.features || [], [geoData]);
  const requestedSurvey = surveyNumber || activeDocument?.extracted_nlp_fields?.survey_number ||
    activeDocument?.extracted_fields?.survey_number || activeDocument?.extracted_survey_number || activeDocument?.survey_number;

  useEffect(() => {
    let cancelled = false;
    setClaimedGeometry(null);
    if (activeDocument?.document_id) {
      getDocumentApi(activeDocument.document_id)
        .then(data => { if (!cancelled) setClaimedGeometry(data?.claimed_geometry || null); })
        .catch(() => { if (!cancelled) setClaimedGeometry(null); });
    }
    return () => { cancelled = true; };
  }, [activeDocument?.document_id]);

  // Initial selection on mount or when activeDocument changes
  useEffect(() => {
    const initialFeat = requestedSurvey
      ? allFeatures.find(feature => feature.properties?.survey_number === requestedSurvey)
      : allFeatures[0];
    setSelectedParcel(initialFeat?.properties || null);
    setSelectedFeature(initialFeat || null);
  }, [allFeatures, requestedSurvey]);

  // Dynamic search and filter logic
  const filteredFeatures = useMemo(() => {
    const rawQuery = searchQuery.trim().toLowerCase();
    const queryClean = rawQuery.replace(/[\\/\-\s]/g, '');

    return allFeatures.filter((feat) => {
      const p = feat.properties || {};

      // 1. Risk Tier Filter
      let matchesRisk = true;
      if (riskFilter === 'DISPUTED') {
        matchesRisk = isDisputedParcel(p);
      } else if (riskFilter !== 'ALL') {
        matchesRisk = (p.risk_level || 'LOW').toUpperCase() === riskFilter;
      }
      if (!matchesRisk) return false;

      // 2. Search Query Filter (dynamic, case-insensitive, partial matching)
      if (!rawQuery) return true;

      const survey = String(p.survey_number || '').toLowerCase();
      const surveyClean = survey.replace(/[\\/\-\s]/g, '');
      const owner = String(p.owner_name || '').toLowerCase();
      const village = String(p.village || '').toLowerCase();
      const mandal = String(p.mandal || '').toLowerCase();
      const district = String(p.district || '').toLowerCase();
      const state = String(p.state || '').toLowerCase();
      const locationFull = `${village} ${mandal} ${district} ${state}`.toLowerCase();
      const locationClean = locationFull.replace(/[\\/\-\s]/g, '');

      // Direct substring match across survey, owner, village, mandal, district, and location
      if (
        survey.includes(rawQuery) ||
        owner.includes(rawQuery) ||
        village.includes(rawQuery) ||
        mandal.includes(rawQuery) ||
        district.includes(rawQuery) ||
        locationFull.includes(rawQuery)
      ) {
        return true;
      }

      // Normalized match (handles formatting differences like 402B vs 402/B or green valley vs Greenvalley)
      if (queryClean.length >= 2) {
        if (surveyClean.includes(queryClean) || locationClean.includes(queryClean)) {
          return true;
        }
      }

      return false;
    });
  }, [allFeatures, searchQuery, riskFilter]);

  // Handle selecting a parcel from list or search results
  const handleSelectParcel = (feat) => {
    if (!feat) return;
    setSelectedParcel(feat.properties);
    setSelectedFeature(feat);
  };

  // Compute selected parcel bounds for map zoom
  const targetBounds = useMemo(() => {
    if (!selectedFeature) return null;
    try {
      return L.geoJSON(selectedFeature).getBounds();
    } catch (e) {
      return null;
    }
  }, [selectedFeature]);

  // Centroid calculation for selected parcel
  const centroid = useMemo(() => {
    if (!selectedFeature) return null;
    try {
      const bounds = L.geoJSON(selectedFeature).getBounds();
      const c = bounds.getCenter();
      return { lat: c.lat.toFixed(5), lng: c.lng.toFixed(5) };
    } catch (e) {
      return null;
    }
  }, [selectedFeature]);

  // Risk styling palette
  const getRiskColor = (riskLevel) => {
    switch (riskLevel?.toUpperCase()) {
      case 'CRITICAL':
        return { fill: '#a855f7', stroke: '#7e22ce', text: 'text-purple-300', bg: 'bg-purple-950', border: 'border-purple-800' };
      case 'HIGH':
        return { fill: '#f43f5e', stroke: '#be123c', text: 'text-rose-400', bg: 'bg-rose-950', border: 'border-rose-900' };
      case 'MEDIUM':
        return { fill: '#f59e0b', stroke: '#b45309', text: 'text-amber-300', bg: 'bg-amber-950', border: 'border-amber-800' };
      case 'LOW':
      default:
        return { fill: '#10b981', stroke: '#047857', text: 'text-emerald-300', bg: 'bg-emerald-950', border: 'border-emerald-800' };
    }
  };

  // GeoJSON style callback
  const getFeatureStyle = (feature) => {
    const p = feature.properties || {};
    const isSelected = selectedParcel && (
      (selectedFeature && selectedFeature.id && feature.id && selectedFeature.id === feature.id) ||
      (selectedParcel.survey_number === p.survey_number && selectedParcel.owner_name === p.owner_name) ||
      (selectedParcel.survey_number === p.survey_number)
    );
    const isDisputed = isDisputedParcel(p);
    const risk = getRiskColor(p.risk_level);

    if (activeLayer === 'encumbrance') {
      if (isDisputed) {
        return {
          fillColor: '#dc2626',
          fillOpacity: isSelected ? 0.75 : 0.50,
          color: isSelected ? '#38bdf8' : '#ef4444',
          weight: isSelected ? 4 : 2.5,
          dashArray: isSelected ? null : '5, 5'
        };
      }
      return {
        fillColor: risk.fill,
        fillOpacity: 0.15,
        color: '#64748b',
        weight: 1,
        dashArray: null
      };
    }

    if (isSelected) {
      return {
        fillColor: risk.fill,
        fillOpacity: 0.70,
        color: '#38bdf8', // high-visibility sky-400 cyan selection border
        weight: 4,
        dashArray: null
      };
    }

    if (activeLayer === 'satellite') {
      return {
        fillColor: risk.fill,
        fillOpacity: 0.35,
        color: '#ffffff',
        weight: 2,
        dashArray: null
      };
    }

    return {
      fillColor: risk.fill,
      fillOpacity: 0.40,
      color: risk.stroke,
      weight: 1.5,
      dashArray: null
    };
  };

  // GeoJSON event callback
  const onEachFeature = (feature, layer) => {
    const p = feature.properties || {};

    layer.bindTooltip(
      `<div class="text-xs">
        <div class="font-bold text-white font-mono">Survey ${p.survey_number || 'N/A'}</div>
        <div class="text-slate-300">${p.owner_name || 'No Owner'}</div>
        <div class="text-slate-400 text-[11px]">${p.land_area_acres || '0'} Acres • ${p.village || 'N/A'}</div>
        <div class="mt-1 font-semibold ${
          p.risk_level === 'CRITICAL' ? 'text-purple-400' :
          p.risk_level === 'HIGH' ? 'text-rose-400' :
          p.risk_level === 'MEDIUM' ? 'text-amber-400' :
          'text-emerald-400'
        }">Risk: ${p.risk_level || 'LOW'}</div>
      </div>`,
      { sticky: true, opacity: 0.95, className: 'leaflet-custom-tooltip' }
    );

    layer.on({
      click: () => {
        handleSelectParcel(feature);
      },
      mouseover: (e) => {
        e.target.setStyle({
          weight: 3.5,
          color: '#38bdf8',
          fillOpacity: 0.70
        });
      },
      mouseout: (e) => {
        if (geoJsonRef.current) {
          geoJsonRef.current.resetStyle(e.target);
        }
      }
    });
  };

  const parcel = selectedParcel || {
    survey_number: requestedSurvey || 'None selected', owner_name: 'Not mapped',
    village: 'Not mapped', mandal: 'Not mapped', district: 'Not mapped', state: 'Not mapped',
    risk_level: 'UNAVAILABLE', conflict_status: 'No parcel selected'
  };

  const selectedRisk = getRiskColor(parcel.risk_level);

  return (
    <div className="space-y-6">
      {!isLoading && requestedSurvey && !selectedParcel && <div role="status" className="p-4 rounded-xl bg-amber-950 text-amber-200">No mapped parcel found for survey {requestedSurvey}. Select another parcel to explore the map.</div>}
      {/* Top Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 flex-wrap">
            <h2 className="text-2xl font-extrabold text-white tracking-tight flex items-center gap-2">
              <Compass className="w-6 h-6 text-blue-400" />
              GIS Map & Spatial Boundaries
            </h2>
            <span className="px-2.5 py-0.5 rounded text-xs font-mono font-bold bg-blue-950 text-blue-300 border border-blue-800 flex items-center gap-1.5">
              <Layers className="w-3.5 h-3.5" />
              Interactive React Leaflet Engine
            </span>
            <span className={`px-2.5 py-0.5 rounded text-xs font-mono font-bold border flex items-center gap-1 ${
              apiSource === 'live'
                ? 'bg-emerald-950 text-emerald-300 border-emerald-800'
                : 'bg-amber-950/70 text-amber-300 border-amber-800'
            }`}>
              {apiSource === 'live' ? <Wifi className="w-3 h-3" /> : <WifiOff className="w-3 h-3" />}
              {apiSource === 'live' ? 'Live API Synced' : 'Bundled Synthetic GeoJSON'}
            </span>
          </div>
          <p className="text-sm text-slate-400 mt-1">
            Imported synthetic parcel polygons. OpenStreetMap provides the base map; parcel tiers are dataset labels.
          </p>
        </div>

        {/* Map Layer Switcher */}
        <div className="flex items-center bg-slate-900 border border-slate-800 p-1 rounded-xl shrink-0">
          <button
            onClick={() => setActiveLayer('cadastral')}
            className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
              activeLayer === 'cadastral'
                ? 'bg-blue-600 text-white shadow-md'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            Cadastral Map
          </button>
          <button
            onClick={() => setActiveLayer('satellite')}
            className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
              activeLayer === 'satellite'
                ? 'bg-blue-600 text-white shadow-md'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            Satellite Hybrid
          </button>
          <button
            onClick={() => setActiveLayer('encumbrance')}
            className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
              activeLayer === 'encumbrance'
                ? 'bg-blue-600 text-white shadow-md'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            Disputed Overlaps
          </button>
        </div>
      </div>

      {/* Layer Honest Notice Banner */}
      {activeLayer === 'satellite' && (
        <div className="bg-blue-950/40 border border-blue-800/60 rounded-xl p-3 text-xs text-blue-200 flex items-start gap-2.5 shadow-sm">
          <Info className="w-4 h-4 text-blue-400 mt-0.5 shrink-0" />
          <div>
            <strong>Satellite Hybrid Mode:</strong> High-resolution global satellite imagery rendered via <em>Esri World Imagery</em>.
            <span className="block text-blue-300/80 mt-0.5">
              Notice: Displayed cadastral parcel boundaries are synthetic benchmark polygons in Ranga Reddy district. Official sub-meter government cadastral satellite overlays require Telangana Survey & Land Records ETS/DGPS ground control points.
            </span>
          </div>
        </div>
      )}

      {activeLayer === 'encumbrance' && (
        <div className="bg-amber-950/40 border border-amber-800/60 rounded-xl p-3 text-xs text-amber-200 flex items-start gap-2.5 shadow-sm">
          <AlertTriangle className="w-4 h-4 text-amber-400 mt-0.5 shrink-0" />
          <div>
            <strong>Boundary comparison mode:</strong> Reference parcels are shown with an attached document claim in red when one is available.
            <span className="block text-amber-300/80 mt-0.5">
              Attach a claimed GeoJSON boundary in Verification Results to calculate differences and overlaps. Without a claim, geometry is not checked.
            </span>
          </div>
        </div>
      )}

      {/* Main 3-Column Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Column: Parcel Search & Selector List */}
        <div className="lg:col-span-3 bg-slate-900 border border-slate-800 rounded-2xl p-4 space-y-3 shadow-lg flex flex-col h-[580px]">
          <div className="border-b border-slate-800 pb-2.5 flex items-center justify-between">
            <div className="flex items-center gap-1.5">
              <Layers className="w-4 h-4 text-blue-400" />
              <h3 className="text-xs font-bold uppercase tracking-wider text-slate-300">GeoJSON Parcels</h3>
            </div>
            <span className="text-[10px] font-mono text-blue-400 font-bold bg-blue-950 px-2 py-0.5 rounded border border-blue-900">
              {filteredFeatures.length} / {allFeatures.length}
            </span>
          </div>

          {/* Search Input with Clear Button */}
          <div className="relative">
            <Search className="w-3.5 h-3.5 text-slate-400 absolute left-2.5 top-2.5 pointer-events-none" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search survey, owner, or village..."
              className="w-full bg-slate-950 border border-slate-800 rounded-lg pl-8 pr-8 py-1.5 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-blue-500 transition-colors"
            />
            {searchQuery && (
              <button
                type="button"
                onClick={() => setSearchQuery('')}
                className="absolute right-2 top-1.5 text-slate-400 hover:text-white transition-colors p-1 rounded-full hover:bg-slate-800"
                title="Clear search"
                aria-label="Clear search"
              >
                <X className="w-3.5 h-3.5" />
              </button>
            )}
          </div>

          {/* Risk Filter Buttons */}
          <div className="flex items-center gap-1 overflow-x-auto pb-1 text-[10px] font-semibold">
            {['ALL', 'LOW', 'MEDIUM', 'HIGH', 'CRITICAL', 'DISPUTED'].map((tier) => (
              <button
                key={tier}
                onClick={() => setRiskFilter(tier)}
                className={`px-2 py-0.5 rounded transition-all shrink-0 ${
                  riskFilter === tier
                    ? 'bg-blue-600 text-white shadow'
                    : 'bg-slate-950 text-slate-400 hover:text-slate-200 border border-slate-800'
                }`}
              >
                {tier}
              </button>
            ))}
          </div>

          {/* Scrollable Parcel List */}
          <div className="flex-1 overflow-y-auto space-y-2 pr-1">
            {filteredFeatures.length === 0 ? (
              <div className="text-center py-10 px-3 space-y-3 bg-slate-950/40 rounded-xl border border-slate-800/80 my-2">
                <div className="w-9 h-9 rounded-full bg-slate-800/60 border border-slate-700 mx-auto flex items-center justify-center text-slate-400">
                  <Search className="w-4 h-4 text-slate-400" />
                </div>
                <div className="space-y-1">
                  <h4 className="text-xs font-bold text-slate-200">No matching parcels found</h4>
                  <p className="text-[11px] text-slate-400 max-w-[200px] mx-auto leading-relaxed">
                    No parcels match <span className="text-blue-300 font-mono font-semibold">"{searchQuery}"</span>
                    {riskFilter !== 'ALL' && <span> with <span className="text-amber-300 font-semibold">{riskFilter}</span> filter</span>}.
                  </p>
                </div>
                <button
                  onClick={() => {
                    setSearchQuery('');
                    setRiskFilter('ALL');
                  }}
                  className="inline-flex items-center gap-1.5 px-3 py-1 bg-slate-800 hover:bg-slate-700 text-slate-200 rounded-lg text-[11px] font-medium border border-slate-700 transition-colors"
                >
                  <RotateCcw className="w-3 h-3 text-slate-400" />
                  Reset Search & Filters
                </button>
              </div>
            ) : (
              filteredFeatures.map((feat) => {
                const p = feat.properties || {};
                const isSelected = selectedParcel && (
                  (selectedFeature && selectedFeature.id && feat.id && selectedFeature.id === feat.id) ||
                  (selectedParcel.survey_number === p.survey_number && selectedParcel.owner_name === p.owner_name) ||
                  (selectedParcel.survey_number === p.survey_number)
                );
                const risk = getRiskColor(p.risk_level);
                const hasConflict = isDisputedParcel(p);

                return (
                  <button
                    key={feat.id || p.survey_number}
                    onClick={() => handleSelectParcel(feat)}
                    className={`w-full p-2.5 rounded-lg border text-left flex items-center justify-between transition-all ${
                      isSelected
                        ? 'bg-blue-950/60 border-blue-500 text-blue-200 ring-1 ring-blue-500/40 shadow-sm'
                        : 'bg-slate-950/60 border-slate-800 text-slate-300 hover:border-slate-700 hover:bg-slate-950'
                    }`}
                  >
                    <div className="truncate pr-2">
                      <div className="text-xs font-mono font-bold text-white flex items-center gap-1.5">
                        <span>Survey {p.survey_number}</span>
                        {hasConflict && (
                          <span className="w-1.5 h-1.5 rounded-full bg-rose-500 shrink-0" title="Disputed parcel" />
                        )}
                      </div>
                      <div className="text-[11px] text-slate-400 truncate">{p.owner_name || 'Unspecified'}</div>
                      <div className="text-[10px] text-slate-500">{p.land_area_acres} Acres • {p.village}</div>
                    </div>
                    <span className={`text-[9px] font-bold px-1.5 py-0.5 rounded border shrink-0 ${risk.bg} ${risk.text} ${risk.border}`}>
                      {p.risk_level || 'LOW'}
                    </span>
                  </button>
                );
              })
            )}
          </div>
        </div>

        {/* Center: Interactive Leaflet Map Canvas */}
        <div className="lg:col-span-6 bg-slate-900 border border-slate-800 rounded-2xl p-4 flex flex-col space-y-3 shadow-xl h-[580px] relative">
          {/* Map Top Bar */}
          <div className="flex items-center justify-between z-20">
            <div className="flex items-center gap-2">
              <span className="text-xs font-mono text-slate-300 bg-slate-950/90 border border-slate-800 px-2.5 py-1 rounded-lg flex items-center gap-1.5">
                <MapPin className="w-3.5 h-3.5 text-blue-400" />
                <span>Survey {parcel.survey_number} • {parcel.village || 'Ranga Reddy'}</span>
              </span>
            </div>

            <div className="flex items-center gap-2">
              <button
                onClick={() => setResetKey((k) => k + 1)}
                className="px-2.5 py-1 bg-slate-950/90 hover:bg-slate-800 text-slate-300 border border-slate-700 rounded-lg text-xs font-semibold flex items-center gap-1 transition-all shadow-sm"
                title="Reset view to region center"
              >
                <RotateCcw className="w-3 h-3 text-slate-400" />
                Reset View
              </button>
            </div>
          </div>

          {/* Leaflet MapContainer */}
          <div className="flex-1 rounded-xl border border-slate-800 overflow-hidden relative z-10 shadow-inner">
            {allFeatures.length === 0 && !isLoading ? (
              <div className="w-full h-full bg-slate-950 flex flex-col items-center justify-center p-6 text-center space-y-3">
                <AlertTriangle className="w-8 h-8 text-amber-400" />
                <h4 className="text-sm font-bold text-white">No Parcel Geometries Loaded</h4>
                <p className="text-xs text-slate-400 max-w-sm">
                  Failed to parse GeoJSON polygon records. Check synthetic parcel files or backend connection.
                </p>
                <button
                  onClick={() => setGeoData(fallbackGeoJson)}
                  className="px-3 py-1.5 bg-blue-600 text-white rounded-lg text-xs font-semibold hover:bg-blue-500"
                >
                  Reload Bundled GeoJSON
                </button>
              </div>
            ) : (
              <MapContainer
                center={defaultCenter}
                zoom={defaultZoom}
                scrollWheelZoom={true}
                className="w-full h-full"
                attributionControl={true}
              >
                <MapController
                  targetBounds={targetBounds}
                  resetKey={resetKey}
                  defaultCenter={defaultCenter}
                  defaultZoom={defaultZoom}
                />

                <ScaleControl position="bottomleft" metric={true} imperial={false} />

                {/* Base Tile Layer */}
                {activeLayer === 'satellite' ? (
                  <TileLayer
                    url="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"
                    attribution="Tiles &copy; Esri &mdash; Source: Esri, i-cubed, USDA, USGS, AEX, GeoEye, Getmapping, Aerogrid, IGN, IGP, UPR-EGP, and GIS User Community"
                    maxZoom={19}
                  />
                ) : (
                  <TileLayer
                    url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                    attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
                    maxZoom={19}
                  />
                )}

                {/* Cadastral GeoJSON Polygons Layer: key depends on active layer, selected parcel, and risk filter only (not raw search typing) */}
                {allFeatures.length > 0 && (
                  <GeoJSON
                    key={`geojson_${activeLayer}_${selectedParcel?.survey_number}_${selectedFeature?.id || ''}_${riskFilter}`}
                    ref={geoJsonRef}
                    data={geoData}
                    style={getFeatureStyle}
                    onEachFeature={onEachFeature}
                  />
                )}

                {claimedGeometry && selectedParcel?.survey_number === requestedSurvey && (
                  <GeoJSON
                    key={`claim_${activeDocument?.document_id}_${JSON.stringify(claimedGeometry)}`}
                    data={claimedGeometry}
                    style={{
                      color: '#ef4444',
                      fillColor: '#f87171',
                      fillOpacity: 0.55,
                      dashArray: '6, 6',
                      weight: 2.5
                    }}
                    onEachFeature={(_, layer) => layer.bindTooltip('Uploaded claimed parcel boundary')}
                  />
                )}
              </MapContainer>
            )}

            {/* Embedded Floating Map Legend */}
            <div className="absolute bottom-3 right-3 bg-slate-900/95 backdrop-blur border border-slate-700/80 p-2.5 rounded-xl shadow-xl z-[400] text-[11px] space-y-1.5 max-w-[170px]">
              <div className="font-bold text-white border-b border-slate-800 pb-1 flex items-center justify-between">
                <span>Dataset tiers</span>
                <span className="text-[9px] text-slate-400">Synthetic</span>
              </div>
              <div className="grid grid-cols-2 gap-x-2 gap-y-1">
                <div className="flex items-center gap-1.5">
                  <span className="w-2.5 h-2.5 rounded-sm bg-emerald-500 shrink-0 border border-emerald-400" />
                  <span className="text-slate-300 text-[10px]">Low (0-29)</span>
                </div>
                <div className="flex items-center gap-1.5">
                  <span className="w-2.5 h-2.5 rounded-sm bg-amber-500 shrink-0 border border-amber-400" />
                  <span className="text-slate-300 text-[10px]">Med (30-59)</span>
                </div>
                <div className="flex items-center gap-1.5">
                  <span className="w-2.5 h-2.5 rounded-sm bg-rose-500 shrink-0 border border-rose-400" />
                  <span className="text-slate-300 text-[10px]">High (60-79)</span>
                </div>
                <div className="flex items-center gap-1.5">
                  <span className="w-2.5 h-2.5 rounded-sm bg-purple-500 shrink-0 border border-purple-400" />
                  <span className="text-slate-300 text-[10px]">Critical (80+)</span>
                </div>
              </div>
              <div className="border-t border-slate-800 pt-1 flex items-center gap-1.5 text-[10px] text-sky-300">
                <span className="w-2.5 h-2.5 rounded-sm border-2 border-sky-400 bg-transparent shrink-0" />
                <span>Selected Parcel</span>
              </div>
            </div>
          </div>
        </div>

        {/* Right Column: Selected Parcel Information Panel */}
        <div className="lg:col-span-3 bg-slate-900 border border-slate-800 rounded-2xl p-5 space-y-4 shadow-lg flex flex-col justify-between h-[580px]">
          <div className="space-y-4">
            <div className="border-b border-slate-800 pb-3 flex items-center justify-between">
              <div>
                <h3 className="text-sm font-bold text-white flex items-center gap-1.5">
                  <MapPin className="w-4 h-4 text-blue-400" />
                  Selected Parcel Info
                </h3>
                <p className="text-[11px] text-slate-400">GIS Cadastral Properties</p>
              </div>
              <span className={`text-[10px] font-bold px-2 py-0.5 rounded border ${selectedRisk.bg} ${selectedRisk.text} ${selectedRisk.border}`}>
                {parcel.risk_level || 'LOW'}
              </span>
            </div>

            <div className="space-y-2.5">
              <div className="p-2.5 rounded-lg bg-slate-950 border border-slate-800 flex justify-between items-center">
                <span className="text-xs text-slate-400 font-semibold">Survey Sub-division</span>
                <span className="text-xs font-mono font-bold text-blue-300">{parcel.survey_number}</span>
              </div>

              <div className="p-2.5 rounded-lg bg-slate-950 border border-slate-800 flex justify-between items-center">
                <span className="text-xs text-slate-400 font-semibold">Registered Owner</span>
                <span className="text-xs font-bold text-white truncate max-w-[140px]" title={parcel.owner_name}>
                  {parcel.owner_name || 'N/A'}
                </span>
              </div>

              <div className="p-2.5 rounded-lg bg-slate-950 border border-slate-800 flex justify-between items-center">
                <span className="text-xs text-slate-400 font-semibold">Parcel Acreage</span>
                <span className="text-xs font-bold text-white">{parcel.land_area_acres == null ? 'Not mapped' : `${parcel.land_area_acres} Acres`}</span>
              </div>

              <div className="p-2.5 rounded-lg bg-slate-950 border border-slate-800 flex justify-between items-center">
                <span className="text-xs text-slate-400 font-semibold">Village / Mandal</span>
                <span className="text-xs font-bold text-white truncate max-w-[140px]">
                  {parcel.village}, {parcel.mandal || 'RR'}
                </span>
              </div>

              <div className="p-2.5 rounded-lg bg-slate-950 border border-slate-800 flex justify-between items-center">
                <span className="text-xs text-slate-400 font-semibold">District & State</span>
                <span className="text-xs font-bold text-white">{parcel.district || 'Ranga Reddy'}, {parcel.state || 'Telangana'}</span>
              </div>

              {centroid && (
                <div className="p-2.5 rounded-lg bg-slate-950 border border-slate-800 flex justify-between items-center font-mono">
                  <span className="text-xs text-slate-400 font-sans font-semibold">Centroid (Lat, Lng)</span>
                  <span className="text-[11px] text-slate-300">{centroid.lat}, {centroid.lng}</span>
                </div>
              )}

              {/* Conflict / Mismatch Status */}
              <div className="p-3 rounded-xl bg-slate-950 border border-slate-800 space-y-1">
                <span className="text-[11px] font-bold text-slate-400 block">Anomaly / Conflict Status</span>
                {isDisputedParcel(parcel) ? (
                  <div className="flex items-start gap-1.5 text-xs text-rose-300 font-semibold">
                    <AlertTriangle className="w-3.5 h-3.5 text-rose-400 mt-0.5 shrink-0" />
                    <span>{parcel.conflict_status}</span>
                  </div>
                ) : (
                  <div className="flex items-center gap-1.5 text-xs text-emerald-400 font-semibold">
                    <CheckCircle2 className="w-3.5 h-3.5" />
                    <span>Dataset label: {parcel.conflict_status || 'No conflict label'}</span>
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Action buttons */}
          <div className="space-y-2 pt-2 border-t border-slate-800">
            <button
              onClick={() => {
                if (targetBounds) {
                  // Re-trigger zoom
                  setSelectedFeature({ ...selectedFeature });
                }
              }}
              className="w-full py-2 bg-blue-600 hover:bg-blue-500 text-white rounded-xl text-xs font-bold flex items-center justify-center gap-1.5 transition-all shadow-md"
            >
              <Crosshair className="w-3.5 h-3.5" />
              Center on Selected Parcel
            </button>
            <p className="text-[10px] text-center text-slate-500">
              Cadastral boundaries derived from synthetic test fixtures.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
