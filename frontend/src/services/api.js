import axios from 'axios';

const API_BASE = import.meta.env.VITE_API_URL || '';

export const api = axios.create({
  baseURL: API_BASE,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Interceptor to inject JWT Bearer Token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('aarka_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Interceptor for 401 handling
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response && error.response.status === 401) {
      const currentPath = window.location.pathname;
      if (!currentPath.includes('/login') && !currentPath.includes('/enquiry') && !currentPath.includes('/public')) {
        localStorage.removeItem('aarka_token');
        localStorage.removeItem('aarka_user');
        window.location.href = '/login';
      }
    }
    return Promise.reject(error);
  }
);

// --- Auth & Team ---
export const authAPI = {
  login: (email, password) => api.post('/api/auth/login', { email, password }),
  register: (data) => api.post('/api/auth/register', data),
  googleAuth: (credential) => api.post('/api/auth/google', { credential }),
  verifyEmail: (token) => api.get('/api/auth/verify-email', { params: { token } }),
  resendVerification: (email) => api.post('/api/auth/resend-verification', { email }),
  forgotPassword: (email) => api.post('/api/auth/forgot-password', { email }),
  resetPassword: (data) => api.post('/api/auth/reset-password', data),
  getProfile: () => api.get('/api/auth/me'),
  getMe: () => api.get('/api/auth/me'),
  getUsers: () => api.get('/api/auth/users'),
  getAll: () => api.get('/api/auth/users'),
  createUser: (data) => api.post('/api/auth/users', data),
  updateUser: (id, data) => api.put(`/api/auth/users/${id}`, data),
};
export const authApi = authAPI;

// --- Public Enquiries ---
export const publicAPI = {
  submitEnquiry: (data) => api.post('/api/public/enquiry', data),
  getPublicPackages: () => api.get('/api/public/packages'),
};
export const publicApi = publicAPI;

// --- Leads ---
export const leadsAPI = {
  getLeads: (params) => api.get('/api/leads', { params }),
  getAll: (params) => api.get('/api/leads', { params }),
  getLead: (id) => api.get(`/api/leads/${id}`),
  getById: (id) => api.get(`/api/leads/${id}`),
  createLead: (data) => api.post('/api/leads', data),
  create: (data) => api.post('/api/leads', data),
  updateLead: (id, data) => api.put(`/api/leads/${id}`, data),
  update: (id, data) => api.put(`/api/leads/${id}`, data),
  qualifyLead: (id, data) => api.post(`/api/leads/${id}/qualify`, data),
  deleteLead: (id) => api.delete(`/api/leads/${id}`),
};
export const leadsApi = leadsAPI;

// --- Customers ---
export const customersAPI = {
  getCustomers: (params) => api.get('/api/customers', { params }),
  getAll: (params) => api.get('/api/customers', { params }),
  getCustomer: (id) => api.get(`/api/customers/${id}`),
  getById: (id) => api.get(`/api/customers/${id}`),
  createCustomer: (data) => api.post('/api/customers', data),
  create: (data) => api.post('/api/customers', data),
  updateCustomer: (id, data) => api.put(`/api/customers/${id}`, data),
};
export const customersApi = customersAPI;

// --- Surveys ---
export const surveysAPI = {
  getSurveys: (params) => api.get('/api/surveys', { params }),
  getAll: (params) => api.get('/api/surveys', { params }),
  getSurvey: (id) => api.get(`/api/surveys/${id}`),
  getById: (id) => api.get(`/api/surveys/${id}`),
  scheduleSurvey: (data) => api.post('/api/surveys', data),
  schedule: (data) => api.post('/api/surveys', data),
  updateSurvey: (id, data) => api.put(`/api/surveys/${id}`, data),
  update: (id, data) => api.put(`/api/surveys/${id}`, data),
  approveSurvey: (id, data) => api.post(`/api/surveys/${id}/approve`, data),
  approve: (id, data) => api.post(`/api/surveys/${id}/approve`, data),
  uploadSurveyPhoto: (id, formData) => api.post(`/api/surveys/${id}/upload-photo`, formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  }),
};
export const surveysApi = surveysAPI;

// --- Products & Packages ---
export const productsAPI = {
  getProducts: (params) => api.get('/api/products', { params }),
  getAll: (params) => api.get('/api/products', { params }),
  createProduct: (data) => api.post('/api/products', data),
  create: (data) => api.post('/api/products', data),
  updateProduct: (id, data) => api.put(`/api/products/${id}`, data),
  getPackages: () => api.get('/api/products/packages'),
};
export const productsApi = productsAPI;
export const packagesApi = {
  getAll: () => api.get('/api/products/packages'),
};

// --- Bill of Materials (BOM) ---
export const bomAPI = {
  calculateBOM: (packageType, capacityKw, includeInstallation = true) =>
    api.get('/api/bom/calculate', {
      params: { package_type: packageType, capacity_kw: capacityKw, include_installation: includeInstallation },
    }),
  calculate: (packageType, capacityKw, includeInstallation = true) =>
    api.get('/api/bom/calculate', {
      params: { package_type: packageType, capacity_kw: capacityKw, include_installation: includeInstallation },
    }),
  getTemplates: () => api.get('/api/bom/templates'),
};
export const bomApi = bomAPI;

// --- Quotations ---
export const quotationsAPI = {
  getQuotations: (params) => api.get('/api/quotations', { params }),
  getAll: (params) => api.get('/api/quotations', { params }),
  getQuotation: (id) => api.get(`/api/quotations/${id}`),
  getById: (id) => api.get(`/api/quotations/${id}`),
  createQuotation: (data) => api.post('/api/quotations', data),
  create: (data) => api.post('/api/quotations', data),
  sendQuotation: (id) => api.post(`/api/quotations/${id}/send`),
  send: (id) => api.post(`/api/quotations/${id}/send`),
  acceptQuotation: (id) => api.post(`/api/quotations/${id}/accept`),
  accept: (id) => api.post(`/api/quotations/${id}/accept`),
};
export const quotationsApi = quotationsAPI;

// --- Orders ---
export const ordersAPI = {
  getOrders: (params) => api.get('/api/orders', { params }),
  getAll: (params) => api.get('/api/orders', { params }),
  getOrder: (id) => api.get(`/api/orders/${id}`),
  getById: (id) => api.get(`/api/orders/${id}`),
  reserveMaterials: (id) => api.post(`/api/orders/${id}/reserve-materials`),
  getPicklist: (id) => api.get(`/api/orders/${id}/picklist`),
};
export const ordersApi = ordersAPI;

// --- Payments ---
export const paymentsAPI = {
  getPayments: (params) => api.get('/api/payments', { params }),
  getAll: (params) => api.get('/api/payments', { params }),
  recordPayment: (data) => api.post('/api/payments', data),
  create: (data) => api.post('/api/payments', data),
};
export const paymentsApi = paymentsAPI;

// --- Inventory ---
export const inventoryAPI = {
  getInventory: (params) => api.get('/api/inventory', { params }),
  getAll: (params) => api.get('/api/inventory', { params }),
  receiveStock: (data) => api.post('/api/inventory/receive', data),
  receive: (data) => api.post('/api/inventory/receive', data),
  adjustStock: (data) => api.post('/api/inventory/adjust', data),
  getMovements: (params) => api.get('/api/inventory/movements', { params }),
};
export const inventoryApi = inventoryAPI;

// --- Serial Numbers ---
export const serialsAPI = {
  getSerials: (params) => api.get('/api/serials', { params }),
  getAll: (params) => api.get('/api/serials', { params }),
  registerSerial: (data) => api.post('/api/serials', data),
  create: (data) => api.post('/api/serials', data),
  scanSerial: (data) => api.post('/api/serials/scan', data),
  scan: (data) => api.post('/api/serials/scan', data),
  getSerialHistory: (sn) => api.get(`/api/serials/history/${sn}`),
  getHistory: (sn) => api.get(`/api/serials/history/${sn}`),
};
export const serialsApi = serialsAPI;

// --- Dispatches ---
export const dispatchesAPI = {
  getDispatches: (params) => api.get('/api/dispatches', { params }),
  getAll: (params) => api.get('/api/dispatches', { params }),
  createDispatch: (data) => api.post('/api/dispatches', data),
  create: (data) => api.post('/api/dispatches', data),
  confirmDelivery: (id, data) => api.post(`/api/dispatches/${id}/confirm-delivery`, data),
};
export const dispatchesApi = dispatchesAPI;

// --- Technicians ---
export const techniciansAPI = {
  getTechnicians: (params) => api.get('/api/technicians', { params }),
  getAll: (params) => api.get('/api/technicians', { params }),
  createTechnician: (data) => api.post('/api/technicians', data),
  create: (data) => api.post('/api/technicians', data),
  getTechnicianSchedule: (id) => api.get(`/api/technicians/${id}/schedule`),
};
export const techniciansApi = techniciansAPI;

// --- Installations ---
export const installationsAPI = {
  getInstallations: (params) => api.get('/api/installations', { params }),
  getAll: (params) => api.get('/api/installations', { params }),
  getInstallation: (id) => api.get(`/api/installations/${id}`),
  getById: (id) => api.get(`/api/installations/${id}`),
  scheduleInstallation: (data) => api.post('/api/installations', data),
  schedule: (data) => api.post('/api/installations', data),
  updateChecklist: (id, data) => api.put(`/api/installations/${id}/checklist`, data),
  uploadInstallPhoto: (id, formData) => api.post(`/api/installations/${id}/upload-photo`, formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  }),
  completeInstallation: (id, data) => api.post(`/api/installations/${id}/complete`, data),
  complete: (id, data) => api.post(`/api/installations/${id}/complete`, data),
};
export const installationsApi = installationsAPI;

// --- Warranties ---
export const warrantiesAPI = {
  getWarranties: (params) => api.get('/api/warranties', { params }),
  getAll: (params) => api.get('/api/warranties', { params }),
  getDashboardSummary: () => api.get('/api/warranties/dashboard-summary'),
  getExpiryAlerts: () => api.get('/api/warranties/expiry-alerts'),
  triggerExpiryAlerts: () => api.post('/api/warranties/expiry-alerts/trigger'),
  getWarranty: (id) => api.get(`/api/warranties/${id}`),
  getCertificate: (id) => api.get(`/api/warranties/${id}/certificate`),
  updateStatus: (id, data) => api.put(`/api/warranties/${id}/status`, data),
  searchWarranties: (query) => api.get('/api/warranties/search', { params: { query } }),
  search: (query) => api.get('/api/warranties/search', { params: { query } }),
  getClaims: (params) => api.get('/api/warranties/claims/all', { params }),
  createClaim: (data) => api.post('/api/warranties/claims', data),
  updateClaimStatus: (id, data) => api.put(`/api/warranties/claims/${id}/status`, data),
};
export const warrantiesApi = warrantiesAPI;

// --- Service Tickets ---
export const serviceAPI = {
  getTickets: (params) => api.get('/api/service/tickets', { params }),
  getAll: (params) => api.get('/api/service/tickets', { params }),
  createTicket: (data) => api.post('/api/service/tickets', data),
  create: (data) => api.post('/api/service/tickets', data),
  assignTechnician: (id, data) => api.put(`/api/service/tickets/${id}/assign`, data),
  replaceEquipment: (id, data) => api.post(`/api/service/tickets/${id}/replacement`, data),
  resolveTicket: (id, data) => api.post(`/api/service/tickets/${id}/resolve`, data),
  confirmTicket: (id) => api.post(`/api/service/tickets/${id}/confirm`),
};
export const serviceApi = serviceAPI;

// --- Suppliers ---
export const suppliersAPI = {
  getSuppliers: () => api.get('/api/suppliers'),
  getAll: () => api.get('/api/suppliers'),
  createSupplier: (data) => api.post('/api/suppliers', data),
  create: (data) => api.post('/api/suppliers', data),
};
export const suppliersApi = suppliersAPI;

// --- Finance ---
export const financeAPI = {
  getOverview: () => api.get('/api/finance/overview'),
  getProjectProfitability: () => api.get('/api/finance/profitability'),
  getProfitability: () => api.get('/api/finance/profitability'),
  getExpenses: (params) => api.get('/api/finance/expenses', { params }),
  recordExpense: (data) => api.post('/api/finance/expenses', data),
  getInvoices: () => api.get('/api/finance/invoices'),
};
export const financeApi = financeAPI;

// --- Subsidies & Government Governance ---
export const subsidiesAPI = {
  getSubsidies: (params) => api.get('/api/subsidies', { params }),
  getAll: (params) => api.get('/api/subsidies', { params }),
  getSubsidy: (id) => api.get(`/api/subsidies/${id}`),
  createSubsidy: (data) => api.post('/api/subsidies', data),
  create: (data) => api.post('/api/subsidies', data),
  updateStatus: (id, data) => api.put(`/api/subsidies/${id}/status`, data),
  updateOfficialStatus: (id, data) => api.post(`/api/subsidies/${id}/official-status`, data),
  getSchemes: (params) => api.get('/api/subsidies/schemes', { params }),
  getScheme: (code) => api.get(`/api/subsidies/schemes/${code}`),
  getSchemeDocuments: (code) => api.get(`/api/subsidies/schemes/${code}/documents`),
  getDashboardMetrics: () => api.get('/api/subsidies/dashboard-metrics'),
  checkEligibility: (data) => api.post('/api/subsidies/check-eligibility', data),
  createAssessment: (data) => api.post('/api/subsidies/assessments', data),
  getAssessments: (params) => api.get('/api/subsidies/assessments', { params }),
  calculate: (params) => api.get('/api/subsidies/calculate', { params }),
  uploadSubsidyDoc: (id, formData) => api.post(`/api/subsidies/${id}/documents`, formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  }),
  getDocuments: (id) => api.get(`/api/subsidies/${id}/documents`),
  reviewDocument: (docId, data) => api.patch(`/api/subsidies/documents/${docId}/review`, data),
  getHistory: (id) => api.get(`/api/subsidies/${id}/history`),
  trackApplication: (ref) => api.get(`/api/subsidies/track/${ref}`),
};
export const subsidiesApi = subsidiesAPI;

// --- Dashboard ---
export const dashboardAPI = {
  getSummary: (period = 'month') => api.get('/api/dashboard/summary', { params: { period } }),
};
export const dashboardApi = dashboardAPI;

// --- Reports ---
export const reportsAPI = {
  getDirectorSummary: () => api.get('/api/reports/director-summary'),
  exportProfitability: () => api.get('/api/reports/export/profitability', { responseType: 'blob' }),
  exportInventory: () => api.get('/api/reports/export/inventory', { responseType: 'blob' }),
  exportInstallations: () => api.get('/api/reports/export/installations', { responseType: 'blob' }),
  exportWarranties: () => api.get('/api/reports/export/warranties', { responseType: 'blob' }),
  exportReceivables: () => api.get('/api/reports/export/receivables', { responseType: 'blob' }),
};
export const reportsApi = reportsAPI;
