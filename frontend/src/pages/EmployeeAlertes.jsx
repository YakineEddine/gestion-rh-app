import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Bell, RotateCcw, ChevronLeft, ChevronRight, CheckCheck, Check,
  AlertTriangle, AlertCircle, Info, ArrowRight, FileText
} from 'lucide-react';
import EmployeeSidebar from '../components/EmployeeSidebar';
import Header from '../components/Header';
import api from '../services/api';
import './Alertes.css';

const TYPE_LABELS = {
  CONTRACT_EXPIRING: 'Contrat bientôt expiré',
  CONTRACT_EXPIRED: 'Contrat expiré',
  PROBATION_ENDING: "Fin de période d'essai",
  DRAFT_CONTRACT: 'Contrat en brouillon',
  OTHER_RH_ALERT: 'Alerte RH',
};

const PRIORITE_CONFIG = {
  CRITICAL: { label: 'Critique', icon: AlertTriangle, cls: 'critical' },
  WARNING:  { label: 'Avertissement', icon: AlertCircle, cls: 'warning' },
  INFO:     { label: 'Information', icon: Info, cls: 'info' },
};

function formatDateHeure(iso) {
  if (!iso) return '—';
  const d = new Date(iso);
  const date = d.toLocaleDateString('fr-FR', { day: '2-digit', month: '2-digit', year: 'numeric' });
  const heure = d.toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' });
  return `${date} à ${heure}`;
}

function PrioriteBadge({ priorite }) {
  const config = PRIORITE_CONFIG[priorite] || { label: priorite, icon: Info, cls: 'info' };
  const Icon = config.icon;
  return (
    <span className={`alerte-priorite-badge alerte-${config.cls}`}>
      <Icon size={12} />
      {config.label}
    </span>
  );
}

export default function EmployeeAlertes() {
  const navigate = useNavigate();

  const [alertes, setAlertes] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [totalGlobal, setTotalGlobal] = useState(0);
  const [unreadCount, setUnreadCount] = useState(0);

  // Filtres simples adaptés à l'employé
  const [filterLue, setFilterLue] = useState('');
  const [filterPriorite, setFilterPriorite] = useState('');

  // Pagination
  const [page, setPage] = useState(1);
  const pageSize = 10;
  const [totalPages, setTotalPages] = useState(1);

  const fetchAlertes = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      const params = { page, page_size: pageSize };
      if (filterLue !== '') params.est_lue = filterLue;
      if (filterPriorite) params.priorite = filterPriorite;

      const res = await api.get('/notifications/', { params });
      setAlertes(res.data.items);
      setTotalGlobal(res.data.total);
      setTotalPages(res.data.total_pages);
      setUnreadCount(res.data.unread_count);
    } catch (err) {
      setError('Impossible de récupérer vos alertes.');
    } finally {
      setLoading(false);
    }
  }, [page, filterLue, filterPriorite]);

  useEffect(() => { fetchAlertes(); }, [fetchAlertes]);
  useEffect(() => { setPage(1); }, [filterLue, filterPriorite]);

  const handleReset = () => {
    setFilterLue('');
    setFilterPriorite('');
  };

  const hasActiveFilters = filterLue !== '' || filterPriorite !== '';

  const handleMarkRead = async (id) => {
    try {
      await api.post(`/notifications/${id}/read`);
      fetchAlertes();
    } catch {
      alert('Erreur lors du marquage comme lue.');
    }
  };

  const handleMarkAllRead = async () => {
    try {
      await api.post('/notifications/mark-all-read');
      fetchAlertes();
    } catch {
      alert('Erreur lors du marquage global.');
    }
  };

  const handleVoirContrat = async (alerte) => {
    if (!alerte.est_lue) {
      try { await api.post(`/notifications/${alerte.id}/read`); } catch { /* non bloquant */ }
    }
    navigate('/mon-espace/contrats');
  };

  const renderPageNumbers = () => {
    const pages = [];
    if (totalPages <= 5) {
      for (let i = 1; i <= totalPages; i++) pages.push(i);
    } else if (page <= 3) {
      pages.push(1, 2, 3, 4, '...', totalPages);
    } else if (page >= totalPages - 2) {
      pages.push(1, '...', totalPages - 3, totalPages - 2, totalPages - 1, totalPages);
    } else {
      pages.push(1, '...', page - 1, page, page + 1, '...', totalPages);
    }
    return pages.map((p, i) => {
      if (p === '...') return <span key={`e-${i}`} className="pagination-ellipsis">...</span>;
      return (
        <button key={p} onClick={() => setPage(p)}
          className={`pagination-circle-btn ${page === p ? 'active' : ''}`}>{p}</button>
      );
    });
  };

  const totalCritiques = alertes.filter(a => a.priorite === 'CRITICAL').length;
  const totalWarning = alertes.filter(a => a.priorite === 'WARNING').length;

  return (
    <div className="app-container">
      <EmployeeSidebar />
      <main className="main-content">
        <Header
          title="Mes Alertes"
          subtitle="Suivi de vos échéances contractuelles et notifications personnelles."
        />
        <div className="content-padding">

          {/* Stats Cards */}
          <div className="stats-grid alertes-stats">
            <div className="stat-card glass-card">
              <div className="stat-icon-wrapper purple">
                <Bell size={22} className="stat-icon" />
              </div>
              <div className="stat-details">
                <span className="stat-label">Total alertes</span>
                <span className="stat-value">{totalGlobal}</span>
                <span className="stat-subtitle">Alertes personnelles</span>
              </div>
            </div>
            <div className="stat-card glass-card">
              <div className="stat-icon-wrapper blue">
                <Info size={22} className="stat-icon" />
              </div>
              <div className="stat-details">
                <span className="stat-label">Non lues</span>
                <span className="stat-value">{unreadCount}</span>
                <span className="stat-subtitle">Nécessitent votre attention</span>
              </div>
            </div>
            <div className="stat-card glass-card">
              <div className="stat-icon-wrapper orange">
                <AlertCircle size={22} className="stat-icon" />
              </div>
              <div className="stat-details">
                <span className="stat-label">Avertissements (page)</span>
                <span className="stat-value">{totalWarning}</span>
                <span className="stat-subtitle">Priorité WARNING</span>
              </div>
            </div>
            <div className="stat-card glass-card">
              <div className="stat-icon-wrapper red">
                <AlertTriangle size={22} className="stat-icon" />
              </div>
              <div className="stat-details">
                <span className="stat-label">Critiques (page)</span>
                <span className="stat-value">{totalCritiques}</span>
                <span className="stat-subtitle">Échéance imminente ou dépassée</span>
              </div>
            </div>
          </div>

          {/* Table / List Card */}
          <div className="table-card glass-card">
            {/* Filters Bar */}
            <div className="alertes-filters-bar">
              <div className="alertes-filter-group">
                <span className="alertes-filter-label">Statut</span>
                <select value={filterLue} onChange={e => setFilterLue(e.target.value)} className="alertes-filter-select">
                  <option value="">Toutes</option>
                  <option value="false">Non lues</option>
                  <option value="true">Lues</option>
                </select>
              </div>

              <div className="alertes-filter-group">
                <span className="alertes-filter-label">Priorité</span>
                <select value={filterPriorite} onChange={e => setFilterPriorite(e.target.value)} className="alertes-filter-select">
                  <option value="">Toutes</option>
                  <option value="CRITICAL">Critique</option>
                  <option value="WARNING">Avertissement</option>
                  <option value="INFO">Information</option>
                </select>
              </div>

              <div className="alertes-filter-actions">
                {hasActiveFilters && (
                  <button className="alertes-reset-btn" onClick={handleReset}>
                    <RotateCcw size={14} />
                    Réinitialiser
                  </button>
                )}
                {unreadCount > 0 && (
                  <button className="alertes-markall-btn" onClick={handleMarkAllRead}>
                    <CheckCheck size={14} />
                    Tout marquer comme lu
                  </button>
                )}
              </div>
            </div>

            {/* List Content */}
            {loading ? (
              <div className="table-message">Chargement de vos alertes...</div>
            ) : error ? (
              <div className="table-message error">{error}</div>
            ) : alertes.length === 0 ? (
              <div className="table-message">Aucune alerte pour le moment. Tout est en ordre ! 🎉</div>
            ) : (
              <div className="alertes-list">
                {alertes.map(alerte => (
                  <div
                    key={alerte.id}
                    className={`alerte-card ${alerte.est_lue ? 'lue' : 'non-lue'}`}
                  >
                    <div className="alerte-card-left">
                      <PrioriteBadge priorite={alerte.priorite} />
                      <div className="alerte-card-content">
                        <div className="alerte-card-header-row">
                          <span className="alerte-card-titre">{alerte.titre}</span>
                          {!alerte.est_lue && <span className="alerte-nonlue-dot" title="Non lue" />}
                        </div>
                        <p className="alerte-card-message">{alerte.message}</p>
                        <div className="alerte-card-meta">
                          <span className="alerte-type-badge">{TYPE_LABELS[alerte.type] || alerte.type}</span>
                          {alerte.entite === 'CONTRAT' && (
                            <span className="alerte-entite-tag">
                              <FileText size={11} />
                              Mon Contrat
                            </span>
                          )}
                          <span className="alerte-date-tag">{formatDateHeure(alerte.date_creation)}</span>
                        </div>
                      </div>
                    </div>

                    <div className="alerte-card-actions">
                      {alerte.entite === 'CONTRAT' && (
                        <button className="alerte-action-btn primary" onClick={() => handleVoirContrat(alerte)}>
                          Voir mon contrat
                          <ArrowRight size={13} />
                        </button>
                      )}
                      {!alerte.est_lue && (
                        <button className="alerte-action-btn secondary" onClick={() => handleMarkRead(alerte.id)}>
                          <Check size={13} />
                          Marquer comme lue
                        </button>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Pagination */}
          <div className="pagination-bar-premium">
            <span className="pagination-info-premium">
              {totalGlobal} alerte(s) — page {page} / {totalPages}
            </span>
            <div className="pagination-controls-premium">
              <button disabled={page <= 1} onClick={() => setPage(p => p - 1)}
                className="pagination-circle-btn arrow-btn"><ChevronLeft size={16} /></button>
              <div className="pagination-numbers-container">{renderPageNumbers()}</div>
              <button disabled={page >= totalPages} onClick={() => setPage(p => p + 1)}
                className="pagination-circle-btn arrow-btn"><ChevronRight size={16} /></button>
            </div>
          </div>

        </div>
      </main>
    </div>
  );
}
