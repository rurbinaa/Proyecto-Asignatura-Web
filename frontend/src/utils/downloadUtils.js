/**
 * Generates a dynamic filename for quality reports.
 * @param {string} startDate - Start date in YYYY-MM-DD format
 * @param {string} endDate - End date in YYYY-MM-DD format
 * @returns {string} Generated filename (e.g., "Reporte_Calidad_Marzo_2026.xlsx")
 */
export function generateReportFilename(startDate, endDate) {
  const formatMonthYear = (dateStr) => {
    const date = new Date(dateStr + 'T00:00:00');
    const month = date.toLocaleDateString('es-ES', { month: 'long' });
    const year = date.getFullYear();
    return `${month.charAt(0).toUpperCase() + month.slice(1)}_${year}`;
  };

  let filename = 'Reporte_Calidad';

  if (startDate && endDate) {
    const start = new Date(startDate + 'T00:00:00');
    const end = new Date(endDate + 'T00:00:00');

    if (startDate === endDate) {
      const day = start.getDate();
      const month = start.toLocaleDateString('es-ES', { month: 'long' });
      const year = start.getFullYear();
      return `Reporte_Calidad_${day}_${month.charAt(0).toUpperCase() + month.slice(1)}_${year}.xlsx`;
    }

    if (start.getFullYear() === end.getFullYear()) {
      const startMonth = start.toLocaleDateString('es-ES', { month: 'long' });
      const endMonth = end.toLocaleDateString('es-ES', { month: 'long' });
      return `Reporte_Calidad_${startMonth.charAt(0).toUpperCase() + startMonth.slice(1)}_a_${endMonth.charAt(0).toUpperCase() + endMonth.slice(1)}_${start.getFullYear()}.xlsx`;
    }

    filename += `_${formatMonthYear(startDate)}_a_${formatMonthYear(endDate)}`;
  } else if (startDate) {
    filename += `_Desde_${formatMonthYear(startDate)}`;
  } else if (endDate) {
    filename += `_Hasta_${formatMonthYear(endDate)}`;
  }

  return `${filename}.xlsx`;
}

/**
 * Forces a file download in the user's browser.
 * @param {Blob} blob - The file blob data
 * @param {string} filename - The name for the downloaded file
 */
export function downloadBlob(blob, filename) {
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
}

/**
 * Reads error response from blob when the server returns an error as JSON blob.
 * @param {Blob} blob - Error response blob
 * @returns {Promise<{message: string}>} Parsed error object
 */
export async function parseBlobError(blob) {
  try {
    const text = await blob.text();
    const data = JSON.parse(text);
    return { message: data.error || data.detail || 'Error desconocido' };
  } catch {
    return { message: 'Error al procesar la respuesta del servidor' };
  }
}