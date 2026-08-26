import React, { useEffect, useState } from 'react';
import api from '../services/api';
import EmployeeSidebar from '../components/EmployeeSidebar';
import Header from '../components/Header';
import './EmployeeDashboard.css';

export default function EmployeeDashboard() {
  const [profil, setProfil] = useState(null);
  const [contrats, setContrats] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [profilRes, contratsRes] = await Promise.all([
          api.get('/mon-espace/profil'),
          api.get('/mon-espace/contrats')
        ]);
        setProfil(profilRes.data);
        setContrats(contratsRes.data);
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, []);

  if (loading) {
    return (
      <div className="app-container">
        <EmployeeSidebar />
        <main className="main-content">
          <Header title="Tableau de bord" subtitle="Chargement..." />
          <div className="content-padding">
            <div className="glass-card" style={{ padding: '40px', textAlign: 'center' }}>
              Chargement de vos informations...
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
        <Header title="Tableau de bord" subtitle={`Bienvenue, ${profil?.prenom} ${profil?.nom}`} />
        <div className="content-padding">

          {/* Carte de bienvenue */}
          <div className="welcome-card">
            <div className="welcome-avatar">
              {profil?.prenom?.[0]}{profil?.nom?.[0]}
            </div>
            <div className="welcome-info">
              <h2>{profil?.prenom} {profil?.nom}</h2>
              <p className="welcome-role">{profil?.poste || 'Employe'} — {profil?.departement || 'Non defini'}</p>
              <p className="welcome-matricule">Matricule : {profil?.matricule}</p>
            </div>
          </div>

          {/* Cartes d'informations rapides */}
          <div className="dashboard-grid">
            <div className="dash-card glass-card">
              <div className="dash-card-icon">📧</div>
              <div className="dash-card-content">
                <p className="dash-card-label">Email</p>
                <p className="dash-card-value">{profil?.email}</p>
              </div>
            </div>

            <div className="dash-card glass-card">
              <div className="dash-card-icon">📱</div>
              <div className="dash-card-content">
                <p className="dash-card-label">Telephone</p>
                <p className="dash-card-value">{profil?.telephone || 'Non renseigne'}</p>
              </div>
            </div>

            <div className="dash-card glass-card">
              <div className="dash-card-icon">🏢</div>
              <div className="dash-card-content">
                <p className="dash-card-label">Departement</p>
                <p className="dash-card-value">{profil?.departement || 'Non defini'}</p>
              </div>
            </div>

            <div className="dash-card glass-card">
              <div className="dash-card-icon">📅</div>
              <div className="dash-card-content">
                <p className="dash-card-label">Date d'embauche</p>
                <p className="dash-card-value">
                  {profil?.date_embauche
                    ? new Date(profil.date_embauche).toLocaleDateString('fr-FR')
                    : 'Non definie'}
                </p>
              </div>
            </div>

            <div className="dash-card glass-card">
              <div className="dash-card-icon">🎂</div>
              <div className="dash-card-content">
                <p className="dash-card-label">Date de naissance</p>
                <p className="dash-card-value">
                  {profil?.date_naissance
                    ? new Date(profil.date_naissance).toLocaleDateString('fr-FR')
                    : 'Non definie'}
                </p>
              </div>
            </div>

            <div className="dash-card glass-card">
              <div className="dash-card-icon">📄</div>
              <div className="dash-card-content">
                <p className="dash-card-label">Contrats</p>
                <p className="dash-card-value">{contrats.length} contrat(s)</p>
              </div>
            </div>
          </div>

          {/* Derniers contrats */}
          {contrats.length > 0 && (
            <div className="glass-card">
              <h3 className="section-title">Mes derniers contrats</h3>
              <table className="custom-table">
                <thead>
                  <tr>
                    <th>Reference</th>
                    <th>Date debut</th>
                    <th>Date fin</th>
                    <th>Statut</th>
                  </tr>
                </thead>
                <tbody>
                  {contrats.slice(0, 3).map(c => (
                    <tr key={c.id}>
                      <td className="emp-matricule">{c.reference}</td>
                      <td>{new Date(c.date_debut).toLocaleDateString('fr-FR')}</td>
                      <td>{c.date_fin ? new Date(c.date_fin).toLocaleDateString('fr-FR') : 'Indefini'}</td>
                      <td>
                        <span className={`badge status-${c.statut.toLowerCase().replace(/\s/g, '-')}`}>
                          {c.statut}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </main>
    </div>
  );
}
