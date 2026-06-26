"""
================================================================
MENU DU RESTAURANT
Fichier séparé pour faciliter la gestion des plats
================================================================
"""

MENU = {
    "Pizza": 5000,
    "Burger": 8000,
    "Jus": 1000,
    "Salade": 5000,
    "Pates": 7000,
    "Dessert": 4000,
    "Coca": 2000,
    "Eau": 1000,
    "Cafe": 2000,
    "The": 2000,
    "Vin": 6000,
    "Biere": 5000,
    "Soupe": 4000,
    "Steak": 12000,
    "Poulet": 9000,
    "Poisson": 11000,
    "Frites": 3000,
    "Glace": 4000,
    "Tarte": 5000,
    "Crepe": 4000,
    "Smoothie": 5000,
    "Cocktail": 7000,
    "Sandwich": 6000,
    "Wrap": 6000,
    "Panini": 5000,
    "Sushi": 10000,
    "Riz": 4000,
    "Nouilles": 5000,
    "Curry": 8000,
    "Tacos": 7000,
    "Burrito": 8000,
    "Quesadilla": 7000,
    "Nachos": 6000,
    "Salmon": 12000,
    "Steak Frites": 14000,
    "Lasagne": 9000,
    "Ravioli": 8000,
    "Crepe Sucree": 5000,
    "Crepe Salee": 6000,
    "Pancakes": 5000,
    "Waffles": 6000,
    "Mousse au Chocolat": 5000,
    "Tiramisu": 6000,
    "Cheesecake": 6000,
    "Mousse au Chocolat": 5000,
    "Tiramisu": 6000,
    "Cheesecake": 6000,
}

# TVA (18%)
TVA = 0.18

def calculer_prix_avec_tva(prix_ht):
    """Calcule le prix TTC à partir du prix HT."""
    return prix_ht * (1 + TVA)

def calculer_total_avec_tva(total_ht):
    """Calcule le total TTC à partir du total HT."""
    return total_ht * (1 + TVA)

def obtenir_tva(total_ht):
    """Retourne le montant de la TVA."""
    return total_ht * TVA