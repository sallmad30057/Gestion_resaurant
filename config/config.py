"""
================================================================
FICHIER DE CONFIGURATION DE L'APPLICATION
================================================================
"""

# Paramètres généraux
APP_NAME = "Chez Sall"
APP_VERSION = "1.0.0"
AUTEUR = "Sall"

# Paramètres d'affichage
THEME = "clair"  # "clair" ou "sombre"
LANGUE = "fr"    # Langue par défaut

# Paramètres de sécurité
TENTATIVES_MAX = 5   # Nombre de tentatives de mot de passe avant blocage

# Paramètres de TVA
TVA_RATE = 0.18

# Dossiers
DOSSIER_RECUS = "recus"
DOSSIER_BACKUPS = "backups"
DOSSIER_LOGS = "logs"

# Base de données
DB_PATH = "db/restaurant.db"

# Moyens de paiement autorisés
MOYENS_PAIEMENT = ["Espèce", "Wave", "Orange Money", "Carte", "Aucun"]

# Statistiques des tables
NB_TABLES_DEFAUT = 10
PREFIXE_TABLE = "T"

# Paramètres d'impression
IMPRIMANTE_PAR_DEFAUT = "Imprimante Reçus"  # Nom de l'imprimante système

# Mode tactile (agrandit les boutons)
MODE_TACTILE = True

# Couleurs du thème clair
COLORS_CLAIR = {
    'primary': '#2c3e50',
    'secondary': '#34495e',
    'success': '#27ae60',
    'danger': '#e74c3c',
    'warning': '#f39c12',
    'light': '#ecf0f1',
    'dark': '#2c3e50',
    'white': '#ffffff',
    'hover': '#3498db',
    'gold': '#f1c40f'
}

# Couleurs du thème sombre
COLORS_SOMBRE = {
    'primary': '#1a1a2e',
    'secondary': '#16213e',
    'success': '#0f3460',
    'danger': '#533483',
    'warning': '#e94560',
    'light': '#2d2d44',
    'dark': '#0a0a1a',
    'white': '#e0e0e0',
    'hover': '#4a4a6a',
    'gold': '#f1c40f'
}

def get_colors():
    """Retourne les couleurs selon le thème actif."""
    if THEME == "sombre":
        return COLORS_SOMBRE
    return COLORS_CLAIR

# Paramètres de log
LOG_LEVEL = "INFO"
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
LOG_FILE = "logs/restaurant.log"

# Paramètres de sauvegarde automatique
SAUVEGARDE_AUTO = True
SAUVEGARDE_INTERVALLE = 86400  # 24 heures
NB_SAUVEGARDES_MAX = 7

# ------------------------------------------------------------
# Fonctions utilitaires
# ------------------------------------------------------------
def get_config(param):
    """Retourne la valeur d'un paramètre de configuration."""
    config = {
        "APP_NAME": APP_NAME,
        "APP_VERSION": APP_VERSION,
        "AUTEUR": AUTEUR,
        "THEME": THEME,
        "LANGUE": LANGUE,
        "TENTATIVES_MAX": TENTATIVES_MAX,
        "TVA_RATE": TVA_RATE,
        "DOSSIER_RECUS": DOSSIER_RECUS,
        "DOSSIER_BACKUPS": DOSSIER_BACKUPS,
        "DOSSIER_LOGS": DOSSIER_LOGS,
        "DB_PATH": DB_PATH,
        "MOYENS_PAIEMENT": MOYENS_PAIEMENT,
        "NB_TABLES_DEFAUT": NB_TABLES_DEFAUT,
        "PREFIXE_TABLE": PREFIXE_TABLE,
        "IMPRIMANTE_PAR_DEFAUT": IMPRIMANTE_PAR_DEFAUT,
        "MODE_TACTILE": MODE_TACTILE,
        "LOG_LEVEL": LOG_LEVEL,
        "LOG_FORMAT": LOG_FORMAT,
        "LOG_FILE": LOG_FILE,
        "SAUVEGARDE_AUTO": SAUVEGARDE_AUTO,
        "SAUVEGARDE_INTERVALLE": SAUVEGARDE_INTERVALLE,
        "NB_SAUVEGARDES_MAX": NB_SAUVEGARDES_MAX,
    }
    return config.get(param)