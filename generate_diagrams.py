import os
import matplotlib.pyplot as plt
import matplotlib.patches as patches

OUTPUT_DIR = r"c:\Users\Home\.gemini\antigravity-ide\scratch\gestion-rh-app\report_assets"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Set global styles
plt.rcParams['font.sans-serif'] = 'Arial'
plt.rcParams['font.family'] = 'sans-serif'

def create_architecture_diagram():
    fig, ax = plt.subplots(figsize=(12, 7.5), dpi=300)
    ax.set_xlim(0, 12)
    ax.set_ylim(0, 7.5)
    ax.axis('off')

    # Background
    fig.patch.set_facecolor('#FFFFFF')

    # Title
    ax.text(6, 7.1, "Architecture Globale 3-Tiers de l'Application RH", 
            ha='center', va='center', fontsize=15, fontweight='bold', color='#1B365D')

    # 1. Presentation Tier (Frontend)
    p_box = patches.FancyBboxPatch((0.5, 3.8), 3.2, 2.8, boxstyle="round,pad=0.2", 
                                  ec="#2B6CB0", fc="#EBF8FF", lw=2)
    ax.add_patch(p_box)
    ax.text(2.1, 6.3, "TIER PRÉSENTATION\n(Frontend SPA)", ha='center', va='center', 
            fontsize=11, fontweight='bold', color='#2B6CB0')
    ax.text(2.1, 5.5, "• React 18 & Vite\n• React Router DOM (v6)\n• Vanilla CSS / Glassmorphism\n• Lucide React Icons\n• Client HTTP (Axios / Fetch)\n• Espace RH & Espace Collaborateur", 
            ha='center', va='center', fontsize=9, color='#2D3748', linespacing=1.4)

    # 2. Application Tier (Backend)
    b_box = patches.FancyBboxPatch((4.4, 1.2), 3.4, 5.4, boxstyle="round,pad=0.2", 
                                  ec="#2C7A7B", fc="#E6FFFA", lw=2)
    ax.add_patch(b_box)
    ax.text(6.1, 6.3, "TIER APPLICATION\n(Backend REST API)", ha='center', va='center', 
            fontsize=11, fontweight='bold', color='#2C7A7B')
    
    # Internal Backend modules
    modules = [
        ("FastAPI Framework", "Asynchrone, validation Pydantic, OpenAPI", 5.4),
        ("Contrôle d'Accès & Sécurité", "JWT (Access/Refresh), Bcrypt, RBAC", 4.5),
        ("Services Métier RH", "Gestion Employés, Contrats & Transitions", 3.6),
        ("Moteur d'Alertes & Traçabilité", "Déduplication déchéances, Audit Logs", 2.7),
        ("Génération DOCX & Service IA", "python-docx natif, Google Gemini API", 1.8)
    ]
    for title, desc, y in modules:
        m_box = patches.FancyBboxPatch((4.6, y - 0.3), 3.0, 0.65, boxstyle="round,pad=0.1", 
                                      ec="#4FD1C5", fc="#FFFFFF", lw=1.2)
        ax.add_patch(m_box)
        ax.text(6.1, y + 0.12, title, ha='center', va='center', fontsize=8.5, fontweight='bold', color='#234E52')
        ax.text(6.1, y - 0.12, desc, ha='center', va='center', fontsize=7.5, color='#4A5568')

    # 3. Data Tier (Database)
    d_box = patches.FancyBboxPatch((8.5, 3.8), 3.0, 2.8, boxstyle="round,pad=0.2", 
                                  ec="#7B341E", fc="#FFFAF0", lw=2)
    ax.add_patch(d_box)
    ax.text(10.0, 6.3, "TIER PERSISTANCE\n(Base de Données)", ha='center', va='center', 
            fontsize=11, fontweight='bold', color='#7B341E')
    ax.text(10.0, 5.5, "• PostgreSQL 15+\n• SQLAlchemy 2.0 (ORM)\n• Migrations Alembic\n• Tables : Utilisateurs, Contrats,\n  Articles, Notifications,\n  Audit_logs, Refresh_tokens", 
            ha='center', va='center', fontsize=9, color='#2D3748', linespacing=1.4)

    # 4. External Services
    e_box = patches.FancyBboxPatch((8.5, 1.2), 3.0, 2.0, boxstyle="round,pad=0.2", 
                                  ec="#6B46C1", fc="#FAF5FF", lw=2)
    ax.add_patch(e_box)
    ax.text(10.0, 2.9, "SERVICES TIERS EXTERNES", ha='center', va='center', 
            fontsize=10, fontweight='bold', color='#6B46C1')
    ax.text(10.0, 2.1, "• Google Gemini 1.5 Pro / Flash API\n  (Génération clauses structurées)\n• Brevo Transactional Email API\n  (Notifications activation & alertes)", 
            ha='center', va='center', fontsize=8.5, color='#2D3748', linespacing=1.3)

    # Connectors & Arrows
    # Frontend -> Backend
    ax.annotate('', xy=(4.3, 5.2), xytext=(3.8, 5.2),
                arrowprops=dict(arrowstyle="<->", color="#2B6CB0", lw=2))
    ax.text(4.05, 5.4, "HTTPS / JSON\nJWT Bearer", ha='center', va='bottom', fontsize=7.5, fontweight='bold', color='#2B6CB0')

    # Backend -> Database
    ax.annotate('', xy=(8.4, 5.2), xytext=(7.9, 5.2),
                arrowprops=dict(arrowstyle="<->", color="#7B341E", lw=2))
    ax.text(8.15, 5.4, "SQL / Pool\nORM Conn", ha='center', va='bottom', fontsize=7.5, fontweight='bold', color='#7B341E')

    # Backend -> External
    ax.annotate('', xy=(8.4, 2.2), xytext=(7.9, 2.2),
                arrowprops=dict(arrowstyle="<->", color="#6B46C1", lw=2))
    ax.text(8.15, 2.4, "REST / HTTPS\nAPI Keys", ha='center', va='bottom', fontsize=7.5, fontweight='bold', color='#6B46C1')

    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, "fig_architecture_3tiers.png"), bbox_inches='tight', dpi=300)
    plt.close()
    print("Architecture diagram generated.")

def create_contract_lifecycle_diagram():
    fig, ax = plt.subplots(figsize=(12, 6.5), dpi=300)
    ax.set_xlim(0, 12)
    ax.set_ylim(0, 6.5)
    ax.axis('off')

    fig.patch.set_facecolor('#FFFFFF')
    ax.text(6, 6.1, "Machine à États & Cycle de Vie des Contrats de Travail", 
            ha='center', va='center', fontsize=14, fontweight='bold', color='#1B365D')

    # Initial state
    start_circle = patches.Circle((0.8, 4.2), 0.22, fc='#1A202C', ec='#1A202C')
    ax.add_patch(start_circle)
    ax.text(0.8, 3.8, "Création", ha='center', va='top', fontsize=8, fontweight='bold')

    # States
    states = [
        ("BROUILLON\n(Brouillon)", 2.3, 4.2, "#ED8936", "#FFFAF0"),
        ("COMMUNIQUE_EN_COURS\n(Communiqué)", 4.8, 4.2, "#3182CE", "#EBF8FF"),
        ("SIGNE\n(Signé)", 7.3, 4.2, "#805AD5", "#FAF5FF"),
        ("ACTIF\n(Actif)", 9.8, 4.2, "#38A169", "#F0FFF4"),
        ("FIN_CDD\n(Fin CDD)", 8.5, 2.0, "#DD6B20", "#FFFAF0"),
        ("DEMISSION_CDI\n(Démission)", 11.0, 2.0, "#E53E3E", "#FFF5F5"),
        ("INACTIF\n(Archivé)", 9.8, 0.6, "#718096", "#F7FAFC"),
        ("PAS_DISCUTE\n(Pas discuté)", 2.3, 2.0, "#A0AEC0", "#EDF2F7")
    ]

    for name, x, y, ec, fc in states:
        box = patches.FancyBboxPatch((x - 1.0, y - 0.45), 2.0, 0.9, boxstyle="round,pad=0.1", 
                                    ec=ec, fc=fc, lw=2)
        ax.add_patch(box)
        ax.text(x, y, name, ha='center', va='center', fontsize=8, fontweight='bold', color=ec)

    # Arrows
    # Start -> Brouillon
    ax.annotate('', xy=(1.3, 4.2), xytext=(1.05, 4.2), arrowprops=dict(arrowstyle="->", color="#1A202C", lw=1.5))
    
    # Brouillon -> Communiqué
    ax.annotate('', xy=(3.8, 4.2), xytext=(3.3, 4.2), arrowprops=dict(arrowstyle="->", color="#2B6CB0", lw=1.5))
    ax.text(3.55, 4.4, "Transmission", ha='center', va='bottom', fontsize=7, color='#2B6CB0')

    # Communiqué -> Signé
    ax.annotate('', xy=(6.3, 4.2), xytext=(5.8, 4.2), arrowprops=dict(arrowstyle="->", color="#805AD5", lw=1.5))
    ax.text(6.05, 4.4, "Signature", ha='center', va='bottom', fontsize=7, color='#805AD5')

    # Signé -> Actif
    ax.annotate('', xy=(8.8, 4.2), xytext=(8.3, 4.2), arrowprops=dict(arrowstyle="->", color="#38A169", lw=1.5))
    ax.text(8.55, 4.4, "Validation / Prise d'effet", ha='center', va='bottom', fontsize=7, color='#38A169')

    # Actif -> Fin CDD
    ax.annotate('', xy=(8.5, 2.5), xytext=(9.4, 3.75), arrowprops=dict(arrowstyle="->", color="#DD6B20", lw=1.5))
    ax.text(8.7, 3.1, "Échéance (CDD)", ha='right', va='center', fontsize=7, fontweight='bold', color='#DD6B20')

    # Actif -> Démission CDI
    ax.annotate('', xy=(11.0, 2.5), xytext=(10.2, 3.75), arrowprops=dict(arrowstyle="->", color="#E53E3E", lw=1.5))
    ax.text(10.8, 3.1, "Rupture (CDI)", ha='left', va='center', fontsize=7, fontweight='bold', color='#E53E3E')

    # Fin CDD -> Inactif
    ax.annotate('', xy=(9.4, 1.1), xytext=(8.5, 1.55), arrowprops=dict(arrowstyle="->", color="#718096", lw=1.5))
    ax.text(8.7, 1.2, "Clôture", ha='center', va='center', fontsize=7, color='#718096')

    # Démission -> Inactif
    ax.annotate('', xy=(10.2, 1.1), xytext=(11.0, 1.55), arrowprops=dict(arrowstyle="->", color="#718096", lw=1.5))
    ax.text(10.8, 1.2, "Archivage", ha='center', va='center', fontsize=7, color='#718096')

    # End State
    end_circle_outer = patches.Circle((9.8, -0.2), 0.22, fill=False, ec='#1A202C', lw=1.5)
    end_circle_inner = patches.Circle((9.8, -0.2), 0.15, fc='#1A202C', ec='#1A202C')
    # ax.add_patch(end_circle_outer)
    # ax.add_patch(end_circle_inner)

    # Pas discuté standalone connection
    ax.annotate('', xy=(2.3, 2.5), xytext=(2.3, 3.75), arrowprops=dict(arrowstyle="<->", color="#A0AEC0", lw=1.2, linestyle="--"))
    ax.text(2.35, 3.1, "Statut Spécifique\nNon Négocié", ha='left', va='center', fontsize=7, color='#718096')

    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, "fig_contract_lifecycle.png"), bbox_inches='tight', dpi=300)
    plt.close()
    print("Contract lifecycle diagram generated.")

def create_use_case_diagram():
    fig, ax = plt.subplots(figsize=(11, 7.5), dpi=300)
    ax.set_xlim(0, 11)
    ax.set_ylim(0, 7.5)
    ax.axis('off')

    fig.patch.set_facecolor('#FFFFFF')
    ax.text(5.5, 7.2, "Diagramme Global des Cas d'Utilisation (UML)", 
            ha='center', va='center', fontsize=14, fontweight='bold', color='#1B365D')

    # System boundary box
    sys_box = patches.FancyBboxPatch((2.2, 0.4), 6.6, 6.5, boxstyle="round,pad=0.2", 
                                     ec="#4A5568", fc="#F7FAFC", lw=2, linestyle='--')
    ax.add_patch(sys_box)
    ax.text(5.5, 6.7, "Application Web de Gestion RH & Contrats", 
            ha='center', va='center', fontsize=11, fontweight='bold', color='#2D3748')

    # Actors
    # Actor 1: Admin RH
    ax.plot(1.0, 5.0, marker='o', markersize=14, color='#1B365D') # Head
    ax.plot([1.0, 1.0], [4.4, 4.9], color='#1B365D', lw=2) # Body
    ax.plot([0.6, 1.4], [4.7, 4.7], color='#1B365D', lw=2) # Arms
    ax.plot([1.0, 0.7], [4.4, 4.0], color='#1B365D', lw=2) # Left Leg
    ax.plot([1.0, 1.3], [4.4, 4.0], color='#1B365D', lw=2) # Right Leg
    ax.text(1.0, 3.7, "Administrateur RH\n/ Responsable RH", ha='center', va='top', fontsize=8.5, fontweight='bold', color='#1B365D')

    # Actor 2: Employe
    ax.plot(9.8, 2.8, marker='o', markersize=14, color='#2B6CB0')
    ax.plot([9.8, 9.8], [2.2, 2.7], color='#2B6CB0', lw=2)
    ax.plot([9.4, 10.2], [2.5, 2.5], color='#2B6CB0', lw=2)
    ax.plot([9.8, 9.5], [2.2, 1.8], color='#2B6CB0', lw=2)
    ax.plot([9.8, 10.1], [2.2, 1.8], color='#2B6CB0', lw=2)
    ax.text(9.8, 1.5, "Employé /\nCollaborateur", ha='center', va='top', fontsize=8.5, fontweight='bold', color='#2B6CB0')

    # Use cases
    use_cases = [
        ("S'authentifier (JWT / Bcrypt)", 5.5, 6.1),
        ("Gérer les Employés (CRUD, Dossiers)", 5.5, 5.3),
        ("Gérer la Bibliothèque d'Articles", 4.3, 4.5),
        ("Rédiger des Clauses via l'Assistant IA", 6.8, 4.5),
        ("Gérer les Contrats (Workflows & Statuts)", 5.5, 3.7),
        ("Générer les Contrats Word (.docx)", 4.3, 2.9),
        ("Consulter les Alertes d'Expiration", 6.8, 2.9),
        ("Suivre le Journal d'Audit & Sécurité", 5.5, 2.1),
        ("Consulter son Profil & Contrat Actif", 5.5, 1.2)
    ]

    uc_centers = {}
    for text, x, y in use_cases:
        ellipse = patches.Ellipse((x, y), 2.2, 0.6, ec='#2B6CB0', fc='#FFFFFF', lw=1.5)
        ax.add_patch(ellipse)
        ax.text(x, y, text, ha='center', va='center', fontsize=7.5, fontweight='bold', color='#1A202C')
        uc_centers[text] = (x, y)

    # Connections Admin RH
    admin_pos = (1.4, 4.8)
    for text in ["S'authentifier (JWT / Bcrypt)", "Gérer les Employés (CRUD, Dossiers)", 
                 "Gérer la Bibliothèque d'Articles", "Gérer les Contrats (Workflows & Statuts)",
                 "Générer les Contrats Word (.docx)", "Consulter les Alertes d'Expiration",
                 "Suivre le Journal d'Audit & Sécurité"]:
        uc_x, uc_y = uc_centers[text]
        ax.plot([admin_pos[0], uc_x - 1.1], [admin_pos[1], uc_y], color='#4A5568', lw=1.2)

    # AI Extension connection
    ax.annotate('<<extend>>', xy=(uc_centers["Gérer la Bibliothèque d'Articles"][0] + 0.9, uc_centers["Gérer la Bibliothèque d'Articles"][1]),
                xytext=(uc_centers["Rédiger des Clauses via l'Assistant IA"][0] - 0.9, uc_centers["Rédiger des Clauses via l'Assistant IA"][1]),
                arrowprops=dict(arrowstyle="<-", color="#805AD5", lw=1.2, linestyle="--"),
                fontsize=7, color="#805AD5", ha='center', va='bottom')

    # Connections Employe
    emp_pos = (9.4, 2.6)
    for text in ["S'authentifier (JWT / Bcrypt)", "Consulter son Profil & Contrat Actif"]:
        uc_x, uc_y = uc_centers[text]
        ax.plot([emp_pos[0], uc_x + 1.1], [emp_pos[1], uc_y], color='#2B6CB0', lw=1.2)

    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, "fig_use_case.png"), bbox_inches='tight', dpi=300)
    plt.close()
    print("Use Case diagram generated.")

def create_class_diagram():
    fig, ax = plt.subplots(figsize=(13, 8), dpi=300)
    ax.set_xlim(0, 13)
    ax.set_ylim(0, 8)
    ax.axis('off')

    fig.patch.set_facecolor('#FFFFFF')
    ax.text(6.5, 7.7, "Diagramme de Classes Métier UML (Modèle Conceptuel & ORM)", 
            ha='center', va='center', fontsize=14, fontweight='bold', color='#1B365D')

    # Draw Class Box helper
    def draw_uml_class(x, y, w, h, title, attributes, methods=None, color="#2B6CB0", bg="#FFFFFF"):
        # Header
        head_box = patches.FancyBboxPatch((x, y + h - 0.55), w, 0.55, boxstyle="round,pad=0.02", 
                                          ec=color, fc=color, lw=1.5)
        ax.add_patch(head_box)
        ax.text(x + w/2, y + h - 0.28, title, ha='center', va='center', fontsize=8.5, fontweight='bold', color='#FFFFFF')
        
        # Body
        body_box = patches.Rectangle((x, y), w, h - 0.55, ec=color, fc=bg, lw=1.5)
        ax.add_patch(body_box)
        
        # Attributes
        attr_text = "\n".join(attributes)
        ax.text(x + 0.15, y + h - 0.75, attr_text, ha='left', va='top', fontsize=7.5, color='#2D3748', linespacing=1.25)
        
        if methods:
            # Separator line
            sep_y = y + len(methods)*0.22 + 0.2
            ax.plot([x, x + w], [sep_y, sep_y], color=color, lw=1)
            meth_text = "\n".join(methods)
            ax.text(x + 0.15, sep_y - 0.1, meth_text, ha='left', va='top', fontsize=7.5, color='#1A202C', linespacing=1.2)

    # 1. Utilisateur
    draw_uml_class(0.5, 3.8, 3.2, 3.5, "Utilisateur (Employé / Admin)", [
        "- id : Integer (PK)",
        "- matricule : String (Unique)",
        "- nom : String",
        "- prenom : String",
        "- email : String (Unique)",
        "- mot_de_passe_hash : String",
        "- role : RoleEnum (RH, EMP, ADMIN)",
        "- departement : String",
        "- poste : String",
        "- date_embauche : Date",
        "- date_naissance : Date",
        "- telephone : String",
        "- est_actif : Boolean",
        "- login_attempts : Integer",
        "- locked_until : DateTime"
    ], [
        "+ verifier_password() : bool",
        "+ reset_login_attempts() : void"
    ], color="#1B365D", bg="#F7FAFC")

    # 2. Contrat
    draw_uml_class(4.8, 3.8, 3.4, 3.5, "Contrat de Travail", [
        "- id : Integer (PK)",
        "- reference : String (Unique)",
        "- type_contrat : TypeContratEnum",
        "- statut : StatutContratEnum",
        "- date_creation : Date",
        "- date_debut : Date",
        "- date_fin : Date (Nullable)",
        "- salaire_mensuel : Integer",
        "- document_path : String",
        "- employe_id : Integer (FK)"
    ], [
        "+ transitionner_statut() : void",
        "+ jours_restants() : int",
        "+ valider_coherence_dates() : bool"
    ], color="#2C7A7B", bg="#F0FFF4")

    # 3. Article
    draw_uml_class(9.3, 4.3, 3.2, 3.0, "Article / Clause", [
        "- id : Integer (PK)",
        "- code : String (Unique)",
        "- titre : String",
        "- contenu_par_defaut : Text/JSON",
        "- est_actif : Boolean",
        "- modifie_le : DateTime"
    ], [
        "+ est_structure() : bool",
        "+ to_markdown() : string",
        "+ to_docx_table() : Table"
    ], color="#7B341E", bg="#FFFAF0")

    # 4. Association Contrat_Articles
    draw_uml_class(9.3, 2.2, 3.2, 1.5, "contrat_articles (Association)", [
        "- contrat_id : Integer (PK, FK)",
        "- article_id : Integer (PK, FK)",
        "- ordre : Integer"
    ], color="#744210", bg="#FEFCBF")

    # 5. AuditLog
    draw_uml_class(0.5, 0.4, 3.6, 2.6, "AuditLog (Journal d'Audit)", [
        "- id : Integer (PK)",
        "- utilisateur_id : Integer (FK Nullable)",
        "- action : AuditActionEnum",
        "- entite : AuditEntiteEnum",
        "- entite_id : Integer",
        "- description : String",
        "- anciennes_valeurs : JSONB",
        "- nouvelles_valeurs : JSONB",
        "- date_action : DateTime",
        "- ip_address : String"
    ], color="#44337A", bg="#FAF5FF")

    # 6. Notification
    draw_uml_class(4.8, 0.4, 3.6, 2.6, "Notification / Alerte RH", [
        "- id : Integer (PK)",
        "- utilisateur_id : Integer (FK)",
        "- type : NotificationTypeEnum",
        "- titre : String",
        "- message : Text",
        "- priorite : NotificationPrioriteEnum",
        "- est_lue : Boolean",
        "- date_creation : DateTime",
        "- date_expiration : DateTime",
        "- dedup_key : String (Unique)"
    ], color="#C53030", bg="#FFF5F5")

    # Lines & Cardinalities
    # Utilisateur -> Contrat (1 to 0..*)
    ax.plot([3.7, 4.8], [5.5, 5.5], color="#2D3748", lw=1.5)
    ax.text(3.8, 5.65, "1", fontsize=8, fontweight='bold')
    ax.text(4.6, 5.65, "0..*", fontsize=8, fontweight='bold')
    ax.text(4.25, 5.25, "possède >", fontsize=7.5, ha='center', color='#4A5568')

    # Contrat -> Contrat_Articles -> Article
    ax.plot([8.2, 9.3], [5.5, 5.5], color="#2D3748", lw=1.5)
    ax.text(8.3, 5.65, "1..*", fontsize=8, fontweight='bold')
    ax.text(9.1, 5.65, "1..*", fontsize=8, fontweight='bold')
    ax.text(8.75, 5.65, "intègre >", fontsize=7.5, ha='center', color='#4A5568')

    # Contrat -> Contrat_articles (association link)
    ax.plot([8.75, 9.3], [5.5, 3.0], color="#744210", lw=1.2, linestyle="--")

    # Utilisateur -> AuditLog (1 to 0..*)
    ax.plot([2.1, 2.1], [3.8, 3.0], color="#2D3748", lw=1.5)
    ax.text(2.2, 3.6, "1", fontsize=8, fontweight='bold')
    ax.text(2.2, 3.1, "0..*", fontsize=8, fontweight='bold')

    # Utilisateur -> Notification (1 to 0..*)
    ax.plot([3.7, 4.8], [4.5, 2.2], color="#2D3748", lw=1.5)
    ax.text(3.8, 4.2, "1", fontsize=8, fontweight='bold')
    ax.text(4.6, 2.4, "0..*", fontsize=8, fontweight='bold')

    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, "fig_class_diagram.png"), bbox_inches='tight', dpi=300)
    plt.close()
    print("Class diagram generated.")

def create_sequence_auth_diagram():
    fig, ax = plt.subplots(figsize=(11, 6), dpi=300)
    ax.set_xlim(0, 11)
    ax.set_ylim(0, 6)
    ax.axis('off')

    fig.patch.set_facecolor('#FFFFFF')
    ax.text(5.5, 5.7, "Diagramme de Séquence : Authentification Sécurisée & JWT", 
            ha='center', va='center', fontsize=13, fontweight='bold', color='#1B365D')

    # Participants
    actors = [
        ("Utilisateur\n(Navigateur)", 1.5),
        ("Frontend\n(React SPA)", 4.0),
        ("API Backend\n(FastAPI)", 6.8),
        ("Base de Données\n(PostgreSQL)", 9.5)
    ]

    for title, x in actors:
        # box
        box = patches.FancyBboxPatch((x - 0.9, 4.7), 1.8, 0.7, boxstyle="round,pad=0.1", 
                                     ec="#1B365D", fc="#EBF8FF", lw=1.5)
        ax.add_patch(box)
        ax.text(x, 5.05, title, ha='center', va='center', fontsize=8, fontweight='bold', color='#1B365D')
        # Lifeline
        ax.plot([x, x], [0.5, 4.7], color="#A0AEC0", lw=1.2, linestyle="--")

    # Messages
    steps = [
        (1.5, 4.0, 4.3, "1. Saisie email, mot de passe", "->"),
        (4.0, 6.8, 3.8, "2. POST /api/auth/login {email, password}", "->"),
        (6.8, 9.5, 3.3, "3. SELECT * FROM utilisateurs WHERE email", "->"),
        (9.5, 6.8, 2.8, "4. Retourne Utilisateur (hash, salt, statut)", "-->"),
        (6.8, 6.8, 2.3, "5. Vérif. Bcrypt + Lockout check", "self"),
        (6.8, 4.0, 1.7, "6. 200 OK : {access_token, refresh_token, user}", "-->"),
        (4.0, 4.0, 1.2, "7. Stockage token & AuthContext State", "self"),
        (4.0, 1.5, 0.7, "8. Redirection selon Rôle (RH / Employé)", "->")
    ]

    for x1, x2, y, text, style in steps:
        if style == "self":
            # Self loop
            ax.plot([x1, x1 + 0.6, x1 + 0.6, x1], [y + 0.15, y + 0.15, y - 0.15, y - 0.15], color="#2B6CB0", lw=1.2)
            ax.plot(x1, y - 0.15, marker='<', color="#2B6CB0", markersize=5)
            ax.text(x1 + 0.7, y, text, ha='left', va='center', fontsize=7.5, color="#2D3748")
        elif style == "-->":
            ax.annotate('', xy=(x2, y), xytext=(x1, y), arrowprops=dict(arrowstyle="->", color="#38A169", lw=1.3, linestyle="--"))
            ax.text((x1 + x2)/2, y + 0.12, text, ha='center', va='bottom', fontsize=7.5, color="#22543D")
        else:
            ax.annotate('', xy=(x2, y), xytext=(x1, y), arrowprops=dict(arrowstyle="->", color="#2B6CB0", lw=1.3))
            ax.text((x1 + x2)/2, y + 0.12, text, ha='center', va='bottom', fontsize=7.5, color="#1A365D")

    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, "fig_sequence_auth.png"), bbox_inches='tight', dpi=300)
    plt.close()
    print("Sequence Auth diagram generated.")

def create_sequence_ai_clause_diagram():
    fig, ax = plt.subplots(figsize=(11, 6), dpi=300)
    ax.set_xlim(0, 11)
    ax.set_ylim(0, 6)
    ax.axis('off')

    fig.patch.set_facecolor('#FFFFFF')
    ax.text(5.5, 5.7, "Diagramme de Séquence : Rédaction de Clause par l'Assistant IA", 
            ha='center', va='center', fontsize=13, fontweight='bold', color='#1B365D')

    actors = [
        ("Responsable RH", 1.2),
        ("Frontend React\n(Modal IA)", 3.6),
        ("Backend FastAPI\n(/api/ai)", 6.0),
        ("Google Gemini\n1.5 API", 8.4),
        ("Audit / DB", 10.2)
    ]

    for title, x in actors:
        box = patches.FancyBboxPatch((x - 0.8, 4.7), 1.6, 0.7, boxstyle="round,pad=0.1", 
                                     ec="#1B365D", fc="#FAF5FF" if "Gemini" in title else "#EBF8FF", lw=1.5)
        ax.add_patch(box)
        ax.text(x, 5.05, title, ha='center', va='center', fontsize=7.5, fontweight='bold', color='#1B365D')
        ax.plot([x, x], [0.5, 4.7], color="#A0AEC0", lw=1.2, linestyle="--")

    steps = [
        (1.2, 3.6, 4.2, "1. Saisie prompt (ex: 'Rémunération avec grille')", "->"),
        (3.6, 6.0, 3.7, "2. POST /api/ai/articles/generate-structured", "->"),
        (6.0, 8.4, 3.2, "3. Envoi System Prompt + Schéma JSON", "->"),
        (8.4, 6.0, 2.7, "4. Réponse JSON structurée (tables / paragraphes)", "-->"),
        (6.0, 10.2, 2.2, "5. Journalisation AuditAction.AI_GENERATE", "->"),
        (6.0, 3.6, 1.7, "6. Payload structuré {type, title, blocks}", "-->"),
        (3.6, 1.2, 1.2, "7. Aperçu interactif & badges dans la modale", "->"),
        (1.2, 3.6, 0.7, "8. Validation RH & Enregistrement dans la bibliothèque", "->")
    ]

    for x1, x2, y, text, style in steps:
        if style == "-->":
            ax.annotate('', xy=(x2, y), xytext=(x1, y), arrowprops=dict(arrowstyle="->", color="#805AD5", lw=1.3, linestyle="--"))
            ax.text((x1 + x2)/2, y + 0.12, text, ha='center', va='bottom', fontsize=7.5, color="#553C9A")
        else:
            ax.annotate('', xy=(x2, y), xytext=(x1, y), arrowprops=dict(arrowstyle="->", color="#2B6CB0", lw=1.3))
            ax.text((x1 + x2)/2, y + 0.12, text, ha='center', va='bottom', fontsize=7.5, color="#1A365D")

    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, "fig_sequence_ai_clause.png"), bbox_inches='tight', dpi=300)
    plt.close()
    print("Sequence AI Clause diagram generated.")

if __name__ == "__main__":
    create_architecture_diagram()
    create_contract_lifecycle_diagram()
    create_use_case_diagram()
    create_class_diagram()
    create_sequence_auth_diagram()
    create_sequence_ai_clause_diagram()
    print("All 6 high-resolution UML/Architecture diagrams successfully created!")
