const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

/**
 * Upload an Excel file for preview analysis.
 * 
 * Sends the file as raw binary body (NOT FormData) to match Django's
 * FileUploadParser expectations.
 * 
 * @param {File} file - The Excel file to upload
 * @returns {Promise<{session_id: number, status: string, preview: object, warnings: string[]}>}
 */
export async function uploadForPreview(file) {
  const filename = encodeURIComponent(file.name);
  const url = `${API_BASE}/quality/excel/preview/${filename}/`;

  const response = await fetch(url, {
    method: 'POST',
    headers: {
      'Content-Disposition': `attachment; filename="${file.name}"`,
    },
    body: file,
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ error: response.statusText }));
    throw new Error(error.error || `Preview failed: ${response.status}`);
  }

  return response.json();
}

/**
 * Confirm and apply changes from a pending preview session.
 * 
 * @param {number} sessionId - The session ID returned by uploadForPreview
 * @returns {Promise<{session_id: number, status: string, message: string}>}
 */
export async function confirmSession(sessionId) {
  const url = `${API_BASE}/quality/excel/confirm/${sessionId}/`;

  const response = await fetch(url, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ error: response.statusText }));
    throw new Error(error.error || `Confirm failed: ${response.status}`);
  }

  return response.json();
}

/**
 * Reject a pending preview session — no changes are applied.
 * 
 * @param {number} sessionId - The session ID returned by uploadForPreview
 * @returns {Promise<{session_id: number, status: string, message: string}>}
 */
export async function rejectSession(sessionId) {
  const url = `${API_BASE}/quality/excel/reject/${sessionId}/`;

  const response = await fetch(url, {
    method: 'DELETE',
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ error: response.statusText }));
    throw new Error(error.error || `Reject failed: ${response.status}`);
  }

  return response.json();
}
