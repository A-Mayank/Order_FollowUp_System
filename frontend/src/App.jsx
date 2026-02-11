import React from 'react';
import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom';
import CreateOrder from './pages/CreateOrder';
import AdminDashboard from './pages/AdminDashboard';
import './index.css';

function App() {
    return (
        <Router>
            <nav className="nav">
                <ul className="nav-links">
                    <li>
                        <Link to="/">Create Order</Link>
                    </li>
                    <li>
                        <Link to="/admin">Admin Dashboard</Link>
                    </li>
                </ul>
            </nav>

            <Routes>
                <Route path="/" element={<CreateOrder />} />
                <Route path="/admin" element={<AdminDashboard />} />
            </Routes>
        </Router>
    );
}

export default App;
