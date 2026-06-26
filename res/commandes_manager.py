"""
================================================================
GESTION AVANCÉE DES COMMANDES (STATUTS, SUIVI) - SQLite
================================================================
"""

from database import get_connection
from datetime import datetime
import sqlite3

class GestionCommandes:
    def __init__(self):
        self.conn = get_connection()

    def ajouter_commande(self, client, table, plats, total_ht, tva, total_ttc, paiement, serveur, avis=""):
        cursor = self.conn.cursor()
        date_actuelle = datetime.now().strftime('%Y-%m-%d')
        heure_actuelle = datetime.now().strftime('%H:%M')
        cursor.execute('''
            INSERT INTO commandes (
                date, heure, client, table_num, plats, total_ht, tva, total_ttc,
                paiement, statut, serveur, avis, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        ''', (
            date_actuelle, heure_actuelle, client, table, plats,
            total_ht, tva, total_ttc, paiement, "En attente", serveur, avis
        ))
        commande_id = cursor.lastrowid
        self.conn.commit()

        if table:
            from tables import GestionTables
            gt = GestionTables()
            gt.occuper_table(table, client, commande_id)
            gt.close()

        return commande_id

    def changer_statut(self, commande_id, nouveau_statut):
        statuts_valides = ["En attente", "En préparation", "Servie", "Payée", "Terminée"]
        if nouveau_statut not in statuts_valides:
            raise ValueError(f"Statut invalide. Choisir parmi {statuts_valides}")
        cursor = self.conn.cursor()
        now = datetime.now().isoformat()
        if nouveau_statut == "Servie":
            cursor.execute('''
                UPDATE commandes SET statut = ?, served_at = ?
                WHERE id = ?
            ''', (nouveau_statut, now, commande_id))
        else:
            cursor.execute('''
                UPDATE commandes SET statut = ?
                WHERE id = ?
            ''', (nouveau_statut, commande_id))
        self.conn.commit()

        if nouveau_statut in ("Payée", "Terminée"):
            cursor.execute('SELECT table_num FROM commandes WHERE id = ?', (commande_id,))
            table = cursor.fetchone()
            if table and table['table_num']:
                from tables import GestionTables
                gt = GestionTables()
                gt.liberer_table(table['table_num'])
                gt.close()

    def get_commande(self, commande_id):
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM commandes WHERE id = ?', (commande_id,))
        return cursor.fetchone()

    def get_commandes_par_statut(self, statut):
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM commandes WHERE statut = ? ORDER BY date DESC, heure DESC', (statut,))
        return cursor.fetchall()

    def get_commandes_par_serveur(self, serveur):
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM commandes WHERE serveur = ? ORDER BY date DESC', (serveur,))
        return cursor.fetchall()

    def get_commandes_par_table(self, table_num):
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM commandes WHERE table_num = ? ORDER BY date DESC', (table_num,))
        return cursor.fetchall()

    def get_commandes_jour(self):
        aujourd = datetime.now().strftime('%Y-%m-%d')
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM commandes WHERE date = ? ORDER BY created_at ASC', (aujourd,))
        return cursor.fetchall()

    def get_commandes_semaine(self):
        from datetime import timedelta, date
        debut = date.today() - timedelta(days=date.today().weekday())
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT * FROM commandes WHERE date >= ? ORDER BY created_at ASC
        ''', (debut.isoformat(),))
        return cursor.fetchall()

    def get_commandes_mois(self):
        mois = datetime.now().strftime('%Y-%m')
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM commandes WHERE date LIKE ? ORDER BY created_at ASC', (mois + '%',))
        return cursor.fetchall()

    def supprimer_commande(self, commande_id):
        cursor = self.conn.cursor()
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