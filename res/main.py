"""
================================================================
POINT D'ENTRÉE PRINCIPAL - RESTAURANT CHEZ SALL
================================================================
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import init_db
from interface_tactile import appliquer_style_tactile
from Restaurant_GUI import FenetreRestaurant
import config.config as config

def main():
    # Initialiser la base de données
    init_db()

    # Appliquer le style tactile si activé
    appliquer_style_tactile()

    # Lancer l'application
    app = FenetreRestaurant()
    app.title(f"{config.APP_NAME} - {config.APP_VERSION}")
    app.mainloop()

if __name__ == "__main__":
    main()