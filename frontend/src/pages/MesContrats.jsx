import React, { useEffect, useState } from 'react';
import { Download, ChevronDown, FileText, Loader2 } from 'lucide-react';
import api from '../services/api';
import EmployeeSidebar from '../components/EmployeeSidebar';
import Header from '../components/Header';
import './MesContrats.css';

export default function MesContrats() {
  const [contrats, setContrats] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedContrat, setSelectedContrat] = useState(null);
  const [expandedArticles, setExpandedArticles] = useState([]);
  const [downloadingId, setDownloadingId] = useState(null);
  const [downloadError, setDownloadError] = useState('');

  useEffect(() => {
    const fetchContrats = async () => {
      try {
        const res = await api.get('/mon-espace/contrats');
        // Securite defensive cote frontend : les contrats BROUILLON ne doivent
        // jamais etre affiches a l'employe (le backend les exclut deja).
        setContrats((res.data || []).filter(c => c.statut !== 'Brouillon'));
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    };
    fetchContrats();
  }, []);

  const toggleArticle = (articleId) => {
    setExpandedArticles(prev =>
      prev.includes(articleId) ? prev.filter(id => id !== articleId) : [...prev, articleId]
    );
  };

  const handleDownload = async (e, contratId, reference) => {
    e.stopPropagation();
    setDownloadError('');
    setDownloadingId(contratId);
    try {
      const res = await api.get(`/mon-espace/contrats/${contratId}/telecharger`, {
        responseType: 'blob'
      });
      const blob = new Blob([res.data], {
        type: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
      });
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `Contrat_${reference}.docx`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    } catch (err) {
      setDownloadError("Impossible de télécharger le contrat. Veuillez réessayer.");
    } finally {
      setDownloadingId(null);
    }
  };

  return (
    <div className="app-container">
      <EmployeeSidebar />
      <main className="main-content">
        <Header title="Mes Contrats" subtitle="Consultez et téléchargez les contrats associés à votre profil" />
        <div className="content-padding">

          {downloadError && (
            <div className="glass-card" style={{ padding: '14px 20px', color: 'var(--danger)', fontWeight: 500 }}>
              {downloadError}
            </div>
          )}

          {loading ? (
            <div className="glass-card" style={{ padding: '40px', textAlign: 'center' }}>
              Chargement de vos contrats...
            </div>
          ) : contrats.length === 0 ? (
            <div className="empty-state glass-card">
              <div className="empty-icon">📄</div>
              <h3>Aucun contrat</h3>
              <p>Vous n'avez aucun contrat associe a votre profil pour le moment. Veuillez contacter votre responsable RH.</p>
            </div>
          ) : (
            <>
              <div className="contrats-list">
                {contrats.map(c => (
                  <div
                    key={c.id}
                    className={`contrat-card glass-card ${selectedContrat?.id === c.id ? 'selected' : ''}`}
                    onClick={() => setSelectedContrat(selectedContrat?.id === c.id ? null : c)}
                  >
                    <div className="contrat-card-header">
                      <div>
                        <h4 className="contrat-ref">{c.reference}</h4>
                        <p className="contrat-dates">
                          Du {new Date(c.date_debut).toLocaleDateString('fr-FR')}
                          {c.date_fin ? ` au ${new Date(c.date_fin).toLocaleDateString('fr-FR')}` : ' — Indefini'}
                        </p>
                      </div>
                      <div className="contrat-card-header-actions">
                        <span className={`contrat-status badge status-${c.statut.toLowerCase().replace(/\s/g, '-')}`}>
                          {c.statut}
                        </span>
                        {c.statut !== 'Brouillon' && (
                          <button
                            className="contrat-download-btn"
                            onClick={(e) => handleDownload(e, c.id, c.reference)}
                            disabled={downloadingId === c.id}
                            title="Télécharger mon contrat (Word)"
                          >
                            {downloadingId === c.id ? (
                              <Loader2 size={15} className="mc-spin" />
                            ) : (
                              <Download size={15} />
                            )}
                            {downloadingId === c.id ? 'Génération...' : 'Télécharger mon contrat (Word)'}
                          </button>
                        )}
                      </div>
                    </div>

                    {selectedContrat?.id === c.id && (
                      <div className="contrat-details">
                        <div className="contrat-detail-grid">
                          <div className="contrat-detail-item">
                            <label>Reference</label>
                            <p>{c.reference}</p>
                          </div>
                          <div className="contrat-detail-item">
                            <label>Date de creation</label>
                            <p>{new Date(c.date_creation).toLocaleDateString('fr-FR')}</p>
                          </div>
                          <div className="contrat-detail-item">
                            <label>Date de debut</label>
                            <p>{new Date(c.date_debut).toLocaleDateString('fr-FR')}</p>
                          </div>
                          <div className="contrat-detail-item">
                            <label>Date de fin</label>
                            <p>{c.date_fin ? new Date(c.date_fin).toLocaleDateString('fr-FR') : 'Non definie'}</p>
                          </div>
                          <div className="contrat-detail-item">
                            <label>Salaire mensuel</label>
                            <p className="salaire-value">{c.salaire_mensuel.toLocaleString('fr-FR')} DT</p>
                          </div>
                          <div className="contrat-detail-item">
                            <label>Statut</label>
                            <p>{c.statut}</p>
                          </div>
                        </div>

                        {/* Clauses / articles associés au contrat */}
                        <div className="contrat-articles-section">
                          <label className="contrat-articles-label">
                            <FileText size={13} />
                            Clauses contractuelles {c.articles?.length ? `(${c.articles.length})` : ''}
                          </label>

                          {!c.articles || c.articles.length === 0 ? (
                            <p className="contrat-articles-empty">Aucune clause associée à ce contrat.</p>
                          ) : (
                            <div className="contrat-articles-accordion" onClick={(e) => e.stopPropagation()}>
                              {c.articles.map(article => {
                                const isOpen = expandedArticles.includes(article.id);
                                return (
                                  <div key={article.id} className={`contrat-article-item ${isOpen ? 'open' : ''}`}>
                                    <button
                                      className="contrat-article-toggle"
                                      onClick={() => toggleArticle(article.id)}
                                    >
                                      <span className="contrat-article-code">{article.code}</span>
                                      <span className="contrat-article-titre">{article.titre}</span>
                                      <ChevronDown size={16} className={`contrat-article-chevron ${isOpen ? 'rotated' : ''}`} />
                                    </button>
                                    {isOpen && (
                                      <div className="contrat-article-content">
                                        {article.contenu_par_defaut || 'Aucun contenu renseigné pour cette clause.'}
                                      </div>
                                    )}
                                  </div>
                                );
                              })}
                            </div>
                          )}
                        </div>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </>
          )}

        </div>
      </main>
    </div>
  );
}
