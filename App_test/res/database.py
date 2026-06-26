"""
================================================================
GESTION DE LA BASE DE DONNÉES SQLITE
================================================================
"""

import sqlite3
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "db", "restaurant.db")

def get_connection():
    """Retourne une connexion à la base de données."""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initialise la base de données avec toutes les tables."""
    conn = get_connection()
    cursor = conn.cursor()

    # Table des commandes
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS commandes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            heure TEXT NOT NULL,
            client TEXT,
            table_num TEXT,
            plats TEXT,
            total_ht REAL,
            tva REAL,
            total_ttc REAL,
            paiement TEXT,
            statut TEXT DEFAULT 'En attente',
            serveur TEXT,
            avis TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Table des tables
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tables (
            numero TEXT PRIMARY KEY,
            statut TEXT DEFAULT 'libre',
            client TEXT,
            commande_id INTEGER,
            FOREIGN KEY (commande_id) REFERENCES commandes(id)
        )
    ''')

    # Table des clients
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS clients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nom TEXT NOT NULL,
            telephone TEXT,
            email TEXT,
            date_inscription TEXT DEFAULT CURRENT_DATE,
            visites INTEGER DEFAULT 0,
            total_depenses REAL DEFAULT 0,
            points_fidelite INTEGER DEFAULT 0
        )
    ''')

    # Table des historiques de commandes par client
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS historique_clients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_id INTEGER,
            commande_id INTEGER,
            date TEXT,
            FOREIGN KEY (client_id) REFERENCES clients(id),
            FOREIGN KEY (commande_id) REFERENCES commandes(id)
        )
    ''')

    # Table des employés (utilisateurs)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS employes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nom TEXT NOT NULL,
            poste TEXT,
            identifiant TEXT UNIQUE NOT NULL,
            mot_de_passe TEXT NOT NULL,
            role TEXT DEFAULT 'serveur'
        )
    ''')

    # Table des logs d'activité
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT DEFAULT CURRENT_TIMESTAMP,
            utilisateur TEXT,
            action TEXT,
            details TEXT
        )
    ''')

    # Table des sauvegardes (métadonnées)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sauvegardes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fichier TEXT,
            date TEXT,
            taille INTEGER
        )
    ''')

    # Insérer quelques tables par défaut
    cursor.execute('SELECT COUNT(*) FROM tables')
    if cursor.fetchone()[0] == 0:
        for i in range(1, 11):
            cursor.execute('INSERT INTO tables (numero, statut) VALUES (?, ?)', (f"T{i}", "libre"))

    # Insérer un employé admin par défaut
    cursor.execute('SELECT COUNT(*) FROM employes')
    if cursor.fetchone()[0] == 0:
        cursor.execute('''
            INSERT INTO employes (nom, poste, identifiant, mot_de_passe, role)
            VALUES (?, ?, ?, ?, ?)
        ''', ("Admin", "Manager", "admin", "admin123", "manager"))

    conn.commit()
    conn.close()

# Appeler l'initialisation si le fichier est exécuté directement
if __name__ == "__main__":
    init_db()
    print("✅ Base de données initialisée avec succès.")