export const mockStats = {
  totalChecked: 1284,
  verifiedRecords: 1142,
  suspiciousRecords: 142,
  averageRiskScore: 18,
  highRiskAlerts: 24
};

export const mockRecentRecords = [
  {
    id: "DOC-2026-8901",
    documentName: "Sale_Deed_Plot_402B.pdf",
    ownerName: "Rajesh Kumar Sharma",
    surveyNumber: "402/B",
    district: "Ranga Reddy, Telangana",
    area: "2.45 Acres",
    uploadDate: "2026-09-04",
    status: "Suspicious",
    riskScore: 78,
    riskLevel: "HIGH",
    issuesCount: 3
  },
  {
    id: "DOC-2026-8895",
    documentName: "7_12_Extract_Survey_118.pdf",
    ownerName: "Sunita Devi Patel",
    surveyNumber: "118/A",
    district: "Pune, Maharashtra",
    area: "1.20 Hectares",
    uploadDate: "2026-09-03",
    status: "Verified",
    riskScore: 12,
    riskLevel: "LOW",
    issuesCount: 0
  },
  {
    id: "DOC-2026-8870",
    documentName: "Patta_Passbook_Ext_55.png",
    ownerName: "Venkata Ramanappa",
    surveyNumber: "55/3C",
    district: "Anantapur, Andhra Pradesh",
    area: "3.10 Acres",
    uploadDate: "2026-09-02",
    status: "Review Needed",
    riskScore: 45,
    riskLevel: "MEDIUM",
    issuesCount: 1
  },
  {
    id: "DOC-2026-8854",
    documentName: "Partition_Deed_89.pdf",
    ownerName: "Mahesh Chandra Verma",
    surveyNumber: "89/1",
    district: "Bhopal, Madhya Pradesh",
    area: "0.85 Acres",
    uploadDate: "2026-09-01",
    status: "Verified",
    riskScore: 8,
    riskLevel: "LOW",
    issuesCount: 0
  }
];

export const mockSelectedRecord = {
  id: "DOC-2026-8901",
  documentName: "Sale_Deed_Plot_402B.pdf",
  documentType: "Registered Sale Deed",
  registrationOffice: "Sub-Registrar Office, Shamshabad",
  registrationDate: "14-May-2023",
  extractedFields: {
    ownerName: "Rajesh Kumar Sharma",
    govtOwnerName: "Ramesh Chandra Sharma (Deceased)",
    surveyNumber: "402/B",
    govtSurveyNumber: "402/B",
    claimedArea: "2.45 Acres",
    govtRecordArea: "1.80 Acres",
    location: "Village Gachibowli, Survey Plot 402/B, RR District",
    encumbranceStatus: "Active Bank Mortgage (State Bank of India)",
    stampDutyPaid: "₹ 1,45,000 (Deficit detected: Expected ₹ 2,10,000)"
  },
  fieldComparisons: [
    { field: "Owner Name", extracted: "Rajesh Kumar Sharma", registered: "Ramesh Chandra Sharma (Deceased)", match: false, severity: "High" },
    { field: "Survey Number", extracted: "402/B", registered: "402/B", match: true, severity: "None" },
    { field: "Land Area", extracted: "2.45 Acres", registered: "1.80 Acres", match: false, severity: "High" },
    { field: "District & Village", extracted: "Shamshabad, RR Dist", registered: "Shamshabad, RR Dist", match: true, severity: "None" },
    { field: "Encumbrance / Lien", extracted: "Nil / Clear Title", registered: "Active Mortgage (SBI - ₹ 45 Lakhs)", match: false, severity: "Critical" },
    { field: "Stamp Duty Calculation", extracted: "₹ 1,45,000 Paid", registered: "₹ 2,10,000 Required", match: false, severity: "Medium" }
  ],
  riskScore: 78,
  riskLevel: "HIGH",
  detectedIssues: [
    {
      id: 1,
      title: "Ownership Identity Mismatch",
      category: "Title Fraud Risk",
      severity: "High",
      description: "Document claims ownership under Rajesh Kumar Sharma, but Revenue Registry lists father Ramesh Chandra Sharma without registered mutation or succession certificate."
    },
    {
      id: 2,
      title: "Land Area Inflation Anomaly",
      category: "Encroachment Risk",
      severity: "High",
      description: "Document lists 2.45 Acres, exceeding the official Cadastral map parcel boundary of 1.80 Acres by 0.65 Acres."
    },
    {
      id: 3,
      title: "Active Undisclosed Mortgage Encumbrance",
      category: "Financial Lien Fraud",
      severity: "Critical",
      description: "Land parcel is currently mortgaged with State Bank of India for ₹45,000,000. Document claims 'Free from all encumbrances'."
    }
  ]
};

export const mockRiskBreakdown = {
  score: 78,
  level: "HIGH",
  statusColor: "red",
  factors: [
    { name: "Ownership Chain Continuity", weight: "35%", score: 85, status: "Critical Failure", desc: "Missing legal heir mutation deed" },
    { name: "Land Area & Parcel Polygon Match", weight: "25%", score: 75, status: "Discrepancy", desc: "0.65 Acre boundary overlap detected" },
    { name: "Encumbrance & Bank Lien Check", weight: "20%", score: 90, status: "Critical Alert", desc: "Undisclosed active bank mortgage" },
    { name: "Stamp Duty & Valuation Audit", weight: "10%", score: 50, status: "Warning", desc: "Under-valued registration fee paid" },
    { name: "OCR Text & Signature Authenticity", weight: "10%", score: 20, status: "Passed", desc: "Standard stamp font & seal match" }
  ]
};

export const mockOwnershipTimeline = [
  {
    year: "1985",
    date: "12-Nov-1985",
    event: "Original Govt Land Grant (Patta)",
    parties: "Govt of Telangana → Gopal Sharma",
    surveyNo: "402",
    area: "1.80 Acres",
    documentRef: "PATTA-GR-1985-004",
    status: "Verified"
  },
  {
    year: "2008",
    date: "04-Mar-2008",
    event: "Inheritance Mutation & Title Transfer",
    parties: "Gopal Sharma → Ramesh Chandra Sharma",
    surveyNo: "402/B",
    area: "1.80 Acres",
    documentRef: "MUT-2008-8812",
    status: "Verified"
  },
  {
    year: "2021",
    date: "18-Aug-2021",
    event: "Equitable Bank Mortgage Created",
    parties: "Ramesh Chandra Sharma → State Bank of India",
    surveyNo: "402/B",
    area: "1.80 Acres",
    documentRef: "MOD-2021-9921",
    status: "Active Encumbrance"
  },
  {
    year: "2023",
    date: "14-May-2023",
    event: "Unverified Sale Deed Attempt",
    parties: "Rajesh Kumar Sharma → Private Buyer",
    surveyNo: "402/B",
    area: "2.45 Acres (Inflated)",
    documentRef: "DEED-2023-402B (FLAGGED)",
    status: "Flagged Suspicious"
  }
];

export const mockGisParcelData = {
  surveyNumber: "402/B",
  village: "Gachibowli",
  mandal: "Serilingampally",
  district: "Ranga Reddy",
  coordinates: {
    lat: 17.4401,
    lng: 78.3489,
    zoom: 15
  },
  registeredBoundary: [
    [17.4410, 78.3480],
    [17.4415, 78.3495],
    [17.4395, 78.3500],
    [17.4390, 78.3485]
  ],
  claimedBoundary: [
    [17.4415, 78.3475],
    [17.4420, 78.3498],
    [17.4392, 78.3508],
    [17.4388, 78.3480]
  ],
  adjacentSurveys: ["402/A", "402/C", "403/1", "401"]
};
