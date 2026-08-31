import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Eye, EyeOff, AlertCircle, Lock, Loader2 } from 'lucide-react';
import api from '../services/api';
import './Login.css';

export default function Login() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  // State pour la modale mot de passe oublie
  const [showForgotModal, setShowForgotModal] = useState(false);
  const [forgotEmail, setForgotEmail] = useState('');
  const [forgotLoading, setForgotLoading] = useState(false);
  const [forgotSuccess, setForgotSuccess] = useState('');
  const [forgotError, setForgotError] = useState('');

  const isLockedMessage = (msg) => {
    return typeof msg === 'string' && msg.toLowerCase().includes('bloqué');
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      const response = await api.post('/auth/login', {
        email: email,
        mot_de_passe: password,
      });

      localStorage.setItem('token', response.data.access_token);
      localStorage.setItem('refresh_token', response.data.refresh_token);
      localStorage.setItem('user', JSON.stringify(response.data.user));

      if (response.data.user.role === 'RH') {
        navigate('/employes');
      } else {
        navigate('/mon-espace');
      }
    } catch (err) {
      const message = err.response?.data?.detail || 'Connexion échouée. Veuillez vérifier vos identifiants.';
      setError(message);
    } finally {
      setLoading(false);
    }
  };

  const handleForgotSubmit = async (e) => {
    e.preventDefault();
    setForgotError('');
    setForgotSuccess('');
    setForgotLoading(true);

    try {
      const res = await api.post('/auth/forgot-password', { email: forgotEmail });
      setForgotSuccess(res.data.message);
    } catch (err) {
      setForgotError(err.response?.data?.detail || "Une erreur s'est produite.");
    } finally {
      setForgotLoading(false);
    }
  };

  const closeForgotModal = () => {
    setShowForgotModal(false);
    setForgotSuccess('');
    setForgotError('');
    setForgotEmail('');
  };

  return (
    <div className="login-container">
      <div className="login-visual">
        <div className="visual-overlay"></div>
        <div className="visual-content">
          <div className="visual-logo-pill">
            <img src="/csi-digital-logo.png" alt="CSI Digital" className="visual-brand-img" />
          </div>
          <h1>Gestion RH & Contrats</h1>
          <p>La plateforme centralisée pour la gestion administrative et le suivi opérationnel de vos collaborateurs.</p>
        </div>
      </div>

      <div className="login-form-side">
        <div className="login-card">
          <div className="login-header">
            <div className="login-brand-wrapper">
              <img src="/csi-digital-logo.png" alt="CSI Digital" className="login-brand-logo" />
            </div>
            <h2>Espace Connexion</h2>
            <p>Connectez-vous pour accéder à votre espace</p>
          </div>

          {error && (
            <div className={`login-error-alert ${isLockedMessage(error) ? 'login-lockout-alert' : ''}`}>
              <AlertCircle size={18} />
              <span>{error}</span>
            </div>
          )}

          <form onSubmit={handleSubmit} className="login-form">
            <div className="form-group">
              <label htmlFor="email">Adresse Email</label>
              <input
                id="email"
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="nom@entreprise.com"
                disabled={loading}
              />
            </div>

            <div className="form-group">
              <div className="label-with-link">
                <label htmlFor="password">Mot de passe</label>
                <button
                  type="button"
                  className="forgot-password-link"
                  onClick={() => {
                    setForgotEmail(email);
                    setShowForgotModal(true);
                  }}
                >
                  Mot de passe oublié ?
                </button>
              </div>
              <div className="password-input-wrapper">
                <input
                  id="password"
                  type={showPassword ? 'text' : 'password'}
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••"
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
            </div>

            <button type="submit" className="login-submit-btn" disabled={loading}>
              {loading ? (
                <>
                  <Loader2 size={18} className="spin-icon" /> Connexion en cours...
                </>
              ) : (
                <>
                  <Lock size={18} /> Se connecter
                </>
              )}
            </button>
          </form>
        </div>
      </div>

      {/* Modale Mot de passe oublié */}
      {showForgotModal && (
        <div className="modal-overlay">
          <div className="modal-card">
            <div className="modal-header">
              <h3>Réinitialisation du mot de passe</h3>
              <button className="close-modal-btn" onClick={closeForgotModal}>
                &times;
              </button>
            </div>

            <p className="modal-desc">
              Saisissez votre adresse email. Un lien de réinitialisation sera envoyé à votre boîte de réception.
            </p>

            {forgotError && <div className="modal-alert error">{forgotError}</div>}

            {forgotSuccess ? (
              <div className="modal-success-box">
                <div className="modal-alert success">{forgotSuccess}</div>
                <p className="modal-success-hint">
                  Consultez votre boîte de réception (et le dossier spam) pour trouver l'email de réinitialisation.
                </p>
                <div className="modal-actions">
                  <button type="button" className="modal-submit-btn" onClick={closeForgotModal}>
                    Fermer
                  </button>
                </div>
              </div>
            ) : (
              <form onSubmit={handleForgotSubmit} className="modal-form">
                <div className="form-group">
                  <label htmlFor="forgot-email">Adresse Email</label>
                  <input
                    id="forgot-email"
                    type="email"
                    required
                    value={forgotEmail}
                    onChange={(e) => setForgotEmail(e.target.value)}
                    placeholder="votre.email@gmail.com"
                    disabled={forgotLoading}
                  />
                </div>
                <div className="modal-actions">
                  <button type="button" className="modal-cancel-btn" onClick={closeForgotModal}>
                    Annuler
                  </button>
                  <button type="submit" className="modal-submit-btn" disabled={forgotLoading}>
                    {forgotLoading ? 'Envoi en cours...' : 'Envoyer le lien'}
                  </button>
                </div>
              </form>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
