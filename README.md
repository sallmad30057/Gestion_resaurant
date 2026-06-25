# Application de gestion de restaurant - Chez Sall

## Description

Cette application gère un restaurant simple avec une interface graphique Tkinter et une logique métier séparée. Elle permet de :
-Saisir de nouvelles commandes
-afficher l'historique des commandes avec des filtres
-générer et afficher un aperçu de reçu
-gérer les dépenses du restaurant
-consulter un bilan financier pour le manager

L'application stocke les commandes dans `commandes.csv`, les dépenses dans `depenses.csv` et génère des reçus PDF dans le dossier `recus/`.

## Structure des fichiers

- `Restaurant_GUI.py` : interface graphique principale et logique d'interaction avec l'utilisateur.
- `Restaurant.py` : classes métier `Personne`, `Serveur`, `Cuisinier`, `Caissier`, `Manager`, `Restaurant` et un mode console de démonstration.
- `menu.py` : définition du menu, des prix et des fonctions de calcul de TVA.
- `reçu.py` : génération et aperçu des reçus PDF.
- `commandes.csv` : fichier de données des commandes (créé/maintenu automatiquement).
- `depenses.csv` : fichier de données des dépenses (créé/maintenu automatiquement).
- `recus/` : dossier contenant les reçus PDF générés.

## Prérequis

- Python 3
- Tkinter (généralement inclus avec Python sur la plupart des systèmes)
- `reportlab` pour la génération des reçus PDF

### Installation des dépendances

Si vous utilisez un environnement virtuel, activez-le puis installez `reportlab` :

```bash
pip install reportlab
```

## Utilisation

1. Ouvrir un terminal dans le dossier `App`.
2. Lancer l'application graphique :

```bash
python Restaurant_GUI.py
```

-Utiliser l'onglet `Nouvelle commande` pour saisir les commandes et générer un reçu.
-Aller dans l'onglet `Commandes` pour voir, filtrer, exporter ou supprimer les -commandes.
-Aller dans l'onglet `Dépenses` pour enregistrer et filtrer les dépenses.
-Aller dans l'onglet `Bilan` pour afficher le bilan financier TTC (accessible au manager).

## Fonctionnalités principales

- sélection d'articles via un menu déroulant
- ajout de quantités pour chaque plat
- calcul automatique du total HT, de la TVA (18%) et du total TTC
- choix du moyen de paiement et avis client
- enregistrement automatique des commandes dans `commandes.csv`
- génération de reçus PDF dans `recus/`
- recherche et filtres par client, plat, ID, avis et période
- export CSV des commandes filtrées
- gestion des dépenses par type et période
- bilan financier avec entrées, sorties et solde

## Notes importantes

- le dossier `recus/` est créé automatiquement s'il n'existe pas
- si `commandes.csv` n'existe pas, il sera généré automatiquement
- le fichier `Restaurant.py` contient un mode console pédagogique en plus de la logique métier

## Suggestions d'amélioration

- ajouter une authentification pour le manager
- ajouter un vrai catalogue de clients
- améliorer la gestion des stocks et des quantités
- ajouter des rapports imprimables pour le bilan
