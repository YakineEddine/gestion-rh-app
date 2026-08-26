import React from 'react';
import { NavLink, useNavigate } from 'react-router-dom';
import { Users, FileText, BookOpen, History, Bell, ChevronDown, LogOut } from 'lucide-react';
import api from '../services/api';
import './Sidebar.css';

export default function Sidebar() {
  const navigate = useNavigate();
  const user = JSON.parse(localStorage.getItem('user') || '{}');

  const handleLogout = async () => {
    try {
      await api.post('/auth/logout');
    } catch {
      // La deconnexion locale doit toujours fonctionner, meme si l'appel echoue.
    }
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    navigate('/login');
  };

  const initials = `${(user.nom || '')[0] || ''}${(user.prenom || '')[0] || ''}`.toUpperCase();

  return (
    <aside className="app-sidebar">
      <div className="sidebar-logo">
        <img src="/logo-csi.png" alt="CSI Digital" className="logo-img" />
        <div className="logo-text-stack">
          <h2>Enterprise RH</h2>
          <span className="logo-subtitle">Gestion des ressources humaines</span>
        </div>
      </div>

      <nav className="sidebar-nav">
        <NavLink 
          to="/employes" 
          className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}
        >
          <Users size={18} className="nav-icon-lucide" />
          <span className="nav-text">Employés</span>
        </NavLink>

        <NavLink 
          to="/articles" 
          className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}
        >
          <BookOpen size={18} className="nav-icon-lucide" />
          <span className="nav-text">Articles</span>
        </NavLink>

        <NavLink 
          to="/contrats" 
          className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}
        >
          <FileText size={18} className="nav-icon-lucide" />
          <span className="nav-text">Contrats</span>
        </NavLink>

        <NavLink
          to="/audit"
          className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}
        >
          <History size={18} className="nav-icon-lucide" />
          <span className="nav-text">Historique</span>
        </NavLink>

        <NavLink
          to="/alertes"
          className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}
        >
          <Bell size={18} className="nav-icon-lucide" />
          <span className="nav-text">Alertes</span>
        </NavLink>
      </nav>

      <div className="sidebar-footer">
        <div className="user-profile-box">
          <div className="user-avatar-circle">{initials || 'RA'}</div>
          <div className="user-info-stack">
            <p className="user-name-text">{user.prenom} {user.nom}</p>
            <p className="user-role-text">{user.role === 'RH' ? 'Responsable RH' : user.role}</p>
          </div>
          <ChevronDown size={14} className="profile-chevron-icon" />
        </div>
        
        <button className="logout-btn-premium" onClick={handleLogout}>
          <LogOut size={15} className="logout-btn-icon" />
          Déconnexion
        </button>
      </div>
    </aside>
  );
}
