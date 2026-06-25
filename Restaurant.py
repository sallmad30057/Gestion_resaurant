"""
================================================================
SYSTEME DE GESTION DE RESTAURANT - v3
Nouveautes :
 - Gestion des fichiers CSV avec structure complete
 - Integration avec l'interface graphique
 - Encapsulation forte des donnees
================================================================
"""

import time
import os
import csv
from datetime import date


# ----------------------------------------------------------------
# CLASSE PARENTE : Personne
# ----------------------------------------------------------------
class Personne:
    def __init__(self, nom, role):
        self._nom = nom
        self._role = role

    def se_presenter(self):
        print(f"Je suis {self._nom}, {self._role}.")

    def get_nom(self):
        return self._nom


# ----------------------------------------------------------------
# CLASSE Serveur
# ----------------------------------------------------------------
class Serveur(Personne):
    def __init__(self, nom):
        super().__init__(nom, "serveur")

    def accueillir_client(self):
        print(f"\n{self._nom} : Bonjour, bienvenue au restaurant !")
        nom_client = input("Quel est votre nom ? > ")
        print(f"{self._nom} : Enchante, {nom_client} !")
        return nom_client

    def afficher_menu(self, menu):
        print(f"{self._nom} : Voici notre menu :")
        for plat, prix in menu.items():
            print(f" - {plat} = {prix}€")

    def prendre_commande(self, menu):
        brut = input("Que voulez-vous commander ? (ex: Pizza + Jus) > ")
        demandes = [p.strip() for p in brut.split("+")]
        commande = []
        for plat in demandes:
            if plat in menu:
                commande.append(plat)
            else:
                print(f"'{plat}' n'est pas au menu, je l'ignore.")
        return commande


# ----------------------------------------------------------------
# CLASSE Cuisinier
# ----------------------------------------------------------------
class Cuisinier(Personne):
    def __init__(self, nom):
        super().__init__(nom, "cuisinier")

    def preparer_commande(self, commande, attente=3):
        print(f"\n{self._nom} : Preparation en cours... Patientez {attente} secondes.")
        time.sleep(attente)
        plats = ", ".join(commande)
        print(f"{self._nom} : Commande prete ! ({plats})")


# ----------------------------------------------------------------
# CLASSE Caissier
# ----------------------------------------------------------------
class Caissier(Personne):
    def __init__(self, nom):
        super().__init__(nom, "caissier")

    def calculer_addition(self, commande, menu):
        total = 0
        for plat in commande:
            total += menu[plat]
        return total

    def demander_avis(self):
        choix_valides = ["bon", "excellent", "pimenté", "parfait"]
        avis = input("Comment trouvez-vous le repas ? (bon/excellent/pimenté/parfait) > ").lower()
        while avis not in choix_valides:
            print("Merci de choisir parmi : bon, excellent, pimenté, parfait.")
            avis = input("Votre avis ? > ").lower()
        return avis


# ----------------------------------------------------------------
# CLASSE Manager
# ----------------------------------------------------------------
class Manager(Personne):
    def __init__(self, nom):
        super().__init__(nom, "manager")

    def superviser(self, restaurant):
        bilan = restaurant.calculer_bilan(self)
        if bilan is not None:
            nb, gain = bilan
            print(f"\n{self._nom} (manager) : {restaurant.get_nom()} a traite {nb} commande(s).")
            print(f"{self._nom} (manager) : Gain total de la journee = {gain}€")


# ----------------------------------------------------------------
# CLASSE Restaurant
# ----------------------------------------------------------------
class Restaurant:
    def __init__(self, nom, menu, employes):
        self._nom = nom
        self.menu = menu
        self.__commandes = []
        self.employes = employes

    def get_nom(self):
        return self._nom

    def ajouter_commande(self, commande_info):
        self.__commandes.append(commande_info)

    def calculer_bilan(self, demandeur):
        if not isinstance(demandeur, Manager):
            print("Acces refuse : seul le manager peut consulter le bilan.")
            return None
        nb_commandes = len(self.__commandes)
        gain_total = sum(c["total"] for c in self.__commandes)
        return nb_commandes, gain_total

    def enregistrer_commande_csv(self, commande_info, fichier="commandes.csv"):
        nouveau_fichier = not os.path.exists(fichier)
        with open(fichier, mode="a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            if nouveau_fichier:
                writer.writerow(["Client", "Plats", "Total (€)", "Avis", "Date"])
            plats_texte = " + ".join(commande_info["plats"])
            writer.writerow([
                commande_info["client"],
                plats_texte,
                commande_info["total"],
                commande_info["avis"],
                date.today().isoformat()
            ])
        print(f"(Commande de {commande_info['client']} enregistree dans {fichier})")


# ==================================================================
# PROGRAMME PRINCIPAL (mode console - conserve pour compatibilite)
# ==================================================================
if __name__ == "__main__":
    menu = {"Pizza": 10, "Burger": 8, "Jus": 3}

    serveur = Serveur("Alex")
    cuisinier = Cuisinier("Sam")
    caissier = Caissier("Lina")
    manager = Manager("Paul")

    employes = {"serveur": serveur, "cuisinier": cuisinier,
                "caissier": caissier, "manager": manager}

    restaurant = Restaurant("Chez Sall", menu, employes)

    continuer = "oui"
    while continuer == "oui":
        nom_client = serveur.accueillir_client()
        serveur.afficher_menu(restaurant.menu)
        commande = serveur.prendre_commande(restaurant.menu)

        accompagne = input("Etes-vous accompagne ? (oui/non) > ").lower()
        if accompagne == "oui":
            print(f"{serveur.get_nom()} : Tres bien, je vous installe a une table pour deux.")
        else:
            print(f"{serveur.get_nom()} : Tres bien, je vous installe seul(e).")

        cuisinier.preparer_commande(commande, attente=10)

        total = caissier.calculer_addition(commande, restaurant.menu)
        print(f"\n{caissier.get_nom()} : {nom_client}, l'addition s'il vous plait. Total = {total}€")

        avis = caissier.demander_avis()

        commande_info = {"client": nom_client, "plats": commande,
                         "total": total, "avis": avis}
        restaurant.ajouter_commande(commande_info)
        restaurant.enregistrer_commande_csv(commande_info)

        continuer = input("\nUn autre client ? (oui/non) > ").lower()

    manager.superviser(restaurant)

    print("\n--- Test d'acces refuse (pedagogique) ---")
    restaurant.calculer_bilan(serveur)