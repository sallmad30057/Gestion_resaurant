# 🍽️ Restaurant Chez Sall - Système de Gestion

Application de gestion de restaurant avec interface graphique Tkinter, conçue pour les restaurants sénégalais.

---

## 📋 Fonctionnalités principales

### ✅ Gestion des commandes

- Panier avec sélection de plats et quantités
- Calcul automatique de la TVA (18%)
- Impression de reçus en PDF (format A6)
- Historique des commandes avec filtres (client, plat, période, avis)
- Export CSV des commandes
- Statuts des commandes : En attente → En préparation → Servie → Payée → Terminée

### ✅ Gestion des clients

- Enregistrement automatique des clients
- Historique des commandes par client
- Points de fidélité (1 point pour 1000 FCFA)
- Recherche de clients par nom ou téléphone

### ✅ Gestion des tables

- Occupation / libération des tables
- Attribution d'une table à une commande
- Visualisation de l'état des tables (libre, occupée, réservée)

### ✅ Gestion des dépenses

- Ajout de dépenses (salaires, loyer, électricité, eau, internet, ménage, etc.)
- Filtres par type et période
- Suppression de dépenses

### ✅ Bilan financier (manager)

- Calcul des entrées (commandes) et sorties (dépenses)
- Périodes : jour, semaine, mois, trimestre, année, personnalisée
- Génération de rapport PDF
- **Protégé par mot de passe manager**

### ✅ Sécurité

- Mot de passe général pour l'application (`admin123`)
- Mot de passe manager pour le bilan (`manager123`)
- 5 tentatives max, puis blocage définitif

### ✅ Interface

- Design moderne avec couleurs
- Barres de défilement (scroll) partout
- Adaptation tactile (optionnelle)
- Affichage des prix en FCFA (23 000 FCFA)

---

## 📁 Structure du projet

App/
├── config/
│ └── config.py # Configuration centralisée (couleurs, paramètres)
├── res/ # Code source principal
│ ├── Restaurant_GUI.py # Interface principale (~2000 lignes)
│ ├── Restaurant.py # Classes (Serveur, Caissier, Manager)
│ ├── menu.py # Menu et TVA
│ ├── recu.py # Gestion des reçus (format FCFA)
│ ├── database.py # Gestion SQLite (tables, connexion)
│ ├── tables.py # Gestion des tables (occupation, statut)
│ ├── clients.py # Gestion des clients (fidélité, historique)
│ ├── commandes_manager.py # Suivi des commandes (statuts, filtres)
│ ├── depenses_manager.py # Gestion des dépenses SQLite
│ ├── interface_tactile.py # Adaptation pour écrans tactiles
│ └── main.py # Point d'entrée principal
├── securite/
│ └── mots_de_passe.py # Mots de passe (application + manager)
├── recus/ # 📁 Reçus PDF générés
├── db/ # 📁 Base de données SQLite
│ └── restaurant.db # Base de données (créée automatiquement)
├── logs/ # 📁 Journaux d'activité
├── backups/ # 📁 Sauvegardes automatiques
├── requirements.txt # Dépendances Python
├── run.py # Script de lancement
├── .gitignore # Fichiers ignorés par Git
└── README.md # Documentation
text


---

## 🚀 Installation

### 1. Cloner le dépôt

```bash
git clone https://github.com/sallmad30057/Gestion_resaurant.git
cd Gestion_resaurant

2. Créer et activer l'environnement virtuel
bash

python3 -m venv venv
source venv/bin/activate   # Linux/Mac
# venv\Scripts\activate    # Windows

3. Installer les dépendances
bash

pip install -r requirements.txt

4. Initialiser la base de données
bash

python -c "import sys; sys.path.append('res'); from database import init_db; init_db(); print('✅ Base de données initialisée')"

5. Lancer l'application
bash

python res/main.py
# OU
python res/Restaurant_GUI.py

🔑 Mots de passe par défaut
Rôle	Mot de passe
Application	admin123
Manager (Bilan)	manager123

⚠️ À modifier dans securite/mots_de_passe.py avant la mise en production.
📊 Base de données (SQLite)

L'application utilise SQLite pour stocker :

    Commandes

    Clients

    Tables

    Dépenses

    Historique des clients

    Logs d'activité

Emplacement : db/restaurant.db
Tables principales
Table	Description
commandes	Historique des commandes
clients	Clients et points de fidélité
tables	État des tables du restaurant
depenses	Dépenses (salaires, loyer, charges)
historique_clients	Liens clients ↔ commandes
employes	Utilisateurs de l'application
logs	Journal des actions
🛠️ Commandes utiles
Lancer l'application
bash

# Avec l'environnement activé
python res/main.py

Voir la base de données
bash

sqlite3 db/restaurant.db
.tables
SELECT * FROM commandes;
.exit

Sauvegarder la base de données
bash

cp db/restaurant.db backups/restaurant_backup_$(date +%Y%m%d).db

📝 Améliorations prévues

    Imprimante thermique pour les reçus (impression directe)

    Écran client / cuisine pour suivre les commandes

    Statistiques avancées (plats les plus vendus, heures d'affluence)

    Mode hors ligne (sans connexion internet)

    Synchronisation avec un serveur central

    Application mobile companion

🐛 Problèmes connus

    Onglets Dépenses et Bilan manager : L'affichage du contenu après déverrouillage peut être vide dans certaines configurations (problème de canvas). Une correction est en cours.

    MacOS : La touche de scroll peut nécessiter un paramétrage supplémentaire.

👤 Auteur

Développé par Sall
📧 sallmad30057@gmail.com
📍 Dakar, Sénégal
🤝 Contribution

    Fork le projet

    Créer une branche (git checkout -b feature/AmazingFeature)

    Committer (git commit -m 'Add some AmazingFeature')

    Pousser (git push origin feature/AmazingFeature)

    Ouvrir une Pull Request

📄 Licence

MIT
🙏 Remerciements

    Tkinter pour l'interface graphique

    ReportLab pour les reçus PDF

    SQLite pour la base de données légère

Développé avec ❤️ pour Chez Sall
text


---

## ✅ Ajouter sur GitHub

```bash
# 1. Se placer dans le dossier du projet
cd ~/Bureau/gcc/App

# 2. Vérifier les modifications
git status

# 3. Ajouter le README.md
git add README.md

# 4. Committer
git commit -m "Mise à jour complète du README.md avec structure du projet, installation et documentation"

# 5. Pousser
git push origin coding

🚀 Le fichier README.md est maintenant complet et prêt à être affiché sur GitHub.
