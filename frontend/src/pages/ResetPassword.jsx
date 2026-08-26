import React, { useState } from 'react';
import { useSearchParams, useNavigate, Link } from 'react-router-dom';
import api from '../services/api';
import './ResetPassword.css';

export default function ResetPassword() {
  const [searchParams] = useSearchParams();
  const token = searchParams.get('token');
  const navigate = useNavigate();

  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');

    if (!token) {
      setError("Le lien de réinitialisation est invalide (token manquant).");
      return;
    }

    if (newPassword.length < 4) {
      setError("Le mot de passe doit contenir au moins 4 caractères.");
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
            <div className="success-icon">✅</div>
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
              <input
                id="new-password"
                type="password"
                required
                value={newPassword}
                onChange={(e) => setNewPassword(e.target.value)}
                placeholder="••••••••"
                disabled={loading || !token}
              />
            </div>

            <div className="form-group">
              <label htmlFor="confirm-password">Confirmer le mot de passe</label>
              <input
                id="confirm-password"
                type="password"
                required
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                placeholder="••••••••"
                disabled={loading || !token}
              />
            </div>

            <button type="submit" className="reset-submit-btn" disabled={loading || !token}>
              {loading ? 'Mise à jour...' : 'Réinitialiser le mot de passe'}
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
