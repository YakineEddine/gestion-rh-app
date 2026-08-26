import React, { useEffect, useState } from 'react';
import { useNavigate, useParams, Link } from 'react-router-dom';
import { Eye, EyeOff, Check, X } from 'lucide-react';
import api from '../services/api';
import Sidebar from '../components/Sidebar';
import Header from '../components/Header';
import './EmployeForm.css';

const DEPARTEMENTS = [
  'Ressources Humaines', 'Informatique', 'Finance',
  'Commercial', 'Production', 'Logistique', 'Direction'
];

export default function EmployeForm() {
  const { id } = useParams();
  const isEditMode = !!id;
  const navigate = useNavigate();

  const [formData, setFormData] = useState({
    nom: '', prenom: '', email: '', mot_de_passe: '',
    telephone: '', date_naissance: '', departement: '',
    poste: '', date_embauche: '', role: 'EMPLOYE'
  });

  const [errors, setErrors] = useState({});
  const [serverError, setServerError] = useState('');
  const [loading, setLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);

  useEffect(() => {
    if (isEditMode) {
      const fetchEmploye = async () => {
        try {
          setLoading(true);
          const response = await api.get(`/employes/${id}`);
          const emp = response.data;
          setFormData({
            nom: emp.nom, prenom: emp.prenom, email: emp.email,
            mot_de_passe: '',
            telephone: emp.telephone || '',
            date_naissance: emp.date_naissance || '',
            departement: emp.departement || '',
            poste: emp.poste || '',
            date_embauche: emp.date_embauche || '',
            role: emp.role
          });
        } catch (err) {
          setServerError("Erreur lors de la recuperation des donnees.");
        } finally {
          setLoading(false);
        }
      };
      fetchEmploye();
    }
  }, [id, isEditMode]);

  const validateForm = () => {
    const tempErrors = {};
    if (!formData.nom.trim()) tempErrors.nom = 'Le nom est obligatoire.';
    if (!formData.prenom.trim()) tempErrors.prenom = 'Le prenom est obligatoire.';
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!formData.email.trim()) {
      tempErrors.email = "L'email est obligatoire.";
    } else if (!emailRegex.test(formData.email)) {
      tempErrors.email = "L'email n'est pas valide.";
    }
    if (!isEditMode) {
      const pwd = formData.mot_de_passe || '';
      if (pwd.length < 8) {
        tempErrors.mot_de_passe = 'Le mot de passe doit contenir au moins 8 caracteres.';
      } else if (!/[A-Z]/.test(pwd)) {
        tempErrors.mot_de_passe = 'Le mot de passe doit contenir au moins une majuscule.';
      } else if (!/[a-z]/.test(pwd)) {
        tempErrors.mot_de_passe = 'Le mot de passe doit contenir au moins une minuscule.';
      } else if (!/[0-9]/.test(pwd)) {
        tempErrors.mot_de_passe = 'Le mot de passe doit contenir au moins un chiffre.';
      } else if (!/[^A-Za-z0-9]/.test(pwd)) {
        tempErrors.mot_de_passe = 'Le mot de passe doit contenir au moins un caractere special.';
      }
    }
    if (!formData.telephone.trim()) tempErrors.telephone = 'Le telephone est obligatoire.';
    if (!formData.departement) tempErrors.departement = 'Le departement est obligatoire.';
    if (!formData.poste.trim()) tempErrors.poste = 'Le poste est obligatoire.';
    if (!formData.date_embauche) tempErrors.date_embauche = "La date d'embauche est obligatoire.";
    if (!formData.date_naissance) tempErrors.date_naissance = 'La date de naissance est obligatoire.';

    setErrors(tempErrors);
    return Object.keys(tempErrors).length === 0;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setServerError('');
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
      } else {
        await api.post('/employes/', formData);
      }
      navigate('/employes');
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
    setFormData({
      nom: '', prenom: '', email: '', mot_de_passe: '',
      telephone: '', date_naissance: '', departement: '',
      poste: '', date_embauche: '', role: 'EMPLOYE'
    });
    setErrors({});
    setServerError('');
  };

  return (
    <div className="app-container">
      <Sidebar />
      <main className="main-content">
        <Header
          title={isEditMode ? "Modifier un Employe" : "Ajouter un Employe"}
          subtitle={isEditMode ? `Modification de ${formData.prenom} ${formData.nom}` : "Remplissez les informations du collaborateur"}
        />
        <div className="content-padding">
          <div className="form-card-wrapper glass-card">
            <div className="form-card-header">
              <Link to="/employes" className="back-link">Retour a la liste</Link>
            </div>

            {!isEditMode && (
              <div className="form-info-banner">
                Le matricule et le mot de passe initial seront generes automatiquement.
              </div>
            )}

            {serverError && <div className="form-server-error">{serverError}</div>}

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
                  <label htmlFor="prenom">Prenom *</label>
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

              {/* Section: Coordonnees */}
              <h3 className="form-section-title">Coordonnees</h3>
              <div className="form-grid">
                <div className="form-field-group">
                  <label htmlFor="email">Email *</label>
                  <input id="email" type="email" name="email" value={formData.email}
                    onChange={handleChange} className={errors.email ? 'input-error' : ''}
                    placeholder="j.dupont@entreprise.com" disabled={loading} />
                  {errors.email && <span className="field-error-msg">{errors.email}</span>}
                </div>
                <div className="form-field-group">
                  <label htmlFor="telephone">Telephone *</label>
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
                  <label htmlFor="departement">Departement *</label>
                  <select id="departement" name="departement" value={formData.departement}
                    onChange={handleChange} className={errors.departement ? 'input-error' : ''}
                    disabled={loading}>
                    <option value="">Selectionner...</option>
                    {DEPARTEMENTS.map(d => <option key={d} value={d}>{d}</option>)}
                  </select>
                  {errors.departement && <span className="field-error-msg">{errors.departement}</span>}
                </div>
                <div className="form-field-group">
                  <label htmlFor="poste">Poste *</label>
                  <input id="poste" type="text" name="poste" value={formData.poste}
                    onChange={handleChange} className={errors.poste ? 'input-error' : ''}
                    placeholder="Developpeur Full Stack" disabled={loading} />
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

              {/* Mot de passe (uniquement en creation) */}
              {!isEditMode && (
                <>
                  <h3 className="form-section-title">Securite</h3>
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
                      {!isEditMode && (
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
                      )}
                      {errors.mot_de_passe && <span className="field-error-msg">{errors.mot_de_passe}</span>}
                    </div>
                  </div>
                </>
              )}

              <div className="form-submit-row">
                <button type="button" className="cancel-btn" onClick={handleReset}>Reinitialiser</button>
                <button type="submit" className="save-btn" disabled={loading}>
                  {loading ? 'Sauvegarde...' : isEditMode ? 'Modifier' : "Creer l'employe"}
                </button>
              </div>
            </form>
          </div>
        </div>
      </main>
    </div>
  );
}
