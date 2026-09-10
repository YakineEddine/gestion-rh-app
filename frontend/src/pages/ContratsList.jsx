import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  FileText, Plus, Search, Edit2, Trash2, Download,
  ChevronLeft, ChevronRight, Calendar, User, DollarSign, TrendingUp, Loader2
} from 'lucide-react';
import Sidebar from '../components/Sidebar';
import Header from '../components/Header';
import api from '../services/api';
import './ContratsList.css';

const STATUTS_FILTER = [
  { code: 'Tous',               label: 'Tous' },
  { code: 'BROUILLON',          label: 'Brouillon' },
  { code: 'COMMUNIQUE_EN_COURS',label: 'Communiqué (en cours)' },
  { code: 'SIGNE',              label: 'Signé' },
  { code: 'ACTIF',              label: 'Actif' },
  { code: 'FIN_CDD',            label: 'Fin CDD' },
  { code: 'DEMISSION_CDI',      label: 'Démission (CDI)' },
  { code: 'PAS_DISCUTE',        label: 'Pas discuté' },
  { code: 'INACTIF',            label: 'Inactif (archivé)' },
];

const STATUT_LABELS = {
  'BROUILLON': 'Brouillon',
  'COMMUNIQUE_EN_COURS': 'Communiqué (en cours)',
  'SIGNE': 'Signé',
  'ACTIF': 'Actif',
  'FIN_CDD': 'Fin CDD',
  'DEMISSION_CDI': 'Démission (CDI)',
  'PAS_DISCUTE': 'Pas discuté',
  'INACTIF': 'Inactif (archivé)',
  // Rétrocompatibilité anciens statuts
  'Brouillon': 'Brouillon',
  'Actif': 'Actif',
  'Suspendu': 'Inactif (archivé)',
  'Terminé': 'Inactif (archivé)',
  'Expiré': 'Fin CDD',
};

function getStatutClass(statut) {
  const map = {
    'BROUILLON':           'statut-brouillon',
    'COMMUNIQUE_EN_COURS': 'statut-communique',
    'SIGNE':               'statut-signe',
    'ACTIF':               'statut-actif',
    'FIN_CDD':             'statut-fin-cdd',
    'DEMISSION_CDI':       'statut-demission',
    'PAS_DISCUTE':         'statut-pas-discute',
    'INACTIF':             'statut-inactif',
    // Rétrocompatibilité
    'Brouillon': 'statut-brouillon',
    'Actif':     'statut-actif',
    'Suspendu':  'statut-inactif',
    'Terminé':   'statut-inactif',
    'Expiré':    'statut-fin-cdd',
  };
  return map[statut] || 'statut-brouillon';
}

function getStatutLabel(statut) {
  return STATUT_LABELS[statut] || statut;
}

function formatDate(d) {
  if (!d) return '—';
  return new Date(d).toLocaleDateString('fr-FR', { day: '2-digit', month: '2-digit', year: 'numeric' });
}

function formatSalaire(s) {
  return s?.toLocaleString('fr-FR') + ' DT';
}

export default function ContratsList() {
  const navigate = useNavigate();
  const [contrats, setContrats] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [searchTerm, setSearchTerm] = useState('');
  const [filterStatut, setFilterStatut] = useState('Tous');
  const [currentPage, setCurrentPage] = useState(1);
  const itemsPerPage = 8;
  const [downloadingId, setDownloadingId] = useState(null);

  useEffect(() => { fetchContrats(); }, []);
  useEffect(() => { setCurrentPage(1); }, [searchTerm, filterStatut]);

  const fetchContrats = async () => {
    try {
      setLoading(true);
      const res = await api.get('/contrats/');
      setContrats(res.data);
    } catch (err) {
      setError('Impossible de récupérer les contrats.');
    } finally {
      setLoading(false);
    }
  };

  // Filtrage côté client
  const today = new Date();
  today.setHours(0, 0, 0, 0);

  const filtered = contrats.filter(c => {
    const fullText = `${c.reference} ${c.employe?.nom || ''} ${c.employe?.prenom || ''} ${c.employe?.matricule || ''}`.toLowerCase();
    const matchSearch = fullText.includes(searchTerm.toLowerCase());
    const matchStatut = filterStatut === 'Tous' || c.statut === filterStatut || (filterStatut === 'INACTIF' && ['Suspendu', 'Terminé'].includes(c.statut));
    return matchSearch && matchStatut;
  });

  const totalPages = Math.max(1, Math.ceil(filtered.length / itemsPerPage));
  const paginated = filtered.slice((currentPage - 1) * itemsPerPage, currentPage * itemsPerPage);

  const handleDelete = async (id, ref) => {
    if (!window.confirm(`Supprimer le contrat ${ref} ? Cette action est irréversible.`)) return;
    try {
      await api.delete(`/contrats/${id}`);
      fetchContrats();
    } catch {
      alert('Erreur lors de la suppression.');
    }
  };

  const handleGenererWord = async (id, ref) => {
    setDownloadingId(id);
    try {
      const res = await api.post(`/contrats/${id}/generer-word`, null, { responseType: 'blob' });
      const blob = new Blob([res.data], {
        type: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
      });
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `Contrat_${ref}.docx`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    } catch {
      alert('Erreur lors de la génération du document Word.');
    } finally {
      setDownloadingId(null);
    }
  };

  // Stats
  const totalActifs   = contrats.filter(c => ['ACTIF', 'Actif'].includes(c.statut)).length;
  const totalBrouillons = contrats.filter(c => ['BROUILLON', 'Brouillon'].includes(c.statut)).length;
  const totalExpires  = contrats.filter(c =>
    c.date_fin && new Date(c.date_fin) < today && !['INACTIF', 'Inactif', 'FIN_CDD', 'DEMISSION_CDI', 'Terminé', 'Expiré'].includes(c.statut)
  ).length;

  // Pagination
  const renderPages = () => {
    const pages = [];
    if (totalPages <= 5) {
      for (let i = 1; i <= totalPages; i++) pages.push(i);
    } else if (currentPage <= 3) {
      pages.push(1, 2, 3, 4, '...', totalPages);
    } else if (currentPage >= totalPages - 2) {
      pages.push(1, '...', totalPages - 3, totalPages - 2, totalPages - 1, totalPages);
    } else {
      pages.push(1, '...', currentPage - 1, currentPage, currentPage + 1, '...', totalPages);
    }
    return pages.map((p, i) => {
      if (p === '...') return <span key={`e-${i}`} className="pagination-ellipsis">...</span>;
      return (
        <button key={p} onClick={() => setCurrentPage(p)}
          className={`pagination-circle-btn ${currentPage === p ? 'active' : ''}`}>{p}</button>
      );
    });
  };

  return (
    <div className="app-container">
      <Sidebar />
      <main className="main-content">
        <Header
          title="Gestion des Contrats"
          subtitle="Créez, suivez et gérez les contrats de travail de vos employés."
        />
        <div className="content-padding">

          {/* Stats */}
          <div className="stats-grid contrats-stats">
            <div className="stat-card glass-card">
              <div className="stat-icon-wrapper blue">
                <FileText size={22} className="stat-icon" />
              </div>
              <div className="stat-details">
                <span className="stat-label">Total contrats</span>
                <span className="stat-value">{contrats.length}</span>
                <span className="stat-subtitle">Tous statuts confondus</span>
              </div>
            </div>
            <div className="stat-card glass-card">
              <div className="stat-icon-wrapper green">
                <TrendingUp size={22} className="stat-icon" />
              </div>
              <div className="stat-details">
                <span className="stat-label">Actifs</span>
                <span className="stat-value">{totalActifs}</span>
                <span className="stat-subtitle">Contrats en cours</span>
              </div>
            </div>
            <div className="stat-card glass-card">
              <div className="stat-icon-wrapper purple">
                <DollarSign size={22} className="stat-icon" />
              </div>
              <div className="stat-details">
                <span className="stat-label">Brouillons</span>
                <span className="stat-value">{totalBrouillons}</span>
                <span className="stat-subtitle">En attente de finalisation</span>
              </div>
            </div>
            <div className="stat-card glass-card">
              <div className="stat-icon-wrapper orange">
                <Calendar size={22} className="stat-icon" />
              </div>
              <div className="stat-details">
                <span className="stat-label">Expirés</span>
                <span className="stat-value">{totalExpires}</span>
                <span className="stat-subtitle">Date de fin dépassée</span>
              </div>
            </div>
          </div>

          {/* Table card */}
          <div className="table-card glass-card">
            {/* Filters */}
            <div className="contrats-filters-bar">
              <div className="contrats-filter-group">
                <span className="contrats-filter-label">Recherche</span>
                <div className="contrats-search-wrapper">
                  <Search size={15} className="contrats-search-icon" />
                  <input
                    type="text"
                    placeholder="Référence, employé..."
                    value={searchTerm}
                    onChange={e => setSearchTerm(e.target.value)}
                    className="contrats-search-input"
                  />
                </div>
              </div>
              <div className="contrats-filter-group">
                <span className="contrats-filter-label">Statut</span>
                <select
                  value={filterStatut}
                  onChange={e => setFilterStatut(e.target.value)}
                  className="contrats-filter-select"
                >
                  {STATUTS_FILTER.map(s => (
                    <option key={s.code} value={s.code}>
                      {s.label}
                    </option>
                  ))}
                </select>
              </div>
              <div className="contrats-filter-actions">
                <button
                  className="contrats-add-btn"
                  onClick={() => navigate('/contrats/nouveau')}
                >
                  <Plus size={18} />
                  Nouveau contrat
                </button>
              </div>
            </div>

            {/* Table */}
            {loading ? (
              <div className="table-message">Chargement...</div>
            ) : error ? (
              <div className="table-message error">{error}</div>
            ) : filtered.length === 0 ? (
              <div className="table-message">Aucun contrat trouvé.</div>
            ) : (
              <div className="table-scroll-container">
                <table className="custom-premium-table">
                  <thead>
                    <tr>
                      <th>Référence</th>
                      <th>Employé</th>
                      <th>Date début</th>
                      <th>Date fin</th>
                      <th>Salaire mensuel</th>
                      <th>Statut</th>
                      <th style={{ textAlign: 'right' }}>Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {paginated.map(c => (
                      <tr key={c.id}>
                        <td>
                          <span className="contrat-ref-badge">{c.reference}</span>
                        </td>
                        <td>
                          {c.employe ? (
                            <div className="contrat-employe-cell">
                              <div className="contrat-employe-avatar">
                                {(c.employe.nom[0] || '') + (c.employe.prenom[0] || '')}
                              </div>
                              <div className="contrat-employe-info">
                                <span className="contrat-employe-nom">{c.employe.nom} {c.employe.prenom}</span>
                                <span className="contrat-employe-matricule">{c.employe.matricule}</span>
                              </div>
                            </div>
                          ) : '—'}
                        </td>
                        <td className="contrat-date-cell">
                          <div className="contrat-date-wrapper">
                            <Calendar size={13} className="contrat-date-icon" />
                            {formatDate(c.date_debut)}
                          </div>
                        </td>
                        <td className="contrat-date-cell">
                          {c.date_fin ? (
                            <div className="contrat-date-wrapper">
                              <Calendar size={13} className="contrat-date-icon" />
                              {formatDate(c.date_fin)}
                            </div>
                          ) : (
                            <span className="contrat-indefini">Indéfini</span>
                          )}
                        </td>
                        <td className="contrat-salaire-cell">
                          {formatSalaire(c.salaire_mensuel)}
                        </td>
                        <td>
                          <span className={`contrat-statut-badge ${getStatutClass(c.statut)}`}>
                            {getStatutLabel(c.statut)}
                          </span>
                        </td>
                        <td>
                          <div className="actions-buttons-container">
                            <button
                              onClick={() => handleGenererWord(c.id, c.reference)}
                              className="action-circle-btn-word"
                              title="Générer Word"
                              disabled={downloadingId === c.id}
                            >
                              {downloadingId === c.id ? <Loader2 size={14} className="cl-spin" /> : <Download size={14} />}
                            </button>
                            <button
                              onClick={() => navigate(`/contrats/modifier/${c.id}`)}
                              className="action-circle-btn-edit"
                              title="Modifier"
                            >
                              <Edit2 size={14} />
                            </button>
                            <button
                              onClick={() => handleDelete(c.id, c.reference)}
                              className="action-circle-btn-delete"
                              title="Supprimer"
                            >
                              <Trash2 size={14} />
                            </button>
                          </div>
                        </td>
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
              {filtered.length} contrat(s) — page {currentPage} / {totalPages}
            </span>
            <div className="pagination-controls-premium">
              <button disabled={currentPage <= 1} onClick={() => setCurrentPage(p => p - 1)}
                className="pagination-circle-btn arrow-btn"><ChevronLeft size={16} /></button>
              <div className="pagination-numbers-container">{renderPages()}</div>
              <button disabled={currentPage >= totalPages} onClick={() => setCurrentPage(p => p + 1)}
                className="pagination-circle-btn arrow-btn"><ChevronRight size={16} /></button>
            </div>
          </div>

        </div>
      </main>
    </div>
  );
}
