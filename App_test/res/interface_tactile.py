"""
================================================================
MODULE D'INTERFACE TACTILE
Agrandit les éléments pour une utilisation sur tablette / écran tactile
================================================================
"""

import tkinter as tk
from tkinter import ttk
from App.App_test.config.config import MODE_TACTILE, get_colors

def appliquer_style_tactile():
    """Applique un style adapté au tactile."""
    if not MODE_TACTILE:
        return

    style = ttk.Style()
    style.theme_use('clam')

    # Taille des polices
    FONT_SIZE_BUTTON = 14
    FONT_SIZE_LABEL = 12
    PADDING_BUTTON = 15

    # Boutons
    style.configure('TButton', font=('Arial', FONT_SIZE_BUTTON, 'bold'),
                    padding=PADDING_BUTTON)
    style.configure('Accent.TButton', font=('Arial', FONT_SIZE_BUTTON, 'bold'),
                    padding=PADDING_BUTTON)
    style.configure('Danger.TButton', font=('Arial', FONT_SIZE_BUTTON, 'bold'),
                    padding=PADDING_BUTTON)
    style.configure('Print.TButton', font=('Arial', FONT_SIZE_BUTTON, 'bold'),
                    padding=PADDING_BUTTON)

    # Entrées
    style.configure('TEntry', font=('Arial', FONT_SIZE_LABEL),
                    padding=10)

    # Combobox
    style.configure('TCombobox', font=('Arial', FONT_SIZE_LABEL),
                    padding=10)

    # Labels
    style.configure('TLabel', font=('Arial', FONT_SIZE_LABEL))
    style.configure('Title.TLabel', font=('Arial', FONT_SIZE_BUTTON+2, 'bold'))

    # Treeview (tableaux)
    style.configure('Treeview', font=('Arial', FONT_SIZE_LABEL),
                    rowheight=40)
    style.configure('Treeview.Heading', font=('Arial', FONT_SIZE_LABEL, 'bold'))

    # Notebook (onglets)
    style.configure('TNotebook.Tab', font=('Arial', FONT_SIZE_LABEL, 'bold'),
                    padding=[15, 10])

    # Taille des Checkbuttons
    style.configure('TCheckbutton', font=('Arial', FONT_SIZE_LABEL),
                    padding=10)

def agrandir_widgets(widget):
    """Parcourt récursivement un widget et agrandit ses enfants."""
    if MODE_TACTILE:
        for child in widget.winfo_children():
            try:
                if isinstance(child, (tk.Button, ttk.Button, ttk.TButton)):
                    child.config(padding=15, font=('Arial', 14))
                elif isinstance(child, (tk.Label, ttk.Label)):
                    child.config(font=('Arial', 12))
                elif isinstance(child, (tk.Entry, ttk.Entry)):
                    child.config(font=('Arial', 12))
                elif isinstance(child, (tk.Text, ttk.Treeview)):
                    child.config(font=('Arial', 12))
                elif isinstance(child, ttk.Combobox):
                    child.config(font=('Arial', 12))
                elif isinstance(child, ttk.Notebook):
                    # Les onglets sont gérés via le style
                    pass
            except:
                pass
            agrandir_widgets(child)

# Exemple d'utilisation dans une fenêtre :
# appliquer_style_tactile()
# agrandir_widgets(fenetre)