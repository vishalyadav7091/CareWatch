import axios from 'axios';

const API_BASE = import.meta.env.VITE_API_BASE_URL || '/api/v1';

export const api = axios.create({
  baseURL: API_BASE,
  headers: {
    'Content-Type': 'application/json',
  },
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('carewatch_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export const authService = {
  login: async (email, password) => {
    const res = await api.post('/auth/login', { email, password });
    if (res.data.token) {
      localStorage.setItem('carewatch_token', res.data.token);
      localStorage.setItem('carewatch_user', JSON.stringify(res.data.user));
    }
    return res.data;
  },
  logout: () => {
    localStorage.removeItem('carewatch_token');
    localStorage.removeItem('carewatch_user');
  },
  getCurrentUser: () => {
    const userStr = localStorage.getItem('carewatch_user');
    return userStr ? JSON.parse(userStr) : null;
  },
};

export const clinicalService = {
  getPatients: () => api.get('/patients'),
  getPatientDetails: (id) => api.get(`/patients/${id}`),
  getBeds: () => api.get('/beds'),
  updateBedStatus: (bedId, status) => api.patch(`/beds/${bedId}/status`, { status }),
  getPatientVitals: (patientId, limit = 20) => api.get(`/vitals/patient/${patientId}?limit=${limit}`),
  getAlerts: (status = 'active', severity = null) => {
    let url = `/alerts?status=${status}`;
    if (severity) url += `&severity=${severity}`;
    return api.get(url);
  },
  acknowledgeAlert: (alertId, userId = 1, remarks = 'Reviewed by nurse') =>
    api.post(`/alerts/${alertId}/acknowledge`, { user_id: userId, remarks }),
  resolveAlert: (alertId, userId = 1) =>
    api.post(`/alerts/${alertId}/resolve`, { user_id: userId }),
  snoozeAlert: (alertId, durationMinutes = 15) =>
    api.post(`/alerts/${alertId}/snooze`, { duration_minutes: durationMinutes }),
  escalateAlert: (alertId, escalateToUserId = 1, notes = 'Escalated from dashboard') =>
    api.post(`/alerts/${alertId}/escalate`, { escalate_to_user_id: escalateToUserId, notes }),
  simulateTelemetry: (patientId, scenario = 'stable') =>
    api.post(`/acquisition/simulate/${patientId}?scenario=${scenario}`),
  getMLStatus: () => api.get('/ml/status'),
  trainMLModel: () => api.post('/ml/train'),
  getPatientRisk: (patientId, window = 10) => api.get(`/ml/infer/${patientId}?window=${window}`),
  getRiskHistory: (patientId) => api.get(`/ml/history/${patientId}`),
  getAuditLogs: (page = 1, perPage = 50) => api.get(`/audit?page=${page}&per_page=${perPage}`),
  getPatientAuditTrail: (patientId) => api.get(`/audit/patient/${patientId}`),
  getStaffDirectory: () => api.get('/audit/staff'),
};

