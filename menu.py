"""
================================================================
MENU DU RESTAURANT
Fichier séparé pour faciliter la gestion des plats
================================================================
"""

MENU = {
    "Pizza": 10,
    "Burger": 8,
    "Jus": 3,
    "Salade": 5,
    "Pates": 7,
    "Dessert": 4,
    "Coca": 2,
    "Eau": 1,
    "Cafe": 2,
    "The": 2,
    "Vin": 6,
    "Biere": 5,
    "Soupe": 4,
    "Steak": 12,
    "Poulet": 9,
    "Poisson": 11,
    "Frites": 3,
    "Glace": 4,
    "Tarte": 5,
    "Crepe": 4,
    "Smoothie": 5,
    "Cocktail": 7,
    "Sandwich": 6,
    "Wrap": 6,
    "Panini": 5,
    "Sushi": 10,
    "Riz": 4,
    "Nouilles": 5,
    "Curry": 8,
    "Tacos": 7,
    "Burrito": 8,
    "Quesadilla": 7,
    "Nachos": 6,
    "Salmon": 12,
    "Steak Frites": 14,
    "Lasagne": 9,
    "Ravioli": 8,
    "Crepe Sucree": 5,
    "Crepe Salee": 6,
    "Pancakes": 5,
    "Waffles": 6,
    "Mousse au Chocolat": 5,
    "Tiramisu": 6,
    "Cheesecake": 6,
    "Mousse au Chocolat": 5,
    "Tiramisu": 6,
    "Cheesecake": 6,
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