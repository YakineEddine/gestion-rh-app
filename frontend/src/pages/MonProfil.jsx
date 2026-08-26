import React, { useEffect, useState } from 'react';
import api from '../services/api';
import EmployeeSidebar from '../components/EmployeeSidebar';
import Header from '../components/Header';
import './MonProfil.css';

export default function MonProfil() {
  const [profil, setProfil] = useState(null);
  const [editMode, setEditMode] = useState(false);
  const [formData, setFormData] = useState({ email: '', telephone: '' });
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState({ type: '', text: '' });

  useEffect(() => {
    const fetchProfil = async () => {
      try {
        const res = await api.get('/mon-espace/profil');
        setProfil(res.data);
        setFormData({ email: res.data.email, telephone: res.data.telephone || '' });
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    };
    fetchProfil();
  }, []);

  const handleSave = async () => {
    setSaving(true);
    setMessage({ type: '', text: '' });
    try {
      const res = await api.put('/mon-espace/profil', formData);
      setProfil(res.data);
      // Mettre a jour le localStorage
      const user = JSON.parse(localStorage.getItem('user') || '{}');
      user.email = res.data.email;
      localStorage.setItem('user', JSON.stringify(user));
      setEditMode(false);
      setMessage({ type: 'success', text: 'Profil mis a jour avec succes !' });
    } catch (err) {
      setMessage({ type: 'error', text: err.response?.data?.detail || 'Erreur lors de la mise a jour.' });
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <div className="app-container">
        <EmployeeSidebar />
        <main className="main-content">
          <Header title="Mon Profil" subtitle="Chargement..." />
        </main>
      </div>
    );
  }

  return (
    <div className="app-container">
      <EmployeeSidebar />
      <main className="main-content">
        <Header title="Mon Profil" subtitle="Consultez et modifiez vos informations personnelles" />
        <div className="content-padding">

          {message.text && (
            <div className={`profil-message ${message.type}`}>{message.text}</div>
          )}

          {/* Carte profil */}
          <div className="profil-top-card">
            <div className="profil-avatar">
              {profil?.prenom?.[0]}{profil?.nom?.[0]}
            </div>
            <div className="profil-top-info">
              <h2>{profil?.prenom} {profil?.nom}</h2>
              <p>{profil?.poste || 'Employe'} — {profil?.departement || 'Non defini'}</p>
              <span className="profil-matricule">{profil?.matricule}</span>
            </div>
            {!editMode && (
              <button className="edit-profil-btn" onClick={() => setEditMode(true)}>
                Modifier mes coordonnees
              </button>
            )}
          </div>

          {/* Details */}
          <div className="profil-details glass-card">
            <h3>Informations personnelles</h3>
            <div className="profil-grid">
              <div className="profil-field">
                <label>Nom</label>
                <p>{profil?.nom}</p>
              </div>
              <div className="profil-field">
                <label>Prenom</label>
                <p>{profil?.prenom}</p>
              </div>
              <div className="profil-field">
                <label>Date de naissance</label>
                <p>{profil?.date_naissance ? new Date(profil.date_naissance).toLocaleDateString('fr-FR') : 'Non definie'}</p>
              </div>
            </div>
          </div>

          <div className="profil-details glass-card">
            <h3>Coordonnees</h3>
            {editMode ? (
              <div className="profil-edit-form">
                <div className="profil-grid">
                  <div className="profil-field">
                    <label htmlFor="edit-email">Email</label>
                    <input
                      id="edit-email"
                      type="email"
                      value={formData.email}
                      onChange={(e) => setFormData(prev => ({ ...prev, email: e.target.value }))}
                    />
                  </div>
                  <div className="profil-field">
                    <label htmlFor="edit-tel">Telephone</label>
                    <input
                      id="edit-tel"
                      type="text"
                      value={formData.telephone}
                      onChange={(e) => setFormData(prev => ({ ...prev, telephone: e.target.value }))}
                    />
                  </div>
                </div>
                <div className="profil-edit-actions">
                  <button className="cancel-edit-btn" onClick={() => {
                    setEditMode(false);
                    setFormData({ email: profil.email, telephone: profil.telephone || '' });
                  }}>Annuler</button>
                  <button className="save-edit-btn" onClick={handleSave} disabled={saving}>
                    {saving ? 'Sauvegarde...' : 'Enregistrer'}
                  </button>
                </div>
              </div>
            ) : (
              <div className="profil-grid">
                <div className="profil-field">
                  <label>Email</label>
                  <p>{profil?.email}</p>
                </div>
                <div className="profil-field">
                  <label>Telephone</label>
                  <p>{profil?.telephone || 'Non renseigne'}</p>
                </div>
              </div>
            )}
          </div>

          <div className="profil-details glass-card">
            <h3>Informations professionnelles</h3>
            <div className="profil-grid">
              <div className="profil-field">
                <label>Departement</label>
                <p>{profil?.departement || 'Non defini'}</p>
              </div>
              <div className="profil-field">
                <label>Poste</label>
                <p>{profil?.poste || 'Non defini'}</p>
              </div>
              <div className="profil-field">
                <label>Date d'embauche</label>
                <p>{profil?.date_embauche ? new Date(profil.date_embauche).toLocaleDateString('fr-FR') : 'Non definie'}</p>
              </div>
              <div className="profil-field">
                <label>Role</label>
                <p>{profil?.role}</p>
              </div>
            </div>
          </div>

        </div>
      </main>
    </div>
  );
}
