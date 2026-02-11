import React, { useState, useEffect } from 'react';
import { adminAPI, orderAPI } from '../utils/api';

function AdminDashboard() {
    const [orders, setOrders] = useState([]);
    const [messages, setMessages] = useState([]);
    const [alerts, setAlerts] = useState([]);
    const [loading, setLoading] = useState(true);
    const [activeTab, setActiveTab] = useState('orders');
    const [selectedOrderId, setSelectedOrderId] = useState(null);
    const [syncing, setSyncing] = useState(false);

    useEffect(() => {
        loadData();

        // Refresh data every 30 seconds
        const interval = setInterval(loadData, 30000);
        return () => clearInterval(interval);
    }, []);

    const loadData = async () => {
        try {
            const [ordersRes, messagesRes, alertsRes] = await Promise.all([
                adminAPI.getOrders(),
                adminAPI.getMessages(),
                adminAPI.getAlerts()
            ]);

            setOrders(ordersRes.data);
            setMessages(messagesRes.data);
            setAlerts(alertsRes.data);
            setLoading(false);
        } catch (error) {
            console.error('Failed to load data:', error);
            setLoading(false);
        }
    };

    const handleUpdatePayment = async (orderId, paid) => {
        try {
            await orderAPI.updatePayment(orderId, paid);
            await loadData();
        } catch (error) {
            alert('Failed to update payment status');
        }
    };

    const handleMarkInProcess = async (orderId) => {
        try {
            await orderAPI.markInProcess(orderId);
            await loadData();
        } catch (error) {
            alert('Failed to mark as in process');
        }
    };

    const handleMarkShipped = async (orderId) => {
        try {
            await orderAPI.markShipped(orderId);
            await loadData();
        } catch (error) {
            alert('Failed to mark as shipped');
        }
    };

    const handleMarkOutForDelivery = async (orderId) => {
        try {
            await orderAPI.markOutForDelivery(orderId);
            await loadData();
        } catch (error) {
            alert('Failed to mark as out for delivery');
        }
    };

    const handleMarkDelivered = async (orderId) => {
        try {
            await orderAPI.markDelivered(orderId);
            await loadData();
        } catch (error) {
            alert('Failed to mark as delivered');
        }
    };

    const handleResolveAlert = async (alertId) => {
        try {
            await adminAPI.resolveAlert(alertId);
            await loadData();
        } catch (error) {
            alert('Failed to resolve alert');
        }
    };

    const handleCancelOrder = async (orderId, alertId) => {
        if (!window.confirm('Are you sure you want to cancel this order? The customer will be notified via WhatsApp.')) {
            return;
        }
        try {
            await adminAPI.cancelOrder(orderId);
            await loadData();
            alert('Order cancelled and customer notified!');
        } catch (error) {
            console.error('Cancel error:', error);
            alert('Failed to cancel order: ' + (error.response?.data?.detail || error.message));
        }
    };

    const handleSyncMessages = async () => {
        try {
            setSyncing(true);
            const response = await adminAPI.syncMessages();
            alert(response.data.message);
            await loadData();
        } catch (error) {
            console.error('Sync error:', error);
            alert('Failed to sync messages from Twilio');
        } finally {
            setSyncing(false);
        }
    };

    const getStatusBadge = (status) => {
        const badges = {
            CREATED: 'badge-info',
            PAYMENT_PENDING: 'badge-warning',
            PAID: 'badge-success',
            IN_PROCESS: 'badge-secondary',
            SHIPPED: 'badge-info',
            OUT_FOR_DELIVERY: 'badge-warning',
            DELIVERED: 'badge-success',
            CANCELLED: 'badge-danger'
        };
        return <span className={`badge ${badges[status] || 'badge-info'}`}>{status}</span>;
    };

    const getSentimentBadge = (sentiment) => {
        const badges = {
            positive: 'badge-success',
            neutral: 'badge-info',
            negative: 'badge-danger',
            unknown: 'badge-secondary'
        };
        const icons = {
            positive: '',
            neutral: '',
            negative: '',
            unknown: ''
        };
        return (
            <span className={`badge ${badges[sentiment] || 'badge-secondary'}`}>
                {icons[sentiment]} {sentiment}
            </span>
        );
    };

    if (loading) {
        return <div className="loading">⏳ Loading dashboard data...</div>;
    }

    return (
        <div className="container">
            <h1 style={{ marginBottom: '2rem' }}>📊 Admin Dashboard</h1>

            <div style={{ marginBottom: '2rem', display: 'flex', gap: '1rem' }}>
                <button
                    className={`btn ${activeTab === 'orders' ? 'btn-primary' : 'btn-secondary'}`}
                    onClick={() => setActiveTab('orders')}
                >
                    📦 Orders ({orders.length})
                </button>
                <button
                    className={`btn ${activeTab === 'messages' ? 'btn-primary' : 'btn-secondary'}`}
                    onClick={() => setActiveTab('messages')}
                >
                    💬 Messages ({messages.length})
                </button>
                <button
                    className={`btn ${activeTab === 'alerts' ? 'btn-primary' : 'btn-secondary'}`}
                    onClick={() => setActiveTab('alerts')}
                >
                    🚨 Alerts ({alerts.filter(a => !a.resolved).length})
                </button>
            </div>

            {activeTab === 'orders' && (
                <div className="card">
                    <h2>All Orders</h2>
                    <div className="table-container">
                        <table>
                            <thead>
                                <tr>
                                    <th>Customer</th>
                                    <th>WhatsApp</th>
                                    <th>Product</th>
                                    <th>Amount</th>
                                    <th>Status</th>
                                    <th>Payment</th>
                                    <th>Sentiment</th>
                                    <th>Feedback</th>
                                    <th>Automation</th>
                                    <th>Actions</th>
                                </tr>
                            </thead>
                            <tbody>
                                {orders.length === 0 ? (
                                    <tr>
                                        <td colSpan="9" className="empty-state">No orders yet</td>
                                    </tr>
                                ) : (
                                    orders.map(order => (
                                        <tr key={order.id}>
                                            <td>{order.user_name}</td>
                                            <td><small>{order.whatsapp_number}</small></td>
                                            <td>{order.product_name || '-'}</td>
                                            <td>{order.amount ? `₹ ${Math.round(order.amount)}` : '-'}</td>
                                            <td>{getStatusBadge(order.status)}</td>
                                            <td>{getStatusBadge(order.payment_status)}</td>
                                            <td>{getSentimentBadge(order.sentiment)}</td>
                                            <td>
                                                {order.feedback_rating && (
                                                    <div style={{ fontWeight: 'bold', color: '#f59e0b' }}>
                                                        {'⭐'.repeat(order.feedback_rating)}
                                                    </div>
                                                )}
                                                {order.feedback_text && (
                                                    <div style={{ fontSize: '0.75rem', maxWidth: '150px', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }} title={order.feedback_text}>
                                                        {order.feedback_text}
                                                    </div>
                                                )}
                                                {!order.feedback_rating && !order.feedback_text && '-'}
                                            </td>
                                            <td>{order.automation_enabled ? '✅' : '❌'}</td>
                                            <td>
                                                <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
                                                    {order.payment_status === 'PENDING' && (
                                                        <button
                                                            className="btn btn-success"
                                                            style={{ fontSize: '0.75rem', padding: '0.25rem 0.5rem' }}
                                                            onClick={() => handleUpdatePayment(order.id, true)}
                                                        >
                                                            Mark Paid
                                                        </button>
                                                    )}
                                                    {(order.status === 'PAID' || order.status === 'IN_PROCESS') && (
                                                        <button
                                                            className="btn btn-primary"
                                                            style={{ fontSize: '0.75rem', padding: '0.25rem 0.5rem' }}
                                                            onClick={() => handleMarkShipped(order.id)}
                                                        >
                                                            Ship
                                                        </button>
                                                    )}
                                                    {order.status === 'SHIPPED' && (
                                                        <button
                                                            className="btn btn-primary"
                                                            style={{ fontSize: '0.75rem', padding: '0.25rem 0.5rem', backgroundColor: '#f59e0b', borderColor: '#f59e0b' }}
                                                            onClick={() => handleMarkOutForDelivery(order.id)}
                                                        >
                                                            Out for Delivery
                                                        </button>
                                                    )}
                                                    {order.status === 'OUT_FOR_DELIVERY' && (
                                                        <button
                                                            className="btn btn-success"
                                                            style={{ fontSize: '0.75rem', padding: '0.25rem 0.5rem' }}
                                                            onClick={() => handleMarkDelivered(order.id)}
                                                        >
                                                            Deliver
                                                        </button>
                                                    )}
                                                </div>
                                            </td>
                                        </tr>
                                    ))
                                )}
                            </tbody>
                        </table>
                    </div>
                </div>
            )}

            {activeTab === 'messages' && (
                <div className="card">
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
                        <h2 style={{ margin: 0 }}>Message Logs</h2>
                        <button
                            className="btn btn-primary"
                            onClick={handleSyncMessages}
                            disabled={syncing}
                        >
                            {syncing ? 'Syncing...' : 'Sync from Twilio'}
                        </button>
                    </div>
                    <div className="table-container">
                        <table>
                            <thead>
                                <tr>
                                    <th>Time</th>
                                    <th>Type</th>
                                    <th>Direction</th>
                                    <th>Message</th>
                                    <th>Sentiment</th>
                                </tr>
                            </thead>
                            <tbody>
                                {messages.length === 0 ? (
                                    <tr>
                                        <td colSpan="5" className="empty-state">No messages yet</td>
                                    </tr>
                                ) : (
                                    messages.map(msg => (
                                        <tr key={msg.id}>
                                            <td><small>{new Date(msg.sent_at).toLocaleString()}</small></td>
                                            <td><small>{msg.message_type}</small></td>
                                            <td>{msg.is_incoming ? '📥 In' : '📤 Out'}</td>
                                            <td style={{ maxWidth: '400px' }}>{msg.message_content}</td>
                                            <td>{msg.sentiment ? getSentimentBadge(msg.sentiment) : '-'}</td>
                                        </tr>
                                    ))
                                )}
                            </tbody>
                        </table>
                    </div>
                </div>
            )}

            {activeTab === 'alerts' && (
                <div className="card">
                    <h2>System Alerts</h2>
                    {alerts.length === 0 ? (
                        <div className="empty-state">No alerts</div>
                    ) : (
                        <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                            {alerts.map(alert => (
                                <div
                                    key={alert.id}
                                    style={{
                                        padding: '1rem',
                                        border: `2px solid ${alert.resolved ? '#10b981' : '#ef4444'}`,
                                        borderRadius: '8px',
                                        background: alert.resolved ? '#d1fae5' : '#fee2e2'
                                    }}
                                >
                                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start' }}>
                                        <div>
                                            <strong>{alert.reason}</strong>
                                            <p style={{ margin: '0.5rem 0', color: 'var(--text-light)' }}>{alert.description}</p>
                                            <small>Created: {new Date(alert.created_at).toLocaleString()}</small>
                                        </div>
                                        <div style={{ display: 'flex', gap: '0.5rem', flexDirection: 'column', alignItems: 'flex-end' }}>
                                            {!alert.resolved && alert.reason === 'CANCELLATION_REQUEST' && (
                                                <button
                                                    className="btn btn-danger"
                                                    style={{ whiteSpace: 'nowrap' }}
                                                    onClick={() => handleCancelOrder(alert.order_id, alert.id)}
                                                >
                                                    Cancel Order
                                                </button>
                                            )}
                                            {!alert.resolved && (
                                                <button
                                                    className="btn btn-success"
                                                    onClick={() => handleResolveAlert(alert.id)}
                                                >
                                                    Resolve
                                                </button>
                                            )}
                                            {alert.resolved && (
                                                <span className="badge badge-success">Resolved</span>
                                            )}
                                        </div>
                                    </div>
                                </div>
                            ))}
                        </div>
                    )}
                </div>
            )}
        </div>
    );
}

export default AdminDashboard;
