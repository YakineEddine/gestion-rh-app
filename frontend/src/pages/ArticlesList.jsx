import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  BookOpen, Plus, Search, Edit2, Trash2, ToggleLeft, ToggleRight,
  ChevronLeft, ChevronRight, X, Save, Hash, Type, AlignLeft,
  Sparkles, Loader2, AlertTriangle, Wand2, Table, Layers, FileText,
  Eye, Code, CheckCircle2, RotateCw
} from 'lucide-react';
import Sidebar from '../components/Sidebar';
import Header from '../components/Header';
import api from '../services/api';
import './ArticlesList.css';

// ── Helpers pour le contenu structuré ─────────────────────────────
export function tryParseStructured(content) {
  if (!content || typeof content !== 'string') return null;
  const trimmed = content.trim();
  if (!trimmed.startsWith('{')) return null;
  try {
    const data = JSON.parse(trimmed);
    if (data && Array.isArray(data.blocks) && data.blocks.length > 0) {
      return data;
    }
  } catch (e) {
    return null;
  }
  return null;
}

export function structuredToMarkdown(data) {
  if (!data || !data.blocks) return '';
  const parts = [];
  data.blocks.forEach(block => {
    if (block.type === 'paragraph' && block.content) {
      parts.push(block.content);
    } else if (block.type === 'table' && block.headers) {
      parts.push('| ' + block.headers.join(' | ') + ' |');
      parts.push('| ' + block.headers.map(() => '---').join(' | ') + ' |');
      (block.rows || []).forEach(row => {
        parts.push('| ' + (Array.isArray(row) ? row.join(' | ') : row) + ' |');
      });
    }
  });
  return parts.join('\n\n');
}

export function getStructuredPreviewText(structured) {
  if (!structured || !structured.blocks) return '';
  const firstPara = structured.blocks.find(b => b.type === 'paragraph');
  if (firstPara && firstPara.content) {
    return firstPara.content.length > 110
      ? firstPara.content.substring(0, 110) + '...'
      : firstPara.content;
  }
  const firstTable = structured.blocks.find(b => b.type === 'table');
  if (firstTable && firstTable.headers) {
    return `Tableau : ${firstTable.headers.slice(0, 3).join(', ')} (${(firstTable.rows || []).length} lignes)`;
  }
  return 'Contenu structuré multi-blocs';
}

// ── Composant d'affichage des blocs structurés ────────────────────
export function StructuredBlocksRenderer({ data }) {
  if (!data || !Array.isArray(data.blocks)) return null;

  return (
    <div className="structured-blocks-renderer">
      {data.blocks.map((block, idx) => {
        if (block.type === 'paragraph') {
          return (
            <p key={idx} className="structured-para">
              {block.content}
            </p>
          );
        }
        if (block.type === 'table') {
          const headers = block.headers || [];
          const rows = block.rows || [];
          return (
            <div key={idx} className="structured-table-container">
              <table className="structured-html-table">
                <thead>
                  <tr>
                    {headers.map((h, hIdx) => (
                      <th key={hIdx}>{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {rows.map((row, rIdx) => (
                    <tr key={rIdx}>
                      {Array.isArray(row) ? (
                        row.map((cell, cIdx) => <td key={cIdx}>{cell}</td>)
                      ) : (
                        <td>{row}</td>
                      )}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          );
        }
        return null;
      })}
    </div>
  );
}

const TYPES_CONTRAT_OPTIONS = ['CDI', 'CDD', 'STAGE', 'ALTERNANCE', 'CIVP'];

export default function ArticlesList() {
  const [articles, setArticles] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [searchTerm, setSearchTerm] = useState('');
  const [filterActif, setFilterActif] = useState('Tous');
  const [filterTypeContrat, setFilterTypeContrat] = useState('Tous');

  // Pagination
  const [currentPage, setCurrentPage] = useState(1);
  const itemsPerPage = 8;

  // Modal CRUD
  const [showModal, setShowModal] = useState(false);
  const [editingArticle, setEditingArticle] = useState(null);
  const [formData, setFormData] = useState({ code: '', titre: '', contenu_par_defaut: '', types_contrat: [] });
  const [formError, setFormError] = useState('');
  const [formLoading, setFormLoading] = useState(false);
  const [viewTab, setViewTab] = useState('preview'); // 'preview' | 'code'

  // IA intégrée au formulaire
  const [aiPrompt, setAiPrompt] = useState('');
  const [aiLoading, setAiLoading] = useState(false);
  const [aiError, setAiError] = useState('');
  const [aiResult, setAiResult] = useState(null);

  useEffect(() => {
    fetchArticles();
  }, []);

  const fetchArticles = async () => {
    try {
      setLoading(true);
      const res = await api.get('/articles/');
      setArticles(res.data);
    } catch (err) {
      setError("Impossible de recuperer les articles.");
    } finally {
      setLoading(false);
    }
  };

  // Filtrage
  const filteredArticles = articles.filter(art => {
    const matchSearch = `${art.code} ${art.titre} ${art.contenu_par_defaut || ''}`
      .toLowerCase().includes(searchTerm.toLowerCase());
    const matchActif = filterActif === 'Tous' ||
      (filterActif === 'Actifs' && art.est_actif) ||
      (filterActif === 'Inactifs' && !art.est_actif);
    const matchType = filterTypeContrat === 'Tous' ||
      (!art.types_contrat || art.types_contrat.length === 0) ||
      (Array.isArray(art.types_contrat) && art.types_contrat.includes(filterTypeContrat));
    return matchSearch && matchActif && matchType;
  });

  // Pagination
  const totalPages = Math.max(1, Math.ceil(filteredArticles.length / itemsPerPage));
  const paginatedArticles = filteredArticles.slice(
    (currentPage - 1) * itemsPerPage,
    currentPage * itemsPerPage
  );

  useEffect(() => { setCurrentPage(1); }, [searchTerm, filterActif, filterTypeContrat]);

  // Génération du prochain code ART-XXX
  const generateNextCode = () => {
    const codes = articles
      .map(a => a.code)
      .filter(c => /^ART-\d+$/.test(c))
      .map(c => parseInt(c.replace('ART-', ''), 10));
    const maxCode = codes.length > 0 ? Math.max(...codes) : 0;
    return `ART-${String(maxCode + 1).padStart(3, '0')}`;
  };

  // CRUD handlers
  const openCreateModal = () => {
    setEditingArticle(null);
    setFormData({ code: generateNextCode(), titre: '', contenu_par_defaut: '', types_contrat: [] });
    setFormError('');
    setAiPrompt('');
    setAiError('');
    setAiResult(null);
    setViewTab('preview');
    setShowModal(true);
  };

  const openEditModal = (article) => {
    setEditingArticle(article);
    setFormData({
      code: article.code,
      titre: article.titre,
      contenu_par_defaut: article.contenu_par_defaut || '',
      types_contrat: Array.isArray(article.types_contrat) ? [...article.types_contrat] : []
    });
    setFormError('');
    setAiPrompt('');
    setAiError('');
    setAiResult(null);
    setViewTab(tryParseStructured(article.contenu_par_defaut) ? 'preview' : 'code');
    setShowModal(true);
  };

  const handleToggleContractType = (type) => {
    setFormData(prev => {
      const current = prev.types_contrat || [];
      const updated = current.includes(type)
        ? current.filter(t => t !== type)
        : [...current, type];
      return { ...prev, types_contrat: updated };
    });
  };

  const handleToggleAllContractTypes = () => {
    setFormData(prev => {
      const current = prev.types_contrat || [];
      if (current.length === TYPES_CONTRAT_OPTIONS.length) {
        return { ...prev, types_contrat: [] };
      } else {
        return { ...prev, types_contrat: [...TYPES_CONTRAT_OPTIONS] };
      }
    });
  };

  const closeModal = () => {
    setShowModal(false);
    setEditingArticle(null);
    setFormError('');
    setAiPrompt('');
    setAiError('');
    setAiResult(null);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setFormError('');
    setFormLoading(true);

    try {
      const payload = {
        ...formData,
        types_contrat: (formData.types_contrat && formData.types_contrat.length > 0)
          ? formData.types_contrat
          : null
      };
      if (editingArticle) {
        await api.put(`/articles/${editingArticle.id}`, payload);
      } else {
        await api.post('/articles/', payload);
      }
      closeModal();
      fetchArticles();
    } catch (err) {
      setFormError(err.response?.data?.detail || "Erreur lors de l'enregistrement.");
    } finally {
      setFormLoading(false);
    }
  };

  const handleToggle = async (article) => {
    try {
      await api.patch(`/articles/${article.id}/toggle`);
      fetchArticles();
    } catch (err) {
      alert("Erreur lors du changement de statut.");
    }
  };

  const handleDelete = async (id) => {
    if (!window.confirm("Supprimer cet article ? Cette action est irréversible.")) return;
    try {
      await api.delete(`/articles/${id}`);
      fetchArticles();
    } catch (err) {
      alert("Erreur lors de la suppression.");
    }
  };

  // ── IA intégrée (Génération structurée) ───────────────────────
  const handleAIGenerate = async () => {
    if (!aiPrompt.trim()) {
      setAiError("Veuillez décrire la clause ou grille que vous souhaitez générer.");
      return;
    }
    setAiError('');
    setAiLoading(true);

    try {
      const res = await api.post('/ai/articles/generate-structured', { prompt: aiPrompt.trim() });
      const structuredData = res.data;
      setAiResult(structuredData);

      // Injecter le résultat structuré dans le formulaire
      setFormData(prev => ({
        ...prev,
        titre: prev.titre || structuredData.title,
        contenu_par_defaut: JSON.stringify(structuredData, null, 2),
      }));
      setViewTab('preview');
    } catch (err) {
      let detail = err.response?.data?.detail;
      if (typeof detail === 'string' && detail.trim()) {
        if (detail.toLowerCase().includes('high demand') || detail.toLowerCase().includes('unavailable') || detail.includes('503')) {
          detail = "Le modèle d'intelligence artificielle subit une forte affluence temporaire. Veuillez patienter quelques secondes et cliquer sur Réessayer.";
        }
        setAiError(detail);
      } else if (err.response?.status === 503) {
        setAiError("Le modèle d'intelligence artificielle subit une forte affluence temporaire. Veuillez patienter quelques secondes et réessayer.");
      } else if (err.response?.status === 429) {
        setAiError("Le quota de requêtes vers le service IA est temporairement dépassé. Veuillez patienter un instant.");
      } else if (err.response?.status === 400) {
        setAiError(detail || "Requête invalide.");
      } else {
        setAiError("Erreur lors de la génération. Veuillez réessayer.");
      }
    } finally {
      setAiLoading(false);
    }
  };

  const handleApplyAsMarkdown = () => {
    if (!aiResult) return;
    const md = structuredToMarkdown(aiResult);
    setFormData(prev => ({
      ...prev,
      contenu_par_defaut: md
    }));
    setViewTab('code');
  };

  const handleApplyAsStructured = () => {
    if (!aiResult) return;
    setFormData(prev => ({
      ...prev,
      contenu_par_defaut: JSON.stringify(aiResult, null, 2)
    }));
    setViewTab('preview');
  };

  // Pagination render
  const renderPageNumbers = () => {
    const pages = [];
    if (totalPages <= 5) {
      for (let i = 1; i <= totalPages; i++) pages.push(i);
    } else {
      if (currentPage <= 3) pages.push(1, 2, 3, 4, '...', totalPages);
      else if (currentPage >= totalPages - 2) pages.push(1, '...', totalPages - 3, totalPages - 2, totalPages - 1, totalPages);
      else pages.push(1, '...', currentPage - 1, currentPage, currentPage + 1, '...', totalPages);
    }
    return pages.map((page, index) => {
      if (page === '...') return <span key={`e-${index}`} className="pagination-ellipsis">...</span>;
      return (
        <button key={page} onClick={() => setCurrentPage(page)}
          className={`pagination-circle-btn ${currentPage === page ? 'active' : ''}`}
        >{page}</button>
      );
    });
  };

  // Stats
  const totalArticles = articles.length;
  const totalActifs = articles.filter(a => a.est_actif).length;
  const totalInactifs = articles.filter(a => !a.est_actif).length;

  return (
    <div className="app-container">
      <Sidebar />
      <main className="main-content">
        <Header
          title="Bibliothèque d'Articles"
          subtitle="Gérez les clauses contractuelles réutilisables pour vos contrats."
        />
        <div className="content-padding">

          {/* Stats */}
          <div className="stats-grid articles-stats">
            <div className="stat-card glass-card">
              <div className="stat-icon-wrapper purple">
                <BookOpen size={22} className="stat-icon" />
              </div>
              <div className="stat-details">
                <span className="stat-label">Total articles</span>
                <span className="stat-value">{totalArticles}</span>
                <span className="stat-subtitle">Clauses disponibles</span>
              </div>
            </div>
            <div className="stat-card glass-card">
              <div className="stat-icon-wrapper green">
                <ToggleRight size={22} className="stat-icon" />
              </div>
              <div className="stat-details">
                <span className="stat-label">Actifs</span>
                <span className="stat-value">{totalActifs}</span>
                <span className="stat-subtitle">Utilisables dans les contrats</span>
              </div>
            </div>
            <div className="stat-card glass-card">
              <div className="stat-icon-wrapper orange">
                <ToggleLeft size={22} className="stat-icon" />
              </div>
              <div className="stat-details">
                <span className="stat-label">Inactifs</span>
                <span className="stat-value">{totalInactifs}</span>
                <span className="stat-subtitle">Désactivés temporairement</span>
              </div>
            </div>
          </div>

          {/* Table card */}
          <div className="table-card glass-card">
            {/* Filters bar */}
            <div className="articles-filters-bar">
              <div className="articles-filter-group">
                <span className="articles-filter-label">Recherche</span>
                <div className="articles-search-wrapper">
                  <Search size={15} className="articles-search-icon" />
                  <input
                    type="text"
                    placeholder="Code, titre..."
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                    className="articles-search-input"
                  />
                </div>
              </div>
              <div className="articles-filter-group">
                <span className="articles-filter-label">Statut</span>
                <select value={filterActif} onChange={(e) => setFilterActif(e.target.value)} className="articles-filter-select">
                  <option>Tous</option>
                  <option>Actifs</option>
                  <option>Inactifs</option>
                </select>
              </div>
              <div className="articles-filter-group">
                <span className="articles-filter-label">Type de contrat</span>
                <select
                  value={filterTypeContrat}
                  onChange={(e) => setFilterTypeContrat(e.target.value)}
                  className="articles-filter-select"
                >
                  <option value="Tous">Tous</option>
                  {TYPES_CONTRAT_OPTIONS.map(t => (
                    <option key={t} value={t}>{t}</option>
                  ))}
                </select>
              </div>
              <div className="articles-filter-actions">
                <button className="articles-add-btn" onClick={openCreateModal}>
                  <Plus size={18} />
                  Nouvel article
                </button>
              </div>
            </div>

            {/* Table */}
            {loading ? (
              <div className="table-message">Chargement...</div>
            ) : error ? (
              <div className="table-message error">{error}</div>
            ) : filteredArticles.length === 0 ? (
              <div className="table-message">Aucun article trouvé.</div>
            ) : (
              <div className="table-scroll-container">
                <table className="custom-premium-table">
                  <thead>
                    <tr>
                      <th>Code</th>
                      <th>Titre</th>
                      <th>Types compatibles</th>
                      <th>Aperçu du contenu</th>
                      <th>Statut</th>
                      <th>Dernière modification</th>
                      <th style={{ textAlign: 'right' }}>Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {paginatedArticles.map(article => (
                      <tr key={article.id}>
                        <td>
                          <span className="article-code-badge">{article.code}</span>
                        </td>
                        <td className="article-titre-cell">{article.titre}</td>
                        <td>
                          {article.types_contrat && Array.isArray(article.types_contrat) && article.types_contrat.length > 0 ? (
                            <div className="article-contract-types-badges">
                              {article.types_contrat.map(t => (
                                <span key={t} className={`contract-type-badge-pill ${t.toLowerCase()}`}>
                                  {t}
                                </span>
                              ))}
                            </div>
                          ) : (
                            <span className="contract-type-badge-pill all">Tous types</span>
                          )}
                        </td>
                        <td className="article-contenu-cell">
                          {(() => {
                            const structured = tryParseStructured(article.contenu_par_defaut);
                            if (structured) {
                              return (
                                <div className="contenu-structured-pill-wrapper">
                                  <span className={`article-type-badge ${structured.type}`}>
                                    {structured.type === 'table' ? <Table size={12} /> : structured.type === 'mixed' ? <Layers size={12} /> : <FileText size={12} />}
                                    {structured.type === 'table' ? 'Tableau' : structured.type === 'mixed' ? 'Mixte' : 'Paragraphe'}
                                  </span>
                                  <span className="contenu-preview">
                                    {getStructuredPreviewText(structured)}
                                  </span>
                                </div>
                              );
                            }
                            return (
                              <span className="contenu-preview">
                                {article.contenu_par_defaut
                                  ? article.contenu_par_defaut.substring(0, 120) + (article.contenu_par_defaut.length > 120 ? '...' : '')
                                  : '—'}
                              </span>
                            );
                          })()}
                        </td>
                        <td>
                          <span className={`status-badge-article ${article.est_actif ? 'actif' : 'inactif'}`}>
                            {article.est_actif ? 'Actif' : 'Inactif'}
                          </span>
                        </td>
                        <td className="article-date-cell">
                          {article.modifie_le
                            ? (() => {
                                const d = new Date(article.modifie_le);
                                const date = d.toLocaleDateString('fr-FR', { day: '2-digit', month: '2-digit', year: 'numeric' });
                                const heure = d.toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' });
                                return <span className="date-modif-text">{date} à {heure}</span>;
                              })()
                            : <span className="date-modif-empty">—</span>}
                        </td>
                        <td>
                          <div className="actions-buttons-container">
                            <button
                              onClick={() => handleToggle(article)}
                              className={`action-circle-btn-toggle ${article.est_actif ? 'on' : 'off'}`}
                              title={article.est_actif ? 'Désactiver' : 'Activer'}
                            >
                              {article.est_actif ? <ToggleRight size={15} /> : <ToggleLeft size={15} />}
                            </button>
                            <button
                              onClick={() => openEditModal(article)}
                              className="action-circle-btn-edit"
                              title="Modifier"
                            >
                              <Edit2 size={14} />
                            </button>
                            <button
                              onClick={() => handleDelete(article.id)}
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
              {filteredArticles.length} article(s) — page {currentPage} / {totalPages}
            </span>
            <div className="pagination-controls-premium">
              <button disabled={currentPage <= 1} onClick={() => setCurrentPage(p => p - 1)}
                className="pagination-circle-btn arrow-btn"><ChevronLeft size={16} /></button>
              <div className="pagination-numbers-container">{renderPageNumbers()}</div>
              <button disabled={currentPage >= totalPages} onClick={() => setCurrentPage(p => p + 1)}
                className="pagination-circle-btn arrow-btn"><ChevronRight size={16} /></button>
            </div>
          </div>

        </div>
      </main>

      {/* Modal Création/Modification avec IA intégrée */}
      {showModal && (
        <div className="article-modal-overlay" onClick={closeModal}>
          <div className="article-modal-card article-modal-card-lg" onClick={(e) => e.stopPropagation()}>
            <div className="article-modal-header">
              <h3>{editingArticle ? 'Modifier l\'article' : 'Nouvel article'}</h3>
              <button className="close-modal-btn" onClick={closeModal}><X size={18} /></button>
            </div>

            {formError && <div className="modal-alert error">{formError}</div>}

            <form onSubmit={handleSubmit} className="article-modal-form">
              <div className="form-row-2cols">
                <div className="form-group">
                  <label><Hash size={14} /> Code</label>
                  <input
                    type="text"
                    value={formData.code}
                    onChange={(e) => setFormData({ ...formData, code: e.target.value })}
                    placeholder="ART-001"
                    required
                    maxLength={20}
                  />
                </div>
                <div className="form-group">
                  <label><Type size={14} /> Titre</label>
                  <input
                    type="text"
                    value={formData.titre}
                    onChange={(e) => setFormData({ ...formData, titre: e.target.value })}
                    placeholder="Clause de confidentialité"
                    required
                  />
                </div>
              </div>

              <div className="contract-types-selector-wrapper">
                <div className="contract-types-selector-header">
                  <span className="contract-types-selector-title">
                    <Layers size={14} /> Types de contrat compatibles
                  </span>
                  <button
                    type="button"
                    className="contract-types-toggle-all-btn"
                    onClick={handleToggleAllContractTypes}
                  >
                    {(formData.types_contrat || []).length === TYPES_CONTRAT_OPTIONS.length
                      ? 'Désélectionner tout'
                      : 'Tous les types'}
                  </button>
                </div>
                <div className="contract-types-checkboxes-grid">
                  {TYPES_CONTRAT_OPTIONS.map(tc => {
                    const isChecked = (formData.types_contrat || []).includes(tc);
                    return (
                      <label
                        key={tc}
                        className={`contract-type-checkbox-item ${isChecked ? 'checked' : ''}`}
                      >
                        <input
                          type="checkbox"
                          checked={isChecked}
                          onChange={() => handleToggleContractType(tc)}
                        />
                        <span>{tc}</span>
                      </label>
                    );
                  })}
                </div>
                <p className="contract-types-help">
                  {(formData.types_contrat || []).length === 0
                    ? '✓ Aucun type restreint : cette clause sera utilisable pour tous les contrats (CDI, CDD, STAGE, ALTERNANCE, CIVP).'
                    : `Clause restreinte aux types : ${(formData.types_contrat || []).join(', ')}.`}
                </p>
              </div>

              <div className="form-group">
                <div className="contenu-header-with-tabs">
                  <label><AlignLeft size={14} /> Contenu par défaut</label>
                  {tryParseStructured(formData.contenu_par_defaut) && (
                    <div className="view-mode-tabs">
                      <button
                        type="button"
                        className={`view-tab-btn ${viewTab === 'preview' ? 'active' : ''}`}
                        onClick={() => setViewTab('preview')}
                      >
                        <Eye size={13} /> Aperçu visuel
                      </button>
                      <button
                        type="button"
                        className={`view-tab-btn ${viewTab === 'code' ? 'active' : ''}`}
                        onClick={() => setViewTab('code')}
                      >
                        <Code size={13} /> Éditeur JSON
                      </button>
                    </div>
                  )}
                </div>

                {tryParseStructured(formData.contenu_par_defaut) && viewTab === 'preview' ? (
                  <div className="structured-preview-box">
                    <StructuredBlocksRenderer data={tryParseStructured(formData.contenu_par_defaut)} />
                  </div>
                ) : (
                  <textarea
                    value={formData.contenu_par_defaut}
                    onChange={(e) => setFormData({ ...formData, contenu_par_defaut: e.target.value })}
                    placeholder="Rédigez le contenu de la clause ici ou utilisez l'assistant IA ci-dessous..."
                    rows={8}
                    className="article-content-textarea"
                  />
                )}
              </div>

              {/* Section IA intégrée */}
              {!editingArticle && (
                <div className="ai-inline-section">
                  <div className="ai-inline-header">
                    <div className="ai-inline-icon">
                      <Sparkles size={16} />
                    </div>
                    <div className="ai-inline-header-text">
                      <span className="ai-inline-title">Assistant IA — Clauses & Grilles structurées</span>
                      <span className="ai-inline-subtitle">Générez des paragraphes, tableaux de rémunération, grilles d'objectifs, etc.</span>
                    </div>
                  </div>

                  <div className="ai-inline-body">
                    <textarea
                      className="ai-inline-textarea"
                      value={aiPrompt}
                      onChange={(e) => setAiPrompt(e.target.value)}
                      placeholder="Ex : Rédige un article sur la rémunération avec un salaire fixe de 2000 DT et une prime variable selon objectifs sous forme de tableau."
                      rows={3}
                      disabled={aiLoading}
                      maxLength={2000}
                    />
                    <div className="ai-inline-footer">
                      <span className="ai-char-count">{aiPrompt.length}/2000</span>
                      <button
                        type="button"
                        className="ai-inline-generate-btn"
                        onClick={handleAIGenerate}
                        disabled={aiLoading || !aiPrompt.trim()}
                      >
                        {aiLoading ? (
                          <>
                            <Loader2 size={15} className="ai-spinner" />
                            Génération en cours...
                          </>
                        ) : (
                          <>
                            <Sparkles size={15} />
                            Générer avec l'IA
                          </>
                        )}
                      </button>
                    </div>

                    {aiError && (
                      <div className="ai-inline-error">
                        <div className="ai-inline-error-content">
                          <AlertTriangle size={15} />
                          <span>{aiError}</span>
                        </div>
                        <button
                          type="button"
                          className="ai-retry-btn"
                          onClick={handleAIGenerate}
                          disabled={aiLoading}
                          title="Relancer la génération"
                        >
                          <RotateCw size={12} className={aiLoading ? "ai-spinner" : ""} />
                          Réessayer
                        </button>
                      </div>
                    )}

                    {/* Carte de résultat IA structuré */}
                    {aiResult && (
                      <div className="ai-result-card">
                        <div className="ai-result-header">
                          <div className="ai-result-title-badge">
                            <CheckCircle2 size={16} className="ai-success-icon" />
                            <span className="ai-result-title">Proposition : <strong>{aiResult.title}</strong></span>
                            <span className={`article-type-badge ${aiResult.type}`}>
                              {aiResult.type === 'table' ? <Table size={12} /> : aiResult.type === 'mixed' ? <Layers size={12} /> : <FileText size={12} />}
                              {aiResult.type === 'table' ? 'Tableau' : aiResult.type === 'mixed' ? 'Mixte' : 'Paragraphe'}
                            </span>
                          </div>
                          <div className="ai-result-actions">
                            <button
                              type="button"
                              onClick={handleApplyAsStructured}
                              className="ai-action-btn primary"
                              title="Conserver les tableaux structurés pour le contrat Word"
                            >
                              Format structuré
                            </button>
                            <button
                              type="button"
                              onClick={handleApplyAsMarkdown}
                              className="ai-action-btn secondary"
                              title="Convertir en texte Markdown simple"
                            >
                              Convertir en Markdown
                            </button>
                          </div>
                        </div>
                        <div className="ai-result-preview-content">
                          <StructuredBlocksRenderer data={aiResult} />
                        </div>
                      </div>
                    )}
                  </div>

                  <div className="ai-inline-disclaimer">
                    <AlertTriangle size={12} />
                    Contenu généré par IA : relisez et vérifiez les clauses avant enregistrement et utilisation.
                  </div>
                </div>
              )}

              <div className="article-modal-actions">
                <button type="button" className="modal-cancel-btn" onClick={closeModal}>Annuler</button>
                <button type="submit" className="modal-submit-btn" disabled={formLoading}>
                  <Save size={15} />
                  {formLoading ? 'Enregistrement...' : (editingArticle ? 'Enregistrer' : 'Créer l\'article')}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
