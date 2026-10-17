import React, { useState, useEffect, useRef } from 'react';
import { Search, X, User, MapPin, ChevronRight, Loader2 } from 'lucide-react';
import { searchRecordsApi } from '../api/config';

export default function Navbar({ onUploadClick, onSelectRecord, activeTab }) {
  const [query, setQuery] = useState('');
  const [isOpen, setIsOpen] = useState(false);
  const [apiResults, setApiResults] = useState([]);
  const [isSearchingApi, setIsSearchingApi] = useState(false);
  const [searchError, setSearchError] = useState(null);
  const searchContainerRef = useRef(null);

  // Close dropdown when clicking outside
  useEffect(() => {
    function handleClickOutside(event) {
      if (searchContainerRef.current && !searchContainerRef.current.contains(event.target)) {
        setIsOpen(false);
      }
    }
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  // Close dropdown on Escape key
  useEffect(() => {
    function handleKeyDown(e) {
      if (e.key === 'Escape') {
        setIsOpen(false);
      }
    }
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, []);

  // Background API search when query changes
  useEffect(() => {
    const raw = query.trim();
    setSearchError(null);
    setApiResults([]);
    if (raw.length < 2) {
      setIsSearchingApi(false);
      setApiResults([]);
      return;
    }

    let isSubscribed = true;
    setIsSearchingApi(true);

    const timer = setTimeout(() => {
      searchRecordsApi(raw)
        .then((data) => {
          if (isSubscribed && data && data.results) {
            setApiResults(data.results);
          }
          if (isSubscribed) setIsSearchingApi(false);
        })
        .catch(() => {
          if (isSubscribed) {
            setSearchError('Search is unavailable. Check the backend connection.');
            setIsSearchingApi(false);
          }
        });
    }, 200);

    return () => {
      isSubscribed = false;
      clearTimeout(timer);
    };
  }, [query]);

  const searchResults = apiResults.slice(0, 12);

  const handleSelect = (record) => {
    if (onSelectRecord) {
      onSelectRecord(record, 'analysis');
    }
    setIsOpen(false);
  };

  const handleClear = () => {
    setQuery('');
    setIsOpen(false);
    setApiResults([]);
  };

  return (
    <header className="min-h-16 py-3 md:py-0 bg-slate-900 border-b border-slate-800 px-4 md:px-6 flex flex-wrap md:flex-nowrap gap-3 items-center justify-between sticky top-0 z-30">
      {/* Brand & Logo */}
      <div className="flex items-center gap-3">
        <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-blue-600 to-indigo-700 flex items-center justify-center text-white shadow-lg shadow-blue-900/30 shrink-0">
          <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
          </svg>
        </div>
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-xl font-bold tracking-tight text-white">LandGuard</h1>
            <span className="text-[10px] uppercase font-bold tracking-widest px-2 py-0.5 rounded bg-amber-950/80 text-amber-300 border border-amber-800">
              Synthetic Demo
            </span>
          </div>
          <p className="text-xs text-slate-400 hidden lg:block">AI-Powered Land Record Validation & Fraud Detection System</p>
        </div>
      </div>

      {/* Global Search Bar & Upload Button Container */}
      <div className="w-full md:w-auto flex items-center gap-3 md:gap-4">
        {/* Global Search Container */}
        <div ref={searchContainerRef} className="relative min-w-0 flex-1">
          <div className="flex items-center bg-slate-800 border border-slate-700 rounded-lg px-3 py-1.5 text-sm text-slate-300 w-full md:w-80 lg:w-96 focus-within:border-blue-500 focus-within:ring-1 focus-within:ring-blue-500 transition-all">
            <Search className="w-4 h-4 text-slate-400 mr-2 shrink-0" />
            <input
              type="text"
              value={query}
              onChange={(e) => {
                setQuery(e.target.value);
                setIsOpen(true);
              }}
              onFocus={() => {
                if (query.trim().length > 0) setIsOpen(true);
              }}
              placeholder="Search Survey No. / Owner..."
              className="bg-transparent border-none outline-none text-slate-200 placeholder-slate-500 text-xs w-full"
            />
            {isSearchingApi && (
              <Loader2 className="w-3.5 h-3.5 text-blue-400 animate-spin mr-1.5 shrink-0" />
            )}
            {query && (
              <button
                type="button"
                onClick={handleClear}
                className="text-slate-400 hover:text-white transition-colors p-0.5 rounded-full hover:bg-slate-700 shrink-0"
                title="Clear search"
                aria-label="Clear search"
              >
                <X className="w-3.5 h-3.5" />
              </button>
            )}
          </div>

          {/* Search Results Dropdown */}
          {isOpen && query.trim().length > 0 && (
            <div className="absolute top-full mt-2 w-[min(24rem,calc(100vw-2rem))] right-0 md:left-0 bg-slate-900 border border-slate-700/90 rounded-2xl shadow-2xl overflow-hidden z-50 backdrop-blur-xl animate-in fade-in slide-in-from-top-2 duration-150">
              <div className="px-3.5 py-2.5 bg-slate-950/80 border-b border-slate-800 flex items-center justify-between text-[11px]">
                <span className="font-semibold text-slate-300">
                  {searchResults.length > 0 ? (
                    <>Found <strong className="text-blue-400">{searchResults.length}</strong> matching records</>
                  ) : (
                    "Search Results"
                  )}
                </span>
                <span className="text-[10px] text-slate-500 font-mono">Press ESC to close</span>
              </div>

              <div className="max-h-[360px] overflow-y-auto divide-y divide-slate-800/60">
                {searchResults.length === 0 ? (
                  <div className="p-6 text-center space-y-2">
                    <div className="w-9 h-9 rounded-full bg-slate-800 mx-auto flex items-center justify-center text-slate-400">
                      <Search className="w-4 h-4" />
                    </div>
                    <div className="text-xs font-bold text-slate-200">{searchError || (isSearchingApi ? 'Searching…' : query.trim().length < 2 ? 'Enter at least two characters' : 'No matching records found')}</div>
                    <p className="text-[11px] text-slate-400 leading-relaxed max-w-[240px] mx-auto">
                      No records match <span className="text-blue-300 font-mono font-semibold">"{query}"</span>. Try searching by survey number (e.g. <em>402/B</em>), owner name (e.g. <em>Kiran</em>), or record ID.
                    </p>
                    <button
                      type="button"
                      onClick={handleClear}
                      className="mt-1 text-xs text-blue-400 hover:text-blue-300 underline font-medium"
                    >
                      Clear search
                    </button>
                  </div>
                ) : (
                  searchResults.map((rec, idx) => {
                    const isDoc = rec.type === 'document_record' || String(rec.record_id || rec.id).startsWith('DOC-');
                    const surveyNo = rec.survey_number || rec.surveyNumber || 'N/A';
                    const owner = rec.owner_name || rec.ownerName || 'Unspecified Owner';
                    const recId = rec.record_id || rec.id || rec.document_id;
                    const area = rec.land_area_acres || rec.area || '';
                    const village = rec.village || '';
                    const district = rec.district || '';

                    return (
                      <button
                        type="button"
                        key={recId || idx}
                        onClick={() => handleSelect(rec)}
                        className="w-full p-3 hover:bg-slate-800/70 transition-colors flex items-center justify-between group text-left"
                      >
                        <div className="space-y-1 pr-2 truncate">
                          <div className="flex items-center gap-1.5 flex-wrap">
                            <span className="font-mono text-xs font-bold text-white group-hover:text-blue-300 transition-colors">
                              Survey {surveyNo}
                            </span>
                            <span className="text-[10px] font-mono text-slate-400 bg-slate-950 px-1.5 py-0.5 rounded border border-slate-800">
                              {recId}
                            </span>
                            <span className={`text-[9px] font-bold px-1.5 py-0.5 rounded border ${
                              isDoc
                                ? 'bg-purple-950/70 text-purple-300 border-purple-800'
                                : 'bg-blue-950/70 text-blue-300 border-blue-800'
                            }`}>
                              {isDoc ? 'DEED DOC' : 'LAND RECORD'}
                            </span>
                          </div>

                          <div className="text-xs text-slate-300 flex items-center gap-1 truncate font-medium">
                            <User className="w-3 h-3 text-slate-500 shrink-0" />
                            <span className="truncate">{owner}</span>
                          </div>

                          <div className="text-[11px] text-slate-400 flex items-center gap-1 truncate">
                            <MapPin className="w-3 h-3 text-slate-500 shrink-0" />
                            <span className="truncate">
                              {village ? `${village}, ` : ''}{district} {area ? `• ${area} ${String(area).includes('Acre') ? '' : 'Acres'}` : ''}
                            </span>
                          </div>
                        </div>

                        <div className="shrink-0 text-slate-500 group-hover:text-blue-400 transition-colors pl-2 flex items-center gap-1 text-[11px] font-semibold">
                          <span className="hidden sm:inline opacity-0 group-hover:opacity-100 transition-opacity">Open</span>
                          <ChevronRight className="w-4 h-4" />
                        </div>
                      </button>
                    );
                  })
                )}
              </div>
            </div>
          )}
        </div>

        {/* Upload Document Button */}
        <button
          onClick={onUploadClick}
          className="flex items-center gap-2 bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 text-white font-medium text-xs md:text-sm px-3.5 md:px-4 py-2 rounded-lg shadow-md shadow-blue-950 transition-all shrink-0"
        >
          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12" />
          </svg>
          <span className="hidden sm:inline">Upload Document</span>
          <span className="sm:hidden">Upload</span>
        </button>
      </div>
    </header>
  );
}
