import axiosClient from './axiosClient';

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
  try {
    const res = await axiosClient.post('/api/v1/inspections/', data);
    return res.data;
  } catch (error) {
    throw new Error(error.response?.data?.error || `Create inspection failed: ${error.response?.status}`);
  }
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
  try {
    const res = await axiosClient.post('/api/v1/defects/', data);
    return res.data;
  } catch (error) {
    throw new Error(error.response?.data?.error || `Create defect failed: ${error.response?.status}`);
  }
}

/**
 * Close an inspection, evaluate PASS/REJECT, and sync to QualityQcFa.
 * 
 * @param {number} inspectionId - The inspection ID
 * @returns {Promise<object>} Result with status, result, and sync info
 */
export async function closeInspection(inspectionId) {
  try {
    const res = await axiosClient.post(`/api/v1/inspections/${inspectionId}/close_inspection/`);
    return res.data;
  } catch (error) {
    throw new Error(error.response?.data?.error || `Close inspection failed: ${error.response?.status}`);
  }
}

