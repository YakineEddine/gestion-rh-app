import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import Login from './pages/Login';
import EmployesList from './pages/EmployesList';
import EmployeForm from './pages/EmployeForm';
import EmployeeDashboard from './pages/EmployeeDashboard';
import MonProfil from './pages/MonProfil';
import MesContrats from './pages/MesContrats';
import EmployeeAlertes from './pages/EmployeeAlertes';
import ResetPassword from './pages/ResetPassword';
import ArticlesList from './pages/ArticlesList';
import ContratsList from './pages/ContratsList';
import ContratForm from './pages/ContratForm';
import AuditLogs from './pages/AuditLogs';
import Alertes from './pages/Alertes';
import Sidebar from './components/Sidebar';
import Header from './components/Header';

import api from './services/api';

// Guard pour les routes RH & ADMIN
const RHRoute = ({ children }) => {
  const token = localStorage.getItem('token');
  const user = JSON.parse(localStorage.getItem('user') || '{}');
  if (!token) return <Navigate to="/login" replace />;
  if (user.role !== 'RH' && user.role !== 'ADMIN') return <Navigate to="/mon-espace" replace />;
  return children;
};

// Guard pour les routes reservees au personnel RH/ADMIN (ex: audit, alertes RH)
const StaffRoute = ({ children }) => {
  const token = localStorage.getItem('token');
  const user = JSON.parse(localStorage.getItem('user') || '{}');
  if (!token) return <Navigate to="/login" replace />;
  if (user.role !== 'RH' && user.role !== 'ADMIN') return <Navigate to="/mon-espace" replace />;
  return children;
};

// Guard pour les routes Espace Collaborateur (EMPLOYE uniquement + gestion du direct_token depuis email)
const EmployeRoute = ({ children }) => {
  const [checking, setChecking] = React.useState(true);
  const [authError, setAuthError] = React.useState('');

  React.useEffect(() => {
    const checkDirectAccess = async () => {
      const urlParams = new URLSearchParams(window.location.search);
      const directToken = urlParams.get('direct_token');

      if (directToken) {
        try {
          const res = await api.post('/auth/direct-access', { token: directToken });
          localStorage.setItem('token', res.data.access_token);
          localStorage.setItem('refresh_token', res.data.refresh_token);
          localStorage.setItem('user', JSON.stringify(res.data.user));

          // Retirer le paramètre direct_token de l'URL sans recharger la page
          const newUrl = window.location.pathname;
          window.history.replaceState({}, document.title, newUrl);
        } catch (err) {
          console.error("Direct access token error:", err);
          setAuthError(err.response?.data?.detail || "Lien d'accès expiré ou invalide.");
        }
      }
      setChecking(false);
    };

    checkDirectAccess();
  }, []);

  if (checking) {
    return (
      <div style={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        minHeight: '100vh',
        background: '#f8fafc',
        fontFamily: 'inherit',
        gap: '12px',
        color: '#475569'
      }}>
        <div style={{
          width: '36px',
          height: '36px',
          border: '3px solid #e2e8f0',
          borderTopColor: '#4f46e5',
          borderRadius: '50%',
          animation: 'spin 0.8s linear infinite'
        }} />
        <p style={{ fontSize: '14px', fontWeight: '500' }}>Accès à votre espace collaborateur...</p>
        <style>{`@keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }`}</style>
      </div>
    );
  }

  const token = localStorage.getItem('token');
  const user = JSON.parse(localStorage.getItem('user') || '{}');

  if (!token || authError) {
    return <Navigate to="/login" replace state={{ message: authError }} />;
  }

  // Si l'utilisateur connecté est RH ou ADMIN, il n'a rien à faire dans l'espace collaborateur
  if (user.role === 'RH' || user.role === 'ADMIN') {
    return <Navigate to="/contrats" replace />;
  }

  return children;
};

// Redirection intelligente apres login ou a la racine
const SmartRedirect = () => {
  const token = localStorage.getItem('token');
  const user = JSON.parse(localStorage.getItem('user') || '{}');
  if (!token) return <Navigate to="/login" replace />;
  if (user.role === 'RH' || user.role === 'ADMIN') return <Navigate to="/employes" replace />;
  return <Navigate to="/mon-espace" replace />;
};



function App() {
  return (
    <BrowserRouter>
      <Routes>
        {/* Routes publiques */}
        <Route path="/login" element={<Login />} />
        <Route path="/reset-password" element={<ResetPassword />} />

        {/* ===== ESPACE RH ===== */}
        <Route path="/employes" element={<RHRoute><EmployesList /></RHRoute>} />
        <Route path="/employes/nouveau" element={<RHRoute><EmployeForm /></RHRoute>} />
        <Route path="/employes/modifier/:id" element={<RHRoute><EmployeForm /></RHRoute>} />
        <Route path="/articles" element={<RHRoute><ArticlesList /></RHRoute>} />
        <Route path="/contrats" element={<RHRoute><ContratsList /></RHRoute>} />
        <Route path="/contrats/nouveau" element={<RHRoute><ContratForm /></RHRoute>} />
        <Route path="/contrats/modifier/:id" element={<RHRoute><ContratForm /></RHRoute>} />
        <Route path="/audit" element={<StaffRoute><AuditLogs /></StaffRoute>} />
        <Route path="/alertes" element={<StaffRoute><Alertes /></StaffRoute>} />

        {/* ===== ESPACE EMPLOYE ===== */}
        <Route path="/mon-espace" element={<EmployeRoute><EmployeeDashboard /></EmployeRoute>} />
        <Route path="/mon-espace/profil" element={<EmployeRoute><MonProfil /></EmployeRoute>} />
        <Route path="/mon-espace/contrats" element={<EmployeRoute><MesContrats /></EmployeRoute>} />
        <Route path="/mon-espace/alertes" element={<EmployeRoute><EmployeeAlertes /></EmployeRoute>} />

        {/* Redirections */}
        <Route path="/" element={<SmartRedirect />} />
        <Route path="*" element={<SmartRedirect />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;

