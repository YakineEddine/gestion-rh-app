import React, { useState, useEffect, useRef, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { Calendar, Bell, CheckCheck, ArrowRight, AlertTriangle, AlertCircle, Info } from 'lucide-react';
import api from '../services/api';
import './Header.css';

const PRIORITE_ICON = {
  CRITICAL: AlertTriangle,
  WARNING: AlertCircle,
  INFO: Info,
};

function formatRelative(iso) {
  const d = new Date(iso);
  const now = new Date();
  const diffMs = now - d;
  const diffMin = Math.floor(diffMs / 60000);
  if (diffMin < 1) return "à l'instant";
  if (diffMin < 60) return `il y a ${diffMin} min`;
  const diffH = Math.floor(diffMin / 60);
  if (diffH < 24) return `il y a ${diffH} h`;
  const diffJ = Math.floor(diffH / 24);
  return `il y a ${diffJ} j`;
}

export default function Header({ title, subtitle }) {
  const navigate = useNavigate();
  const dropdownRef = useRef(null);

  const [unreadCount, setUnreadCount] = useState(0);
  const [notifications, setNotifications] = useState([]);
  const [showDropdown, setShowDropdown] = useState(false);
  const [loadingNotifs, setLoadingNotifs] = useState(false);

  const dateStr = new Date().toLocaleDateString('fr-FR', {
    weekday: 'long',
    year: 'numeric',
    month: 'long',
    day: 'numeric'
  });
  const formattedDate = dateStr.charAt(0).toUpperCase() + dateStr.slice(1);

  const fetchUnreadCount = useCallback(async () => {
    try {
      const res = await api.get('/notifications/unread-count');
      setUnreadCount(res.data.unread_count);
    } catch {
      // Utilisateur sans droit ou route indisponible : on ignore silencieusement.
    }
  }, []);

  useEffect(() => {
    fetchUnreadCount();
    const interval = setInterval(fetchUnreadCount, 60000);
    return () => clearInterval(interval);
  }, [fetchUnreadCount]);

  useEffect(() => {
    const handleClickOutside = (e) => {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target)) {
        setShowDropdown(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleToggleDropdown = async () => {
    const next = !showDropdown;
    setShowDropdown(next);
    if (next) {
      setLoadingNotifs(true);
      try {
        const res = await api.get('/notifications/', { params: { page: 1, page_size: 5 } });
        setNotifications(res.data.items);
      } catch {
        setNotifications([]);
      } finally {
        setLoadingNotifs(false);
      }
    }
  };

  const handleNotifClick = async (notif) => {
    try {
      await api.post(`/notifications/${notif.id}/read`);
      setUnreadCount(c => Math.max(0, c - (notif.est_lue ? 0 : 1)));
      setNotifications(prev => prev.map(n => n.id === notif.id ? { ...n, est_lue: true } : n));
    } catch {
      // Non bloquant : la navigation doit fonctionner meme si le marquage echoue.
    }
    setShowDropdown(false);
    const user = JSON.parse(localStorage.getItem('user') || '{}');
    const isEmploye = user.role === 'EMPLOYE';

    if (notif.entite === 'CONTRAT') {
      navigate(isEmploye ? '/mon-espace/contrats' : `/contrats/modifier/${notif.entite_id}`);
    } else if (notif.entite === 'EMPLOYE') {
      navigate(isEmploye ? '/mon-espace/profil' : `/employes/modifier/${notif.entite_id}`);
    } else {
      navigate(isEmploye ? '/mon-espace/alertes' : '/alertes');
    }
  };

  const handleMarkAllRead = async (e) => {
    e.stopPropagation();
    try {
      await api.post('/notifications/mark-all-read');
      setUnreadCount(0);
      setNotifications(prev => prev.map(n => ({ ...n, est_lue: true })));
    } catch {
      // silencieux
    }
  };

  return (
    <header className="app-header">
      <div className="header-titles">
        <h1>{title}</h1>
        {subtitle && <p className="header-subtitle">{subtitle}</p>}
      </div>
      <div className="header-meta">
        <span className="current-date">
          <Calendar size={15} className="header-calendar-icon" />
          {formattedDate}
        </span>

        <div className="header-notif-wrapper" ref={dropdownRef}>
          <button
            className="header-bell-btn"
            onClick={handleToggleDropdown}
            title="Notifications"
          >
            <Bell size={19} />
            {unreadCount > 0 && (
              <span className="header-bell-badge">{unreadCount > 9 ? '9+' : unreadCount}</span>
            )}
          </button>

          {showDropdown && (
            <div className="header-notif-dropdown">
              <div className="header-notif-dropdown-title">
                <span>Notifications</span>
                {unreadCount > 0 && (
                  <button className="header-notif-markall" onClick={handleMarkAllRead}>
                    <CheckCheck size={13} /> Tout marquer lu
                  </button>
                )}
              </div>

              <div className="header-notif-list">
                {loadingNotifs ? (
                  <div className="header-notif-empty">Chargement...</div>
                ) : notifications.length === 0 ? (
                  <div className="header-notif-empty">Aucune notification.</div>
                ) : (
                  notifications.map(notif => {
                    const Icon = PRIORITE_ICON[notif.priorite] || Info;
                    return (
                      <div
                        key={notif.id}
                        className={`header-notif-item priorite-${notif.priorite?.toLowerCase()} ${notif.est_lue ? 'lue' : 'non-lue'}`}
                        onClick={() => handleNotifClick(notif)}
                      >
                        <Icon size={16} className="header-notif-icon" />
                        <div className="header-notif-content">
                          <span className="header-notif-titre">{notif.titre}</span>
                          <span className="header-notif-message">{notif.message}</span>
                          <span className="header-notif-date">{formatRelative(notif.date_creation)}</span>
                        </div>
                        {!notif.est_lue && <span className="header-notif-dot" />}
                      </div>
                    );
                  })
                )}
              </div>

              <button
                className="header-notif-viewall"
                onClick={() => {
                  setShowDropdown(false);
                  const user = JSON.parse(localStorage.getItem('user') || '{}');
                  navigate(user.role === 'EMPLOYE' ? '/mon-espace/alertes' : '/alertes');
                }}
              >
                Voir toutes les alertes
                <ArrowRight size={14} />
              </button>
            </div>
          )}
        </div>
      </div>
    </header>
  );
}
