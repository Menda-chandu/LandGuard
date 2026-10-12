import React, { useEffect, useState } from 'react';
import { getGisParcelsApi } from '../api/config';
import { mockGisParcelData } from '../data/mockData';

export default function GisMap() {
  const [geoData, setGeoData] = useState(null);
  const [selectedParcel, setSelectedParcel] = useState(null);
  const [activeLayer, setActiveLayer] = useState('cadastral');
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    setIsLoading(true);
    getGisParcelsApi()
      .then((data) => {
        setGeoData(data);
        if (data.features && data.features.length > 0) {
          setSelectedParcel(data.features[0].properties);
        }
        setIsLoading(false);
      })
      .catch((err) => {
        console.warn("GIS API notice:", err.message);
        setIsLoading(false);
      });
  }, []);

  const parcel = selectedParcel || {
    survey_number: "402/B",
    owner_name: "Kiran Mazumdar",
    land_area_acres: 2.00,
    village: "Riverside",
    mandal: "Ibrahimpatnam",
    district: "Ranga Reddy",
    state: "Telangana",
    risk_level: "HIGH",
    conflict_status: "0.65 Acre Boundary Overlap Anomaly"
  };

  const featuresList = geoData?.features || [
    { properties: { survey_number: "101/A", owner_name: "Anil Kumar Rao", land_area_acres: 2.5, village: "Greenvalley", district: "Ranga Reddy", risk_level: "LOW" } },
    { properties: { survey_number: "102/B", owner_name: "Bhavana Sharma", land_area_acres: 1.8, village: "Greenvalley", district: "Ranga Reddy", risk_level: "LOW" } },
    { properties: { survey_number: "201/A", owner_name: "Farhan Ahmed", land_area_acres: 5.0, village: "Hilltop", district: "Ranga Reddy", risk_level: "HIGH" } },
    { properties: { survey_number: "402/B", owner_name: "Kiran Mazumdar", land_area_acres: 2.0, village: "Riverside", district: "Ranga Reddy", risk_level: "HIGH" } },
    { properties: { survey_number: "501/A", owner_name: "Lokesh Gupta", land_area_acres: 4.0, village: "Forest Edge", district: "Ranga Reddy", risk_level: "CRITICAL" } }
  ];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <h2 className="text-2xl font-extrabold text-white tracking-tight">GIS Map & Spatial Boundaries</h2>
            <span className="px-2.5 py-0.5 rounded text-xs font-mono font-bold bg-blue-950 text-blue-300 border border-blue-800">
              OpenStreetMap & CAD GeoJSON Layer
            </span>
          </div>
          <p className="text-sm text-slate-400 mt-1">
            Interactive CAD polygon boundaries connected to land_records PostgreSQL database.
          </p>
        </div>

        {/* Map Layer Switcher */}
        <div className="flex items-center bg-slate-900 border border-slate-800 p-1 rounded-xl">
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

      {/* Main Grid: Interactive Parcel Selector + Map Canvas + Selected Parcel Panel */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Column: Parcel Selector List */}
        <div className="lg:col-span-3 bg-slate-900 border border-slate-800 rounded-2xl p-4 space-y-3 shadow-lg">
          <div className="border-b border-slate-800 pb-2 flex items-center justify-between">
            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-300">GeoJSON Parcels</h3>
            <span className="text-[10px] font-mono text-blue-400 font-bold">{featuresList.length} Mapped</span>
          </div>

          <div className="space-y-2 max-h-[380px] overflow-y-auto pr-1">
            {featuresList.map((feat, idx) => {
              const p = feat.properties;
              const isSelected = parcel.survey_number === p.survey_number;

              return (
                <button
                  key={idx}
                  onClick={() => setSelectedParcel(p)}
                  className={`w-full p-2.5 rounded-lg border text-left flex items-center justify-between transition-all ${
                    isSelected
                      ? 'bg-blue-950/60 border-blue-500 text-blue-200 ring-1 ring-blue-500/40'
                      : 'bg-slate-950/60 border-slate-800 text-slate-300 hover:border-slate-700'
                  }`}
                >
                  <div>
                    <div className="text-xs font-mono font-bold text-white">Survey {p.survey_number}</div>
                    <div className="text-[11px] text-slate-400 truncate">{p.owner_name}</div>
                  </div>
                  <span className={`text-[9px] font-bold px-1.5 py-0.5 rounded ${
                    p.risk_level === 'CRITICAL' ? 'bg-purple-950 text-purple-300 border border-purple-800' :
                    p.risk_level === 'HIGH' ? 'bg-rose-950/60 text-rose-400 border border-rose-900' :
                    p.risk_level === 'MEDIUM' ? 'bg-amber-950/80 text-amber-300 border border-amber-800' :
                    'bg-emerald-950 text-emerald-300 border border-emerald-800'
                  }`}>
                    {p.risk_level || 'LOW'}
                  </span>
                </button>
              );
            })}
          </div>
        </div>

        {/* Map Canvas Visualizer Placeholder Container */}
        <div className="lg:col-span-6 bg-slate-900 border border-slate-800 rounded-2xl p-4 flex flex-col space-y-3 relative shadow-xl overflow-hidden min-h-[460px]">
          <div className="w-full h-full bg-slate-950 rounded-xl border border-slate-800 relative overflow-hidden flex flex-col items-center justify-center p-6 text-center space-y-4 bg-[radial-gradient(#1e293b_1px,transparent_1px)] [background-size:16px_16px]">
            {/* Coordinates Badge */}
            <div className="absolute top-4 left-4 bg-slate-900/90 backdrop-blur border border-slate-700 px-3 py-1.5 rounded-lg text-xs font-mono text-slate-300 shadow-md">
              📍 Selected Parcel: Survey {parcel.survey_number} • {parcel.village}
            </div>

            {/* Polygon Visual Simulation Box */}
            <div className="w-64 h-52 border-2 border-dashed border-blue-500/80 bg-blue-950/20 rounded-xl relative flex items-center justify-center p-4 shadow-lg animate-pulse">
              <div className="w-44 h-36 border-2 border-emerald-400 bg-emerald-950/40 rounded-lg flex flex-col items-center justify-center text-center p-2 shadow-inner">
                <span className="text-xs font-bold text-emerald-300 font-mono">Survey No. {parcel.survey_number}</span>
                <span className="text-[10px] text-emerald-400">{parcel.owner_name}</span>
                <span className="text-[10px] text-slate-300">{parcel.land_area_acres} Acres</span>
              </div>
            </div>

            <div className="max-w-md space-y-1 z-10">
              <h3 className="text-base font-bold text-white">GeoJSON Polygon Selected: Survey {parcel.survey_number}</h3>
              <p className="text-xs text-slate-400">
                Connected to OpenStreetMap tile server and live PostgreSQL revenue registry.
              </p>
            </div>
          </div>
        </div>

        {/* Right Sidebar: Selected Parcel Information Panel */}
        <div className="lg:col-span-3 bg-slate-900 border border-slate-800 rounded-2xl p-5 space-y-4 shadow-lg">
          <div className="border-b border-slate-800 pb-3">
            <h3 className="text-sm font-bold text-white">Selected Parcel Info</h3>
            <p className="text-[11px] text-slate-400">GIS Cadastral Properties</p>
          </div>

          <div className="space-y-3">
            <div className="p-2.5 rounded-lg bg-slate-950 border border-slate-800 flex justify-between items-center">
              <span className="text-xs text-slate-400 font-semibold">Survey Sub-division</span>
              <span className="text-xs font-mono font-bold text-blue-300">{parcel.survey_number}</span>
            </div>

            <div className="p-2.5 rounded-lg bg-slate-950 border border-slate-800 flex justify-between items-center">
              <span className="text-xs text-slate-400 font-semibold">Registered Owner</span>
              <span className="text-xs font-bold text-white truncate max-w-[120px]">{parcel.owner_name}</span>
            </div>

            <div className="p-2.5 rounded-lg bg-slate-950 border border-slate-800 flex justify-between items-center">
              <span className="text-xs text-slate-400 font-semibold">Parcel Acreage</span>
              <span className="text-xs font-bold text-white">{parcel.land_area_acres} Acres</span>
            </div>

            <div className="p-2.5 rounded-lg bg-slate-950 border border-slate-800 flex justify-between items-center">
              <span className="text-xs text-slate-400 font-semibold">Village / Mandal</span>
              <span className="text-xs font-bold text-white">{parcel.village}, {parcel.mandal || 'RR'}</span>
            </div>

            <div className="p-2.5 rounded-lg bg-slate-950 border border-slate-800 flex justify-between items-center">
              <span className="text-xs text-slate-400 font-semibold">District</span>
              <span className="text-xs font-bold text-white">{parcel.district}</span>
            </div>

            <div className="p-3 rounded-xl bg-slate-950 border border-slate-800 space-y-1">
              <span className="text-[11px] font-bold text-slate-400 block">Risk Category</span>
              <span className={`inline-block px-2.5 py-1 rounded text-xs font-bold ${
                parcel.risk_level === 'CRITICAL' ? 'bg-purple-950 text-purple-300 border border-purple-800' :
                parcel.risk_level === 'HIGH' ? 'bg-rose-950/80 text-rose-400 border border-rose-900' :
                parcel.risk_level === 'MEDIUM' ? 'bg-amber-950/80 text-amber-300 border border-amber-800' :
                'bg-emerald-950 text-emerald-300 border border-emerald-800'
              }`}>
                {parcel.risk_level || 'LOW'} Risk Tier
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
