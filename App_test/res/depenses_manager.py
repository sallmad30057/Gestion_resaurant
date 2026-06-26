"""
================================================================
GESTION DES DÉPENSES - SQLite
================================================================
"""

from database import get_connection
from datetime import datetime

class GestionDepenses:
    def __init__(self):
        self.conn = get_connection()
        self._init_table()

    def _init_table(self):
        """Crée la table des dépenses si elle n'existe pas."""
        cursor = self.conn.cursor()
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
        self.conn.commit()

    def ajouter_depense(self, type_depense, description, montant):
        """Ajoute une nouvelle dépense."""
        cursor = self.conn.cursor()
        date_actuelle = datetime.now().strftime('%Y-%m-%d')
        cursor.execute('''
            INSERT INTO depenses (date, type, description, montant)
            VALUES (?, ?, ?, ?)
        ''', (date_actuelle, type_depense, description, montant))
        self.conn.commit()
        return cursor.lastrowid

    def get_depenses(self, type_filtre=None):
        """Récupère toutes les dépenses."""
        cursor = self.conn.cursor()
        query = 'SELECT * FROM depenses WHERE 1=1'
        params = []

        if type_filtre and type_filtre != "Tous":
            query += ' AND type = ?'
            params.append(type_filtre)

        query += ' ORDER BY date DESC, id DESC'
        cursor.execute(query, params)
        return cursor.fetchall()

    def get_depenses_par_periode(self, debut=None, fin=None):
        """Récupère les dépenses sur une période donnée."""
        cursor = self.conn.cursor()
        query = 'SELECT * FROM depenses WHERE 1=1'
        params = []

        if debut:
            query += ' AND date >= ?'
            params.append(debut)
        if fin:
            query += ' AND date <= ?'
            params.append(fin)

        query += ' ORDER BY date DESC'
        cursor.execute(query, params)
        return cursor.fetchall()

    def get_depense(self, depense_id):
        """Récupère une dépense par son ID."""
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM depenses WHERE id = ?', (depense_id,))
        return cursor.fetchone()

    def supprimer_depense(self, depense_id):
        """Supprime une dépense."""
        cursor = self.conn.cursor()
        cursor.execute('DELETE FROM depenses WHERE id = ?', (depense_id,))
        self.conn.commit()

    def get_total_depenses(self, debut=None, fin=None):
        """Calcule le total des dépenses sur une période."""
        cursor = self.conn.cursor()
        query = 'SELECT SUM(montant) as total FROM depenses WHERE 1=1'
        params = []

        if debut:
            query += ' AND date >= ?'
            params.append(debut)
        if fin:
            query += ' AND date <= ?'
            params.append(fin)

        cursor.execute(query, params)
        result = cursor.fetchone()
        return result['total'] if result and result['total'] else 0

    def fermer(self):
        self.conn.close()

# ============================================================
# FONCTIONS DE COMPATIBILITÉ POUR L'ANCIEN CODE CSV
# ============================================================

def charger_depenses():
    """Retourne la liste des dépenses (compatibilité)."""
    gd = GestionDepenses()
    depenses = gd.get_depenses()
    gd.fermer()
    return [dict(d) for d in depenses]

def sauvegarder_depenses(depenses):
    """Sauvegarde les dépenses (compatibilité - ne fait rien)."""
    pass

def ajouter_depense_fichier(type_depense, description, montant):
    """Ajoute une dépense (compatibilité)."""
    gd = GestionDepenses()
    gd.ajouter_depense(type_depense, description, montant)
    gd.fermer()