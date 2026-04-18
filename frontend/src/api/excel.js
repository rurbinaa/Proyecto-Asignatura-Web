import axiosClient from './axiosClient';
const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

/**
 * Upload an Excel file for preview analysis.
 *
 * Uses FormData with field name 'file' to match Django's FileUploadParser.
 * Browser auto-sets Content-Type with boundary — do NOT set manually.
 *
 * @param {File} file - The Excel file to upload
 * @returns {Promise<{session_id: number, status: string, preview: object, warnings: string[]}>}
 */
export async function uploadForPreview(file) {
  const filename = encodeURIComponent(file.name);
  const url = `/quality/excel/preview/${filename}/`;
  const formData = new FormData();
  formData.append('file', file, filename);
  try {
    const res = await axiosClient.post(url, formData);
    return res.data;
  } catch (error) {
    if (error.response) {
      throw new Error(error.response.data?.error || `Preview failed: ${error.response.status}`);
    } else if (error.message) {
      throw new Error(error.message);
    } else {
      throw new Error('Preview failed: unknown error');
    }
  }
}

/**
 * Confirm and apply changes from a pending preview session.
 * 
 * @param {number} sessionId - The session ID returned by uploadForPreview
 * @returns {Promise<{session_id: number, status: string, message: string}>}
 */
export async function confirmSession(sessionId) {
  const url = `/quality/excel/confirm/${sessionId}/`;
  try {
    const res = await axiosClient.post(url);
    return res.data;
  } catch (error) {
    throw new Error(error.response?.data?.error || `Confirm failed: ${error.response?.status}`);
  }
}

/**
 * Reject a pending preview session — no changes are applied.
 * 
 * @param {number} sessionId - The session ID returned by uploadForPreview
 * @returns {Promise<{session_id: number, status: string, message: string}>}
 */
export async function rejectSession(sessionId) {
  const url = `/quality/excel/reject/${sessionId}/`;
  try {
    const res = await axiosClient.delete(url);
    return res.data;
  } catch (error) {
    throw new Error(error.response?.data?.error || `Reject failed: ${error.response?.status}`);
  }
}
