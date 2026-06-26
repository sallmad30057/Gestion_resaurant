"""
================================================================
GESTION AVANCÉE DES COMMANDES (STATUTS, SUIVI)
================================================================
"""

from database import get_connection
from datetime import datetime
import sqlite3

class GestionCommandes:
    def __init__(self):
        self.conn = get_connection()

    def ajouter_commande(self, client, table, plats, total_ht, tva, total_ttc, paiement, serveur, avis=""):
        """Ajoute une nouvelle commande dans la base de données."""
        cursor = self.conn.cursor()
        date_actuelle = datetime.now().strftime('%Y-%m-%d')
        heure_actuelle = datetime.now().strftime('%H:%M')
        cursor.execute('''
            INSERT INTO commandes (
                date, heure, client, table_num, plats, total_ht, tva, total_ttc,
                paiement, statut, serveur, avis
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            date_actuelle, heure_actuelle, client, table, plats,
            total_ht, tva, total_ttc, paiement, "En attente", serveur, avis
        ))
        commande_id = cursor.lastrowid
        self.conn.commit()

        # Si table est fournie, occuper la table
        if table:
            from tables import GestionTables
            gt = GestionTables()
            gt.occuper_table(table, client, commande_id)
            gt.close()

        return commande_id

    def changer_statut(self, commande_id, nouveau_statut):
        """Change le statut d'une commande."""
        statuts_valides = ["En attente", "En préparation", "Servie", "Payée", "Terminée"]
        if nouveau_statut not in statuts_valides:
            raise ValueError(f"Statut invalide. Choisir parmi {statuts_valides}")
        cursor = self.conn.cursor()
        cursor.execute('''
            UPDATE commandes SET statut = ? WHERE id = ?
        ''', (nouveau_statut, commande_id))
        self.conn.commit()

        # Si la commande est payée ou terminée, libérer la table associée
        if nouveau_statut in ("Payée", "Terminée"):
            cursor.execute('SELECT table_num FROM commandes WHERE id = ?', (commande_id,))
            table = cursor.fetchone()
            if table and table['table_num']:
                from tables import GestionTables
                gt = GestionTables()
                gt.liberer_table(table['table_num'])
                gt.close()

    def get_commande(self, commande_id):
        """Récupère les détails d'une commande."""
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM commandes WHERE id = ?', (commande_id,))
        return cursor.fetchone()

    def get_commandes_par_statut(self, statut):
        """Récupère toutes les commandes avec un statut donné."""
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM commandes WHERE statut = ? ORDER BY date DESC, heure DESC', (statut,))
        return cursor.fetchall()

    def get_commandes_par_serveur(self, serveur):
        """Récupère les commandes d'un serveur donné."""
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM commandes WHERE serveur = ? ORDER BY date DESC', (serveur,))
        return cursor.fetchall()

    def get_commandes_par_table(self, table_num):
        """Récupère les commandes d'une table donnée."""
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM commandes WHERE table_num = ? ORDER BY date DESC', (table_num,))
        return cursor.fetchall()

    def get_commandes_jour(self):
        """Récupère les commandes du jour."""
        aujourd_hui = datetime.now().strftime('%Y-%m-%d')
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM commandes WHERE date = ? ORDER BY heure', (aujourd_hui,))
        return cursor.fetchall()

    def get_commandes_semaine(self):
        """Récupère les commandes de la semaine en cours."""
        from datetime import timedelta, date
        debut_semaine = date.today() - timedelta(days=date.today().weekday())
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT * FROM commandes WHERE date >= ? ORDER BY date, heure
        ''', (debut_semaine.isoformat(),))
        return cursor.fetchall()

    def get_commandes_mois(self):
        """Récupère les commandes du mois en cours."""
        aujourd_hui = datetime.now().strftime('%Y-%m')
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM commandes WHERE date LIKE ? ORDER BY date, heure', (aujourd_hui + '%',))
        return cursor.fetchall()

    def supprimer_commande(self, commande_id):
        """Supprime une commande et libère la table associée."""
        cursor = self.conn.cursor()
        # Récupérer la table avant suppression
        cursor.execute('SELECT table_num FROM commandes WHERE id = ?', (commande_id,))
        table = cursor.fetchone()
        if table and table['table_num']:
            from tables import GestionTables
            gt = GestionTables()
            gt.liberer_table(table['table_num'])
            gt.close()
        cursor.execute('DELETE FROM commandes WHERE id = ?', (commande_id,))
        self.conn.commit()

    def fermer(self):
        self.conn.close()

if __name__ == "__main__":
    gc = GestionCommandes()
    print(gc.get_commandes_jour())
    gc.fermer()