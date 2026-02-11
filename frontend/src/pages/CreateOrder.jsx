import React, { useState, useEffect } from 'react';
import { orderAPI } from '../utils/api';
import riverFish from '../components/riverwater_fishes.json';
import seaFish from '../components/seawater_fishes.json';

function CreateOrder() {
    const [products, setProducts] = useState([]);
    const [cart, setCart] = useState([]);
    const [formData, setFormData] = useState({
        name: '',
        whatsapp_number: ''
    });
    const [loading, setLoading] = useState(false);
    const [success, setSuccess] = useState(null);
    const [error, setError] = useState(null);

    useEffect(() => {
        // Merge and process products
        const allProducts = [...riverFish, ...seaFish].map(p => ({
            ...p,
            priceNum: Math.round(parseFloat(p.price.replace(/[^0-9.]/g, ''))) || 0
        }));
        setProducts(allProducts);
    }, []);

    const addToCart = (product) => {
        setCart([...cart, product]);
    };

    const removeFromCart = (index) => {
        const newCart = [...cart];
        newCart.splice(index, 1);
        setCart(newCart);
    };

    const calculateTotal = () => {
        return cart.reduce((sum, item) => sum + item.priceNum, 0);
    };

    const handleChange = (e) => {
        setFormData({
            ...formData,
            [e.target.name]: e.target.value
        });
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        if (cart.length === 0) {
            setError("Please add at least one product to the cart.");
            return;
        }

        setLoading(true);
        setError(null);
        setSuccess(null);

        try {
            // Aggregate product names and calculate total amount
            const productNames = cart.map(p => p.name).join(", ");
            const totalAmount = calculateTotal();

            const payload = {
                name: formData.name,
                whatsapp_number: formData.whatsapp_number,
                product_name: productNames,
                amount: totalAmount
            };

            const response = await orderAPI.create(payload);

            setSuccess({
                orderId: response.data.id,
                message: `Order placed successfully for ${cart.length} items! WhatsApp confirmation sent.`
            });

            // Reset form and cart
            setFormData({ name: '', whatsapp_number: '' });
            setCart([]);

        } catch (err) {
            console.error(err);
            setError(err.response?.data?.detail || 'Failed to create order. Please check your connection.');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="container" style={{ maxWidth: '1200px' }}>
            <h1 style={{ textAlign: 'center', marginBottom: '2rem' }}>Fresh Fish Market</h1>

            {success && (
                <div className="alert alert-success" style={{ marginBottom: '2rem' }}>
                    <h3>{success.message}</h3>
                    <p>Order ID: {success.orderId}</p>
                </div>
            )}

            {error && (
                <div className="alert alert-error" style={{ marginBottom: '2rem' }}>
                    {error}
                </div>
            )}

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 350px', gap: '2rem' }}>
                {/* Product Catalog */}
                <div className="product-list">
                    <h2>Our Catch of the Day</h2>
                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(250px, 1fr))', gap: '1.5rem' }}>
                        {products.map((product) => (
                            <div key={product.id} className="card" style={{ padding: '0', overflow: 'hidden', display: 'flex', flexDirection: 'column' }}>
                                <img
                                    src={product.image}
                                    alt={product.name}
                                    style={{ width: '100%', height: '200px', objectFit: 'cover' }}
                                />
                                <div style={{ padding: '1rem', flex: 1, display: 'flex', flexDirection: 'column' }}>
                                    <h3 style={{ fontSize: '1.1rem', marginBottom: '0.5rem' }}>{product.name}</h3>
                                    <p style={{ color: '#666', fontSize: '0.9rem' }}>{product.category.replace('_', ' ')}</p>
                                    <div style={{ marginTop: 'auto', paddingTop: '1rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                                        <span style={{ fontWeight: 'bold', fontSize: '1.2rem', color: '#2c3e50' }}>{product.price}</span>
                                        <button
                                            onClick={() => addToCart(product)}
                                            className="btn btn-secondary"
                                            style={{ padding: '0.5rem 1rem', fontSize: '0.9rem' }}
                                        >
                                            Add to Cart
                                        </button>
                                    </div>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>

                {/* Cart & Checkout Sidebar */}
                <div className="cart-sidebar">
                    <div className="card" style={{ position: 'sticky', top: '2rem' }}>
                        <h2>Your Cart ({cart.length})</h2>

                        {cart.length === 0 ? (
                            <p style={{ color: '#888', fontStyle: 'italic', margin: '2rem 0' }}>Your cart is empty. Add some fish!</p>
                        ) : (
                            <div style={{ maxHeight: '300px', overflowY: 'auto', margin: '1rem 0' }}>
                                {cart.map((item, index) => (
                                    <div key={index} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.8rem', paddingBottom: '0.8rem', borderBottom: '1px solid #eee' }}>
                                        <div>
                                            <div style={{ fontWeight: '500' }}>{item.name}</div>
                                            <div style={{ fontSize: '0.85rem', color: '#666' }}>₹ {item.priceNum}</div>
                                        </div>
                                        <button
                                            onClick={() => removeFromCart(index)}
                                            style={{ background: 'none', border: 'none', color: '#e74c3c', cursor: 'pointer', fontSize: '1.2rem' }}
                                            title="Remove"
                                        >
                                            &times;
                                        </button>
                                    </div>
                                ))}
                            </div>
                        )}

                        <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '1.2rem', fontWeight: 'bold', margin: '1.5rem 0', paddingTop: '1rem', borderTop: '2px solid #eee' }}>
                            <span>Total:</span>
                            <span>₹ {Math.round(calculateTotal())}</span>
                        </div>

                        <form onSubmit={handleSubmit}>
                            <div className="form-group">
                                <label>Your Name</label>
                                <input
                                    type="text"
                                    name="name"
                                    value={formData.name}
                                    onChange={handleChange}
                                    required
                                    placeholder="Enter full name"
                                    style={{ width: '100%' }}
                                />
                            </div>
                            <div className="form-group">
                                <label>WhatsApp Number</label>
                                <input
                                    type="tel"
                                    name="whatsapp_number"
                                    value={formData.whatsapp_number}
                                    onChange={handleChange}
                                    required
                                    placeholder="+91..."
                                    style={{ width: '100%' }}
                                />
                            </div>
                            <button
                                type="submit"
                                className="btn btn-primary"
                                style={{ width: '100%' }}
                                disabled={loading || cart.length === 0}
                            >
                                {loading ? 'Processing...' : 'Place Order'}
                            </button>
                        </form>
                    </div>
                </div>
            </div>
        </div>
    );
}

export default CreateOrder;
