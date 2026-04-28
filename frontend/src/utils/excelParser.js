/**
 * Excel parsing utility functions extracted from ExcelUploader component
 * These are pure functions that can be tested independently
 */

export const REQUIRED_COLUMNS = {
  "QC FA Plant": ["date", "week", "customer", "team", "coord", "po", "style", "batch", "color", "qty"],
  "QC FA Customer": ["date", "week", "customer", "line", "artcode", "po", "style", "batch", "color", "quantity"],
  "SecondsA4": ["year", "week", "date", "cut", "style", "color", "accepted", "rejected"],
  "Seconds General": ["date", "week", "picado", "manchas", "grasa", "tono", "fuera", "definitive"],
  "Container": ["container", "customer", "palette", "pass"]
};

export const SHEET_GROUPS_MAP = {
  QFA: ["QC FA Plant", "QC FA Customer"],
  SECONDS: ["SecondsA4", "Seconds General"],
  CONTAINER: ["Container"],
  ALL: ["QC FA Plant", "QC FA Customer", "SecondsA4", "Seconds General", "Container"]
};

/**
 * Cleans text by removing special characters and converting to lowercase
 * @param {any} text - Input text to clean
 * @returns {string} Cleaned text
 */
export const cleanText = (text) => String(text || "").replace(/[^a-zA-Z0-9]/g, "").toLowerCase();

/**
 * Formats Excel serial numbers or date strings to YYYY-MM-DD format
 * @param {any} serial - Excel serial number, date string, or already formatted date
 * @returns {string|number} Formatted date string or original value
 */
export const formatExcelDate = (serial) => {
  if (serial == null || serial === '') return serial;

  // Already a valid YYYY-MM-DD string
  if (typeof serial === 'string' && /^\d{4}-\d{2}-\d{2}$/.test(serial)) {
    return serial;
  }

  // Excel serial number (e.g. 45665)
  if (typeof serial === 'number') {
    const date = new Date(Math.round((serial - 25569) * 86400 * 1000));
    if (!isNaN(date.getTime())) {
      return date.toISOString().split('T')[0];
    }
    return serial;
  }

  // String date in various formats (MM/DD/YYYY, DD-MM-YYYY, etc.)
  if (typeof serial === 'string') {
    const date = new Date(serial);
    if (!isNaN(date.getTime())) {
      return date.toISOString().split('T')[0];
    }
  }

  return serial;
};

/**
 * Finds headers and data rows in Excel data
 * @param {Array} rows - Array of row arrays from Excel
 * @param {string} sheetName - Sheet name to find headers for
 * @returns {Object|null} { headers, data } or null if not found
 */
export const findHeadersAndData = (rows, sheetName) => {
  const required = REQUIRED_COLUMNS[sheetName];
  if (!required) return null;
  
  for (let i = 0; i < Math.min(rows.length, 40); i++) {
    if (!rows[i] || rows[i].length === 0) continue;
    
    const potentialRow = rows[i].map(cell => cleanText(cell));
    
    const matchCount = required.filter(req => 
      potentialRow.some(cell => cell.includes(cleanText(req)))
    ).length;
    
    if (matchCount >= required.length - 1) {
      return { headers: rows[i], data: rows.slice(i + 1) };
    }
  }
  return null;
};
