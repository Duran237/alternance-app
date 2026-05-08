# Application d'Alternance Intelligente

Assistant intelligent pour trouver une alternance rapidement en cybersécurité, réseaux, Linux et SOC.

## Fonctionnalités

- **Création de compte** : Inscription, connexion, gestion du profil complet
- **Upload CV** : Analyse automatique du PDF et extraction des compétences
- **Dashboard** : Statistiques visuelles de vos candidatures
- **Scraping d'offres** : Récupération automatique sur Indeed et HelloWork
- **Matching intelligent** : Score de compatibilité profil/offre
- **Génération de lettres** : Lettres de motivation personnalisées (IA optionnelle)
- **Suivi des candidatures** : Statut en temps réel (envoyée, entretien, refus, acceptée)
- **Statistiques** : Taux de réponse, entretiens, technologies les plus demandées
- **Notifications** : Alertes pour les nouvelles offres et les changements de statut

## Stack technique

- **Backend** : Python 3.11+ · FastAPI · SQLAlchemy · SQLite · JWT
- **Frontend** : React 18 · Vite · TailwindCSS · Recharts
- **IA** : Claude (Anthropic) — optionnel, fonctionne sans clé API
- **Scraping** : httpx · BeautifulSoup4

## Démarrage rapide

### 1. Backend (Terminal 1)

```bash
# Double-cliquez sur start_backend.bat
# OU manuellement :
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload
```

Le backend démarre sur **http://localhost:8000**  
Documentation API : **http://localhost:8000/docs**

### 2. Frontend (Terminal 2)

```bash
# Double-cliquez sur start_frontend.bat
# OU manuellement :
cd frontend
npm install
npm run dev
```

L'application est accessible sur **http://localhost:5173**

## Configuration IA (optionnel)

Pour activer la génération IA de lettres de motivation :

1. Créez un compte sur [console.anthropic.com](https://console.anthropic.com)
2. Copiez votre clé API
3. Modifiez `backend/.env` :
   ```
   ANTHROPIC_API_KEY=sk-ant-votre-cle-ici
   ```

Sans clé API, des modèles de lettres prédéfinis sont utilisés.

## Structure du projet

```
alternance-app/
├── backend/
│   ├── main.py          # Point d'entrée FastAPI
│   ├── config.py        # Configuration
│   ├── database.py      # SQLAlchemy async
│   ├── models/          # Modèles de données
│   ├── routers/         # Routes API
│   ├── services/        # Logique métier (scraping, IA, matching)
│   └── utils/           # Utilitaires (auth, CV parser)
├── frontend/
│   └── src/
│       ├── pages/       # Login, Dashboard, Jobs, Applications, Stats, Profile
│       ├── components/  # Layout, Sidebar
│       ├── contexts/    # Auth context
│       └── services/    # Client API axios
├── start_backend.bat
└── start_frontend.bat
```

## API Reference

| Méthode | Endpoint | Description |
|---------|----------|-------------|
| POST | `/auth/register` | Créer un compte |
| POST | `/auth/login` | Connexion |
| GET | `/users/me` | Profil utilisateur |
| POST | `/cv/upload` | Uploader un CV (PDF) |
| GET | `/jobs/` | Lister les offres |
| POST | `/jobs/scrape` | Scraper de nouvelles offres |
| GET | `/jobs/recommended` | Offres recommandées |
| GET | `/applications/` | Mes candidatures |
| POST | `/applications/` | Créer une candidature |
| PUT | `/applications/{id}` | Mettre à jour le statut |
| GET | `/stats/` | Statistiques globales |
