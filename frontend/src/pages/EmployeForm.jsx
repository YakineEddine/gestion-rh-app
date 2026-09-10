import React, { useEffect, useState } from 'react';
import { useNavigate, useParams, useSearchParams, Link } from 'react-router-dom';
import {
  Eye, EyeOff, Check, X, FileText, History, User, Calendar,
  Download, ExternalLink, ChevronDown, ChevronUp, Plus, Clock,
  ArrowRight, Briefcase, Building, Mail, Phone, ShieldCheck,
  CheckCircle2, AlertCircle, Loader2
} from 'lucide-react';
import api from '../services/api';
import Sidebar from '../components/Sidebar';
import Header from '../components/Header';
import './EmployeForm.css';

const DEPARTEMENTS = [
  'Ressources Humaines', 'Informatique', 'Finance',
  'Commercial', 'Production', 'Logistique', 'Direction'
];

const STATUT_LABELS = {
  BROUILLON: 'Brouillon',
  COMMUNIQUE_EN_COURS: 'Communiqué (en cours)',
  SIGNE: 'Signé',
  ACTIF: 'Actif',
  FIN_CDD: 'Fin de CDD',
  DEMISSION_CDI: 'Démission',
  SUSPENDU: 'Suspendu',
  RESILIE: 'Résilié',
  EXPIRE: 'Expiré',
  PAS_DISCUTE: 'Pas discuté',
  INACTIF: 'Inactif (archivé)',
  'Inactif (archivé)': 'Inactif (archivé)',
  'Inactif': 'Inactif (archivé)',
  Brouillon: 'Brouillon',
  Actif: 'Actif',
  Suspendu: 'Suspendu',
  Terminé: 'Inactif (archivé)',
  Expiré: 'Expiré'
};

const getStatutBadgeClass = (statut) => {
  const map = {
    BROUILLON: 'statut-brouillon',
    COMMUNIQUE_EN_COURS: 'statut-communique',
    SIGNE: 'statut-signe',
    ACTIF: 'statut-actif',
    FIN_CDD: 'statut-fin-cdd',
    DEMISSION_CDI: 'statut-demission',
    PAS_DISCUTE: 'statut-pas-discute',
    INACTIF: 'statut-inactif',
    SUSPENDU: 'statut-suspendu',
    Brouillon: 'statut-brouillon',
    Actif: 'statut-actif',
    Suspendu: 'statut-suspendu',
    Terminé: 'statut-inactif',
    Expiré: 'statut-fin-cdd'
  };
  return map[statut] || 'statut-brouillon';
};

const formatStatut = (statut) => {
  if (!statut) return '—';
  return STATUT_LABELS[statut] || statut;
};

export default function EmployeForm() {
  const { id } = useParams();
  const isEditMode = !!id;
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();

  const tabParam = searchParams.get('tab');
  const [activeTab, setActiveTab] = useState(
    tabParam && ['compte', 'contrats', 'statuts'].includes(tabParam) ? tabParam : 'compte'
  );

  const [formData, setFormData] = useState({
    nom: '', prenom: '', email: '', mot_de_passe: '',
    telephone: '', date_naissance: '', departement: '',
    poste: '', date_embauche: '', role: 'EMPLOYE'
  });

  const [employeDetails, setEmployeDetails] = useState(null);
  const [contrats, setContrats] = useState([]);
  const [loadingContrats, setLoadingContrats] = useState(false);
  const [historiqueStatuts, setHistoriqueStatuts] = useState([]);
  const [loadingHistorique, setLoadingHistorique] = useState(false);

  const [expandedArticles, setExpandedArticles] = useState({});
  const [expandedContractHistory, setExpandedContractHistory] = useState({});
  const [downloadingContractId, setDownloadingContractId] = useState(null);

  const [errors, setErrors] = useState({});
  const [serverError, setServerError] = useState('');
  const [successMsg, setSuccessMsg] = useState('');
  const [loading, setLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);

  useEffect(() => {
    const t = searchParams.get('tab');
    if (t && ['compte', 'contrats', 'statuts'].includes(t)) {
      setActiveTab(t);
    }
  }, [searchParams]);

  const handleTabChange = (tabKey) => {
    setActiveTab(tabKey);
    setSearchParams({ tab: tabKey });
  };

  useEffect(() => {
    if (isEditMode) {
      const fetchAllData = async () => {
        try {
          setLoading(true);
          const response = await api.get(`/employes/${id}`);
          const emp = response.data;
          setEmployeDetails(emp);
          setFormData({
            nom: emp.nom || '',
            prenom: emp.prenom || '',
            email: emp.email || '',
            mot_de_passe: '',
            telephone: emp.telephone || '',
            date_naissance: emp.date_naissance || '',
            departement: emp.departement || '',
            poste: emp.poste || '',
            date_embauche: emp.date_embauche || '',
            role: emp.role || 'EMPLOYE'
          });

          // Récupération des contrats
          setLoadingContrats(true);
          try {
            const ctrRes = await api.get('/contrats', { params: { employe_id: id } });
            setContrats(ctrRes.data || []);
          } catch (err) {
            console.error("Erreur récupération contrats:", err);
          } finally {
            setLoadingContrats(false);
          }

          // Récupération de l'historique des statuts
          setLoadingHistorique(true);
          try {
            const histRes = await api.get(`/contrats/employe/${id}/historique-statuts`);
            setHistoriqueStatuts(histRes.data || []);
          } catch (err) {
            console.error("Erreur récupération historique statuts:", err);
          } finally {
            setLoadingHistorique(false);
          }

        } catch (err) {
          setServerError("Erreur lors de la récupération des données de l'employé.");
        } finally {
          setLoading(false);
        }
      };
      fetchAllData();
    }
  }, [id, isEditMode]);

  const validateForm = () => {
    const tempErrors = {};
    if (!formData.nom.trim()) tempErrors.nom = 'Le nom est obligatoire.';
    if (!formData.prenom.trim()) tempErrors.prenom = 'Le prénom est obligatoire.';
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!formData.email.trim()) {
      tempErrors.email = "L'email est obligatoire.";
    } else if (!emailRegex.test(formData.email)) {
      tempErrors.email = "L'email n'est pas valide.";
    }
    if (!isEditMode) {
      const pwd = formData.mot_de_passe || '';
      if (pwd.length < 8) {
        tempErrors.mot_de_passe = 'Le mot de passe doit contenir au moins 8 caractères.';
      } else if (!/[A-Z]/.test(pwd)) {
        tempErrors.mot_de_passe = 'Le mot de passe doit contenir au moins une majuscule.';
      } else if (!/[a-z]/.test(pwd)) {
        tempErrors.mot_de_passe = 'Le mot de passe doit contenir au moins une minuscule.';
      } else if (!/[0-9]/.test(pwd)) {
        tempErrors.mot_de_passe = 'Le mot de passe doit contenir au moins un chiffre.';
      } else if (!/[^A-Za-z0-9]/.test(pwd)) {
        tempErrors.mot_de_passe = 'Le mot de passe doit contenir au moins un caractère spécial.';
      }
    }
    if (!formData.telephone.trim()) tempErrors.telephone = 'Le téléphone est obligatoire.';
    if (!formData.departement) tempErrors.departement = 'Le département est obligatoire.';
    if (!formData.poste.trim()) tempErrors.poste = 'Le poste est obligatoire.';
    if (!formData.date_embauche) tempErrors.date_embauche = "La date d'embauche est obligatoire.";
    if (!formData.date_naissance) tempErrors.date_naissance = 'La date de naissance est obligatoire.';

    setErrors(tempErrors);
    return Object.keys(tempErrors).length === 0;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setServerError('');
    setSuccessMsg('');
    if (!validateForm()) return;

    setLoading(true);
    try {
      if (isEditMode) {
        const updateData = {
          nom: formData.nom, prenom: formData.prenom, email: formData.email,
          telephone: formData.telephone, date_naissance: formData.date_naissance || null,
          departement: formData.departement, poste: formData.poste,
          date_embauche: formData.date_embauche || null, role: formData.role
        };
        await api.put(`/employes/${id}`, updateData);
        setSuccessMsg("Informations mises à jour avec succès !");
        setTimeout(() => setSuccessMsg(''), 4000);
      } else {
        await api.post('/employes/', formData);
        navigate('/employes');
      }
    } catch (err) {
      setServerError(err.response?.data?.detail || "Une erreur serveur est survenue.");
    } finally {
      setLoading(false);
    }
  };

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
    if (errors[name]) setErrors(prev => ({ ...prev, [name]: '' }));
  };

  const handleReset = () => {
    if (isEditMode && employeDetails) {
      setFormData({
        nom: employeDetails.nom || '',
        prenom: employeDetails.prenom || '',
        email: employeDetails.email || '',
        mot_de_passe: '',
        telephone: employeDetails.telephone || '',
        date_naissance: employeDetails.date_naissance || '',
        departement: employeDetails.departement || '',
        poste: employeDetails.poste || '',
        date_embauche: employeDetails.date_embauche || '',
        role: employeDetails.role || 'EMPLOYE'
      });
    } else {
      setFormData({
        nom: '', prenom: '', email: '', mot_de_passe: '',
        telephone: '', date_naissance: '', departement: '',
        poste: '', date_embauche: '', role: 'EMPLOYE'
      });
    }
    setErrors({});
    setServerError('');
  };

  const toggleArticles = (contratId) => {
    setExpandedArticles(prev => ({ ...prev, [contratId]: !prev[contratId] }));
  };

  const toggleContractHistory = (contratId) => {
    setExpandedContractHistory(prev => ({ ...prev, [contratId]: !prev[contratId] }));
  };

  const handleGenererWord = async (contratId, ref) => {
    setDownloadingContractId(contratId);
    try {
      const res = await api.post(`/contrats/${contratId}/generer-word`, null, { responseType: 'blob' });
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
      alert('Erreur lors du téléchargement du contrat Word.');
    } finally {
      setDownloadingContractId(null);
    }
  };

  const hasActiveContract = contrats.some(c => c.statut === 'ACTIF' || c.statut === 'Actif');
  const statutRH = hasActiveContract ? 'Employé' : 'Candidat';

  return (
    <div className="app-container">
      <Sidebar />
      <main className="main-content">
        <Header
          title={isEditMode ? "Aperçu & Gestion Collaborateur" : "Ajouter un Collaborateur"}
          subtitle={isEditMode ? `Dossier complet de ${formData.prenom} ${formData.nom}` : "Remplissez les informations du nouveau collaborateur"}
        />
        <div className="content-padding">
          <div className="form-card-wrapper glass-card">
            
            <div className="form-card-header">
              <Link to="/employes" className="back-link">← Retour à la liste</Link>
            </div>

            {/* Header Profil Récapitulatif (en mode aperçu/modification) */}
            {isEditMode && (
              <div className="employe-profile-header">
                <div className="profile-header-main">
                  <div className="profile-avatar-large">
                    {formData.prenom?.[0] || ''}{formData.nom?.[0] || ''}
                  </div>
                  <div className="profile-identity">
                    <div className="profile-name-row">
                      <h2 className="profile-fullname">{formData.prenom} {formData.nom}</h2>
                      <span className={`employe-statut-badge ${statutRH === 'Employé' ? 'statut-employe' : 'statut-candidat'}`}>
                        <span className="statut-dot"></span>
                        {statutRH}
                      </span>
                      <span className="profile-role-badge">{formData.role}</span>
                    </div>
                    <div className="profile-meta-row">
                      <span className="meta-chip">
                        <ShieldCheck size={13} /> {employeDetails?.matricule || `ID #${id}`}
                      </span>
                      {formData.poste && (
                        <span className="meta-chip">
                          <Briefcase size={13} /> {formData.poste}
                        </span>
                      )}
                      {formData.departement && (
                        <span className="meta-chip">
                          <Building size={13} /> {formData.departement}
                        </span>
                      )}
                      {formData.email && (
                        <span className="meta-chip">
                          <Mail size={13} /> {formData.email}
                        </span>
                      )}
                      {formData.telephone && (
                        <span className="meta-chip">
                          <Phone size={13} /> {formData.telephone}
                        </span>
                      )}
                    </div>
                  </div>
                </div>

                {/* Onglets de navigation intégrés */}
                <div className="employe-nav-tabs">
                  <button
                    type="button"
                    className={`nav-tab-btn ${activeTab === 'compte' ? 'active' : ''}`}
                    onClick={() => handleTabChange('compte')}
                  >
                    <User size={16} />
                    <span>Informations du compte</span>
                  </button>

                  <button
                    type="button"
                    className={`nav-tab-btn ${activeTab === 'contrats' ? 'active' : ''}`}
                    onClick={() => handleTabChange('contrats')}
                  >
                    <FileText size={16} />
                    <span>Historique des contrats</span>
                    <span className="tab-counter-badge">{contrats.length}</span>
                  </button>

                  <button
                    type="button"
                    className={`nav-tab-btn ${activeTab === 'statuts' ? 'active' : ''}`}
                    onClick={() => handleTabChange('statuts')}
                  >
                    <History size={16} />
                    <span>Historique des statuts</span>
                    <span className="tab-counter-badge">{historiqueStatuts.length}</span>
                  </button>
                </div>
              </div>
            )}

            {!isEditMode && (
              <div className="form-info-banner">
                Le matricule et le mot de passe initial seront générés automatiquement.
              </div>
            )}

            {serverError && <div className="form-server-error">{serverError}</div>}
            {successMsg && <div className="form-success-banner">{successMsg}</div>}

            {/* ======================================================== */}
            {/* ONGLET 1 : INFORMATIONS DE COMPTE (FORMULAIRE)           */}
            {/* ======================================================== */}
            {(!isEditMode || activeTab === 'compte') && (
              <form onSubmit={handleSubmit} className="custom-form">
                {/* Section: Informations personnelles */}
                <h3 className="form-section-title">Informations personnelles</h3>
                <div className="form-grid form-grid-3">
                  <div className="form-field-group">
                    <label htmlFor="nom">Nom *</label>
                    <input id="nom" type="text" name="nom" value={formData.nom}
                      onChange={handleChange} className={errors.nom ? 'input-error' : ''}
                      placeholder="Dupont" disabled={loading} />
                    {errors.nom && <span className="field-error-msg">{errors.nom}</span>}
                  </div>
                  <div className="form-field-group">
                    <label htmlFor="prenom">Prénom *</label>
                    <input id="prenom" type="text" name="prenom" value={formData.prenom}
                      onChange={handleChange} className={errors.prenom ? 'input-error' : ''}
                      placeholder="Jean" disabled={loading} />
                    {errors.prenom && <span className="field-error-msg">{errors.prenom}</span>}
                  </div>
                  <div className="form-field-group">
                    <label htmlFor="date_naissance">Date de naissance *</label>
                    <input id="date_naissance" type="date" name="date_naissance"
                      value={formData.date_naissance} onChange={handleChange}
                      className={errors.date_naissance ? 'input-error' : ''} disabled={loading} />
                    {errors.date_naissance && <span className="field-error-msg">{errors.date_naissance}</span>}
                  </div>
                </div>

                {/* Section: Coordonnées */}
                <h3 className="form-section-title">Coordonnées</h3>
                <div className="form-grid">
                  <div className="form-field-group">
                    <label htmlFor="email">Email *</label>
                    <input id="email" type="email" name="email" value={formData.email}
                      onChange={handleChange} className={errors.email ? 'input-error' : ''}
                      placeholder="j.dupont@entreprise.com" disabled={loading} />
                    {errors.email && <span className="field-error-msg">{errors.email}</span>}
                  </div>
                  <div className="form-field-group">
                    <label htmlFor="telephone">Téléphone *</label>
                    <input id="telephone" type="text" name="telephone" value={formData.telephone}
                      onChange={handleChange} className={errors.telephone ? 'input-error' : ''}
                      placeholder="0612345678" disabled={loading} />
                    {errors.telephone && <span className="field-error-msg">{errors.telephone}</span>}
                  </div>
                </div>

                {/* Section: Informations professionnelles */}
                <h3 className="form-section-title">Informations professionnelles</h3>
                <div className="form-grid form-grid-3">
                  <div className="form-field-group">
                    <label htmlFor="departement">Département *</label>
                    <select id="departement" name="departement" value={formData.departement}
                      onChange={handleChange} className={errors.departement ? 'input-error' : ''}
                      disabled={loading}>
                      <option value="">Sélectionner...</option>
                      {DEPARTEMENTS.map(d => <option key={d} value={d}>{d}</option>)}
                    </select>
                    {errors.departement && <span className="field-error-msg">{errors.departement}</span>}
                  </div>
                  <div className="form-field-group">
                    <label htmlFor="poste">Poste *</label>
                    <input id="poste" type="text" name="poste" value={formData.poste}
                      onChange={handleChange} className={errors.poste ? 'input-error' : ''}
                      placeholder="Développeur Full Stack" disabled={loading} />
                    {errors.poste && <span className="field-error-msg">{errors.poste}</span>}
                  </div>
                  <div className="form-field-group">
                    <label htmlFor="date_embauche">Date d'embauche *</label>
                    <input id="date_embauche" type="date" name="date_embauche"
                      value={formData.date_embauche} onChange={handleChange}
                      className={errors.date_embauche ? 'input-error' : ''} disabled={loading} />
                    {errors.date_embauche && <span className="field-error-msg">{errors.date_embauche}</span>}
                  </div>
                </div>

                {/* Mot de passe (uniquement en création) */}
                {!isEditMode && (
                  <>
                    <h3 className="form-section-title">Sécurité</h3>
                    <div className="form-grid">
                      <div className="form-field-group">
                        <label htmlFor="mot_de_passe">Mot de passe temporaire *</label>
                        <div className="password-input-wrapper">
                          <input
                            id="mot_de_passe"
                            type={showPassword ? 'text' : 'password'}
                            name="mot_de_passe"
                            value={formData.mot_de_passe}
                            onChange={handleChange}
                            className={errors.mot_de_passe ? 'input-error' : ''}
                            placeholder="Min. 8 caractères, majuscule, minuscule, chiffre, spécial"
                            disabled={loading}
                          />
                          <button
                            type="button"
                            className="password-toggle-btn"
                            onClick={() => setShowPassword((v) => !v)}
                            tabIndex={-1}
                            aria-label={showPassword ? 'Masquer le mot de passe' : 'Afficher le mot de passe'}
                          >
                            {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
                          </button>
                        </div>
                        <div className="password-rules small">
                          {[
                            { label: '8 caractères minimum', test: (v) => v.length >= 8 },
                            { label: 'Une majuscule', test: (v) => /[A-Z]/.test(v) },
                            { label: 'Une minuscule', test: (v) => /[a-z]/.test(v) },
                            { label: 'Un chiffre', test: (v) => /[0-9]/.test(v) },
                            { label: 'Un caractère spécial', test: (v) => /[^A-Za-z0-9]/.test(v) },
                          ].map((rule, idx) => {
                            const valid = rule.test(formData.mot_de_passe || '');
                            return (
                              <div key={idx} className={`password-rule ${valid ? 'valid' : ''}`}>
                                {valid ? <Check size={12} /> : <X size={12} />}
                                <span>{rule.label}</span>
                              </div>
                            );
                          })}
                        </div>
                        {errors.mot_de_passe && <span className="field-error-msg">{errors.mot_de_passe}</span>}
                      </div>
                    </div>
                  </>
                )}

                <div className="form-submit-row">
                  <button type="button" className="cancel-btn" onClick={handleReset}>Réinitialiser</button>
                  <button type="submit" className="save-btn" disabled={loading}>
                    {loading ? 'Sauvegarde...' : isEditMode ? 'Enregistrer les modifications' : "Créer l'employé"}
                  </button>
                </div>
              </form>
            )}

            {/* ======================================================== */}
            {/* ONGLET 2 : HISTORIQUE DES CONTRATS ET LEURS DÉTAILS      */}
            {/* ======================================================== */}
            {isEditMode && activeTab === 'contrats' && (
              <div className="contracts-tab-content">
                <div className="tab-section-header">
                  <div>
                    <h3 className="tab-title">Historique des contrats de {formData.prenom} {formData.nom}</h3>
                    <p className="tab-subtitle">Consultez l'ensemble des contrats, les clauses contractuelles rattachées et téléchargez les documents Word officiels.</p>
                  </div>
                  <Link to="/contrats/nouveau" className="btn-create-contract-quick">
                    <Plus size={15} />
                    <span>Nouveau contrat</span>
                  </Link>
                </div>

                {loadingContrats ? (
                  <div className="loading-state-container">
                    <Loader2 size={28} className="spin-icon" />
                    <span>Chargement des contrats...</span>
                  </div>
                ) : contrats.length === 0 ? (
                  <div className="empty-state-contracts">
                    <div className="empty-icon-circle">
                      <FileText size={32} />
                    </div>
                    <h4>Aucun contrat enregistré</h4>
                    <p>Cet employé ne possède actuellement aucun contrat dans la base de données.</p>
                    <Link to="/contrats/nouveau" className="btn-create-contract-quick">
                      <Plus size={15} />
                      <span>Rédiger son premier contrat</span>
                    </Link>
                  </div>
                ) : (
                  <div className="contracts-cards-list">
                    {contrats.map((c) => {
                      const specificLogs = historiqueStatuts.filter(h => h.contrat_id === c.id);
                      const isArticlesOpen = !!expandedArticles[c.id];
                      const isHistoryOpen = !!expandedContractHistory[c.id];

                      return (
                        <div key={c.id} className="contract-detail-card">
                          {/* Card Top Bar */}
                          <div className="contract-card-header">
                            <div className="contract-ref-block">
                              <span className="contract-ref-code">{c.reference}</span>
                              <span className={`contract-type-pill pill-${c.type_contrat?.toLowerCase()}`}>
                                {c.type_contrat}
                              </span>
                              <span className={`contrat-statut-badge ${getStatutBadgeClass(c.statut)}`}>
                                {formatStatut(c.statut)}
                              </span>
                            </div>

                            <div className="contract-header-actions">
                              <button
                                type="button"
                                className="contract-action-btn btn-word"
                                onClick={() => handleGenererWord(c.id, c.reference)}
                                disabled={downloadingContractId === c.id}
                                title="Télécharger le contrat Word (.docx)"
                              >
                                {downloadingContractId === c.id ? (
                                  <Loader2 size={14} className="spin-icon" />
                                ) : (
                                  <Download size={14} />
                                )}
                                <span>Word (.docx)</span>
                              </button>

                              <Link
                                to={`/contrats/modifier/${c.id}`}
                                className="contract-action-btn btn-manage"
                                title="Gérer ou modifier ce contrat"
                              >
                                <ExternalLink size={14} />
                                <span>Gérer</span>
                              </Link>
                            </div>
                          </div>

                          {/* Card Key Metrics Grid */}
                          <div className="contract-metrics-grid">
                            <div className="metric-box">
                              <span className="metric-label">Date de début</span>
                              <span className="metric-value">
                                <Calendar size={13} />
                                {c.date_debut ? new Date(c.date_debut).toLocaleDateString('fr-FR') : '—'}
                              </span>
                            </div>

                            <div className="metric-box">
                              <span className="metric-label">Date de fin</span>
                              <span className="metric-value">
                                <Calendar size={13} />
                                {c.date_fin ? new Date(c.date_fin).toLocaleDateString('fr-FR') : 'Indéterminée (CDI)'}
                              </span>
                            </div>

                            <div className="metric-box">
                              <span className="metric-label">Rémunération brute</span>
                              <span className="metric-value salary-highlight">
                                {c.salaire_mensuel != null ? `${Number(c.salaire_mensuel).toLocaleString('fr-FR')} DT` : '—'}
                              </span>
                            </div>

                            <div className="metric-box">
                              <span className="metric-label">Créé le</span>
                              <span className="metric-value">
                                <Clock size={13} />
                                {c.date_creation ? new Date(c.date_creation).toLocaleDateString('fr-FR') : '—'}
                              </span>
                            </div>
                          </div>

                          {/* Accordéons / Détails supplémentaires */}
                          <div className="contract-accordions-row">
                            {/* Accordéon Articles */}
                            <button
                              type="button"
                              className={`accordion-trigger-btn ${isArticlesOpen ? 'active' : ''}`}
                              onClick={() => toggleArticles(c.id)}
                            >
                              <div className="trigger-label">
                                <FileText size={15} />
                                <span>Articles contractuels ({c.articles?.length || 0})</span>
                              </div>
                              {isArticlesOpen ? <ChevronUp size={15} /> : <ChevronDown size={15} />}
                            </button>

                            {/* Accordéon Historique des statuts de ce contrat */}
                            <button
                              type="button"
                              className={`accordion-trigger-btn ${isHistoryOpen ? 'active' : ''}`}
                              onClick={() => toggleContractHistory(c.id)}
                            >
                              <div className="trigger-label">
                                <History size={15} />
                                <span>Historique des statuts ({specificLogs.length})</span>
                              </div>
                              {isHistoryOpen ? <ChevronUp size={15} /> : <ChevronDown size={15} />}
                            </button>
                          </div>

                          {/* Contenu Déplié : Articles */}
                          {isArticlesOpen && (
                            <div className="articles-accordion-content">
                              {(!c.articles || c.articles.length === 0) ? (
                                <p className="empty-subtext">Aucun article spécifique rattaché à ce contrat.</p>
                              ) : (
                                <div className="articles-sublist">
                                  {c.articles.map((art, idx) => (
                                    <div key={art.id || idx} className="article-mini-card">
                                      <div className="article-mini-header">
                                        <span className="article-number">Article {idx + 1}</span>
                                        <h5 className="article-mini-title">{art.titre}</h5>
                                        {art.est_obligatoire && (
                                          <span className="badge-mandatory">Obligatoire</span>
                                        )}
                                      </div>
                                      <div className="article-mini-body">
                                        {art.contenu_par_defaut || 'Clause contractuelle standard.'}
                                      </div>
                                    </div>
                                  ))}
                                </div>
                              )}
                            </div>
                          )}

                          {/* Contenu Déplié : Historique des statuts de ce contrat */}
                          {isHistoryOpen && (
                            <div className="contract-timeline-subcontent">
                              {specificLogs.length === 0 ? (
                                <p className="empty-subtext">Aucune transition de statut enregistrée pour ce contrat.</p>
                              ) : (
                                <div className="subtimeline-list">
                                  {specificLogs.map((log) => (
                                    <div key={log.id} className="subtimeline-item">
                                      <div className="subtimeline-dot"></div>
                                      <div className="subtimeline-body">
                                        <div className="subtimeline-header">
                                          <div className="subtimeline-statuts">
                                            {log.ancien_statut ? (
                                              <>
                                                <span className={`contrat-statut-badge ${getStatutBadgeClass(log.ancien_statut)}`}>
                                                  {formatStatut(log.ancien_statut)}
                                                </span>
                                                <ArrowRight size={13} className="transition-arrow-icon" />
                                              </>
                                            ) : (
                                              <>
                                                <span className="contrat-statut-badge statut-initial">Création</span>
                                                <ArrowRight size={13} className="transition-arrow-icon" />
                                              </>
                                            )}
                                            <span className={`contrat-statut-badge ${getStatutBadgeClass(log.nouveau_statut)}`}>
                                              {formatStatut(log.nouveau_statut)}
                                            </span>
                                          </div>
                                          <span className="subtimeline-date">
                                            {new Date(log.date_action).toLocaleString('fr-FR', {
                                              day: '2-digit', month: '2-digit', year: 'numeric',
                                              hour: '2-digit', minute: '2-digit'
                                            })}
                                          </span>
                                        </div>
                                        <div className="subtimeline-meta">
                                          <span>Auteur : <strong>{log.utilisateur_nom || 'Système'}</strong></span>
                                          {log.description && <span className="subtimeline-desc">({log.description})</span>}
                                        </div>
                                      </div>
                                    </div>
                                  ))}
                                </div>
                              )}
                            </div>
                          )}
                        </div>
                      );
                    })}
                  </div>
                )}
              </div>
            )}

            {/* ======================================================== */}
            {/* ONGLET 3 : HISTORIQUE DE MODIFICATION DES STATUTS        */}
            {/* ======================================================== */}
            {isEditMode && activeTab === 'statuts' && (
              <div className="statuts-tab-content">
                <div className="tab-section-header">
                  <div>
                    <h3 className="tab-title">Journal d'audit des modifications de statuts</h3>
                    <p className="tab-subtitle">Traçabilité complète des passages de statuts sur l'ensemble des contrats de {formData.prenom} {formData.nom}.</p>
                  </div>
                </div>

                {loadingHistorique ? (
                  <div className="loading-state-container">
                    <Loader2 size={28} className="spin-icon" />
                    <span>Chargement de l'historique des statuts...</span>
                  </div>
                ) : historiqueStatuts.length === 0 ? (
                  <div className="empty-state-contracts">
                    <div className="empty-icon-circle">
                      <History size={32} />
                    </div>
                    <h4>Aucune modification de statut enregistrée</h4>
                    <p>Aucun événement d'audit de statut n'a encore été enregistré pour les contrats de cet employé.</p>
                  </div>
                ) : (
                  <div className="global-status-timeline">
                    {historiqueStatuts.map((item, index) => (
                      <div key={item.id || index} className="timeline-entry-row">
                        <div className="timeline-axis">
                          <div className="timeline-axis-node">
                            <CheckCircle2 size={14} />
                          </div>
                          {index < historiqueStatuts.length - 1 && <div className="timeline-axis-line"></div>}
                        </div>

                        <div className="timeline-card glass-card">
                          <div className="timeline-card-header">
                            <div className="timeline-contrat-ref">
                              <FileText size={14} className="icon-prefix" />
                              <strong>{item.contrat_reference || `Contrat #${item.contrat_id}`}</strong>
                            </div>
                            <div className="timeline-timestamp">
                              <Clock size={13} className="icon-prefix" />
                              <span>
                                {new Date(item.date_action).toLocaleString('fr-FR', {
                                  day: '2-digit', month: '2-digit', year: 'numeric',
                                  hour: '2-digit', minute: '2-digit', second: '2-digit'
                                })}
                              </span>
                            </div>
                          </div>

                          <div className="timeline-transition-display">
                            {item.ancien_statut ? (
                              <div className="statut-flow-box">
                                <span className="statut-flow-label">Statut précédent :</span>
                                <span className={`contrat-statut-badge ${getStatutBadgeClass(item.ancien_statut)}`}>
                                  {formatStatut(item.ancien_statut)}
                                </span>
                              </div>
                            ) : (
                              <div className="statut-flow-box">
                                <span className="statut-flow-label">Étape :</span>
                                <span className="contrat-statut-badge statut-initial">Création du contrat</span>
                              </div>
                            )}

                            <div className="flow-arrow-container">
                              <ArrowRight size={18} className="flow-arrow" />
                            </div>

                            <div className="statut-flow-box">
                              <span className="statut-flow-label">Nouveau statut :</span>
                              <span className={`contrat-statut-badge ${getStatutBadgeClass(item.nouveau_statut)}`}>
                                {formatStatut(item.nouveau_statut)}
                              </span>
                            </div>
                          </div>

                          <div className="timeline-card-footer">
                            <div className="timeline-author-info">
                              <User size={13} className="author-icon" />
                              <span>Modifié par : <strong>{item.utilisateur_nom || 'Système'}</strong></span>
                            </div>
                            {item.description && (
                              <span className="timeline-desc-pill">{item.description}</span>
                            )}
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}

          </div>
        </div>
      </main>
    </div>
  );
}
