import React, { useEffect, useState } from 'react';
import api from '../services/api';
import EmployeeSidebar from '../components/EmployeeSidebar';
import Header from '../components/Header';
import './MonProfil.css';

export default function MonProfil() {
  const [profil, setProfil] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchProfil = async () => {
      try {
        const res = await api.get('/mon-espace/profil');
        setProfil(res.data);
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    };
    fetchProfil();
  }, []);

  if (loading) {
    return (
      <div className="app-container">
        <EmployeeSidebar />
        <main className="main-content">
          <Header title="Mon Profil" subtitle="Chargement de vos informations..." />
          <div className="content-padding">
            <div className="glass-card" style={{ padding: '40px', textAlign: 'center' }}>
              Chargement de votre profil...
            </div>
          </div>
        </main>
      </div>
    );
  }

  return (
    <div className="app-container">
      <EmployeeSidebar />
      <main className="main-content">
        <Header title="Mon Profil" subtitle="Consultez vos informations personnelles et professionnelles" />
        <div className="content-padding">

          {/* Carte profil */}
          <div className="profil-top-card">
            <div className="profil-avatar">
              {profil?.prenom?.[0]}{profil?.nom?.[0]}
            </div>
            <div className="profil-top-info">
              <h2>{profil?.prenom} {profil?.nom}</h2>
              <p>{profil?.poste || 'Employé'} — {profil?.departement || 'Non défini'}</p>
              <span className="profil-matricule">{profil?.matricule}</span>
            </div>
          </div>

          {/* Details - Informations personnelles */}
          <div className="profil-details glass-card">
            <h3>Informations personnelles</h3>
            <div className="profil-grid">
              <div className="profil-field">
                <label>Nom</label>
                <p>{profil?.nom}</p>
              </div>
              <div className="profil-field">
                <label>Prénom</label>
                <p>{profil?.prenom}</p>
              </div>
              <div className="profil-field">
                <label>Date de naissance</label>
                <p>{profil?.date_naissance ? new Date(profil.date_naissance).toLocaleDateString('fr-FR') : 'Non définie'}</p>
              </div>
            </div>
          </div>

          {/* Details - Coordonnées */}
          <div className="profil-details glass-card">
            <h3>Coordonnées</h3>
            <div className="profil-grid">
              <div className="profil-field">
                <label>Email</label>
                <p>{profil?.email}</p>
              </div>
              <div className="profil-field">
                <label>Téléphone</label>
                <p>{profil?.telephone || 'Non renseigné'}</p>
              </div>
            </div>
          </div>

          {/* Details - Informations professionnelles */}
          <div className="profil-details glass-card">
            <h3>Informations professionnelles</h3>
            <div className="profil-grid">
              <div className="profil-field">
                <label>Département</label>
                <p>{profil?.departement || 'Non défini'}</p>
              </div>
              <div className="profil-field">
                <label>Poste</label>
                <p>{profil?.poste || 'Non défini'}</p>
              </div>
              <div className="profil-field">
                <label>Date d'embauche</label>
                <p>{profil?.date_embauche ? new Date(profil.date_embauche).toLocaleDateString('fr-FR') : 'Non définie'}</p>
              </div>
              <div className="profil-field">
                <label>Rôle</label>
                <p>{profil?.role}</p>
              </div>
            </div>
          </div>

        </div>
      </main>
    </div>
  );
}
