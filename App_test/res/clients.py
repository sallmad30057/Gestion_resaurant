"""
================================================================
GESTION DES CLIENTS
================================================================
"""

from database import get_connection
from datetime import datetime

class GestionClients:
    def __init__(self):
        self.conn = get_connection()

    def ajouter_client(self, nom, telephone=None, email=None):
        """Ajoute un nouveau client."""
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO clients (nom, telephone, email, date_inscription)
            VALUES (?, ?, ?, ?)
        ''', (nom, telephone, email, datetime.now().strftime('%Y-%m-%d')))
        self.conn.commit()
        return cursor.lastrowid

    def get_client(self, client_id):
        """Récupère un client par son ID."""
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM clients WHERE id = ?', (client_id,))
        return cursor.fetchone()

    def get_client_par_nom(self, nom):
        """Recherche des clients par nom (partiel)."""
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM clients WHERE nom LIKE ?', (f"%{nom}%",))
        return cursor.fetchall()

    def get_client_par_telephone(self, telephone):
        """Recherche un client par téléphone."""
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM clients WHERE telephone = ?', (telephone,))
        return cursor.fetchone()

    def enregistrer_commande_client(self, client_id, commande_id, date_commande=None):
        """Enregistre qu'un client a passé une commande."""
        if date_commande is None:
            date_commande = datetime.now().strftime('%Y-%m-%d')
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO historique_clients (client_id, commande_id, date)
            VALUES (?, ?, ?)
        ''', (client_id, commande_id, date_commande))
        # Mettre à jour les statistiques du client
        cursor.execute('''
            UPDATE clients SET visites = visites + 1
            WHERE id = ?
        ''', (client_id,))
        self.conn.commit()

    def ajouter_depense_client(self, client_id, montant):
        """Ajoute un montant dépensé par un client."""
        cursor = self.conn.cursor()
        cursor.execute('''
            UPDATE clients SET total_depenses = total_depenses + ?
            WHERE id = ?
        ''', (montant, client_id))
        # Ajouter des points de fidélité (1 point pour 1000 FCFA)
        points = int(montant // 1000)
        if points > 0:
            cursor.execute('''
                UPDATE clients SET points_fidelite = points_fidelite + ?
                WHERE id = ?
            ''', (points, client_id))
        self.conn.commit()

    def get_historique_client(self, client_id):
        """Récupère l'historique des commandes d'un client."""
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT c.id, c.date, c.total_ttc, c.statut
            FROM commandes c
            JOIN historique_clients h ON c.id = h.commande_id
            WHERE h.client_id = ?
            ORDER BY c.date DESC
        ''', (client_id,))
        return cursor.fetchall()

    def fermer(self):
        self.conn.close()

if __name__ == "__main__":
    gc = GestionClients()
    # Exemple: ajouter un client
    # gc.ajouter_client("Jean Dupont", "77 123 45 67")
    print(gc.get_client_par_nom("Jean"))
    gc.fermer()