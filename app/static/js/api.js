/**
 * Bariq Al-Yusr API Helper
 * Handles all API calls with authentication
 */

const API_BASE = '/api/v1';

// Token management
const TokenManager = {
  getAccessToken: () => localStorage.getItem('access_token'),
  getRefreshToken: () => localStorage.getItem('refresh_token'),
  getUser: () => {
    const user = localStorage.getItem('user');
    return user ? JSON.parse(user) : null;
  },
  getUserType: () => localStorage.getItem('user_type'),
  
  setTokens: (accessToken, refreshToken) => {
    localStorage.setItem('access_token', accessToken);
    localStorage.setItem('refresh_token', refreshToken);
  },
  
  setUser: (user, userType) => {
    localStorage.setItem('user', JSON.stringify(user));
    localStorage.setItem('user_type', userType);
  },
  
  clear: () => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    localStorage.removeItem('user');
    localStorage.removeItem('user_type');
  },
  
  isAuthenticated: () => {
    return !!TokenManager.getAccessToken() && !!TokenManager.getUser();
  }
};

// API Request Helper
async function apiRequest(endpoint, options = {}) {
  const url = `${API_BASE}${endpoint}`;
  
  const defaultHeaders = {
    'Content-Type': 'application/json',
  };
  
  const token = TokenManager.getAccessToken();
  if (token) {
    defaultHeaders['Authorization'] = `Bearer ${token}`;
  }
  
  const config = {
    ...options,
    headers: {
      ...defaultHeaders,
      ...options.headers,
    },
  };
  
  try {
    const response = await fetch(url, config);
    const data = await response.json();
    
    // Handle 401 - try to refresh token
    if (response.status === 401 && !options._retry) {
      const refreshed = await refreshToken();
      if (refreshed) {
        options._retry = true;
        return apiRequest(endpoint, options);
      } else {
        // Refresh failed, logout
        TokenManager.clear();
        window.location.href = '/login';
        return null;
      }
    }
    
    return { success: response.ok, status: response.status, data };
  } catch (error) {
    console.error('API Error:', error);
    return { success: false, error: error.message };
  }
}

// Refresh token
async function refreshToken() {
  const refreshToken = TokenManager.getRefreshToken();
  if (!refreshToken) return false;
  
  try {
    const response = await fetch(`${API_BASE}/auth/refresh`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${refreshToken}`,
        'Content-Type': 'application/json',
      },
    });
    
    if (response.ok) {
      const data = await response.json();
      if (data.success) {
        localStorage.setItem('access_token', data.data.access_token);
        return true;
      }
    }
  } catch (error) {
    console.error('Refresh token error:', error);
  }
  
  return false;
}

// API Methods
const API = {
  // Auth
  auth: {
    customerLogin: (username, password) => 
      apiRequest('/auth/customer/login', {
        method: 'POST',
        body: JSON.stringify({ username, password }),
      }),
    
    merchantLogin: (email, password) =>
      apiRequest('/auth/merchant/login', {
        method: 'POST',
        body: JSON.stringify({ email, password }),
      }),
    
    adminLogin: (email, password) =>
      apiRequest('/auth/admin/login', {
        method: 'POST',
        body: JSON.stringify({ email, password }),
      }),
    
    logout: () => apiRequest('/auth/logout', { method: 'POST' }),
  },
  
  // Customer
  customer: {
    getProfile: () => apiRequest('/customers/me'),
    updateProfile: (data) => 
      apiRequest('/customers/me', {
        method: 'PUT',
        body: JSON.stringify(data),
      }),
    
    getCredit: () => apiRequest('/customers/me/credit'),
    getDebt: () => apiRequest('/customers/me/debt'),
    
    getTransactions: (params = {}) => {
      const query = new URLSearchParams(params).toString();
      return apiRequest(`/customers/me/transactions${query ? '?' + query : ''}`);
    },
    
    confirmTransaction: (id) =>
      apiRequest(`/customers/me/transactions/${id}/confirm`, { method: 'POST' }),

    rejectTransaction: (id, reason) =>
      apiRequest(`/customers/me/transactions/${id}/reject`, {
        method: 'POST',
        body: JSON.stringify({ reason }),
      }),

    changePassword: (currentPassword, newPassword) =>
      apiRequest('/customers/me/password', {
        method: 'PUT',
        body: JSON.stringify({
          current_password: currentPassword,
          new_password: newPassword,
        }),
      }),

    getPayments: (params = {}) => {
      const query = new URLSearchParams(params).toString();
      return apiRequest(`/customers/me/payments${query ? '?' + query : ''}`);
    },
    
    makePayment: (transactionId, amount, method) =>
      apiRequest('/customers/me/payments', {
        method: 'POST',
        body: JSON.stringify({ transaction_id: transactionId, amount, payment_method: method }),
      }),
  },
  
  // Merchant
  merchant: {
    getProfile: () => apiRequest('/merchants/me'),
    getDashboard: () => apiRequest('/merchants/me/reports/summary'),
    
    lookupCustomer: (bariqId) => apiRequest(`/merchants/customers/lookup/${bariqId}`),
    
    getTransactions: (params = {}) => {
      const query = new URLSearchParams(params).toString();
      return apiRequest(`/merchants/me/transactions${query ? '?' + query : ''}`);
    },
    
    createTransaction: (data) =>
      apiRequest('/merchants/me/transactions', {
        method: 'POST',
        body: JSON.stringify(data),
      }),
    
    getBranches: () => apiRequest('/merchants/me/branches'),
    getStaff: () => apiRequest('/merchants/me/staff'),
    
    addStaff: (data) =>
      apiRequest('/merchants/me/staff', {
        method: 'POST',
        body: JSON.stringify(data),
      }),
    
    getSettlements: (params = {}) => {
      const query = new URLSearchParams(params).toString();
      return apiRequest(`/merchants/me/settlements${query ? '?' + query : ''}`);
    },

    getSettlementDetails: (id) => apiRequest(`/merchants/me/settlements/${id}`),
  },
};

// Helper functions
function formatNumber(num) {
  return num ? num.toLocaleString('ar-SA') : '0';
}

function formatDate(dateStr) {
  if (!dateStr) return '';
  const date = new Date(dateStr);
  return date.toLocaleDateString('ar-SA');
}

function formatDateTime(dateStr) {
  if (!dateStr) return '';
  const date = new Date(dateStr);
  return date.toLocaleString('ar-SA');
}

// Status translations
const statusLabels = {
  paid: 'مدفوعة',
  pending: 'بانتظار التأكيد',
  confirmed: 'مؤكدة',
  overdue: 'متأخرة',
  cancelled: 'ملغية',
  active: 'نشط',
  inactive: 'غير نشط',
  suspended: 'موقوف',
};

function getStatusLabel(status) {
  return statusLabels[status] || status;
}

function getStatusBadgeClass(status) {
  const classes = {
    paid: 'badge-success',
    confirmed: 'badge-info',
    pending: 'badge-warning',
    overdue: 'badge-danger',
    cancelled: 'badge-gray',
    active: 'badge-success',
    inactive: 'badge-gray',
    suspended: 'badge-danger',
  };
  return classes[status] || 'badge-gray';
}

// Show loading spinner
function showLoading(container) {
  container.innerHTML = `
    <div class="loading-container">
      <div class="spinner"></div>
    </div>
  `;
}

// Show error message
function showError(container, message) {
  container.innerHTML = `
    <div class="alert alert-error">
      ${message}
    </div>
  `;
}

// Check auth and redirect if needed
function requireAuth(allowedTypes = []) {
  if (!TokenManager.isAuthenticated()) {
    window.location.href = '/login';
    return false;
  }
  
  if (allowedTypes.length > 0) {
    const userType = TokenManager.getUserType();
    if (!allowedTypes.includes(userType)) {
      // Redirect to appropriate dashboard
      const dashboards = {
        customer: '/customer',
        merchant: '/merchant',
        admin: '/admin',
      };
      window.location.href = dashboards[userType] || '/login';
      return false;
    }
  }
  
  return true;
}

// Logout function
function logout() {
  TokenManager.clear();
  window.location.href = '/login';
}
