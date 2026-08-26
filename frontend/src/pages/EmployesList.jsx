import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { 
  Users, 
  Network, 
  Briefcase, 
  Calendar, 
  Search, 
  RotateCcw, 
  Plus, 
  ArrowUpDown, 
  Mail, 
  Eye, 
  Edit2, 
  Trash2, 
  ChevronLeft, 
  ChevronRight,
  Monitor,
  TrendingUp,
  DollarSign,
  Truck,
  Wrench,
  Award
} from 'lucide-react';
import api from '../services/api';
import Sidebar from '../components/Sidebar';
import Header from '../components/Header';
import './EmployesList.css';

const DEPARTEMENTS = [
  'Tous', 'Ressources Humaines', 'Informatique', 'Finance',
  'Commercial', 'Production', 'Logistique', 'Direction'
];

const ITEMS_PER_PAGE_OPTIONS = [5, 10, 20];

// Color and icon mapping for departments
const getDeptBadgeConfig = (dept) => {
  const normalized = (dept || '').toLowerCase().trim();
  switch (normalized) {
    case 'informatique':
      return { bg: '#e0e7ff', text: '#4f46e5', icon: Monitor };
    case 'ressources humaines':
      return { bg: '#ffe4e6', text: '#e11d48', icon: Users };
    case 'commercial':
      return { bg: '#ecfdf5', text: '#059669', icon: TrendingUp };
    case 'finance':
      return { bg: '#eff6ff', text: '#2563eb', icon: DollarSign };
    case 'logistique':
      return { bg: '#f0fdf4', text: '#15803d', icon: Truck };
    case 'production':
      return { bg: '#fef3c7', text: '#d97706', icon: Wrench };
    case 'direction':
      return { bg: '#faf5ff', text: '#7c3aed', icon: Award };
    default:
      return { bg: '#f1f5f9', text: '#64748b', icon: Briefcase };
  }
};

// Deterministic avatar colors
const getAvatarStyle = (nom, prenom) => {
  const stringToHash = `${nom || ''} ${prenom || ''}`;
  const hash = stringToHash.split('').reduce((acc, char) => acc + char.charCodeAt(0), 0);
  const colors = [
    { bg: '#e0e7ff', text: '#4f46e5' }, // indigo
    { bg: '#fce7f3', text: '#db2777' }, // pink
    { bg: '#dcfce7', text: '#15803d' }, // green
    { bg: '#eff6ff', text: '#2563eb' }, // blue
    { bg: '#fef3c7', text: '#d97706' }, // amber
    { bg: '#faf5ff', text: '#7c3aed' }  // purple
  ];
  return colors[hash % colors.length];
};

export default function EmployesList() {
  const [employes, setEmployes] = useState([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [filterDepartement, setFilterDepartement] = useState('Tous');
  const [filterPoste, setFilterPoste] = useState('Tous');
  const [currentPage, setCurrentPage] = useState(1);
  const [itemsPerPage, setItemsPerPage] = useState(10);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  // Sorting state
  const [sortField, setSortField] = useState('');
  const [sortOrder, setSortOrder] = useState('asc');

  const fetchEmployes = async () => {
    try {
      setLoading(true);
      const response = await api.get('/employes');
      setEmployes(response.data);
    } catch (err) {
      setError('Impossible de récupérer la liste des employés.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchEmployes(); }, []);

  const handleDelete = async (id) => {
    if (window.confirm('Êtes-vous sûr de vouloir supprimer cet employé ?')) {
      try {
        await api.delete(`/employes/${id}`);
        setEmployes(employes.filter(emp => emp.id !== id));
      } catch (err) {
        alert(err.response?.data?.detail || 'Erreur lors de la suppression.');
      }
    }
  };

  const handleReset = () => {
    setSearchTerm('');
    setFilterDepartement('Tous');
    setFilterPoste('Tous');
    setSortField('');
    setSortOrder('asc');
    setCurrentPage(1);
  };

  const handleSort = (field) => {
    if (sortField === field) {
      setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc');
    } else {
      setSortField(field);
      setSortOrder('asc');
    }
  };

  // Get dynamic unique list of posts/jobs
  const uniquePostes = Array.from(new Set(employes.map(emp => emp.poste).filter(Boolean))).sort();

  // Stats calculation
  const totalEmployes = employes.length;
  const totalDepts = new Set(employes.map(emp => emp.departement).filter(Boolean)).size;
  const totalPostes = new Set(employes.map(emp => emp.poste).filter(Boolean)).size;
  
  const calculateAncienneteMoyenne = () => {
    if (employes.length === 0) return '0 ans';
    const today = new Date();
    const seniorities = employes
      .filter(emp => emp.date_embauche)
      .map(emp => {
        const embauche = new Date(emp.date_embauche);
        const diffTime = Math.abs(today - embauche);
        return diffTime / (1000 * 60 * 60 * 24 * 365.25);
      });
    if (seniorities.length === 0) return '0 ans';
    const avg = seniorities.reduce((a, b) => a + b, 0) / seniorities.length;
    return `${avg.toFixed(1).replace('.', ',')} ans`;
  };

  const ancienneteMoyenne = calculateAncienneteMoyenne();

  // Filtering logic
  const filteredEmployes = employes.filter(emp => {
    const matchSearch = `${emp.nom} ${emp.prenom} ${emp.matricule} ${emp.departement || ''} ${emp.poste || ''}`
      .toLowerCase().includes(searchTerm.toLowerCase());
    const matchDept = filterDepartement === 'Tous' || emp.departement === filterDepartement;
    const matchPoste = filterPoste === 'Tous' || emp.poste === filterPoste;
    return matchSearch && matchDept && matchPoste;
  });

  // Sorting logic
  const sortedEmployes = [...filteredEmployes].sort((a, b) => {
    if (!sortField) return 0;
    
    let valA = a[sortField] || '';
    let valB = b[sortField] || '';

    // Handle date embauche string comparison
    if (sortField === 'date_embauche') {
      valA = valA ? new Date(valA).getTime() : 0;
      valB = valB ? new Date(valB).getTime() : 0;
    } else {
      valA = String(valA).toLowerCase();
      valB = String(valB).toLowerCase();
    }

    if (valA < valB) return sortOrder === 'asc' ? -1 : 1;
    if (valA > valB) return sortOrder === 'asc' ? 1 : -1;
    return 0;
  });

  // Pagination logic
  const totalPages = Math.max(1, Math.ceil(sortedEmployes.length / itemsPerPage));
  const startIndex = (currentPage - 1) * itemsPerPage;
  const paginatedEmployes = sortedEmployes.slice(startIndex, startIndex + itemsPerPage);

  // Reset page when filtering or items per page changes
  useEffect(() => { setCurrentPage(1); }, [searchTerm, filterDepartement, filterPoste, itemsPerPage]);

  const renderPageNumbers = () => {
    const pages = [];
    if (totalPages <= 5) {
      for (let i = 1; i <= totalPages; i++) {
        pages.push(i);
      }
    } else {
      if (currentPage <= 3) {
        pages.push(1, 2, 3, 4, '...', totalPages);
      } else if (currentPage >= totalPages - 2) {
        pages.push(1, '...', totalPages - 3, totalPages - 2, totalPages - 1, totalPages);
      } else {
        pages.push(1, '...', currentPage - 1, currentPage, currentPage + 1, '...', totalPages);
      }
    }
    
    return pages.map((page, index) => {
      if (page === '...') {
        return <span key={`ellipsis-${index}`} className="pagination-ellipsis">...</span>;
      }
      return (
        <button
          key={page}
          onClick={() => setCurrentPage(page)}
          className={`pagination-circle-btn ${currentPage === page ? 'active' : ''}`}
        >
          {page}
        </button>
      );
    });
  };

  return (
    <div className="app-container">
      <Sidebar />
      <main className="main-content">
        <Header 
          title="Gestion des Employés" 
          subtitle="Consultez, ajoutez et gérez les collaborateurs de l'entreprise." 
        />
        <div className="content-padding">

          {/* Stats Cards Section */}
          <div className="stats-grid">
            <div className="stat-card glass-card">
              <div className="stat-icon-wrapper purple">
                <Users size={22} className="stat-icon" />
              </div>
              <div className="stat-details">
                <span className="stat-label">Total employés</span>
                <span className="stat-value">{totalEmployes}</span>
                <span className="stat-subtitle">Collaborateurs actifs</span>
              </div>
            </div>

            <div className="stat-card glass-card">
              <div className="stat-icon-wrapper green">
                <Network size={22} className="stat-icon" />
              </div>
              <div className="stat-details">
                <span className="stat-label">Départements</span>
                <span className="stat-value">{totalDepts}</span>
                <span className="stat-subtitle">Départements historiques</span>
              </div>
            </div>

            <div className="stat-card glass-card">
              <div className="stat-icon-wrapper blue">
                <Briefcase size={22} className="stat-icon" />
              </div>
              <div className="stat-details">
                <span className="stat-label">Postes</span>
                <span className="stat-value">{totalPostes}</span>
                <span className="stat-subtitle">Fonctions occupées</span>
              </div>
            </div>

            <div className="stat-card glass-card">
              <div className="stat-icon-wrapper orange">
                <Calendar size={22} className="stat-icon" />
              </div>
              <div className="stat-details">
                <span className="stat-label">Ancienneté moyenne</span>
                <span className="stat-value">{ancienneteMoyenne}</span>
                <span className="stat-subtitle">Au sein de l'entreprise</span>
              </div>
            </div>
          </div>

          {/* Filters and Search Section */}
          <div className="filters-bar-card glass-card">
            <div className="filters-inner-row">
              <div className="filter-group flex-2">
                <label>Recherche</label>
                <div className="input-with-icon">
                  <Search className="input-search-icon" size={16} />
                  <input
                    type="text"
                    placeholder="Nom, prénom, matricule, département, poste..."
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                  />
                </div>
              </div>
              
              <div className="filter-group flex-1">
                <label>Département</label>
                <select value={filterDepartement} onChange={(e) => setFilterDepartement(e.target.value)}>
                  {DEPARTEMENTS.map(d => <option key={d} value={d}>{d}</option>)}
                </select>
              </div>
              
              <div className="filter-group flex-1">
                <label>Poste</label>
                <select value={filterPoste} onChange={(e) => setFilterPoste(e.target.value)}>
                  <option value="Tous">Filtrer par poste</option>
                  {uniquePostes.map(p => <option key={p} value={p}>{p}</option>)}
                </select>
              </div>
              
              <div className="filter-actions-row">
                <button className="reset-filters-btn-icon" onClick={handleReset} title="Réinitialiser">
                  <RotateCcw size={16} />
                  Réinitialiser
                </button>
                <Link to="/employes/nouveau" className="add-btn-icon">
                  <Plus size={16} />
                  Ajouter un employé
                </Link>
              </div>
            </div>
          </div>

          {/* Table Container */}
          <div className="table-card glass-card">
            {loading ? (
              <div className="table-message">Chargement des données...</div>
            ) : error ? (
              <div className="table-message error">{error}</div>
            ) : paginatedEmployes.length === 0 ? (
              <div className="table-message">Aucun employé trouvé.</div>
            ) : (
              <div className="table-scroll-container">
                <table className="custom-premium-table">
                  <thead>
                    <tr>
                      <th onClick={() => handleSort('matricule')} className="sortable-header">
                        <div className="header-cell-content">
                          Matricule
                          <ArrowUpDown size={12} className="sort-arrow-icon" />
                        </div>
                      </th>
                      <th onClick={() => handleSort('nom')} className="sortable-header">
                        <div className="header-cell-content">
                          Nom & Prénom
                          <ArrowUpDown size={12} className="sort-arrow-icon" />
                        </div>
                      </th>
                      <th onClick={() => handleSort('email')} className="sortable-header">
                        <div className="header-cell-content">
                          Email
                          <ArrowUpDown size={12} className="sort-arrow-icon" />
                        </div>
                      </th>
                      <th onClick={() => handleSort('departement')} className="sortable-header">
                        <div className="header-cell-content">
                          Département
                          <ArrowUpDown size={12} className="sort-arrow-icon" />
                        </div>
                      </th>
                      <th onClick={() => handleSort('poste')} className="sortable-header">
                        <div className="header-cell-content">
                          Poste
                          <ArrowUpDown size={12} className="sort-arrow-icon" />
                        </div>
                      </th>
                      <th onClick={() => handleSort('date_embauche')} className="sortable-header">
                        <div className="header-cell-content">
                          Date Embauche
                          <ArrowUpDown size={12} className="sort-arrow-icon" />
                        </div>
                      </th>
                      <th className="actions-header">Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {paginatedEmployes.map((emp) => {
                      const badgeConfig = getDeptBadgeConfig(emp.departement);
                      const DeptIcon = badgeConfig.icon;
                      const avatarColors = getAvatarStyle(emp.nom, emp.prenom);
                      const initials = `${(emp.nom || '')[0] || ''}${(emp.prenom || '')[0] || ''}`.toUpperCase();
                      
                      return (
                        <tr key={emp.id}>
                          <td className="matricule-cell">
                            <span className="matricule-premium-badge">
                              {emp.matricule}
                            </span>
                          </td>
                          <td className="user-profile-cell">
                            <div className="avatar-circle-small" style={{ backgroundColor: avatarColors.bg, color: avatarColors.text }}>
                              {initials}
                            </div>
                            <div className="user-name-stack">
                              <span className="user-lastname-text">{emp.nom}</span>
                              <span className="user-firstname-text">{emp.prenom}</span>
                            </div>
                          </td>
                          <td className="email-cell">
                            <div className="email-link-wrapper">
                              <Mail size={13} className="cell-icon-prefix" />
                              <span className="email-text-value">{emp.email}</span>
                            </div>
                          </td>
                          <td className="dept-cell">
                            <span 
                              className="dept-premium-badge"
                              style={{ backgroundColor: badgeConfig.bg, color: badgeConfig.text }}
                            >
                              <DeptIcon size={12} className="badge-icon-prefix" />
                              {emp.departement || '—'}
                            </span>
                          </td>
                          <td className="poste-cell">
                            {emp.poste || '—'}
                          </td>
                          <td className="date-cell">
                            <div className="date-wrapper">
                              <Calendar size={13} className="cell-icon-prefix" />
                              <span>
                                {emp.date_embauche
                                  ? new Date(emp.date_embauche).toLocaleDateString('fr-FR')
                                  : '—'}
                              </span>
                            </div>
                          </td>
                          <td className="actions-cell-premium">
                            <div className="actions-buttons-container">
                              <Link 
                                to={`/employes/modifier/${emp.id}`} 
                                className="action-circle-btn-view"
                                title="Voir"
                              >
                                <Eye size={14} />
                              </Link>
                              <Link 
                                to={`/employes/modifier/${emp.id}`} 
                                className="action-circle-btn-edit"
                                title="Modifier"
                              >
                                <Edit2 size={14} />
                              </Link>
                              <button 
                                onClick={() => handleDelete(emp.id)} 
                                className="action-circle-btn-delete"
                                title="Supprimer"
                              >
                                <Trash2 size={14} />
                              </button>
                            </div>
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            )}
          </div>

          {/* Pagination Container */}
          <div className="pagination-bar-premium">
            <span className="pagination-info-premium">
              {sortedEmployes.length} employé(s) — page {currentPage} / {totalPages}
            </span>
            <div className="pagination-controls-premium">
              <button
                disabled={currentPage <= 1}
                onClick={() => setCurrentPage(p => p - 1)}
                className="pagination-circle-btn arrow-btn"
              >
                <ChevronLeft size={16} />
              </button>
              
              <div className="pagination-numbers-container">
                {renderPageNumbers()}
              </div>
              
              <button
                disabled={currentPage >= totalPages}
                onClick={() => setCurrentPage(p => p + 1)}
                className="pagination-circle-btn arrow-btn"
              >
                <ChevronRight size={16} />
              </button>
            </div>
          </div>

        </div>
      </main>
    </div>
  );
}
