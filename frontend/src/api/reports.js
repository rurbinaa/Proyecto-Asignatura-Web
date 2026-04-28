import axiosClient, { handleApiError } from './axiosClient';
import { generateReportFilename, downloadBlob, parseBlobError } from '../utils/downloadUtils';

/**
 * Downloads the quality report as an Excel file.
 * @param {string} startDate - Start date (YYYY-MM-DD)
 * @param {string} endDate - End date (YYYY-MM-DD)
 * @returns {Promise<{filename: string}>} Object with the generated filename
 */
export const downloadQualityReport = async (startDate, endDate) => {
  if (!startDate || !endDate) {
    throw new Error('Se requiere seleccionar un período de fechas');
  }

  const start = new Date(startDate + 'T00:00:00');
  const end = new Date(endDate + 'T00:00:00');

  if (start > end) {
    throw new Error('La fecha de inicio debe ser anterior a la fecha de fin');
  }

  try {
    const response = await axiosClient.get('/quality/reports/corporate-xlsx/', {
      params: {
        date_from: startDate,
        date_to: endDate,
      },
      responseType: 'blob',
      timeout: 600000,
    });

    const blob = response.data;
    const filename = generateReportFilename(startDate, endDate);
    downloadBlob(blob, filename);

    return { filename };
  } catch (error) {
    if (error.response?.data instanceof Blob) {
      const errorData = await parseBlobError(error.response.data);
      throw new Error(errorData.message);
    }

    const apiError = handleApiError(error);
    throw new Error(apiError.message);
  }
};

/**
 * Validates if the date range is valid for report generation.
 * @param {string} startDate - Start date
 * @param {string} endDate - End date
 * @returns {{valid: boolean, message?: string}}
 */
export const validateDateRange = (startDate, endDate) => {
  if (!startDate || !endDate) {
    return { valid: false, message: 'Seleccione un período de fechas' };
  }

  const start = new Date(startDate + 'T00:00:00');
  const end = new Date(endDate + 'T00:00:00');

  if (start > end) {
    return { valid: false, message: 'La fecha de inicio debe ser anterior a la fecha de fin' };
  }

  const maxRangeDays = 365;
  const diffDays = Math.ceil((end - start) / (1000 * 60 * 60 * 24));

  if (diffDays > maxRangeDays) {
    return { valid: false, message: 'El período no puede exceder 365 días' };
  }

  return { valid: true };
};
