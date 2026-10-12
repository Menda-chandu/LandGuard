export const API_BASE_URL =
  import.meta.env.VITE_API_URL ||
  (typeof window !== "undefined" &&
  (window.location.hostname === "localhost" ||
    window.location.hostname === "127.0.0.1")
    ? "http://localhost:8000/api"
    : "https://landguard-1-a465.onrender.com/api");

export async function uploadDocumentApi(file) {
  const formData = new FormData();
  formData.append("file", file);

  const response = await fetch(`${API_BASE_URL}/documents/upload`, {
    method: "POST",
    body: formData,
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || "Failed to upload document.");
  }

  return response.json();
}

export async function getDocumentNlpApi(documentId) {
  const response = await fetch(`${API_BASE_URL}/documents/${documentId}/nlp`);
  if (!response.ok) {
    throw new Error("Failed to fetch NLP extraction details.");
  }
  return response.json();
}

export async function getVerificationApi(documentId) {
  const response = await fetch(`${API_BASE_URL}/verification/verify/${documentId}`, {
    method: "POST"
  });
  if (!response.ok) {
    throw new Error("Failed to fetch verification results.");
  }
  return response.json();
}

export async function getRiskAssessmentApi(documentId) {
  const response = await fetch(`${API_BASE_URL}/risk/assess/${documentId}`, {
    method: "POST"
  });
  if (!response.ok) {
    throw new Error("Failed to fetch risk assessment.");
  }
  return response.json();
}

export async function getGisParcelsApi() {
  const response = await fetch(`${API_BASE_URL}/gis/parcels`);
  if (!response.ok) {
    throw new Error("Failed to fetch GIS parcel boundaries.");
  }
  return response.json();
}

export async function getOwnershipHistoryApi(documentId) {
  const response = await fetch(`${API_BASE_URL}/documents/${documentId}/history`);
  if (!response.ok) {
    throw new Error("Failed to fetch ownership history timeline.");
  }
  return response.json();
}

export async function searchRecordsApi(query) {
  if (!query || !query.trim()) return { count: 0, results: [] };
  const response = await fetch(`${API_BASE_URL}/documents/search?q=${encodeURIComponent(query.trim())}`);
  if (!response.ok) {
    throw new Error("Failed to search records.");
  }
  return response.json();
}

