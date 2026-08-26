import React, { useState, useEffect, useCallback } from 'react';
import {
  History, Search, RotateCcw, ChevronLeft, ChevronRight, X,
  User, Calendar, Tag, Layers, FileText as FileTextIcon,
  LogIn, LogOut, PlusCircle, Edit2, Trash2, ToggleRight, ToggleLeft,
  Download, FileCog, ArrowRightLeft, ShieldAlert, Activity, Mail, Bell, Sparkles
} from 'lucide-react';
import Sidebar from '../components/Sidebar';
import Header from '../components/Header';
import api from '../services/api';
import './AuditLogs.css';

const ACTIONS = [
  'CREATE', 'UPDATE', 'DELETE', 'LOGIN', 'LOGIN_FAILED', 'LOGOUT',
  'ACTIVATE', 'DEACTIVATE', 'DOWNLOAD', 'GENERATE', 'STATUS_CHANGE',
  'ALERT_GENERATED', 'EMAIL_SENT', 'AI_GENERATE'
];
const ENTITES = ['EMPLOYE', 'ARTICLE', 'CONTRAT', 'AUTH'];

const ACTION_CONFIG = {
  CREATE:          { label: 'Création',          icon: PlusCircle,     cls: 'create' },
  UPDATE:          { label: 'Modification',      icon: Edit2,          cls: 'update' },
  DELETE:          { label: 'Suppression',       icon: Trash2,         cls: 'delete' },
  LOGIN:           { label: 'Connexion',         icon: LogIn,          cls: 'login' },
  LOGIN_FAILED:    { label: 'Échec connexion',   icon: ShieldAlert,    cls: 'login-failed' },
  LOGOUT:          { label: 'Déconnexion',       icon: LogOut,         cls: 'logout' },
  ACTIVATE:        { label: 'Activation',        icon: ToggleRight,    cls: 'activate' },
  DEACTIVATE:      { label: 'Désactivation',     icon: ToggleLeft,     cls: 'deactivate' },
  DOWNLOAD:        { label: 'Téléchargement',    icon: Download,       cls: 'download' },
  GENERATE:        { label: 'Génération',        icon: FileCog,        cls: 'generate' },
  STATUS_CHANGE:   { label: 'Changement statut', icon: ArrowRightLeft, cls: 'status-change' },
  ALERT_GENERATED: { label: 'Alerte générée',    icon: Bell,           cls: 'alert-generated' },
  EMAIL_SENT:      { label: 'Email envoyé',      icon: Mail,           cls: 'email-sent' },
  AI_GENERATE:     { label: 'Génération IA',     icon: Sparkles,       cls: 'ai-generate' },
};

const ENTITE_LABELS = {
  EMPLOYE: 'Employé',
  ARTICLE: 'Article',
  CONTRAT: 'Contrat',
  AUTH: 'Authentification',
};

function formatDateHeure(iso) {
  if (!iso) return '—';
  const d = new Date(iso);
  const date = d.toLocaleDateString('fr-FR', { day: '2-digit', month: '2-digit', year: 'numeric' });
  const heure = d.toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' });
  return `${date} à ${heure}`;
}

function ActionBadge({ action }) {
  const config = ACTION_CONFIG[action] || { label: action, icon: Activity, cls: 'default' };
  const Icon = config.icon;
  return (
    <span className={`audit-action-badge audit-${config.cls}`}>
      <Icon size={12} />
      {action}
    </span>
  );
}

export default function AuditLogs() {
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [employes, setEmployes] = useState([]);

  // Filtres
  const [search, setSearch] = useState('');
  const [filterAction, setFilterAction] = useState('');
  const [filterEntite, setFilterEntite] = useState('');
  const [filterUtilisateur, setFilterUtilisateur] = useState('');
  const [dateDebut, setDateDebut] = useState('');
  const [dateFin, setDateFin] = useState('');

  // Pagination (côté backend)
  const [page, setPage] = useState(1);
  const pageSize = 15;
  const [total, setTotal] = useState(0);
  const [totalPages, setTotalPages] = useState(1);

  // Modal détail
  const [selectedLog, setSelectedLog] = useState(null);

  useEffect(() => {
    api.get('/employes/').then(res => setEmployes(res.data)).catch(() => {});
  }, []);

  const fetchLogs = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      const params = { page, page_size: pageSize };
      if (search.trim()) params.search = search.trim();
      if (filterAction) params.action = filterAction;
      if (filterEntite) params.entite = filterEntite;
      if (filterUtilisateur) params.utilisateur_id = filterUtilisateur;
      if (dateDebut) params.date_debut = dateDebut;
      if (dateFin) params.date_fin = dateFin;

      const res = await api.get('/audit/', { params });
      setLogs(res.data.items);
      setTotal(res.data.total);
      setTotalPages(res.data.total_pages);
    } catch (err) {
      setError("Impossible de récupérer l'historique des activités.");
    } finally {
      setLoading(false);
    }
  }, [page, search, filterAction, filterEntite, filterUtilisateur, dateDebut, dateFin]);

  useEffect(() => {
    // Debounce léger pour la recherche texte
    const timer = setTimeout(() => fetchLogs(), 300);
    return () => clearTimeout(timer);
  }, [fetchLogs]);

  useEffect(() => { setPage(1); }, [search, filterAction, filterEntite, filterUtilisateur, dateDebut, dateFin]);

  const handleReset = () => {
    setSearch('');
    setFilterAction('');
    setFilterEntite('');
    setFilterUtilisateur('');
    setDateDebut('');
    setDateFin('');
  };

  const hasActiveFilters = search || filterAction || filterEntite || filterUtilisateur || dateDebut || dateFin;

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

  // Stats
  const totalAujourdhui = logs.filter(l => {
    const d = new Date(l.date_action);
    const now = new Date();
    return d.toDateString() === now.toDateString();
  }).length;
  const totalConnexions = logs.filter(l => l.action === 'LOGIN').length;
  const totalModifications = logs.filter(l => ['CREATE', 'UPDATE', 'DELETE'].includes(l.action)).length;

  return (
    <div className="app-container">
      <Sidebar />
      <main className="main-content">
        <Header
          title="Historique des Activités"
          subtitle="Consultez la traçabilité complète des actions effectuées dans l'application."
        />
        <div className="content-padding">

          {/* Stats */}
          <div className="stats-grid audit-stats">
            <div className="stat-card glass-card">
              <div className="stat-icon-wrapper purple">
                <History size={22} className="stat-icon" />
              </div>
              <div className="stat-details">
                <span className="stat-label">Total évènements</span>
                <span className="stat-value">{total}</span>
                <span className="stat-subtitle">Toutes actions confondues</span>
              </div>
            </div>
            <div className="stat-card glass-card">
              <div className="stat-icon-wrapper blue">
                <Calendar size={22} className="stat-icon" />
              </div>
              <div className="stat-details">
                <span className="stat-label">Sur cette page</span>
                <span className="stat-value">{totalAujourdhui}</span>
                <span className="stat-subtitle">Évènements du jour affichés</span>
              </div>
            </div>
            <div className="stat-card glass-card">
              <div className="stat-icon-wrapper green">
                <LogIn size={22} className="stat-icon" />
              </div>
              <div className="stat-details">
                <span className="stat-label">Connexions</span>
                <span className="stat-value">{totalConnexions}</span>
                <span className="stat-subtitle">Sur cette page</span>
              </div>
            </div>
            <div className="stat-card glass-card">
              <div className="stat-icon-wrapper orange">
                <Edit2 size={22} className="stat-icon" />
              </div>
              <div className="stat-details">
                <span className="stat-label">Modifications</span>
                <span className="stat-value">{totalModifications}</span>
                <span className="stat-subtitle">Créations/modifs/suppressions</span>
              </div>
            </div>
          </div>

          {/* Table card */}
          <div className="table-card glass-card">
            {/* Filters */}
            <div className="audit-filters-bar">
              <div className="audit-filter-group audit-filter-search">
                <span className="audit-filter-label">Recherche</span>
                <div className="audit-search-wrapper">
                  <Search size={15} className="audit-search-icon" />
                  <input
                    type="text"
                    placeholder="Rechercher dans les descriptions..."
                    value={search}
                    onChange={e => setSearch(e.target.value)}
                    className="audit-search-input"
                  />
                </div>
              </div>

              <div className="audit-filter-group">
                <span className="audit-filter-label">Action</span>
                <select value={filterAction} onChange={e => setFilterAction(e.target.value)} className="audit-filter-select">
                  <option value="">Toutes</option>
                  {ACTIONS.map(a => <option key={a} value={a}>{a}</option>)}
                </select>
              </div>

              <div className="audit-filter-group">
                <span className="audit-filter-label">Entité</span>
                <select value={filterEntite} onChange={e => setFilterEntite(e.target.value)} className="audit-filter-select">
                  <option value="">Toutes</option>
                  {ENTITES.map(e => <option key={e} value={e}>{ENTITE_LABELS[e] || e}</option>)}
                </select>
              </div>

              <div className="audit-filter-group">
                <span className="audit-filter-label">Utilisateur</span>
                <select value={filterUtilisateur} onChange={e => setFilterUtilisateur(e.target.value)} className="audit-filter-select">
                  <option value="">Tous</option>
                  {employes.map(e => (
                    <option key={e.id} value={e.id}>{e.prenom} {e.nom}</option>
                  ))}
                </select>
              </div>

              <div className="audit-filter-group">
                <span className="audit-filter-label">Date début</span>
                <input type="date" value={dateDebut} onChange={e => setDateDebut(e.target.value)} className="audit-filter-select" />
              </div>

              <div className="audit-filter-group">
                <span className="audit-filter-label">Date fin</span>
                <input type="date" value={dateFin} onChange={e => setDateFin(e.target.value)} className="audit-filter-select" min={dateDebut || undefined} />
              </div>

              {hasActiveFilters && (
                <div className="audit-filter-actions">
                  <button className="audit-reset-btn" onClick={handleReset}>
                    <RotateCcw size={14} />
                    Réinitialiser
                  </button>
                </div>
              )}
            </div>

            {/* Table */}
            {loading ? (
              <div className="table-message">Chargement...</div>
            ) : error ? (
              <div className="table-message error">{error}</div>
            ) : logs.length === 0 ? (
              <div className="table-message">Aucun évènement trouvé.</div>
            ) : (
              <div className="table-scroll-container">
                <table className="custom-premium-table">
                  <thead>
                    <tr>
                      <th>Date</th>
                      <th>Utilisateur</th>
                      <th>Action</th>
                      <th>Entité</th>
                      <th>Élément</th>
                      <th>Description</th>
                    </tr>
                  </thead>
                  <tbody>
                    {logs.map(log => (
                      <tr key={log.id} className="audit-row" onClick={() => setSelectedLog(log)}>
                        <td className="audit-date-cell">{formatDateHeure(log.date_action)}</td>
                        <td className="audit-user-cell">
                          {log.utilisateur_nom || <span className="audit-user-unknown">Système</span>}
                        </td>
                        <td><ActionBadge action={log.action} /></td>
                        <td>
                          <span className="audit-entite-badge">{ENTITE_LABELS[log.entite] || log.entite}</span>
                        </td>
                        <td className="audit-element-cell">
                          {log.entite_id ? `#${log.entite_id}` : '—'}
                        </td>
                        <td className="audit-description-cell">{log.description}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>

          {/* Pagination */}
          <div className="pagination-bar-premium">
            <span className="pagination-info-premium">
              {total} évènement(s) — page {page} / {totalPages}
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

      {/* Modal détail */}
      {selectedLog && (
        <div className="audit-modal-overlay" onClick={() => setSelectedLog(null)}>
          <div className="audit-modal-card" onClick={e => e.stopPropagation()}>
            <div className="audit-modal-header">
              <h3><History size={18} /> Détail de l'activité</h3>
              <button className="close-modal-btn" onClick={() => setSelectedLog(null)}><X size={18} /></button>
            </div>

            <div className="audit-modal-body">
              <div className="audit-detail-grid">
                <div className="audit-detail-item">
                  <label><User size={13} /> Utilisateur</label>
                  <p>{selectedLog.utilisateur_nom || 'Système / Inconnu'}</p>
                </div>
                <div className="audit-detail-item">
                  <label><Calendar size={13} /> Date</label>
                  <p>{formatDateHeure(selectedLog.date_action)}</p>
                </div>
                <div className="audit-detail-item">
                  <label><Tag size={13} /> Action</label>
                  <p><ActionBadge action={selectedLog.action} /></p>
                </div>
                <div className="audit-detail-item">
                  <label><Layers size={13} /> Entité</label>
                  <p>{ENTITE_LABELS[selectedLog.entite] || selectedLog.entite} {selectedLog.entite_id ? `#${selectedLog.entite_id}` : ''}</p>
                </div>
              </div>

              <div className="audit-detail-description">
                <label><FileTextIcon size={13} /> Description</label>
                <p>{selectedLog.description}</p>
              </div>

              {(selectedLog.anciennes_valeurs || selectedLog.nouvelles_valeurs) && (
                <div className="audit-values-grid">
                  {selectedLog.anciennes_valeurs && (
                    <div className="audit-values-col avant">
                      <span className="audit-values-title">Anciennes valeurs</span>
                      {Object.entries(selectedLog.anciennes_valeurs).map(([k, v]) => (
                        <div key={k} className="audit-value-row">
                          <span className="audit-value-key">{k}</span>
                          <span className="audit-value-val">{v === null || v === undefined || v === '' ? '—' : String(v)}</span>
                        </div>
                      ))}
                    </div>
                  )}
                  {selectedLog.nouvelles_valeurs && (
                    <div className="audit-values-col apres">
                      <span className="audit-values-title">Nouvelles valeurs</span>
                      {Object.entries(selectedLog.nouvelles_valeurs).map(([k, v]) => (
                        <div key={k} className="audit-value-row">
                          <span className="audit-value-key">{k}</span>
                          <span className="audit-value-val">{v === null || v === undefined || v === '' ? '—' : String(v)}</span>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}

              {selectedLog.ip_address && (
                <p className="audit-ip-note">Adresse IP : {selectedLog.ip_address}</p>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
