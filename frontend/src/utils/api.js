import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || '/api';

const api = axios.create({
    baseURL: API_BASE_URL,
    headers: {
        'Content-Type': 'application/json',
    },
});

// Order APIs
export const orderAPI = {
    create: (data) => api.post('/orders/', data),
    get: (orderId) => api.get(`/orders/${orderId}`),
    updatePayment: (orderId, paid) => api.patch(`/orders/${orderId}/payment-status`, null, { params: { paid } }),
    markInProcess: (orderId) => api.patch(`/orders/${orderId}/process`),
    markShipped: (orderId) => api.patch(`/orders/${orderId}/ship`),
    markOutForDelivery: (orderId) => api.patch(`/orders/${orderId}/out-for-delivery`),
    markDelivered: (orderId) => api.patch(`/orders/${orderId}/deliver`),
};

// Admin APIs
export const adminAPI = {
    getOrders: (skip = 0, limit = 50) => api.get('/admin/orders', { params: { skip, limit } }),
    getMessages: (orderId = null, skip = 0, limit = 100) => api.get('/admin/messages', { params: { order_id: orderId, skip, limit } }),
    syncMessages: () => api.post('/admin/sync-messages'),
    getAlerts: (resolved = null, skip = 0, limit = 50) => api.get('/admin/alerts', { params: { resolved, skip, limit } }),
    resolveAlert: (alertId) => api.patch(`/admin/alerts/${alertId}/resolve`),
    cancelOrder: (orderId) => api.patch(`/admin/orders/${orderId}/cancel`),
};

export default api;
