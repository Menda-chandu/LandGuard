import React, { useState } from 'react';
import Navbar from './components/Navbar';
import Sidebar from './components/Sidebar';
import Dashboard from './pages/Dashboard';
import UploadDocument from './pages/UploadDocument';
import DocumentAnalysis from './pages/DocumentAnalysis';
import VerificationResults from './pages/VerificationResults';
import RiskScoreView from './pages/RiskScoreView';
import OwnershipHistory from './pages/OwnershipHistory';
import GisMap from './pages/GisMap';

export default function App() {
  const [activeTab, setActiveTab] = useState('dashboard');
  const [activeDocument, setActiveDocument] = useState(null);
  const [verificationResult, setVerificationResult] = useState(null);

  const handleUploadSuccess = (uploadedDocPayload) => {
    setActiveDocument(uploadedDocPayload);
    setVerificationResult(null);
    setActiveTab('analysis');
  };

  const renderActivePage = () => {
    switch (activeTab) {
      case 'dashboard':
        return <Dashboard onNavigate={(tab) => setActiveTab(tab)} />;
      case 'upload':
        return <UploadDocument onUploadSuccess={handleUploadSuccess} />;
      case 'analysis':
        return <DocumentAnalysis activeDocument={activeDocument} onProceedToResults={() => setActiveTab('verification')} />;
      case 'verification':
        return (
          <VerificationResults
            activeDocument={activeDocument}
            verificationResult={verificationResult}
            onVerificationComplete={setVerificationResult}
            onNavigate={(tab) => setActiveTab(tab)}
          />
        );
      case 'risk':
        return (
          <RiskScoreView
            activeDocument={activeDocument}
            verificationResult={verificationResult}
          />
        );
      case 'history':
        return <OwnershipHistory activeDocument={activeDocument} />;
      case 'gis':
        return <GisMap activeDocument={activeDocument} />;
      default:
        return <Dashboard onNavigate={(tab) => setActiveTab(tab)} />;
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col font-sans">
      {/* Top Bar */}
      <Navbar onUploadClick={() => setActiveTab('upload')} />

      {/* Persistent Synthetic / Demo Disclaimer Banner */}
      <div className="bg-amber-950/40 border-b border-amber-800/50 px-4 py-2 text-center text-xs text-amber-300/90 flex items-center justify-center gap-2">
        <span className="text-sm">⚠️</span>
        <span>
          <strong>Notice:</strong> This application operates on a <strong>synthetic demonstration dataset</strong>. Verification outcomes, risk indices, and anomaly alerts are generated for algorithmic testing and <strong>do not constitute official government verification</strong>.
        </span>
      </div>

      {/* Main Layout Area */}
      <div className="flex-1 flex overflow-hidden">
        {/* Sidebar Navigation */}
        <Sidebar activeTab={activeTab} setActiveTab={setActiveTab} />

        {/* Mobile Navigation Pills for Small Screens */}
        <div className="lg:hidden fixed bottom-0 left-0 right-0 z-40 bg-slate-900 border-t border-slate-800 p-2 flex items-center justify-around overflow-x-auto">
          {[
            { id: 'dashboard', label: 'Dash' },
            { id: 'upload', label: 'Upload' },
            { id: 'analysis', label: 'OCR' },
            { id: 'verification', label: 'Results' },
            { id: 'risk', label: 'Risk' },
            { id: 'history', label: 'History' },
            { id: 'gis', label: 'GIS' }
          ].map((item) => (
            <button
              key={item.id}
              onClick={() => setActiveTab(item.id)}
              className={`px-3 py-1.5 rounded-lg text-xs font-semibold shrink-0 ${
                activeTab === item.id ? 'bg-blue-600 text-white' : 'text-slate-400'
              }`}
            >
              {item.label}
            </button>
          ))}
        </div>

        {/* Dynamic Page Content */}
        <main className="flex-1 overflow-y-auto p-4 md:p-8 pb-20 lg:pb-8">
          {renderActivePage()}
        </main>
      </div>
    </div>
  );
}
