# Application de gestion de restaurant - Chez Sall

## Description

Cette application permet de gérer les commandes, les dépenses et les reçus d’un restaurant via une interface graphique en Python avec Tkinter.

Elle est organisée dans le dossier App et comprend :

- la logique principale de l’interface dans le dossier res/
- la gestion des mots de passe dans securite/
- la génération des reçus dans recus/
- les fichiers de données comme commandes.csv et depenses.csv

## Structure du dossier App

- res/Restaurant_GUI.py : interface principale de l’application
- res/Restaurant.py : classes métier et logique du restaurant
- res/menu.py : définition du menu et des calculs de TVA
- res/recu.py : génération des reçus
- securite/mots_de_passe.py : gestion des mots de passe
- recus/ : dossier où sont enregistrés les reçus PDF générés
- commandes.csv : données des commandes
- depenses.csv : données des dépenses

## Prérequis

- Python 3
- Tkinter
- reportlab

### Installation

Dans le dossier App, exécuter :

```bash
pip install reportlab
```

## Lancement

Depuis le dossier App, lancer :

```bash
python res/Restaurant_GUI.py
```

## Fonctionnalités principales

- saisie de nouvelles commandes
- consultation et filtrage des commandes
- génération de reçus PDF
- enregistrement des dépenses
- affichage d’un bilan financier

## Notes importantes

- le dossier recus/ est créé automatiquement s’il n’existe pas
- les fichiers commandes.csv et depenses.csv sont générés ou mis à jour automatiquement
- l’application est pensée pour fonctionner directement depuis le dossier App
