const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

/**
 * Create a new inspection session.
 * 
 * @param {object} data - Inspection data
 * @param {string} data.lot - Lot number
 * @param {string} data.style - Style name
 * @param {string} data.size - Size
 * @param {string} data.color - Color name
 * @returns {Promise<object>} Created inspection with ID
 */
export async function createInspection(data) {
  const response = await fetch(`${API_BASE}/api/v1/inspections/`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(data),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ error: response.statusText }));
    throw new Error(error.error || `Create inspection failed: ${response.status}`);
  }

  return response.json();
}

/**
 * Create a defect record for an inspection.
 * 
 * @param {object} data - Defect data
 * @param {number} data.inspection - Inspection ID
 * @param {string} data.defect_type - Defect type name (string, not ID)
 * @param {string} data.defect_size - Size/description
 * @param {number[]} data.coordinates_x - Array of X coordinates
 * @param {number[]} data.coordinates_y - Array of Y coordinates
 * @param {number} data.defect_count - Number of defects at these coordinates
 * @returns {Promise<object>} Created defect record
 */
export async function createDefect(data) {
  const response = await fetch(`${API_BASE}/api/v1/defects/`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(data),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ error: response.statusText }));
    throw new Error(error.error || `Create defect failed: ${response.status}`);
  }

  return response.json();
}

/**
 * Remove the last captured defect for an inspection.
 * 
 * @param {number} inspectionId - The inspection ID
 * @returns {Promise<object>} Result message
 */
export async function undoDefect(inspectionId) {
  const response = await fetch(
    `${API_BASE}/api/v1/defects/undo/?inspection=${inspectionId}`,
    {
      method: 'DELETE',
    }
  );

  if (!response.ok) {
    const error = await response.json().catch(() => ({ error: response.statusText }));
    throw new Error(error.error || `Undo defect failed: ${response.status}`);
  }

  return response.json();
}

/**
 * Close an inspection, evaluate PASS/REJECT, and sync to QualityQcFa.
 * 
 * @param {number} inspectionId - The inspection ID
 * @returns {Promise<object>} Result with status, result, and sync info
 */
export async function closeInspection(inspectionId) {
  const response = await fetch(
    `${API_BASE}/api/v1/inspections/${inspectionId}/close_inspection/`,
    {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
    }
  );

  if (!response.ok) {
    const error = await response.json().catch(() => ({ error: response.statusText }));
    throw new Error(error.error || `Close inspection failed: ${response.status}`);
  }

  return response.json();
}

/**
 * Fetch available mockup images for the capture interface.
 * 
 * @returns {Promise<object[]>} List of mockup objects
 */
export async function getMockups() {
  const response = await fetch(`${API_BASE}/api/v1/mockups/`);

  if (!response.ok) {
    const error = await response.json().catch(() => ({ error: response.statusText }));
    throw new Error(error.error || `Get mockups failed: ${response.status}`);
  }

  return response.json();
}