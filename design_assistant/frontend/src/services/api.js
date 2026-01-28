/**
 * HydroDraft API Service
 * Centralized API calls for all backend endpoints
 */

import axios from 'axios';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

// Axios instance with default config
const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
    'Cache-Control': 'no-cache',
    'Pragma': 'no-cache',
  },
});

// Add timestamp to prevent caching
api.interceptors.request.use((config) => {
  if (config.method === 'get') {
    config.params = { ...config.params, _t: Date.now() };
  }
  return config;
});

// ============== SYSTEM ==============
export const systemAPI = {
  healthCheck: () => api.get('/api/v1/health'),
  getSystemInfo: () => api.get('/health'),
};

// ============== TANK DESIGN V2 (Traceable) ==============
export const tankAPI = {
  // Basic design
  design: (data) => api.post('/api/v1/design/tank/', data),
  calculate: (data) => api.post('/api/v1/design/tank/calculate', data),
  
  // V2 - Traceable
  designV2: (data) => api.post('/api/v1/design/tank/v2', data),
  overrideViolation: (data) => api.post('/api/v1/design/tank/v2/override', data),
  getCalculationReport: (jobId) => api.get(`/api/v1/design/tank/v2/report/${jobId}`),
  getSafetyStatus: (jobId) => api.get(`/api/v1/design/tank/v2/safety/${jobId}`),
};

// ============== PIPELINE DESIGN ==============
export const pipelineAPI = {
  design: (data) => api.post('/api/v1/design/pipeline/', data),
};

// ============== WELL DESIGN ==============
export const wellAPI = {
  design: (data) => api.post('/api/v1/design/well/', data),
};

// ============== CAD V2 (Professional) ==============
export const cadAPI = {
  // Tank drawing
  createTankDrawing: (data) => api.post('/api/v1/cad/v2/tank', data),
  
  // Validation
  validateDrawing: (data) => api.post('/api/v1/cad/v2/validate', data),
  
  // Standards
  getBlocks: () => api.get('/api/v1/cad/v2/blocks'),
  getLayers: () => api.get('/api/v1/cad/v2/layers'),
  getStandards: () => api.get('/api/v1/cad/v2/standards'),
};

// ============== BIM (Sprint 4) ==============
export const bimAPI = {
  // Export
  exportTank: (data) => api.post('/api/v1/bim/export/tank', data),
  exportProject: (data) => api.post('/api/v1/bim/export/project', data),
  
  // Download
  downloadFile: (filename) => `${API_URL}/api/v1/bim/download/${filename}`,
};

// ============== VERSION MANAGEMENT (Sprint 4) ==============
export const versionAPI = {
  // CRUD
  createVersion: (data) => api.post('/api/v1/versions/create', data),
  getVersion: (versionId) => api.get(`/api/v1/versions/${versionId}`),
  listVersions: (projectId) => api.get(`/api/v1/versions/${projectId}/list`),
  
  // Actions
  compareVersions: (data) => api.post('/api/v1/versions/compare', data),
  approveVersion: (versionId, approvedBy) => 
    api.post(`/api/v1/versions/${versionId}/approve?approved_by=${encodeURIComponent(approvedBy)}`),
  rollbackVersion: (projectId, versionId) => 
    api.post(`/api/v1/versions/${projectId}/rollback/${versionId}`),
};

// ============== REPORTS (Sprint 4) ==============
export const reportAPI = {
  // Generate
  generateTechnicalReport: (data) => api.post('/api/v1/reports/technical', data),
  generateCalculationReport: (projectName, calculationLog) => 
    api.post(`/api/v1/reports/calculation?project_name=${encodeURIComponent(projectName)}`, calculationLog),
  
  // Download
  downloadReport: (filename) => `${API_URL}/api/v1/reports/download/${filename}`,
};

// ============== VIEWER (Sprint 4) ==============
export const viewerAPI = {
  getConfig: () => api.get('/api/v1/viewer/config'),
  getViewerHTML: (ifcUrl) => api.get(`/api/v1/viewer/html?ifc_url=${encodeURIComponent(ifcUrl)}`),
  getReactComponent: () => api.get('/api/v1/viewer/react-component'),
};

// ============== EXPORT/DOWNLOAD ==============
export const exportAPI = {
  download: (jobId, filename) => `${API_URL}/api/v1/export/download/${jobId}/${filename}`,
};

// Sprint 4 Health Check
export const sprint4API = {
  healthCheck: () => api.get('/api/v1/sprint4/health'),
};

export default api;
