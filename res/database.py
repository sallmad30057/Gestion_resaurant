"""
================================================================
GESTION DE LA BASE DE DONNÉES SQLite
================================================================
"""

import sqlite3
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "db", "restaurant.db")

def get_connection():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    # Table des commandes (avec served_at)
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
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            served_at TEXT
        )
    ''')

    # Vérifier si la colonne served_at existe (pour mise à jour)
    cursor.execute("PRAGMA table_info(commandes)")
    columns = [col[1] for col in cursor.fetchall()]
    if 'served_at' not in columns:
        cursor.execute("ALTER TABLE commandes ADD COLUMN served_at TEXT")

    # Autres tables
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

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tables (
            numero TEXT PRIMARY KEY,
            statut TEXT DEFAULT 'libre',
            client TEXT,
            commande_id INTEGER,
            FOREIGN KEY (commande_id) REFERENCES commandes(id)
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS depenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            type TEXT NOT NULL,
            description TEXT,
            montant REAL NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')

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

    # Initialisation des tables par défaut
    cursor.execute('SELECT COUNT(*) FROM tables')
    if cursor.fetchone()[0] == 0:
        for i in range(1, 11):
            cursor.execute('INSERT INTO tables (numero, statut) VALUES (?, ?)', (f"T{i}", "libre"))

    cursor.execute('SELECT COUNT(*) FROM employes')
    if cursor.fetchone()[0] == 0:
        cursor.execute('''
            INSERT INTO employes (nom, poste, identifiant, mot_de_passe, role)
            VALUES (?, ?, ?, ?, ?)
        ''', ("Admin", "Manager", "admin", "admin123", "manager"))

    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()