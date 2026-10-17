export const API_BASE_URL =
  import.meta.env.VITE_API_URL || "/api";

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

export async function getDashboardApi() {
  const response = await fetch(`${API_BASE_URL}/dashboard`);
  if (!response.ok) throw new Error('Could not load database records. Check that the backend is running.');
  return response.json();
}

export async function getSampleDocumentsApi() {
  const response = await fetch(`${API_BASE_URL}/documents/samples`);
  if (!response.ok) throw new Error('Could not load the dataset sample files.');
  return response.json();
}

export async function getSampleDocumentApi(filename) {
  const response = await fetch(`${API_BASE_URL}/documents/samples/${encodeURIComponent(filename)}`);
  if (!response.ok) throw new Error('Could not download the sample document.');
  const blob = await response.blob();
  return new File([blob], filename, { type: blob.type });
}

export async function getDocumentApi(documentId) {
  const response = await fetch(`${API_BASE_URL}/documents/${encodeURIComponent(documentId)}`);
  if (!response.ok) throw new Error('Could not load the uploaded document.');
  return response.json();
}

export async function setDocumentBoundaryApi(documentId, geometry) {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), 20000);
  try {
    const response = await fetch(`${API_BASE_URL}/documents/${encodeURIComponent(documentId)}/boundary`, {
      method: 'PUT', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(geometry), signal: controller.signal,
    });
    if (!response.ok) {
      const data = await response.json().catch(() => ({}));
      throw new Error(typeof data.detail === 'string' ? data.detail : 'Could not validate the claimed boundary.');
    }
    return response.json();
  } catch (error) {
    if (error.name === 'AbortError') throw new Error('Boundary comparison timed out. Check the API connection and retry.');
    throw error;
  } finally {
    clearTimeout(timer);
  }
}

export async function getRegistryRecordApi(recordId) {
  const response = await fetch(`${API_BASE_URL}/registry/${encodeURIComponent(recordId)}`);
  if (!response.ok) throw new Error('Could not load the registry record.');
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

