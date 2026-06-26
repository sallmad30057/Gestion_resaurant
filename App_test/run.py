#!/usr/bin/env python3
"""
================================================================
SCRIPT DE LANCEMENT DE L'APPLICATION
================================================================
"""

import sys
import os
import subprocess

def main():
    # Vérifier que l'environnement virtuel est activé
    # Si non, on peut l'activer automatiquement ou afficher un message

    # Lancer l'application principale
    python = sys.executable
    script = os.path.join(os.path.dirname(__file__), "res", "main.py")
    subprocess.run([python, script])

if __name__ == "__main__":
    main()