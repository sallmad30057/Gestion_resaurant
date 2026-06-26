"""
================================================================
GESTION DES TABLES
================================================================
"""

from database import get_connection

class GestionTables:
    def __init__(self):
        self.conn = get_connection()

    def get_tables(self):
        """Retourne la liste de toutes les tables."""
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM tables ORDER BY numero')
        return cursor.fetchall()

    def get_table(self, numero):
        """Retourne les informations d'une table."""
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM tables WHERE numero = ?', (numero,))
        return cursor.fetchone()

    def occuper_table(self, numero, client=None, commande_id=None):
        """Marque une table comme occupée."""
        cursor = self.conn.cursor()
        cursor.execute('''
            UPDATE tables SET statut = 'occupée', client = ?, commande_id = ?
            WHERE numero = ?
        ''', (client, commande_id, numero))
        self.conn.commit()

    def liberer_table(self, numero):
        """Libère une table."""
        cursor = self.conn.cursor()
        cursor.execute('''
            UPDATE tables SET statut = 'libre', client = NULL, commande_id = NULL
            WHERE numero = ?
        ''', (numero,))
        self.conn.commit()

    def reserver_table(self, numero):
        """Réserve une table (statut 'réservée')."""
        cursor = self.conn.cursor()
        cursor.execute('UPDATE tables SET statut = "réservée" WHERE numero = ?', (numero,))
        self.conn.commit()

    def get_statut(self, numero):
        """Retourne le statut d'une table."""
        table = self.get_table(numero)
        return table['statut'] if table else None

    def liberer_toutes(self):
        """Libère toutes les tables (fin de service)."""
        cursor = self.conn.cursor()
        cursor.execute('UPDATE tables SET statut = "libre", client = NULL, commande_id = NULL')
        self.conn.commit()

    def close(self):
        self.conn.close()

# Exemple d'utilisation
if __name__ == "__main__":
    gt = GestionTables()
    print(gt.get_tables())
    gt.close()