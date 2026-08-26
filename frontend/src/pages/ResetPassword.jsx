import React, { useState } from 'react';
import { useSearchParams, useNavigate, Link } from 'react-router-dom';
import { Eye, EyeOff, Check, X, Loader2 } from 'lucide-react';
import api from '../services/api';
import './ResetPassword.css';

export default function ResetPassword() {
  const [searchParams] = useSearchParams();
  const token = searchParams.get('token');
  const navigate = useNavigate();

  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [showNewPassword, setShowNewPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState(false);

  const passwordRules = [
    { label: `Au moins ${8} caractères`, test: (v) => v.length >= 8 },
    { label: 'Au moins une majuscule', test: (v) => /[A-Z]/.test(v) },
    { label: 'Au moins une minuscule', test: (v) => /[a-z]/.test(v) },
    { label: 'Au moins un chiffre', test: (v) => /[0-9]/.test(v) },
    { label: 'Au moins un caractère spécial', test: (v) => /[^A-Za-z0-9]/.test(v) },
  ];

  const allRulesValid = passwordRules.every((rule) => rule.test(newPassword));

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');

    if (!token) {
      setError("Le lien de réinitialisation est invalide (token manquant).");
      return;
    }

    if (!allRulesValid) {
      setError("Le mot de passe ne respecte pas toutes les règles de robustesse.");
      return;
    }

    if (newPassword !== confirmPassword) {
      setError("Les mots de passe ne correspondent pas.");
      return;
    }

    setLoading(true);
    try {
      await api.post('/auth/reset-password', {
        token: token,
        nouveau_mot_de_passe: newPassword,
      });
      setSuccess(true);
    } catch (err) {
      setError(err.response?.data?.detail || "Erreur lors de la réinitialisation du mot de passe.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="reset-container">
      <div className="reset-card glass-card">
        <div className="reset-header">
          <h2>Nouveau mot de passe</h2>
          <p>Saisissez votre nouveau mot de passe sécurisé.</p>
        </div>

        {error && <div className="reset-alert error">{error}</div>}

        {success ? (
          <div className="reset-success-box">
            <h3>Mot de passe réinitialisé !</h3>
            <p>Votre mot de passe a été mis à jour avec succès.</p>
            <button className="reset-submit-btn" onClick={() => navigate('/login')}>
              Se connecter maintenant
            </button>
          </div>
        ) : (
          <form onSubmit={handleSubmit} className="reset-form">
            <div className="form-group">
              <label htmlFor="new-password">Nouveau mot de passe</label>
              <div className="password-input-wrapper">
                <input
                  id="new-password"
                  type={showNewPassword ? 'text' : 'password'}
                  required
                  value={newPassword}
                  onChange={(e) => setNewPassword(e.target.value)}
                  placeholder="••••••••"
                  disabled={loading || !token}
                />
                <button
                  type="button"
                  className="password-toggle-btn"
                  onClick={() => setShowNewPassword((v) => !v)}
                  tabIndex={-1}
                  aria-label={showNewPassword ? 'Masquer le mot de passe' : 'Afficher le mot de passe'}
                >
                  {showNewPassword ? <EyeOff size={18} /> : <Eye size={18} />}
                </button>
              </div>

              <div className="password-rules">
                {passwordRules.map((rule, idx) => {
                  const valid = rule.test(newPassword);
                  return (
                    <div key={idx} className={`password-rule ${valid ? 'valid' : ''}`}>
                      {valid ? <Check size={14} /> : <X size={14} />}
                      <span>{rule.label}</span>
                    </div>
                  );
                })}
              </div>
            </div>

            <div className="form-group">
              <label htmlFor="confirm-password">Confirmer le mot de passe</label>
              <div className="password-input-wrapper">
                <input
                  id="confirm-password"
                  type={showConfirmPassword ? 'text' : 'password'}
                  required
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  placeholder="••••••••"
                  disabled={loading || !token}
                />
                <button
                  type="button"
                  className="password-toggle-btn"
                  onClick={() => setShowConfirmPassword((v) => !v)}
                  tabIndex={-1}
                  aria-label={showConfirmPassword ? 'Masquer le mot de passe' : 'Afficher le mot de passe'}
                >
                  {showConfirmPassword ? <EyeOff size={18} /> : <Eye size={18} />}
                </button>
              </div>
            </div>

            <button type="submit" className="reset-submit-btn" disabled={loading || !token}>
              {loading ? (
                <>
                  <Loader2 size={18} className="spin-icon" /> Mise à jour...
                </>
              ) : (
                'Réinitialiser le mot de passe'
              )}
            </button>

            <div className="reset-footer">
              <Link to="/login" className="back-to-login">
                ← Retour à la connexion
              </Link>
            </div>
          </form>
        )}
      </div>
    </div>
  );
}
