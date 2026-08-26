import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import Login from './pages/Login';
import EmployesList from './pages/EmployesList';
import EmployeForm from './pages/EmployeForm';
import EmployeeDashboard from './pages/EmployeeDashboard';
import MonProfil from './pages/MonProfil';
import MesContrats from './pages/MesContrats';
import ResetPassword from './pages/ResetPassword';
import ArticlesList from './pages/ArticlesList';
import ContratsList from './pages/ContratsList';
import ContratForm from './pages/ContratForm';
import AuditLogs from './pages/AuditLogs';
import Alertes from './pages/Alertes';
import Sidebar from './components/Sidebar';
import Header from './components/Header';

// Guard pour les routes RH uniquement
const RHRoute = ({ children }) => {
  const token = localStorage.getItem('token');
  const user = JSON.parse(localStorage.getItem('user') || '{}');
  if (!token) return <Navigate to="/login" replace />;
  if (user.role !== 'RH') return <Navigate to="/mon-espace" replace />;
  return children;
};

// Guard pour les routes reservees au personnel RH/ADMIN (ex: audit)
const StaffRoute = ({ children }) => {
  const token = localStorage.getItem('token');
  const user = JSON.parse(localStorage.getItem('user') || '{}');
  if (!token) return <Navigate to="/login" replace />;
  if (user.role !== 'RH' && user.role !== 'ADMIN') return <Navigate to="/mon-espace" replace />;
  return children;
};

// Guard pour les routes employe (tous les utilisateurs connectes)
const PrivateRoute = ({ children }) => {
  const token = localStorage.getItem('token');
  if (!token) return <Navigate to="/login" replace />;
  return children;
};

// Redirection intelligente apres login
const SmartRedirect = () => {
  const token = localStorage.getItem('token');
  const user = JSON.parse(localStorage.getItem('user') || '{}');
  if (!token) return <Navigate to="/login" replace />;
  if (user.role === 'RH') return <Navigate to="/employes" replace />;
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
        <Route path="/mon-espace" element={<PrivateRoute><EmployeeDashboard /></PrivateRoute>} />
        <Route path="/mon-espace/profil" element={<PrivateRoute><MonProfil /></PrivateRoute>} />
        <Route path="/mon-espace/contrats" element={<PrivateRoute><MesContrats /></PrivateRoute>} />

        {/* Redirections */}
        <Route path="/" element={<SmartRedirect />} />
        <Route path="*" element={<SmartRedirect />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
