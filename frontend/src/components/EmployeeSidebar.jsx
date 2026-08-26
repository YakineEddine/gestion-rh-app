import React from 'react';
import { NavLink, useNavigate } from 'react-router-dom';
import { Home, User, FileText, ChevronDown, LogOut } from 'lucide-react';
import api from '../services/api';
import './Sidebar.css';

export default function EmployeeSidebar() {
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
          <h2>Mon Espace</h2>
          <span className="logo-subtitle">Espace Collaborateur</span>
        </div>
      </div>

      <nav className="sidebar-nav">
        <NavLink
          to="/mon-espace"
          end
          className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}
        >
          <Home size={18} className="nav-icon-lucide" />
          <span className="nav-text">Tableau de bord</span>
        </NavLink>

        <NavLink
          to="/mon-espace/profil"
          className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}
        >
          <User size={18} className="nav-icon-lucide" />
          <span className="nav-text">Mon Profil</span>
        </NavLink>

        <NavLink
          to="/mon-espace/contrats"
          className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}
        >
          <FileText size={18} className="nav-icon-lucide" />
          <span className="nav-text">Mes Contrats</span>
        </NavLink>
      </nav>

      <div className="sidebar-footer">
        <div className="user-profile-box">
          <div className="user-avatar-circle">{initials || 'EC'}</div>
          <div className="user-info-stack">
            <p className="user-name-text">{user.prenom} {user.nom}</p>
            <p className="user-role-text">{user.poste || 'Employé'}</p>
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
