import React, { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import {
  User, Calendar, DollarSign, BookOpen,
  ChevronRight, ChevronLeft, Check, Search,
  AlertCircle, CheckCircle2, Loader2
} from 'lucide-react';
import Sidebar from '../components/Sidebar';
import Header from '../components/Header';
import api from '../services/api';
import './ContratForm.css';

const ALLOWED_STATUS_TRANSITIONS = {
  'Brouillon': ['Brouillon', 'Actif'],
  'Actif':     ['Actif', 'Suspendu', 'Terminé'],
  'Suspendu':  ['Suspendu', 'Actif', 'Terminé'],
  'Terminé':   ['Terminé'],
  'Expiré':    ['Expiré'],
};

const TYPES_CONTRAT = ['CDI', 'CDD', 'STAGE', 'ALTERNANCE'];

const STEPS = [
  { id: 1, label: 'Employé',      icon: User },
  { id: 2, label: 'Informations', icon: Calendar },
  { id: 3, label: 'Articles',     icon: BookOpen },
];

export default function ContratForm() {
  const navigate = useNavigate();
  const { id } = useParams();
  const isEdit = !!id;

  const [step, setStep] = useState(1);
  const [submitting, setSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState('');

  // Step 1 — Employé
  const [employes, setEmployes] = useState([]);
  const [loadingEmployes, setLoadingEmployes] = useState(false);
  const [searchEmploye, setSearchEmploye] = useState('');
  const [selectedEmploye, setSelectedEmploye] = useState(null);

  // Step 2 — Informations
  const [typeContrat, setTypeContrat]     = useState('');
  const [dateDebut, setDateDebut]         = useState('');
  const [dateFin, setDateFin]             = useState('');
  const [salaire, setSalaire]             = useState('');
  const [statut, setStatut]               = useState('Brouillon');
  const [initialStatut, setInitialStatut] = useState('Brouillon');

  // Step 3 — Articles
  const [articles, setArticles]           = useState([]);
  const [loadingArticles, setLoadingArticles] = useState(false);
  const [selectedArticleIds, setSelectedArticleIds] = useState([]);
  const [searchArticle, setSearchArticle] = useState('');

  // ─── Chargement initial ───────────────────────────────────────────────────

  useEffect(() => {
    loadEmployes();
    loadArticles();
    if (isEdit) loadContrat();
  }, []);

  const loadEmployes = async () => {
    setLoadingEmployes(true);
    try {
      const res = await api.get('/employes/');
      setEmployes(res.data);
    } catch {
      // silencieux
    } finally {
      setLoadingEmployes(false);
    }
  };

  const loadArticles = async () => {
    setLoadingArticles(true);
    try {
      const res = await api.get('/articles/');
      setArticles(res.data.filter(a => a.est_actif));
    } catch {
      // silencieux
    } finally {
      setLoadingArticles(false);
    }
  };

  const loadContrat = async () => {
    try {
      const res = await api.get(`/contrats/${id}`);
      const c = res.data;
      setTypeContrat(c.type_contrat || '');
      setDateDebut(c.date_debut || '');
      setDateFin(c.date_fin || '');
      setSalaire(String(c.salaire_mensuel || ''));
      setStatut(c.statut || 'Brouillon');
      setInitialStatut(c.statut || 'Brouillon');
      setSelectedArticleIds((c.articles || []).map(a => a.id));
      if (c.employe) setSelectedEmploye(c.employe);
    } catch {
      setSubmitError('Impossible de charger le contrat.');
    }
  };

  // Changer de type de contrat : reinitialiser la date de fin si on passe a CDI
  const handleTypeContratChange = (value) => {
    setTypeContrat(value);
    if (value === 'CDI') {
      setDateFin('');
    }
  };

  // ─── Navigation entre étapes ─────────────────────────────────────────────

  const validateStep = (s) => {
    if (s === 1) return !!selectedEmploye;
    if (s === 2) {
      if (!typeContrat) return false;
      if (dateDebut.trim() === '' || salaire.trim() === '' || Number(salaire) <= 0) return false;
      if (typeContrat !== 'CDI') {
        if (!dateFin) return false;
        if (dateFin <= dateDebut) return false;
      }
      return true;
    }
    return true;
  };

  const goNext = () => {
    if (validateStep(step)) setStep(s => s + 1);
  };

  const goPrev = () => setStep(s => s - 1);

  // ─── Toggle article ──────────────────────────────────────────────────────

  const toggleArticle = (artId) => {
    setSelectedArticleIds(prev =>
      prev.includes(artId) ? prev.filter(x => x !== artId) : [...prev, artId]
    );
  };

  // ─── Soumission ──────────────────────────────────────────────────────────

  const handleSubmit = async () => {
    setSubmitError('');
    setSubmitting(true);
    try {
      if (isEdit) {
        const payload = {
          type_contrat:    typeContrat,
          date_debut:      dateDebut || undefined,
          salaire_mensuel: Number(salaire),
          statut,
          article_ids:     selectedArticleIds,
        };
        // Un CDI n'a jamais de date de fin : on ne l'envoie pas du tout.
        if (typeContrat !== 'CDI') {
          payload.date_fin = dateFin;
        } else {
          payload.date_fin = null;
        }
        await api.put(`/contrats/${id}`, payload);
      } else {
        const payload = {
          employe_id:      selectedEmploye.id,
          type_contrat:    typeContrat,
          date_debut:      dateDebut,
          salaire_mensuel: Number(salaire),
          article_ids:     selectedArticleIds,
        };
        // Ne pas envoyer de date_fin lors de la creation d'un CDI.
        if (typeContrat !== 'CDI') {
          payload.date_fin = dateFin;
        }
        await api.post('/contrats/', payload);
      }
      navigate('/contrats');
    } catch (err) {
      setSubmitError(err.response?.data?.detail || "Erreur lors de l'enregistrement.");
    } finally {
      setSubmitting(false);
    }
  };

  // ─── Filtres locaux ───────────────────────────────────────────────────────

  const filteredEmployes = employes.filter(e =>
    `${e.nom} ${e.prenom} ${e.matricule} ${e.poste || ''} ${e.departement || ''}`
      .toLowerCase().includes(searchEmploye.toLowerCase())
  );

  const filteredArticles = articles.filter(a =>
    `${a.code} ${a.titre} ${a.contenu_par_defaut || ''}`
      .toLowerCase().includes(searchArticle.toLowerCase())
  );

  // ─── Render ───────────────────────────────────────────────────────────────

  return (
    <div className="app-container">
      <Sidebar />
      <main className="main-content">
        <Header
          title={isEdit ? 'Modifier le contrat' : 'Nouveau contrat'}
          subtitle={isEdit
            ? 'Modifiez les informations et les articles associés.'
            : 'Créez un contrat en 3 étapes simples.'}
        />
        <div className="content-padding">

          {/* Stepper */}
          <div className="cf-stepper glass-card">
            {STEPS.map((s, i) => {
              const Icon = s.icon;
              const isDone    = step > s.id;
              const isCurrent = step === s.id;
              return (
                <React.Fragment key={s.id}>
                  <div className={`cf-step ${isCurrent ? 'current' : ''} ${isDone ? 'done' : ''}`}>
                    <div className="cf-step-circle">
                      {isDone ? <Check size={16} /> : <Icon size={16} />}
                    </div>
                    <span className="cf-step-label">{s.label}</span>
                  </div>
                  {i < STEPS.length - 1 && (
                    <div className={`cf-step-connector ${step > s.id ? 'done' : ''}`} />
                  )}
                </React.Fragment>
              );
            })}
          </div>

          {/* Contenu de l'étape */}
          <div className="cf-card glass-card">

            {/* ─── ÉTAPE 1 : Employé ─────────────────────────────── */}
            {step === 1 && (
              <div className="cf-step-content">
                <h3 className="cf-step-title">
                  <User size={20} />
                  Sélectionner un employé
                </h3>

                {isEdit && selectedEmploye ? (
                  <div className="cf-readonly-employe">
                    <div className="cf-employe-avatar">
                      {(selectedEmploye.nom?.[0] || '') + (selectedEmploye.prenom?.[0] || '')}
                    </div>
                    <div className="cf-employe-info">
                      <span className="cf-employe-name">{selectedEmploye.nom} {selectedEmploye.prenom}</span>
                      <span className="cf-employe-meta">{selectedEmploye.matricule} · {selectedEmploye.poste || 'Poste non défini'}</span>
                    </div>
                    <span className="cf-readonly-badge">Employé associé</span>
                  </div>
                ) : (
                  <>
                    {/* Employé sélectionné */}
                    {selectedEmploye && (
                      <div className="cf-selected-employe">
                        <CheckCircle2 size={18} className="cf-selected-icon" />
                        <div className="cf-employe-avatar sm">
                          {(selectedEmploye.nom?.[0] || '') + (selectedEmploye.prenom?.[0] || '')}
                        </div>
                        <div>
                          <span className="cf-employe-name">{selectedEmploye.nom} {selectedEmploye.prenom}</span>
                          <span className="cf-employe-meta"> — {selectedEmploye.matricule}</span>
                        </div>
                        <button className="cf-clear-btn" onClick={() => setSelectedEmploye(null)}>
                          Changer
                        </button>
                      </div>
                    )}

                    {/* Recherche employés */}
                    <div className="cf-search-wrapper">
                      <Search size={15} className="cf-search-icon" />
                      <input
                        type="text"
                        placeholder="Rechercher par nom, prénom, matricule..."
                        value={searchEmploye}
                        onChange={e => setSearchEmploye(e.target.value)}
                        className="cf-search-input"
                      />
                    </div>

                    {loadingEmployes ? (
                      <div className="cf-loading"><Loader2 size={20} className="cf-spin" /> Chargement...</div>
                    ) : (
                      <div className="cf-employe-list">
                        {filteredEmployes.length === 0 ? (
                          <p className="cf-empty-msg">Aucun employé trouvé.</p>
                        ) : filteredEmployes.map(e => (
                          <div
                            key={e.id}
                            className={`cf-employe-row ${selectedEmploye?.id === e.id ? 'selected' : ''}`}
                            onClick={() => setSelectedEmploye(e)}
                          >
                            <div className="cf-employe-avatar sm">
                              {(e.nom?.[0] || '') + (e.prenom?.[0] || '')}
                            </div>
                            <div className="cf-employe-row-info">
                              <span className="cf-employe-name">{e.nom} {e.prenom}</span>
                              <span className="cf-employe-meta">
                                {e.matricule}
                                {e.poste ? ` · ${e.poste}` : ''}
                                {e.departement ? ` · ${e.departement}` : ''}
                              </span>
                            </div>
                            {selectedEmploye?.id === e.id && (
                              <CheckCircle2 size={18} className="cf-selected-icon" />
                            )}
                          </div>
                        ))}
                      </div>
                    )}

                    {!validateStep(1) && (
                      <p className="cf-hint">
                        <AlertCircle size={14} /> Sélectionnez un employé pour continuer.
                      </p>
                    )}
                  </>
                )}
              </div>
            )}

            {/* ─── ÉTAPE 2 : Informations ────────────────────────── */}
            {step === 2 && (
              <div className="cf-step-content">
                <h3 className="cf-step-title">
                  <Calendar size={20} />
                  Informations contractuelles
                </h3>

                <div className="cf-form-grid">
                  <div className="cf-form-group">
                    <label className="cf-label">Type de contrat <span className="cf-required">*</span></label>
                    <select
                      value={typeContrat}
                      onChange={e => handleTypeContratChange(e.target.value)}
                      className="cf-input"
                    >
                      <option value="">Sélectionnez un type</option>
                      {TYPES_CONTRAT.map(t => <option key={t} value={t}>{t}</option>)}
                    </select>
                  </div>

                  <div className="cf-form-group">
                    <label className="cf-label">Date de début <span className="cf-required">*</span></label>
                    <input
                      type="date"
                      value={dateDebut}
                      onChange={e => setDateDebut(e.target.value)}
                      className="cf-input"
                    />
                  </div>

                  {typeContrat !== 'CDI' && (
                    <div className="cf-form-group">
                      <label className="cf-label">Date de fin <span className="cf-required">*</span></label>
                      <input
                        type="date"
                        value={dateFin}
                        onChange={e => setDateFin(e.target.value)}
                        className="cf-input"
                        min={dateDebut || undefined}
                      />
                    </div>
                  )}

                  {typeContrat === 'CDI' && (
                    <div className="cf-form-group">
                      <label className="cf-label">Date de fin</label>
                      <div className="cf-cdi-indefini">
                        Contrat à durée indéterminée — aucune date de fin
                      </div>
                    </div>
                  )}

                  <div className="cf-form-group">
                    <label className="cf-label">
                      <DollarSign size={14} />
                      Salaire mensuel (DT) <span className="cf-required">*</span>
                    </label>
                    <input
                      type="number"
                      value={salaire}
                      onChange={e => setSalaire(e.target.value)}
                      placeholder="Ex : 1200"
                      min="1"
                      className="cf-input"
                    />
                  </div>

                  {isEdit && (() => {
                    const availableStatuts = ALLOWED_STATUS_TRANSITIONS[initialStatut] || [statut];
                    const isFinal = availableStatuts.length <= 1;
                    return (
                      <div className="cf-form-group">
                        <label className="cf-label">Statut du contrat</label>
                        <select
                          value={statut}
                          onChange={e => setStatut(e.target.value)}
                          className="cf-input"
                          disabled={isFinal}
                        >
                          {availableStatuts.map(s => <option key={s} value={s}>{s}</option>)}
                        </select>
                        {isFinal && (
                          <span style={{ fontSize: '12px', color: 'var(--text-muted)', marginTop: '4px', display: 'block' }}>
                            Statut final — aucune modification ultérieure possible.
                          </span>
                        )}
                      </div>
                    );
                  })()}
                </div>

                {!validateStep(2) && (
                  <p className="cf-hint">
                    <AlertCircle size={14} />
                    {!typeContrat
                      ? ' Le type de contrat est obligatoire.'
                      : typeContrat !== 'CDI' && (!dateFin || dateFin <= dateDebut)
                        ? ' La date de fin est obligatoire et doit être postérieure à la date de début.'
                        : ' La date de début et le salaire sont obligatoires.'}
                  </p>
                )}
              </div>
            )}

            {/* ─── ÉTAPE 3 : Articles ────────────────────────────── */}
            {step === 3 && (
              <div className="cf-step-content">
                <h3 className="cf-step-title">
                  <BookOpen size={20} />
                  Articles à inclure
                  <span className="cf-articles-count">
                    {selectedArticleIds.length} sélectionné(s)
                  </span>
                </h3>

                <div className="cf-search-wrapper">
                  <Search size={15} className="cf-search-icon" />
                  <input
                    type="text"
                    placeholder="Rechercher un article..."
                    value={searchArticle}
                    onChange={e => setSearchArticle(e.target.value)}
                    className="cf-search-input"
                  />
                </div>

                {loadingArticles ? (
                  <div className="cf-loading"><Loader2 size={20} className="cf-spin" /> Chargement...</div>
                ) : filteredArticles.length === 0 ? (
                  <p className="cf-empty-msg">Aucun article actif trouvé.</p>
                ) : (
                  <div className="cf-articles-list">
                    {filteredArticles.map(a => {
                      const isSelected = selectedArticleIds.includes(a.id);
                      return (
                        <div
                          key={a.id}
                          className={`cf-article-row ${isSelected ? 'selected' : ''}`}
                          onClick={() => toggleArticle(a.id)}
                        >
                          <div className={`cf-article-checkbox ${isSelected ? 'checked' : ''}`}>
                            {isSelected && <Check size={12} />}
                          </div>
                          <div className="cf-article-info">
                            <div className="cf-article-header-row">
                              <span className="cf-article-code">{a.code}</span>
                              <span className="cf-article-titre">{a.titre}</span>
                            </div>
                            {a.contenu_par_defaut && (
                              <p className="cf-article-preview">
                                {a.contenu_par_defaut.substring(0, 100)}
                                {a.contenu_par_defaut.length > 100 ? '...' : ''}
                              </p>
                            )}
                          </div>
                        </div>
                      );
                    })}
                  </div>
                )}

                <p className="cf-articles-hint">
                  Les articles sélectionnés seront inclus dans le document Word du contrat.
                  La sélection est optionnelle.
                </p>
              </div>
            )}

            {/* ─── Erreur de soumission ─────────────────────────── */}
            {submitError && (
              <div className="cf-submit-error">
                <AlertCircle size={16} />
                {submitError}
              </div>
            )}

            {/* ─── Navigation ───────────────────────────────────── */}
            <div className="cf-nav-bar">
              <button
                className="cf-nav-btn secondary"
                onClick={() => step === 1 ? navigate('/contrats') : goPrev()}
              >
                <ChevronLeft size={16} />
                {step === 1 ? 'Annuler' : 'Précédent'}
              </button>

              <div className="cf-step-indicator">
                Étape {step} / {STEPS.length}
              </div>

              {step < STEPS.length ? (
                <button
                  className="cf-nav-btn primary"
                  onClick={goNext}
                  disabled={!validateStep(step)}
                >
                  Suivant
                  <ChevronRight size={16} />
                </button>
              ) : (
                <button
                  className="cf-nav-btn primary"
                  onClick={handleSubmit}
                  disabled={submitting || !validateStep(1) || !validateStep(2)}
                >
                  {submitting ? (
                    <><Loader2 size={15} className="cf-spin" /> Enregistrement...</>
                  ) : (
                    <><Check size={15} /> {isEdit ? 'Enregistrer' : 'Créer le contrat'}</>
                  )}
                </button>
              )}
            </div>

          </div>
        </div>
      </main>
    </div>
  );
}
