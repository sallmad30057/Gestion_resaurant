"""
================================================================
INTERFACE GRAPHIQUE - Restaurant Chez Sall (version FCFA)
Avec sécurité (mot de passe application + mot de passe manager)
================================================================
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import csv
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import date, datetime, timedelta
import subprocess
import platform

from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT

from Restaurant import Serveur, Caissier, Manager, Restaurant
from menu import MENU, TVA
from recu import afficher_apercu_recu, generer_recu, imprimer_recu_depuis_commande, get_dossier_recus
from securite.mots_de_passe import MOT_DE_PASSE_APPLICATION, MOT_DE_PASSE_MANAGER


# ============================================================
# FONCTION DE FORMATAGE DES PRIX EN FCFA
# ============================================================

def format_price(amount):
    """
    Formate un prix en FCFA avec séparation des milliers
    Exemple: 23000 -> "23 000 FCFA"
             134565 -> "134 565 FCFA"
             1234.56 -> "1 234 FCFA"
    """
    try:
        amount = round(float(amount))
        formatted = f"{amount:,}".replace(",", " ")
        return f"{formatted} FCFA"
    except (ValueError, TypeError):
        return "0 FCFA"

def format_price_table(amount):
    """
    Formate un prix pour le tableau (sans FCFA pour économiser de l'espace)
    Exemple: 23000 -> "23 000"
    """
    try:
        amount = round(float(amount))
        formatted = f"{amount:,}".replace(",", " ")
        return formatted
    except (ValueError, TypeError):
        return "0"


# ------------------------------------------------------------------
# CONFIGURATION GENERALE
# ------------------------------------------------------------------
FICHIER_COMMANDES = "commandes.csv"
COLONNES_COMMANDES = ["ID", "Date", "Heure", "Client", "Plats", "Total HT (€)", "TVA (€)", "Total TTC (€)", "Avis", "Paiement"]

FICHIER_DEPENSES = "depenses.csv"
COLONNES_DEPENSES = ["ID", "Date", "Type", "Description", "Montant (€)"]

TYPES_DEPENSE = ["Salaire", "Loyer", "Électricité", "Eau", "Internet", "Ménage", "Autre"]
PERIODES = ["Toutes", "Aujourd'hui", "Cette semaine", "Ce mois", "Ce trimestre", "Cette année"]

MOYENS_PAIEMENT = ["Espèce", "Wave", "Orange Money", "Carte", "Aucun"]

COLORS = {
    'primary': '#2c3e50',
    'secondary': '#34495e',
    'success': '#27ae60',
    'danger': '#e74c3c',
    'warning': '#f39c12',
    'light': '#ecf0f1',
    'dark': '#2c3e50',
    'white': '#ffffff',
    'hover': '#3498db',
    'gold': '#f1c40f'
}

# Employes crees une seule fois au demarrage
serveur = Serveur("Alex")
caissier = Caissier("Lina")
manager = Manager("Paul")
restaurant = Restaurant("Chez Sall", MENU, {"serveur": serveur, "caissier": caissier, "manager": manager})


# ------------------------------------------------------------------
# OUTILS : DATES ET PERIODES
# ------------------------------------------------------------------
def date_dans_periode(date_texte, periode):
    """Renvoie True si une date (texte 'AAAA-MM-JJ') appartient a la periode demandee."""
    if periode == "Toutes":
        return True
    try:
        d = datetime.strptime(date_texte, "%Y-%m-%d").date()
    except ValueError:
        return False

    aujourd_hui = date.today()

    if periode == "Aujourd'hui":
        return d == aujourd_hui
    if periode == "Cette semaine":
        debut_semaine = aujourd_hui - timedelta(days=aujourd_hui.weekday())
        fin_semaine = debut_semaine + timedelta(days=6)
        return debut_semaine <= d <= fin_semaine
    if periode == "Ce mois":
        return d.year == aujourd_hui.year and d.month == aujourd_hui.month
    if periode == "Ce trimestre":
        tri_actuel = (aujourd_hui.month - 1) // 3
        tri_date = (d.month - 1) // 3
        return d.year == aujourd_hui.year and tri_date == tri_actuel
    if periode == "Cette année":
        return d.year == aujourd_hui.year
    return True


# ------------------------------------------------------------------
# OUTILS : LECTURE / ECRITURE DES COMMANDES
# ------------------------------------------------------------------
def charger_commandes():
    """Lit commandes.csv et renvoie une liste de dictionnaires."""
    if not os.path.exists(FICHIER_COMMANDES):
        return []
    with open(FICHIER_COMMANDES, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        commandes = list(reader)
        
        if commandes and "ID" not in commandes[0]:
            commandes = migrer_ancien_fichier(commandes)
        
        return commandes

def migrer_ancien_fichier(anciennes_commandes):
    """Migre un ancien fichier commandes.csv vers le nouveau format."""
    nouvelles_commandes = []
    for i, cmd in enumerate(anciennes_commandes, 1):
        if "Date" not in cmd:
            cmd["Date"] = date.today().isoformat()
        if "Heure" not in cmd:
            cmd["Heure"] = datetime.now().strftime("%H:%M")
        if "Paiement" not in cmd:
            cmd["Paiement"] = "Non spécifié"
        cmd["ID"] = str(i)
        
        if "Total HT (€)" not in cmd:
            ancien_total = cmd.get("Total (€)", "0")
            try:
                total_ht = float(ancien_total)
            except:
                total_ht = 0
            cmd["Total HT (€)"] = str(total_ht)
            cmd["TVA (€)"] = str(total_ht * TVA)
            cmd["Total TTC (€)"] = str(total_ht * (1 + TVA))
        
        nouvelles_commandes.append(cmd)
    
    sauvegarder_commandes(nouvelles_commandes)
    return nouvelles_commandes

def sauvegarder_commandes(commandes):
    """Reecrit ENTIEREMENT commandes.csv avec les colonnes TVA."""
    with open(FICHIER_COMMANDES, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=COLONNES_COMMANDES)
        writer.writeheader()
        writer.writerows(commandes)

def ajouter_commande_fichier(client, plats, total_ht, avis, paiement):
    """Ajoute une nouvelle commande avec ID unique, TVA, heure et paiement."""
    commandes = charger_commandes()
    nouvel_id = max([int(c["ID"]) for c in commandes], default=0) + 1
    
    tva = total_ht * TVA
    total_ttc = total_ht + tva
    
    commandes.append({
        "ID": str(nouvel_id),
        "Date": date.today().isoformat(),
        "Heure": datetime.now().strftime("%H:%M"),
        "Client": client,
        "Plats": " + ".join(plats),
        "Total HT (€)": f"{total_ht:.2f}",
        "TVA (€)": f"{tva:.2f}",
        "Total TTC (€)": f"{total_ttc:.2f}",
        "Avis": avis,
        "Paiement": paiement,
    })
    sauvegarder_commandes(commandes)
    
    return nouvel_id, total_ht, tva, total_ttc


# ------------------------------------------------------------------
# OUTILS : LECTURE / ECRITURE DES DEPENSES
# ------------------------------------------------------------------
def charger_depenses():
    if not os.path.exists(FICHIER_DEPENSES):
        return []
    with open(FICHIER_DEPENSES, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))

def sauvegarder_depenses(depenses):
    with open(FICHIER_DEPENSES, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=COLONNES_DEPENSES)
        writer.writeheader()
        writer.writerows(depenses)

def ajouter_depense_fichier(type_depense, description, montant):
    depenses = charger_depenses()
    nouvel_id = max([int(d["ID"]) for d in depenses], default=0) + 1
    depenses.append({
        "ID": str(nouvel_id),
        "Date": date.today().isoformat(),
        "Type": type_depense,
        "Description": description,
        "Montant (€)": str(montant),
    })
    sauvegarder_depenses(depenses)


# ------------------------------------------------------------------
# BILAN FINANCIER - RESERVE AU MANAGER
# ------------------------------------------------------------------
def calculer_bilan_financier(demandeur, periode="Toutes", date_debut=None, date_fin=None):
    if not isinstance(demandeur, Manager):
        return None

    commandes = charger_commandes()
    depenses = charger_depenses()

    def filtrer_par_periode(item_date):
        if periode == "Toutes":
            return True
        if date_debut and date_fin:
            try:
                d = datetime.strptime(item_date, "%Y-%m-%d").date()
                debut = datetime.strptime(date_debut, "%Y-%m-%d").date()
                fin = datetime.strptime(date_fin, "%Y-%m-%d").date()
                return debut <= d <= fin
            except:
                return False
        return date_dans_periode(item_date, periode)

    entrees = sum(float(c.get("Total TTC (€)", c.get("Total (€)", "0"))) 
                  for c in commandes if filtrer_par_periode(c.get("Date", "")))
    
    sorties = sum(float(d["Montant (€)"]) for d in depenses if filtrer_par_periode(d["Date"]))
    
    depenses_par_type = {}
    for d in depenses:
        if filtrer_par_periode(d["Date"]):
            type_dep = d["Type"]
            depenses_par_type[type_dep] = depenses_par_type.get(type_dep, 0) + float(d["Montant (€)"])
    
    return entrees, sorties, entrees - sorties, depenses_par_type


# ============================================================
# FENÊTRE DE CONNEXION (CORRIGÉE)
# ============================================================
class FenetreConnexion(tk.Toplevel):
    def __init__(self, parent, titre="Connexion", message="Entrez le mot de passe :"):
        super().__init__(parent)
        self.parent = parent
        self.titre = titre
        self.message = message
        self.mot_de_passe = None
        self.ok = False
        self.geometry("350x150")
        self.title(titre)
        self.configure(bg=COLORS['light'])
        self.transient(parent)
        # SUPPRESSION de grab_set() pour éviter de bloquer la souris
        # self.grab_set()
        self.focus_force()

        # Centrer la fenêtre
        self.update_idletasks()
        x = (self.winfo_screenwidth() - self.winfo_width()) // 2
        y = (self.winfo_screenheight() - self.winfo_height()) // 2
        self.geometry(f"+{x}+{y}")

        tk.Label(self, text=message, font=('Arial', 10, 'bold'), bg=COLORS['light']).pack(pady=15)
        self.entry = ttk.Entry(self, show="*", width=25)
        self.entry.pack(pady=5)
        self.entry.bind("<Return>", lambda e: self.valider())
        # Support du copier-coller
        self.entry.bind("<Control-v>", lambda e: self.entry.event_generate("<<Paste>>"))
        self.entry.bind("<Control-c>", lambda e: self.entry.event_generate("<<Copy>>"))
        self.entry.bind("<Control-x>", lambda e: self.entry.event_generate("<<Cut>>"))

        bouton_frame = tk.Frame(self, bg=COLORS['light'])
        bouton_frame.pack(pady=10)
        ttk.Button(bouton_frame, text="OK", command=self.valider, style='Accent.TButton').pack(side="left", padx=5)
        ttk.Button(bouton_frame, text="Annuler", command=self.annuler, style='Danger.TButton').pack(side="left", padx=5)

        self.entry.focus()
        # Forcer le focus après un court délai pour que le clavier fonctionne
        self.after(100, self.entry.focus_set)

    def valider(self):
        self.mot_de_passe = self.entry.get()
        self.ok = True
        self.destroy()

    def annuler(self):
        self.ok = False
        self.destroy()


# ==================================================================
# CLASSE PRINCIPALE
# ==================================================================
class FenetreRestaurant(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(f"{restaurant.get_nom()} - Gestion du restaurant")
        self.geometry("1300x750")
        self.minsize(1000, 600)
        self.configure(bg=COLORS['light'])

        # Créer le dossier des reçus au démarrage
        get_dossier_recus()

        self.appliquer_style()

        # Initialiser le notebook et les onglets (mais pas encore le contenu)
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=10)

        self.onglet_commande = tk.Frame(self.notebook, bg=COLORS['light'])
        self.onglet_commandes = tk.Frame(self.notebook, bg=COLORS['light'])
        self.onglet_depenses = tk.Frame(self.notebook, bg=COLORS['light'])
        self.onglet_bilan = tk.Frame(self.notebook, bg=COLORS['light'])

        self.notebook.add(self.onglet_commande, text="📝 Nouvelle commande")
        self.notebook.add(self.onglet_commandes, text="📋 Commandes")
        self.notebook.add(self.onglet_depenses, text="💰 Depenses")
        self.notebook.add(self.onglet_bilan, text="📊 Bilan (manager)")

        # Variables
        self.derniere_commande_id = None
        self.derniere_commande_info = None
        self.commande_selectionnee_id = None
        
        # Gestion de l'accès manager avec compteur de tentatives
        self.tentatives_manager_bilan = 0
        self.tentatives_manager_depenses = 0
        self.acces_bilan = False
        self.acces_depenses = False
        self.bloque_bilan = False
        self.bloque_depenses = False

        # Demander le mot de passe général avant de construire l'interface
        self.verifier_acces_application()

    def appliquer_style(self):
        """Applique un style moderne a l'interface."""
        style = ttk.Style()
        style.theme_use('clam')
        
        style.configure('TNotebook', background=COLORS['light'])
        style.configure('TNotebook.Tab', padding=[15, 5], font=('Arial', 10, 'bold'))
        style.map('TNotebook.Tab', 
                  background=[('selected', COLORS['primary']), ('active', COLORS['hover'])],
                  foreground=[('selected', COLORS['white']), ('active', COLORS['white'])])
        
        style.configure('Accent.TButton', 
                       background=COLORS['success'],
                       foreground=COLORS['white'],
                       padding=10,
                       font=('Arial', 10, 'bold'))
        style.map('Accent.TButton',
                  background=[('active', '#2ecc71')])
        
        style.configure('Danger.TButton',
                       background=COLORS['danger'],
                       foreground=COLORS['white'],
                       padding=10)
        style.map('Danger.TButton',
                  background=[('active', '#c0392b')])
        
        style.configure('Print.TButton',
                       background=COLORS['warning'],
                       foreground=COLORS['white'],
                       padding=10,
                       font=('Arial', 10, 'bold'))
        style.map('Print.TButton',
                  background=[('active', '#e67a2a')])
        
        style.configure('Treeview', 
                       background=COLORS['white'],
                       foreground=COLORS['dark'],
                       rowheight=25,
                       font=('Arial', 9))
        style.map('Treeview',
                  background=[('selected', COLORS['hover'])],
                  foreground=[('selected', COLORS['white'])])
        style.configure('Treeview.Heading',
                       background=COLORS['primary'],
                       foreground=COLORS['white'],
                       font=('Arial', 9, 'bold'))

    # ============================================================
    # REDIMENSIONNEMENT
    # ============================================================
    def on_resize(self, event):
        """Gere le redimensionnement de la fenetre."""
        if hasattr(self, 'tableau_commandes'):
            largeur_totale = self.tableau_commandes.winfo_width()
            if largeur_totale > 100:
                largeurs = [40, 80, 60, 100, 150, 80, 80, 80, 80, 90]
                colonnes = ["id", "date", "heure", "client", "plats", "total_ht", "tva", "total_ttc", "avis", "paiement"]
                for col, largeur in zip(colonnes, largeurs):
                    self.tableau_commandes.column(col, width=largeur)
        
        if hasattr(self, 'tableau_depenses'):
            largeur_totale = self.tableau_depenses.winfo_width()
            if largeur_totale > 100:
                largeurs = [40, 90, 120, int(largeur_totale * 0.3), 90]
                colonnes = ["id", "date", "type", "description", "montant"]
                for col, largeur in zip(colonnes, largeurs):
                    self.tableau_depenses.column(col, width=largeur)

    # ============================================================
    # OUVRIR DOSSIER DES REÇUS
    # ============================================================
    def ouvrir_dossier_recus(self):
        """Ouvre le dossier des reçus dans le gestionnaire de fichiers."""
        dossier = get_dossier_recus()
        if platform.system() == "Windows":
            os.startfile(dossier)
        elif platform.system() == "Darwin":  # macOS
            subprocess.run(["open", dossier])
        else:  # Linux
            subprocess.run(["xdg-open", dossier])

    # ============================================================
    # VÉRIFICATION DU MOT DE PASSE APPLICATION (avec réessai)
    # ============================================================
    def verifier_acces_application(self):
        """Affiche la fenêtre de connexion et vérifie le mot de passe, avec réessai."""
        while True:
            fenetre = FenetreConnexion(self, "Connexion à l'application", "Entrez le mot de passe de l'application :")
            self.wait_window(fenetre)
            if fenetre.ok and fenetre.mot_de_passe == MOT_DE_PASSE_APPLICATION:
                self.creer_interface()
                return
            elif fenetre.ok:
                messagebox.showerror("Accès refusé", "Mot de passe incorrect. Veuillez réessayer.")
                # On boucle, la fenêtre se rouvre
            else:
                # L'utilisateur a cliqué sur Annuler
                self.destroy()
                return

    def creer_interface(self):
        """Construit l'interface après validation du mot de passe général."""
        self.construire_onglet_commande()
        self.construire_onglet_commandes()
        self.construire_onglet_depenses()
        self.construire_onglet_bilan()
        self.bind("<Configure>", self.on_resize)

    # ==============================================================
    # GESTION GENERIQUE DE L'ACCÈS MANAGER (avec compteur de tentatives)
    # ==============================================================
    def demander_mot_de_passe_manager(self, nom_onglet):
        """
        Gère la demande de mot de passe manager pour un onglet donné.
        Retourne True si l'accès est accordé, False si refus définitif.
        """
        # Récupérer les variables de compteur et de verrouillage selon l'onglet
        if nom_onglet == "bilan":
            if self.bloque_bilan:
                messagebox.showerror("Accès refusé", "Trop de tentatives. Accès au Bilan définitivement bloqué.")
                return False
            compteur_attr = "tentatives_manager_bilan"
            max_tentatives = 5
        elif nom_onglet == "depenses":
            if self.bloque_depenses:
                messagebox.showerror("Accès refusé", "Trop de tentatives. Accès aux Dépenses définitivement bloqué.")
                return False
            compteur_attr = "tentatives_manager_depenses"
            max_tentatives = 5
        else:
            return False

        # Demander le mot de passe
        fenetre = FenetreConnexion(self, f"Accès Manager - {nom_onglet.capitalize()}", 
                                   f"Entrez le mot de passe manager pour accéder à {nom_onglet.capitalize()} :")
        self.wait_window(fenetre)
        if fenetre.ok and fenetre.mot_de_passe == MOT_DE_PASSE_MANAGER:
            # Réinitialiser le compteur en cas de succès
            setattr(self, compteur_attr, 0)
            return True
        elif fenetre.ok:
            # Incrémenter le compteur
            nouvelles_tentatives = getattr(self, compteur_attr) + 1
            setattr(self, compteur_attr, nouvelles_tentatives)
            restant = max_tentatives - nouvelles_tentatives
            if restant <= 0:
                # Bloquer définitivement
                if nom_onglet == "bilan":
                    self.bloque_bilan = True
                else:
                    self.bloque_depenses = True
                messagebox.showerror("Accès bloqué", 
                                     f"Vous avez dépassé le nombre maximal de tentatives ({max_tentatives}).\n"
                                     f"L'accès à {nom_onglet.capitalize()} est définitivement refusé.")
                return False
            else:
                messagebox.showerror("Mot de passe incorrect", 
                                     f"Mot de passe incorrect. Il vous reste {restant} tentative(s).")
                # Relancer la demande (appel récursif)
                return self.demander_mot_de_passe_manager(nom_onglet)
        else:
            # L'utilisateur a annulé
            return False

    # ==============================================================
    # ONGLET 1 : NOUVELLE COMMANDE
    # ==============================================================
    def construire_onglet_commande(self):
        cadre = self.onglet_commande
        cadre.configure(bg=COLORS['light'])
        
        # EN-TÊTE AVEC TITRE ET BOUTON RECU
        cadre_entete = tk.Frame(cadre, bg=COLORS['light'])
        cadre_entete.pack(fill="x", padx=20, pady=(10, 5))
        
        titre = tk.Label(cadre_entete, text="🛎️ Nouvelle commande", 
                        font=('Arial', 14, 'bold'), fg=COLORS['primary'], bg=COLORS['light'])
        titre.pack(side="left")
        
        self.btn_imprimer_recu = ttk.Button(
            cadre_entete, 
            text="🖨️ Imprimer le reçu", 
            command=self.imprimer_recu_derniere_commande,
            style='Print.TButton'
        )
        self.btn_imprimer_recu.pack(side="right", padx=5)
        self.btn_imprimer_recu.config(state="disabled")
        
        ttk.Button(
            cadre_entete, 
            text="📁 Voir les reçus", 
            command=self.ouvrir_dossier_recus,
            style='Accent.TButton'
        ).pack(side="right", padx=5)
        
        # Canvas avec scroll
        canvas = tk.Canvas(cadre, bg=COLORS['light'], highlightthickness=0)
        scrollbar = ttk.Scrollbar(cadre, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg=COLORS['light'])

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw", width=canvas.winfo_width())
        canvas.configure(yscrollcommand=scrollbar.set)

        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        
        def _on_enter(event):
            canvas.bind_all("<MouseWheel>", _on_mousewheel)
        
        def _on_leave(event):
            canvas.unbind_all("<MouseWheel>")
        
        canvas.bind("<Enter>", _on_enter)
        canvas.bind("<Leave>", _on_leave)
        # Pour Linux (X11)
        canvas.bind("<Button-4>", lambda e: canvas.yview_scroll(-1, "units"))
        canvas.bind("<Button-5>", lambda e: canvas.yview_scroll(1, "units"))

        def _configure_canvas(event):
            canvas.itemconfig(1, width=event.width)
        
        canvas.bind("<Configure>", _configure_canvas)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        contenu = scrollable_frame
        contenu.configure(bg=COLORS['light'])

        cadre_contenu = tk.Frame(contenu, bg=COLORS['light'])
        cadre_contenu.pack(fill="both", expand=True, padx=20, pady=10)

        # Nom du client
        tk.Label(cadre_contenu, text="Nom du client :", font=('Arial', 10), 
                bg=COLORS['light'], fg=COLORS['dark']).pack(anchor="w", pady=(0, 5))
        self.champ_client = ttk.Entry(cadre_contenu, width=40, font=('Arial', 10))
        self.champ_client.pack(anchor="w", pady=(0, 15))

        # SELECTEUR DE PLATS
        tk.Label(cadre_contenu, text="🔽 Selectionner un plat :", font=('Arial', 10), 
                bg=COLORS['light'], fg=COLORS['dark']).pack(anchor="w", pady=(0, 5))
        
        cadre_selecteur = tk.Frame(cadre_contenu, bg=COLORS['light'])
        cadre_selecteur.pack(anchor="w", pady=(0, 10), fill="x")
        
        self.selecteur_plat = ttk.Combobox(cadre_selecteur, 
                                           values=sorted(MENU.keys()),
                                           width=30, 
                                           font=('Arial', 10))
        self.selecteur_plat.pack(side="left", padx=(0, 10))
        self.selecteur_plat.bind("<<ComboboxSelected>>", self.ajouter_plat_selectionne)
        self.selecteur_plat.bind("<Return>", self.ajouter_plat_selectionne)
        
        ttk.Button(cadre_selecteur, text="➕ Ajouter au panier", 
                  command=self.ajouter_plat_selectionne).pack(side="left", padx=5)
        
        # Panier
        tk.Label(cadre_contenu, text="🛒 Panier :", font=('Arial', 10), 
                bg=COLORS['light'], fg=COLORS['dark']).pack(anchor="w", pady=(10, 5))
        
        cadre_panier = tk.Frame(cadre_contenu, bg=COLORS['light'], height=150)
        cadre_panier.pack(anchor="w", pady=(0, 15), fill="x")
        cadre_panier.pack_propagate(False)
        
        canvas_panier = tk.Canvas(cadre_panier, bg=COLORS['light'], height=150, highlightthickness=1)
        scrollbar_panier = ttk.Scrollbar(cadre_panier, orient="vertical", command=canvas_panier.yview)
        panier_frame = tk.Frame(canvas_panier, bg=COLORS['light'])

        panier_frame.bind(
            "<Configure>",
            lambda e: canvas_panier.configure(scrollregion=canvas_panier.bbox("all"))
        )

        canvas_panier.create_window((0, 0), window=panier_frame, anchor="nw", width=canvas_panier.winfo_width())
        canvas_panier.configure(yscrollcommand=scrollbar_panier.set)

        def _configure_panier_canvas(event):
            canvas_panier.itemconfig(1, width=event.width)
        
        canvas_panier.bind("<Configure>", _configure_panier_canvas)

        canvas_panier.pack(side="left", fill="both", expand=True, padx=(0, 5))
        scrollbar_panier.pack(side="right", fill="y")
        
        self.panier_frame = panier_frame
        self.panier_items = []

        # Totaux
        cadre_total = tk.Frame(cadre_contenu, bg=COLORS['light'])
        cadre_total.pack(anchor="w", pady=10, fill="x")
        
        self.label_total_ht = tk.Label(cadre_total, text="Total HT : 0 FCFA", 
                                       font=('Arial', 11, 'bold'), fg=COLORS['primary'], bg=COLORS['light'])
        self.label_total_ht.pack(anchor="w")
        
        self.label_tva = tk.Label(cadre_total, text="TVA (18%) : 0 FCFA", 
                                  font=('Arial', 11), fg=COLORS['warning'], bg=COLORS['light'])
        self.label_tva.pack(anchor="w")
        
        self.label_total_ttc = tk.Label(cadre_total, text="Total TTC : 0 FCFA", 
                                        font=('Arial', 14, 'bold'), fg=COLORS['success'], bg=COLORS['light'])
        self.label_total_ttc.pack(anchor="w", pady=(5, 0))

        # ============================================================
        # LIGNE : Moyen de paiement (gauche) + Boutons (droite)
        # ============================================================
        cadre_ligne_basse = tk.Frame(cadre_contenu, bg=COLORS['light'])
        cadre_ligne_basse.pack(anchor="w", pady=(10, 10), fill="x")

        # Partie gauche : Moyen de paiement
        cadre_gauche_paiement = tk.Frame(cadre_ligne_basse, bg=COLORS['light'])
        cadre_gauche_paiement.pack(side="left", fill="x", expand=True)

        tk.Label(cadre_gauche_paiement, text="Moyen de paiement :", font=('Arial', 10), 
                bg=COLORS['light'], fg=COLORS['dark']).pack(side="left", padx=(0, 10))
        self.combo_paiement = ttk.Combobox(cadre_gauche_paiement, values=MOYENS_PAIEMENT, 
                                           state="readonly", width=20, font=('Arial', 10))
        self.combo_paiement.current(0)
        self.combo_paiement.pack(side="left")

        # Partie droite : Boutons Valider + Vider alignés à droite
        cadre_droite_boutons = tk.Frame(cadre_ligne_basse, bg=COLORS['light'])
        cadre_droite_boutons.pack(side="right")

        ttk.Button(cadre_droite_boutons, text="✅ Valider la commande", 
                  command=self.valider_commande, style='Accent.TButton').pack(side="left", padx=5)
        
        ttk.Button(cadre_droite_boutons, text="🗑️ Vider le panier", 
                  command=self.vider_panier, style='Danger.TButton').pack(side="left", padx=5)

        # Avis (en dessous)
        tk.Label(cadre_contenu, text="Avis :", font=('Arial', 10), 
                bg=COLORS['light'], fg=COLORS['dark']).pack(anchor="w", pady=(10, 5))
        self.combo_avis = ttk.Combobox(cadre_contenu, values=["bon", "excellent", "pimenté", "parfait"], 
                                       state="readonly", width=20, font=('Arial', 10))
        self.combo_avis.current(0)
        self.combo_avis.pack(anchor="w", pady=(0, 20))

        tk.Frame(contenu, height=50, bg=COLORS['light']).pack()

    # ==============================================================
    # ONGLET 2 : COMMANDES
    # ==============================================================
    def construire_onglet_commandes(self):
        cadre = self.onglet_commandes
        cadre.configure(bg=COLORS['light'])

        # Canvas avec scroll pour la liste
        canvas = tk.Canvas(cadre, bg=COLORS['light'], highlightthickness=0)
        scrollbar = ttk.Scrollbar(cadre, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg=COLORS['light'])

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw", width=canvas.winfo_width())
        canvas.configure(yscrollcommand=scrollbar.set)

        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        
        def _on_enter(event):
            canvas.bind_all("<MouseWheel>", _on_mousewheel)
        
        def _on_leave(event):
            canvas.unbind_all("<MouseWheel>")
        
        canvas.bind("<Enter>", _on_enter)
        canvas.bind("<Leave>", _on_leave)
        # Pour Linux
        canvas.bind("<Button-4>", lambda e: canvas.yview_scroll(-1, "units"))
        canvas.bind("<Button-5>", lambda e: canvas.yview_scroll(1, "units"))

        def _configure_canvas(event):
            canvas.itemconfig(1, width=event.width)
        
        canvas.bind("<Configure>", _configure_canvas)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        contenu = scrollable_frame
        contenu.configure(bg=COLORS['light'])

        titre = tk.Label(contenu, text="📋 Liste des commandes", 
                        font=('Arial', 14, 'bold'), fg=COLORS['primary'], bg=COLORS['light'])
        titre.pack(anchor="w", padx=10, pady=(10, 10))

        cadre_filtres = ttk.LabelFrame(contenu, text="🔍 Filtres", padding=15)
        cadre_filtres.pack(anchor="w", padx=10, pady=10, fill="x")

        ligne1 = tk.Frame(cadre_filtres, bg=COLORS['light'])
        ligne1.pack(fill="x", pady=5)
        
        tk.Label(ligne1, text="Client :", font=('Arial', 9), bg=COLORS['light']).pack(side="left", padx=5)
        self.filtre_client = ttk.Entry(ligne1, width=12)
        self.filtre_client.pack(side="left", padx=5)

        tk.Label(ligne1, text="Plat :", font=('Arial', 9), bg=COLORS['light']).pack(side="left", padx=5)
        self.filtre_plat = ttk.Entry(ligne1, width=12)
        self.filtre_plat.pack(side="left", padx=5)

        tk.Label(ligne1, text="ID :", font=('Arial', 9), bg=COLORS['light']).pack(side="left", padx=5)
        self.filtre_id = ttk.Entry(ligne1, width=8)
        self.filtre_id.pack(side="left", padx=5)

        ligne2 = tk.Frame(cadre_filtres, bg=COLORS['light'])
        ligne2.pack(fill="x", pady=5)
        
        tk.Label(ligne2, text="Periode :", font=('Arial', 9), bg=COLORS['light']).pack(side="left", padx=5)
        self.filtre_periode_commande = ttk.Combobox(ligne2, values=PERIODES, state="readonly", width=12)
        self.filtre_periode_commande.current(0)
        self.filtre_periode_commande.pack(side="left", padx=5)

        tk.Label(ligne2, text="Avis :", font=('Arial', 9), bg=COLORS['light']).pack(side="left", padx=5)
        self.filtre_avis = ttk.Combobox(ligne2, values=["Tous", "bon", "excellent", "pimenté", "parfait"], 
                                        state="readonly", width=10)
        self.filtre_avis.current(0)
        self.filtre_avis.pack(side="left", padx=5)

        ligne3 = tk.Frame(cadre_filtres, bg=COLORS['light'])
        ligne3.pack(fill="x", pady=10)
        
        ttk.Button(ligne3, text="🔍 Filtrer", command=self.appliquer_filtres_commandes).pack(side="left", padx=5)
        ttk.Button(ligne3, text="🔄 Reinitialiser", command=self.reinitialiser_filtres_commandes).pack(side="left", padx=5)
        ttk.Button(ligne3, text="📤 Exporter CSV", command=self.exporter_commandes_csv).pack(side="left", padx=5)

        cadre_tableau = tk.Frame(contenu, bg=COLORS['light'])
        cadre_tableau.pack(fill="both", expand=True, padx=10, pady=5)

        scroll_y = ttk.Scrollbar(cadre_tableau, orient="vertical")
        scroll_x = ttk.Scrollbar(cadre_tableau, orient="horizontal")

        colonnes = ("id", "date", "heure", "client", "plats", "total_ht", "tva", "total_ttc", "avis", "paiement")
        self.tableau_commandes = ttk.Treeview(cadre_tableau, columns=colonnes, show="headings",
                                             yscrollcommand=scroll_y.set, xscrollcommand=scroll_x.set,
                                             height=15, selectmode='extended')
        titres = ["ID", "Date", "Heure", "Client", "Plats", "HT", "TVA", "TTC", "Avis", "Paiement"]
        largeurs = [40, 80, 60, 100, 150, 80, 80, 80, 80, 90]
        for col, titre, largeur in zip(colonnes, titres, largeurs):
            self.tableau_commandes.heading(col, text=titre)
            self.tableau_commandes.column(col, width=largeur, minwidth=largeur//2)

        scroll_y.config(command=self.tableau_commandes.yview)
        scroll_x.config(command=self.tableau_commandes.xview)

        self.tableau_commandes.pack(side="left", fill="both", expand=True)
        scroll_y.pack(side="right", fill="y")
        scroll_x.pack(side="bottom", fill="x")
        
        # Bind pour la sélection → stocke l'ID sans ouvrir la fenêtre
        self.tableau_commandes.bind("<<TreeviewSelect>>", self.on_commande_selectionnee)

        cadre_bas = tk.Frame(contenu, bg=COLORS['light'])
        cadre_bas.pack(anchor="w", padx=10, pady=10, fill="x")
        
        self.label_resultat_commandes = tk.Label(cadre_bas, text="", font=('Arial', 10), 
                                                bg=COLORS['light'], fg=COLORS['primary'])
        self.label_resultat_commandes.pack(side="left")

        cadre_boutons = tk.Frame(cadre_bas, bg=COLORS['light'])
        cadre_boutons.pack(side="right")
        
        # Bouton "🖨️ Recu" → ouvre les détails de la commande sélectionnée
        ttk.Button(cadre_boutons, text="🖨️ Recu", 
                  command=self.afficher_recu_selection,
                  style='Print.TButton').pack(side="right", padx=5)
        
        ttk.Button(cadre_boutons, text="🗑️ Supprimer", 
                  command=self.supprimer_commandes_selectionnees,
                  style='Danger.TButton').pack(side="right", padx=5)
        
        tk.Frame(contenu, height=50, bg=COLORS['light']).pack()

        self.appliquer_filtres_commandes()

    # ==============================================================
    # GESTION DE LA SÉLECTION (sans ouverture automatique)
    # ==============================================================

    def on_commande_selectionnee(self, event):
        """Stocke l'ID de la commande sélectionnée sans ouvrir de fenêtre."""
        selection = self.tableau_commandes.selection()
        if not selection:
            self.commande_selectionnee_id = None
            return
        valeurs = self.tableau_commandes.item(selection[0], "values")
        if not valeurs:
            self.commande_selectionnee_id = None
            return
        self.commande_selectionnee_id = valeurs[0]

    # ==============================================================
    # AFFICHAGE DU RECU POUR LA COMMANDE SÉLECTIONNÉE
    # ==============================================================

    def afficher_recu_selection(self):
        """Ouvre la fenêtre de détails pour la commande sélectionnée."""
        if not self.commande_selectionnee_id:
            messagebox.showwarning("Aucune sélection", "Veuillez sélectionner une commande dans la liste.")
            return
        self.ouvrir_details_commande(self.commande_selectionnee_id)

    # ==============================================================
    # FENÊTRE FLOTTANTE DES DÉTAILS
    # ==============================================================

    def ouvrir_details_commande(self, commande_id):
        """Ouvre une fenêtre flottante avec les détails de la commande."""
        commandes = charger_commandes()
        cmd = None
        for c in commandes:
            if str(c.get('ID', '')) == str(commande_id):
                cmd = c
                break
        if cmd is None:
            messagebox.showerror("Erreur", "Commande non trouvée.")
            return

        fenetre = tk.Toplevel(self)
        fenetre.title(f"Détails de la commande #{commande_id}")
        fenetre.geometry("420x600")
        fenetre.configure(bg=COLORS['white'])
        fenetre.transient(self)
        # Ne pas utiliser grab_set() pour éviter de bloquer la souris
        # fenetre.grab_set()
        fenetre.focus_force()

        # Centrer la fenêtre
        fenetre.update_idletasks()
        x = (self.winfo_screenwidth() - fenetre.winfo_width()) // 2
        y = (self.winfo_screenheight() - fenetre.winfo_height()) // 2
        fenetre.geometry(f"+{x}+{y}")

        # Titre
        tk.Label(fenetre, text=f"📄 Détails de la commande n°{commande_id}",
                font=('Arial', 14, 'bold'), bg=COLORS['white'], fg=COLORS['primary']).pack(pady=(15, 10))

        # Zone de texte avec scroll
        cadre_texte = tk.Frame(fenetre, bg=COLORS['white'])
        cadre_texte.pack(fill="both", expand=True, padx=15, pady=5)

        scrollbar = ttk.Scrollbar(cadre_texte)
        scrollbar.pack(side="right", fill="y")

        texte_details = tk.Text(cadre_texte, height=20, width=45, font=('Arial', 9),
                                wrap='word', yscrollcommand=scrollbar.set, bg='white')
        texte_details.pack(side="left", fill="both", expand=True)
        scrollbar.config(command=texte_details.yview)

        # Remplir les détails
        total_ht = float(cmd.get('Total HT (€)', '0'))
        tva = float(cmd.get('TVA (€)', '0'))
        total_ttc = float(cmd.get('Total TTC (€)', '0'))

        details = f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📋 COMMANDE N°{cmd.get('ID', '0000')}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

👤 Client : {cmd.get('Client', 'Non spécifié')}
📅 Date : {cmd.get('Date', 'Non spécifiée')}
🕐 Heure : {cmd.get('Heure', 'Non spécifiée')}
💳 Paiement : {cmd.get('Paiement', 'Non spécifié')}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🛒 PLATS COMMANDÉS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{self.formater_plats(cmd.get('Plats', ''))}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
💰 TOTAUX
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Total HT : {format_price(total_ht)}
TVA (18%) : {format_price(tva)}
Total TTC : {format_price(total_ttc)}

⭐ Avis : {cmd.get('Avis', 'Non spécifié')}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
        texte_details.insert("1.0", details)
        texte_details.config(state="disabled")
        texte_details.update_idletasks()

        # Frame pour les boutons (alignés verticalement à gauche)
        bouton_frame = tk.Frame(fenetre, bg=COLORS['white'])
        bouton_frame.pack(fill="x", pady=10, padx=15)

        # Bouton Aperçu
        ttk.Button(
            bouton_frame,
            text="🖨️ Aperçu",
            command=lambda: self._imprimer_recu_par_id(commande_id, fenetre),
            style='Print.TButton'
        ).pack(fill="x", pady=3)

        # Bouton Générer PDF
        ttk.Button(
            bouton_frame,
            text="📄 Générer PDF",
            command=lambda: self._generer_pdf_par_id(commande_id, fenetre),
            style='Accent.TButton'
        ).pack(fill="x", pady=3)

        # Bouton Voir les reçus
        ttk.Button(
            bouton_frame,
            text="📁 Voir les reçus",
            command=self.ouvrir_dossier_recus,
            style='Accent.TButton'
        ).pack(fill="x", pady=3)

        # Bouton Fermer
        ttk.Button(
            bouton_frame,
            text="❌ Fermer",
            command=fenetre.destroy,
            style='Danger.TButton'
        ).pack(fill="x", pady=3)

    # ==============================================================
    # FONCTIONS D'IMPRESSION / GÉNÉRATION DEPUIS LA FENÊTRE
    # ==============================================================

    def _imprimer_recu_par_id(self, commande_id, fenetre=None):
        """Affiche l'aperçu du reçu pour l'ID donné, puis ferme la fenêtre."""
        if commande_id:
            imprimer_recu_depuis_commande(commande_id, self)
            if fenetre:
                fenetre.destroy()

    def _generer_pdf_par_id(self, commande_id, fenetre=None):
        """Génère le PDF pour l'ID donné, puis ferme la fenêtre."""
        if not commande_id:
            messagebox.showwarning("Aucune commande", "Veuillez sélectionner une commande.")
            return
        try:
            commandes = charger_commandes()
            for cmd in commandes:
                if str(cmd.get('ID', '')) == str(commande_id):
                    commande_info = {
                        'id': cmd.get('ID', '0000'),
                        'date': cmd.get('Date', datetime.now().strftime('%Y-%m-%d')),
                        'heure': cmd.get('Heure', datetime.now().strftime('%H:%M')),
                        'client': cmd.get('Client', 'Client'),
                        'plats': [p.strip() for p in cmd.get('Plats', '').split('+') if p.strip()],
                        'avis': cmd.get('Avis', ''),
                        'paiement': cmd.get('Paiement', 'Non spécifié')
                    }
                    fichier = generer_recu(commande_info)
                    messagebox.showinfo("Succès", f"✅ Reçu généré avec succès !\n\nFichier : {os.path.basename(fichier)}")
                    if fenetre:
                        fenetre.destroy()
                    return
            messagebox.showerror("Erreur", "Commande non trouvée.")
        except Exception as e:
            messagebox.showerror("Erreur", f"❌ Erreur lors de la génération du PDF : {str(e)}")

    # ==============================================================
    # AUTRES MÉTHODES DE GESTION DES COMMANDES
    # ==============================================================

    def formater_plats(self, plats_str):
        if not plats_str:
            return "Aucun plat"
        plats = [p.strip() for p in plats_str.split('+') if p.strip()]
        resultat = ""
        for plat in plats:
            if ' x' in plat:
                nom, qte = plat.split(' x')
                resultat += f"   • {nom.strip()} x{qte}\n"
            else:
                resultat += f"   • {plat}\n"
        return resultat

    def imprimer_recu_selectionne(self):
        """Imprime un reçu pour la commande sélectionnée (ancienne méthode)."""
        selection = self.tableau_commandes.selection()
        if not selection:
            messagebox.showwarning("Aucune selection", "Veuillez selectionner une commande.")
            return
        
        valeurs = self.tableau_commandes.item(selection[0], "values")
        if not valeurs:
            return
        
        commande_id = valeurs[0]
        imprimer_recu_depuis_commande(commande_id, self)

    def supprimer_commandes_selectionnees(self):
        selection = self.tableau_commandes.selection()
        if not selection:
            messagebox.showwarning("Aucune selection", "Selectionne d'abord une ou plusieurs commandes.")
            return
        
        ids_a_supprimer = []
        for item in selection:
            valeurs = self.tableau_commandes.item(item, "values")
            if valeurs:
                ids_a_supprimer.append(valeurs[0])
        
        if not ids_a_supprimer:
            return
        
        if len(ids_a_supprimer) == 1:
            confirmation = messagebox.askyesno("Confirmation", f"⚠️ Supprimer la commande n°{ids_a_supprimer[0]} ?")
        else:
            confirmation = messagebox.askyesno("Confirmation", 
                f"⚠️ Supprimer {len(ids_a_supprimer)} commandes (IDs: {', '.join(ids_a_supprimer)}) ?")
        
        if not confirmation:
            return
        
        commandes = [c for c in charger_commandes() if str(c.get("ID", "")) not in ids_a_supprimer]
        sauvegarder_commandes(commandes)
        
        self.appliquer_filtres_commandes()
        
        # Réinitialiser la sélection
        self.commande_selectionnee_id = None
        
        messagebox.showinfo("Succes", f"✅ {len(ids_a_supprimer)} commande(s) supprimee(s).")

    def appliquer_filtres_commandes(self):
        client_recherche = self.filtre_client.get().strip().lower()
        plat_recherche = self.filtre_plat.get().strip().lower()
        id_recherche = self.filtre_id.get().strip()
        avis_recherche = self.filtre_avis.get()
        periode = self.filtre_periode_commande.get()

        for ligne in self.tableau_commandes.get_children():
            self.tableau_commandes.delete(ligne)

        total_ht = 0
        total_ttc = 0
        nb = 0
        
        try:
            for c in charger_commandes():
                if id_recherche and str(c.get("ID", "")) != id_recherche:
                    continue
                if client_recherche and client_recherche not in c.get("Client", "").lower():
                    continue
                if plat_recherche and plat_recherche not in c.get("Plats", "").lower():
                    continue
                if avis_recherche != "Tous" and c.get("Avis", "") != avis_recherche:
                    continue
                if periode != "Toutes" and not date_dans_periode(c.get("Date", ""), periode):
                    continue

                total_ht_cmd = float(c.get("Total HT (€)", c.get("Total (€)", "0")))
                tva_cmd = float(c.get("TVA (€)", "0"))
                total_ttc_cmd = float(c.get("Total TTC (€)", c.get("Total (€)", "0")))
                
                self.tableau_commandes.insert("", "end", values=(
                    c.get("ID", ""), 
                    c.get("Date", ""), 
                    c.get("Heure", ""), 
                    c.get("Client", ""), 
                    c.get("Plats", ""), 
                    format_price_table(total_ht_cmd),
                    format_price_table(tva_cmd),
                    format_price_table(total_ttc_cmd),
                    c.get("Avis", ""),
                    c.get("Paiement", "")
                ))
                total_ht += total_ht_cmd
                total_ttc += total_ttc_cmd
                nb += 1
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur lors du chargement : {str(e)}")

        self.label_resultat_commandes.config(
            text=f"📊 {nb} commande(s) - HT : {format_price(total_ht)} - TTC : {format_price(total_ttc)}"
        )

    def reinitialiser_filtres_commandes(self):
        self.filtre_client.delete(0, tk.END)
        self.filtre_plat.delete(0, tk.END)
        self.filtre_id.delete(0, tk.END)
        self.filtre_avis.current(0)
        self.filtre_periode_commande.current(0)
        self.appliquer_filtres_commandes()

    def exporter_commandes_csv(self):
        if not self.tableau_commandes.get_children():
            messagebox.showwarning("Aucune donnee", "Aucune commande a exporter.")
            return
        
        nom_fichier = f"export_commandes_{date.today().isoformat()}.csv"
        try:
            with open(nom_fichier, mode="w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(["ID", "Date", "Heure", "Client", "Plats", "Total HT (€)", "TVA (€)", "Total TTC (€)", "Avis", "Paiement"])
                for ligne in self.tableau_commandes.get_children():
                    valeurs = self.tableau_commandes.item(ligne, "values")
                    writer.writerow(valeurs)
            messagebox.showinfo("Export reussi", f"✅ Commandes exportees dans {nom_fichier}")
        except Exception as e:
            messagebox.showerror("Erreur d'export", f"Erreur : {str(e)}")

    # ==============================================================
    # ONGLET 3 : DEPENSES (protégé par mot de passe manager)
    # ==============================================================
    def construire_onglet_depenses(self):
        """Construit l'onglet Dépenses avec un verrouillage par mot de passe manager."""
        cadre = self.onglet_depenses
        cadre.configure(bg=COLORS['light'])

        # Frame conteneur qui sera rempli soit par le verrou soit par le contenu
        self.depenses_frame = tk.Frame(cadre, bg=COLORS['light'])
        self.depenses_frame.pack(fill="both", expand=True)

        # Par défaut, afficher l'écran de verrouillage
        self.afficher_verrou_depenses()

    def afficher_verrou_depenses(self):
        """Affiche l'écran de verrouillage pour l'onglet Dépenses."""
        # Vider le frame
        for widget in self.depenses_frame.winfo_children():
            widget.destroy()

        if self.bloque_depenses:
            # Affichage définitif de blocage
            label_bloque = tk.Label(self.depenses_frame, 
                                    text="🔒 Accès aux Dépenses définitivement bloqué\n\nTrop de tentatives échouées.",
                                    font=('Arial', 14, 'bold'), 
                                    bg=COLORS['light'], fg=COLORS['danger'])
            label_bloque.pack(pady=(100, 20))
            return

        # Message de verrouillage
        label_verrou = tk.Label(self.depenses_frame, 
                                text="🔒 Accès aux Dépenses\n\nCe service est protégé par le mot de passe manager.",
                                font=('Arial', 14, 'bold'), 
                                bg=COLORS['light'], fg=COLORS['danger'])
        label_verrou.pack(pady=(100, 20))

        # Bouton pour déverrouiller
        self.btn_deverrouiller_depenses = ttk.Button(self.depenses_frame, 
                                     text="🔑 Déverrouiller", 
                                     command=self.demander_mot_de_passe_depenses,
                                     style='Accent.TButton')
        self.btn_deverrouiller_depenses.pack(pady=10)

        self.acces_depenses = False

    def demander_mot_de_passe_depenses(self):
        """Demande le mot de passe manager pour déverrouiller les dépenses."""
        if self.bloque_depenses:
            messagebox.showerror("Accès refusé", "Accès aux Dépenses définitivement bloqué.")
            return
        if self.demander_mot_de_passe_manager("depenses"):
            self.acces_depenses = True
            self.afficher_contenu_depenses()
        else:
            # En cas d'échec, le verrou reste affiché (avec message d'erreur déjà géré)
            if not self.bloque_depenses:
                # Réessayer
                self.afficher_verrou_depenses()
            else:
                # Si bloqué, afficher le message définitif
                self.afficher_verrou_depenses()

    def afficher_contenu_depenses(self):
        """Affiche le contenu réel des dépenses après déverrouillage."""
        # Vider le frame
        for widget in self.depenses_frame.winfo_children():
            widget.destroy()

        # --- CORRECTION : Forcer la largeur du canvas avec update_idletasks ---
        # Créer un canvas avec scroll
        canvas = tk.Canvas(self.depenses_frame, bg=COLORS['light'], highlightthickness=0)
        scrollbar = ttk.Scrollbar(self.depenses_frame, orient="vertical", command=canvas.yview)

        # Pack d'abord pour que le canvas prenne sa taille
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Forcer la mise à jour de la géométrie
        self.depenses_frame.update_idletasks()

        # Maintenant on peut créer le frame défilant avec la bonne largeur
        scrollable_frame = tk.Frame(canvas, bg=COLORS['light'])

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw",
                             width=canvas.winfo_width())
        canvas.configure(yscrollcommand=scrollbar.set)

        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        def _on_enter(event):
            canvas.bind_all("<MouseWheel>", _on_mousewheel)
        def _on_leave(event):
            canvas.unbind_all("<MouseWheel>")
        canvas.bind("<Enter>", _on_enter)
        canvas.bind("<Leave>", _on_leave)
        # Pour Linux
        canvas.bind("<Button-4>", lambda e: canvas.yview_scroll(-1, "units"))
        canvas.bind("<Button-5>", lambda e: canvas.yview_scroll(1, "units"))

        # Redimensionnement automatique
        def _configure_canvas(event):
            canvas.itemconfig(1, width=event.width)
        canvas.bind("<Configure>", _configure_canvas)

        contenu = scrollable_frame
        contenu.configure(bg=COLORS['light'])

        # --- Contenu des dépenses (copié depuis l'ancienne version) ---
        titre = tk.Label(contenu, text="💰 Gestion des depenses", 
                        font=('Arial', 14, 'bold'), fg=COLORS['primary'], bg=COLORS['light'])
        titre.pack(anchor="w", padx=10, pady=(10, 10))

        cadre_form = ttk.LabelFrame(contenu, text="➕ Ajouter une depense", padding=15)
        cadre_form.pack(anchor="w", padx=10, pady=10, fill="x")

        ligne_form = tk.Frame(cadre_form, bg=COLORS['light'])
        ligne_form.pack(fill="x", pady=5)

        tk.Label(ligne_form, text="Type :", font=('Arial', 9), bg=COLORS['light']).pack(side="left", padx=5)
        self.combo_type_depense = ttk.Combobox(ligne_form, values=TYPES_DEPENSE, state="readonly", width=15)
        self.combo_type_depense.current(0)
        self.combo_type_depense.pack(side="left", padx=5)

        tk.Label(ligne_form, text="Description :", font=('Arial', 9), bg=COLORS['light']).pack(side="left", padx=5)
        self.champ_description_depense = ttk.Entry(ligne_form, width=25)
        self.champ_description_depense.pack(side="left", padx=5)

        tk.Label(ligne_form, text="Montant :", font=('Arial', 9), bg=COLORS['light']).pack(side="left", padx=5)
        self.champ_montant_depense = ttk.Entry(ligne_form, width=12)
        self.champ_montant_depense.pack(side="left", padx=5)

        ttk.Button(ligne_form, text="➕ Ajouter", command=self.ajouter_depense, 
                  style='Accent.TButton').pack(side="left", padx=10)

        cadre_filtres = ttk.LabelFrame(contenu, text="🔍 Filtres", padding=15)
        cadre_filtres.pack(anchor="w", padx=10, pady=10, fill="x")

        ligne_filtre = tk.Frame(cadre_filtres, bg=COLORS['light'])
        ligne_filtre.pack(fill="x", pady=5)

        tk.Label(ligne_filtre, text="Type :", font=('Arial', 9), bg=COLORS['light']).pack(side="left", padx=5)
        self.filtre_type_depense = ttk.Combobox(ligne_filtre, values=["Tous"] + TYPES_DEPENSE, 
                                                state="readonly", width=15)
        self.filtre_type_depense.current(0)
        self.filtre_type_depense.pack(side="left", padx=5)

        tk.Label(ligne_filtre, text="Periode :", font=('Arial', 9), bg=COLORS['light']).pack(side="left", padx=5)
        self.filtre_periode_depense = ttk.Combobox(ligne_filtre, values=PERIODES, state="readonly", width=14)
        self.filtre_periode_depense.current(0)
        self.filtre_periode_depense.pack(side="left", padx=5)

        ttk.Button(ligne_filtre, text="🔍 Filtrer", command=self.appliquer_filtres_depenses).pack(side="left", padx=5)
        ttk.Button(ligne_filtre, text="🔄 Reinitialiser", command=self.reinitialiser_filtres_depenses).pack(side="left", padx=5)

        cadre_tableau = tk.Frame(contenu, bg=COLORS['light'])
        cadre_tableau.pack(fill="both", expand=True, padx=10, pady=5)

        scroll_y = ttk.Scrollbar(cadre_tableau, orient="vertical")
        scroll_x = ttk.Scrollbar(cadre_tableau, orient="horizontal")

        colonnes = ("id", "date", "type", "description", "montant")
        self.tableau_depenses = ttk.Treeview(cadre_tableau, columns=colonnes, show="headings",
                                            yscrollcommand=scroll_y.set, xscrollcommand=scroll_x.set,
                                            height=10)
        titres = ["ID", "Date", "Type", "Description", "Montant"]
        largeurs = [40, 90, 120, 180, 90]
        for col, titre, largeur in zip(colonnes, titres, largeurs):
            self.tableau_depenses.heading(col, text=titre)
            self.tableau_depenses.column(col, width=largeur, minwidth=largeur//2)

        scroll_y.config(command=self.tableau_depenses.yview)
        scroll_x.config(command=self.tableau_depenses.xview)

        self.tableau_depenses.pack(side="left", fill="both", expand=True)
        scroll_y.pack(side="right", fill="y")
        scroll_x.pack(side="bottom", fill="x")

        cadre_bas = tk.Frame(contenu, bg=COLORS['light'])
        cadre_bas.pack(anchor="w", padx=10, pady=10, fill="x")
        
        self.label_resultat_depenses = tk.Label(cadre_bas, text="", font=('Arial', 10), 
                                               bg=COLORS['light'], fg=COLORS['primary'])
        self.label_resultat_depenses.pack(side="left")

        ttk.Button(cadre_bas, text="🗑️ Supprimer la depense", 
                  command=self.supprimer_depense_selectionnee,
                  style='Danger.TButton').pack(side="right", padx=5)

        self.appliquer_filtres_depenses()
        # Mise à jour finale de la scrollregion
        canvas.configure(scrollregion=canvas.bbox("all"))

    # ==============================================================
    # MÉTHODES DE GESTION DES DEPENSES
    # ==============================================================
    def ajouter_depense(self):
        type_depense = self.combo_type_depense.get()
        description = self.champ_description_depense.get().strip()
        try:
            montant = float(self.champ_montant_depense.get().strip())
        except ValueError:
            messagebox.showwarning("Montant invalide", "Le montant doit etre un nombre.")
            return

        ajouter_depense_fichier(type_depense, description, montant)
        messagebox.showinfo("Depense ajoutee", f"✅ {type_depense} : {format_price(montant)} ajoutee.")

        self.champ_description_depense.delete(0, tk.END)
        self.champ_montant_depense.delete(0, tk.END)
        self.appliquer_filtres_depenses()

    def appliquer_filtres_depenses(self):
        type_recherche = self.filtre_type_depense.get()
        periode = self.filtre_periode_depense.get()

        for ligne in self.tableau_depenses.get_children():
            self.tableau_depenses.delete(ligne)

        total_affiche = 0
        nb = 0
        for d in charger_depenses():
            if type_recherche != "Tous" and d.get("Type", "") != type_recherche:
                continue
            if not date_dans_periode(d.get("Date", ""), periode):
                continue
            self.tableau_depenses.insert("", "end", values=(
                d.get("ID", ""), 
                d.get("Date", ""), 
                d.get("Type", ""), 
                d.get("Description", ""), 
                format_price_table(float(d.get("Montant (€)", "0")))
            ))
            try:
                total_affiche += float(d.get("Montant (€)", "0"))
            except:
                pass
            nb += 1

        self.label_resultat_depenses.config(
            text=f"📊 {nb} depense(s) affichee(s) - Total : {format_price(total_affiche)}"
        )

    def reinitialiser_filtres_depenses(self):
        self.filtre_type_depense.current(0)
        self.filtre_periode_depense.current(0)
        self.appliquer_filtres_depenses()

    def supprimer_depense_selectionnee(self):
        selection = self.tableau_depenses.selection()
        if not selection:
            messagebox.showwarning("Aucune selection", "Selectionne d'abord une depense dans le tableau.")
            return
        valeurs = self.tableau_depenses.item(selection[0], "values")
        id_a_supprimer = valeurs[0] if valeurs else ""
        if not id_a_supprimer:
            return
        if not messagebox.askyesno("Confirmation", f"⚠️ Supprimer la depense n°{id_a_supprimer} ?"):
            return
        depenses = [d for d in charger_depenses() if str(d.get("ID", "")) != str(id_a_supprimer)]
        sauvegarder_depenses(depenses)
        self.appliquer_filtres_depenses()
        messagebox.showinfo("Succes", f"✅ Depense n°{id_a_supprimer} supprimee.")

    # ==============================================================
    # ONGLET 4 : BILAN (protégé par mot de passe manager, avec scroll)
    # ==============================================================
    def construire_onglet_bilan(self):
        """Construit l'onglet Bilan avec un verrouillage par mot de passe manager."""
        cadre = self.onglet_bilan
        cadre.configure(bg=COLORS['light'])

        # Frame conteneur qui sera rempli soit par le verrou soit par le contenu
        self.bilan_frame = tk.Frame(cadre, bg=COLORS['light'])
        self.bilan_frame.pack(fill="both", expand=True)

        # Par défaut, afficher l'écran de verrouillage
        self.afficher_verrou_bilan()

    def afficher_verrou_bilan(self):
        """Affiche l'écran de verrouillage pour l'onglet Bilan."""
        # Vider le frame
        for widget in self.bilan_frame.winfo_children():
            widget.destroy()

        if self.bloque_bilan:
            label_bloque = tk.Label(self.bilan_frame, 
                                    text="🔒 Accès au Bilan définitivement bloqué\n\nTrop de tentatives échouées.",
                                    font=('Arial', 14, 'bold'), 
                                    bg=COLORS['light'], fg=COLORS['danger'])
            label_bloque.pack(pady=(100, 20))
            return

        # Message de verrouillage
        label_verrou = tk.Label(self.bilan_frame, 
                                text="🔒 Accès au Bilan Manager\n\nCe service est protégé par un mot de passe.",
                                font=('Arial', 14, 'bold'), 
                                bg=COLORS['light'], fg=COLORS['danger'])
        label_verrou.pack(pady=(100, 20))

        # Bouton pour déverrouiller
        self.btn_deverrouiller_bilan = ttk.Button(self.bilan_frame, 
                                     text="🔑 Déverrouiller", 
                                     command=self.demander_mot_de_passe_bilan,
                                     style='Accent.TButton')
        self.btn_deverrouiller_bilan.pack(pady=10)

        self.acces_bilan = False

    def demander_mot_de_passe_bilan(self):
        """Demande le mot de passe manager pour déverrouiller le bilan."""
        if self.bloque_bilan:
            messagebox.showerror("Accès refusé", "Accès au Bilan définitivement bloqué.")
            return
        if self.demander_mot_de_passe_manager("bilan"):
            self.acces_bilan = True
            self.afficher_contenu_bilan()
        else:
            if not self.bloque_bilan:
                self.afficher_verrou_bilan()
            else:
                self.afficher_verrou_bilan()

    def afficher_contenu_bilan(self):
        """Affiche le contenu réel du bilan avec une barre de défilement."""
        # Vider le frame
        for widget in self.bilan_frame.winfo_children():
            widget.destroy()

        # --- CORRECTION : Forcer la largeur du canvas avec update_idletasks ---
        canvas = tk.Canvas(self.bilan_frame, bg=COLORS['light'], highlightthickness=0)
        scrollbar = ttk.Scrollbar(self.bilan_frame, orient="vertical", command=canvas.yview)

        # Pack d'abord pour que le canvas prenne sa taille
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Forcer la mise à jour de la géométrie
        self.bilan_frame.update_idletasks()

        # Créer le frame intérieur avec la bonne largeur
        scrollable_frame = tk.Frame(canvas, bg=COLORS['light'])

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw",
                             width=canvas.winfo_width())
        canvas.configure(yscrollcommand=scrollbar.set)

        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        def _on_enter(event):
            canvas.bind_all("<MouseWheel>", _on_mousewheel)
        def _on_leave(event):
            canvas.unbind_all("<MouseWheel>")
        canvas.bind("<Enter>", _on_enter)
        canvas.bind("<Leave>", _on_leave)
        # Pour Linux
        canvas.bind("<Button-4>", lambda e: canvas.yview_scroll(-1, "units"))
        canvas.bind("<Button-5>", lambda e: canvas.yview_scroll(1, "units"))

        # Redimensionnement automatique
        def _configure_canvas(event):
            canvas.itemconfig(1, width=event.width)
        canvas.bind("<Configure>", _configure_canvas)

        contenu = scrollable_frame
        contenu.configure(bg=COLORS['light'])

        # --- Contenu du bilan ---
        cadre_entete = tk.Frame(contenu, bg=COLORS['light'])
        cadre_entete.pack(fill="x", padx=20, pady=(20, 10))

        titre = tk.Label(cadre_entete, text="📊 Bilan financier", 
                        font=('Arial', 16, 'bold'), fg=COLORS['primary'], bg=COLORS['light'])
        titre.pack(side="left")

        cadre_solde = tk.Frame(cadre_entete, bg=COLORS['light'], relief='ridge', bd=2)
        cadre_solde.pack(side="right", padx=10)

        tk.Label(cadre_solde, text="SOLDE", 
                font=('Arial', 10, 'bold'), fg=COLORS['white'], 
                bg=COLORS['primary'], padx=15, pady=2).pack(fill="x")

        self.label_solde_principal = tk.Label(cadre_solde, text="0 FCFA", 
                                              font=('Arial', 24, 'bold'), 
                                              fg=COLORS['success'], bg=COLORS['white'],
                                              padx=20, pady=10)
        self.label_solde_principal.pack()

        self.label_status = tk.Label(cadre_solde, text="✅ Bénéfice", 
                                     font=('Arial', 10, 'bold'), 
                                     fg=COLORS['success'], bg=COLORS['white'],
                                     padx=15, pady=2)
        self.label_status.pack()

        cadre_contenu = tk.Frame(contenu, bg=COLORS['light'])
        cadre_contenu.pack(fill="both", expand=True, padx=20, pady=10)

        cadre_periode = ttk.LabelFrame(cadre_contenu, text="📅 Selection de la periode", padding=15)
        cadre_periode.pack(anchor="w", pady=10, fill="x")

        ligne1 = tk.Frame(cadre_periode, bg=COLORS['light'])
        ligne1.pack(fill="x", pady=5)
        
        tk.Label(ligne1, text="Periode :", font=('Arial', 10), bg=COLORS['light']).pack(side="left", padx=5)
        self.combo_periode_bilan = ttk.Combobox(ligne1, values=PERIODES + ["Personnalisee"], 
                                                state="readonly", width=18)
        self.combo_periode_bilan.current(0)
        self.combo_periode_bilan.pack(side="left", padx=5)
        self.combo_periode_bilan.bind("<<ComboboxSelected>>", self.on_bilan_periode_changed)

        ligne2 = tk.Frame(cadre_periode, bg=COLORS['light'])
        ligne2.pack(fill="x", pady=5)
        
        tk.Label(ligne2, text="Du :", font=('Arial', 10), bg=COLORS['light']).pack(side="left", padx=5)
        self.bilan_date_debut = ttk.Entry(ligne2, width=12)
        self.bilan_date_debut.pack(side="left", padx=5)
        self.bilan_date_debut.insert(0, date.today().isoformat())
        self.bilan_date_debut.config(state="disabled")

        tk.Label(ligne2, text="Au :", font=('Arial', 10), bg=COLORS['light']).pack(side="left", padx=5)
        self.bilan_date_fin = ttk.Entry(ligne2, width=12)
        self.bilan_date_fin.pack(side="left", padx=5)
        self.bilan_date_fin.insert(0, date.today().isoformat())
        self.bilan_date_fin.config(state="disabled")

        ttk.Button(cadre_periode, text="📊 Calculer le bilan", 
                  command=self.calculer_et_afficher_bilan,
                  style='Accent.TButton').pack(pady=5)

        ttk.Button(cadre_periode, text="📊 Générer rapport PDF", 
                  command=self.generer_rapport_bilan_pdf,
                  style='Print.TButton').pack(pady=5)

        cadre_resultats = ttk.LabelFrame(cadre_contenu, text="📈 Details", padding=15)
        cadre_resultats.pack(anchor="w", pady=10, fill="both", expand=True)

        grille_resultats = tk.Frame(cadre_resultats, bg=COLORS['light'])
        grille_resultats.pack(fill="x", pady=5)

        cadre_entrees = tk.Frame(grille_resultats, bg=COLORS['light'], relief='groove', bd=1)
        cadre_entrees.pack(side="left", fill="both", expand=True, padx=5)

        tk.Label(cadre_entrees, text="💰 Entrees", 
                font=('Arial', 10, 'bold'), bg=COLORS['success'], fg=COLORS['white'],
                padx=10, pady=5).pack(fill="x")
        self.label_entrees = tk.Label(cadre_entrees, text="0 FCFA", 
                                      font=('Arial', 14, 'bold'), 
                                      fg=COLORS['success'], bg=COLORS['light'],
                                      padx=10, pady=10)
        self.label_entrees.pack()

        cadre_sorties = tk.Frame(grille_resultats, bg=COLORS['light'], relief='groove', bd=1)
        cadre_sorties.pack(side="right", fill="both", expand=True, padx=5)

        tk.Label(cadre_sorties, text="💸 Sorties", 
                font=('Arial', 10, 'bold'), bg=COLORS['danger'], fg=COLORS['white'],
                padx=10, pady=5).pack(fill="x")
        self.label_sorties = tk.Label(cadre_sorties, text="0 FCFA", 
                                      font=('Arial', 14, 'bold'), 
                                      fg=COLORS['danger'], bg=COLORS['light'],
                                      padx=10, pady=10)
        self.label_sorties.pack()

        ttk.Separator(cadre_resultats, orient='horizontal').pack(fill='x', pady=10)

        tk.Label(cadre_resultats, text="📋 Details des depenses par type :", 
                font=('Arial', 11, 'bold'), bg=COLORS['light']).pack(anchor="w", pady=5)
        
        self.text_details_depenses = tk.Text(cadre_resultats, height=8, width=50, 
                                            font=('Arial', 10), state="disabled")
        self.text_details_depenses.pack(anchor="w", fill="both", expand=True, pady=5)

        tk.Frame(contenu, height=50, bg=COLORS['light']).pack()
        
        # Appel initial pour afficher les données (si le bilan a déjà été déverrouillé)
        if self.acces_bilan:
            self.calculer_et_afficher_bilan()

        # Mise à jour finale de la scrollregion
        canvas.configure(scrollregion=canvas.bbox("all"))

    # ==============================================================
    # MÉTHODES DU BILAN
    # ==============================================================
    def on_bilan_periode_changed(self, event=None):
        periode = self.combo_periode_bilan.get()
        etat = "normal" if periode == "Personnalisee" else "disabled"
        self.bilan_date_debut.config(state=etat)
        self.bilan_date_fin.config(state=etat)

    def calculer_et_afficher_bilan(self):
        if not self.acces_bilan:
            messagebox.showerror("Accès refusé", "Vous devez déverrouiller le bilan manager.")
            return
        periode = self.combo_periode_bilan.get()
        date_debut = None
        date_fin = None
        
        if periode == "Personnalisee":
            date_debut = self.bilan_date_debut.get().strip()
            date_fin = self.bilan_date_fin.get().strip()
            if not date_debut or not date_fin:
                messagebox.showwarning("Dates manquantes", "Veuillez saisir les dates de debut et de fin.")
                return

        resultat = calculer_bilan_financier(manager, periode, date_debut, date_fin)
        
        if resultat is None:
            messagebox.showerror("Acces refuse", "❌ Seul le manager peut consulter le bilan.")
            return
            
        entrees, sorties, solde, depenses_par_type = resultat
        
        self.label_entrees.config(text=format_price(entrees))
        self.label_sorties.config(text=format_price(sorties))
        
        self.label_solde_principal.config(text=format_price(solde))
        
        if solde >= 0:
            self.label_solde_principal.config(fg=COLORS['success'])
            self.label_status.config(text="✅ Bénéfice", fg=COLORS['success'])
        else:
            self.label_solde_principal.config(fg=COLORS['danger'])
            self.label_status.config(text="❌ Perte", fg=COLORS['danger'])

        self.text_details_depenses.config(state="normal")
        self.text_details_depenses.delete("1.0", tk.END)
        if depenses_par_type:
            for type_dep, montant in sorted(depenses_par_type.items()):
                self.text_details_depenses.insert(tk.END, f"  • {type_dep}: {format_price(montant)}\n")
        else:
            self.text_details_depenses.insert(tk.END, "Aucune depense sur cette periode.")
        self.text_details_depenses.config(state="disabled")

    # ==============================================================
    # GÉNÉRATION DU RAPPORT PDF (COMPLETE)
    # ==============================================================
    def generer_rapport_bilan_pdf(self):
        """Génère un rapport PDF des entrées et sorties sur la période sélectionnée."""
        if not self.acces_bilan:
            messagebox.showerror("Accès refusé", "Vous devez déverrouiller le bilan manager.")
            return
        periode = self.combo_periode_bilan.get()
        date_debut = None
        date_fin = None
        
        if periode == "Personnalisee":
            date_debut = self.bilan_date_debut.get().strip()
            date_fin = self.bilan_date_fin.get().strip()
            if not date_debut or not date_fin:
                messagebox.showwarning("Dates manquantes", "Veuillez saisir les dates de debut et de fin.")
                return
        else:
            aujourd_hui = date.today()
            if periode == "Aujourd'hui":
                date_debut = aujourd_hui.isoformat()
                date_fin = aujourd_hui.isoformat()
            elif periode == "Cette semaine":
                debut_semaine = aujourd_hui - timedelta(days=aujourd_hui.weekday())
                date_debut = debut_semaine.isoformat()
                date_fin = (debut_semaine + timedelta(days=6)).isoformat()
            elif periode == "Ce mois":
                date_debut = aujourd_hui.replace(day=1).isoformat()
                next_month = aujourd_hui.replace(day=28) + timedelta(days=4)
                date_fin = (next_month - timedelta(days=next_month.day)).isoformat()
            elif periode == "Ce trimestre":
                trimestre = (aujourd_hui.month - 1) // 3
                mois_debut = trimestre * 3 + 1
                date_debut = aujourd_hui.replace(month=mois_debut, day=1).isoformat()
                mois_fin = mois_debut + 2
                if mois_fin > 12:
                    mois_fin = 12
                date_fin = aujourd_hui.replace(month=mois_fin, day=1) + timedelta(days=32)
                date_fin = date_fin.replace(day=1) - timedelta(days=1)
                date_fin = date_fin.isoformat()
            elif periode == "Cette année":
                date_debut = aujourd_hui.replace(month=1, day=1).isoformat()
                date_fin = aujourd_hui.replace(month=12, day=31).isoformat()
            else:
                date_debut = None
                date_fin = None

        commandes = charger_commandes()
        depenses = charger_depenses()

        def filtrer_par_periode(item_date):
            if not date_debut or not date_fin:
                return True
            try:
                d = datetime.strptime(item_date, "%Y-%m-%d").date()
                debut = datetime.strptime(date_debut, "%Y-%m-%d").date()
                fin = datetime.strptime(date_fin, "%Y-%m-%d").date()
                return debut <= d <= fin
            except:
                return False

        commandes_filtrees = [c for c in commandes if filtrer_par_periode(c.get("Date", ""))]
        depenses_filtrees = [d for d in depenses if filtrer_par_periode(d.get("Date", ""))]

        total_entrees = sum(float(c.get("Total TTC (€)", c.get("Total (€)", "0"))) for c in commandes_filtrees)
        total_sorties = sum(float(d["Montant (€)"]) for d in depenses_filtrees)
        solde = total_entrees - total_sorties

        try:
            now = datetime.now().strftime("%Y%m%d_%H%M%S")
            nom_fichier = f"rapport_bilan_{now}.pdf"
            chemin = os.path.join(get_dossier_recus(), nom_fichier)

            doc = SimpleDocTemplate(chemin, pagesize=A4,
                                    rightMargin=20, leftMargin=20,
                                    topMargin=20, bottomMargin=20)
            styles = getSampleStyleSheet()
            style_normal = styles['Normal']
            style_heading = styles['Heading1']
            style_heading2 = styles['Heading2']
            style_heading.alignment = TA_CENTER

            story = []

            story.append(Paragraph("Rapport financier - Chez Sall", style_heading))
            story.append(Spacer(1, 12))

            if periode == "Personnalisee" and date_debut and date_fin:
                story.append(Paragraph(f"Période du {date_debut} au {date_fin}", style_normal))
            else:
                story.append(Paragraph(f"Période : {periode}", style_normal))
            story.append(Spacer(1, 12))

            story.append(Paragraph("Entrées (Commandes)", style_heading2))
            story.append(Spacer(1, 6))
            if commandes_filtrees:
                data = [["ID", "Date", "Client", "Plats", "Total TTC"]]
                for c in commandes_filtrees:
                    data.append([
                        c.get("ID", ""),
                        c.get("Date", ""),
                        c.get("Client", ""),
                        c.get("Plats", ""),
                        format_price_table(float(c.get('Total TTC (€)', c.get('Total (€)', '0'))))
                    ])
                table = Table(data, colWidths=[40, 80, 100, 180, 80])
                table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 10),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black),
                    ('FONTSIZE', (0, 1), (-1, -1), 8),
                ]))
                story.append(table)
                story.append(Spacer(1, 6))
                story.append(Paragraph(f"Total Entrées : {format_price(total_entrees)}", style_normal))
            else:
                story.append(Paragraph("Aucune commande sur cette période.", style_normal))
            story.append(Spacer(1, 12))

            story.append(Paragraph("Sorties (Dépenses)", style_heading2))
            story.append(Spacer(1, 6))
            if depenses_filtrees:
                data = [["ID", "Date", "Type", "Description", "Montant"]]
                for d in depenses_filtrees:
                    data.append([
                        d.get("ID", ""),
                        d.get("Date", ""),
                        d.get("Type", ""),
                        d.get("Description", ""),
                        format_price_table(float(d['Montant (€)']))
                    ])
                table = Table(data, colWidths=[40, 80, 100, 150, 80])
                table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 10),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black),
                    ('FONTSIZE', (0, 1), (-1, -1), 8),
                ]))
                story.append(table)
                story.append(Spacer(1, 6))
                story.append(Paragraph(f"Total Sorties : {format_price(total_sorties)}", style_normal))
            else:
                story.append(Paragraph("Aucune dépense sur cette période.", style_normal))
            story.append(Spacer(1, 12))

            if solde >= 0:
                solde_text = f"Solde : {format_price(solde)} (Bénéfice)"
            else:
                solde_text = f"Solde : {format_price(solde)} (Perte)"
            story.append(Paragraph(solde_text, style_heading2))
            story.append(Spacer(1, 12))

            story.append(Paragraph(f"Rapport généré le {datetime.now().strftime('%d/%m/%Y %H:%M')}", style_normal))

            doc.build(story)
            messagebox.showinfo("Rapport PDF", f"✅ Rapport généré avec succès !\n\nFichier : {nom_fichier}\nDossier : recus/")
        except Exception as e:
            messagebox.showerror("Erreur", f"❌ Erreur lors de la génération du rapport : {str(e)}")

    # ==============================================================
    # AUTRES METHODES (PANIER, AJOUT, SUPPRESSION...)
    # ==============================================================

    def ajouter_plat_selectionne(self, event=None):
        plat = self.selecteur_plat.get().strip()
        if not plat:
            messagebox.showwarning("Aucun plat", "Veuillez selectionner un plat dans la liste.")
            return
        
        if plat not in MENU:
            messagebox.showwarning("Plat invalide", f"'{plat}' n'est pas dans le menu.")
            return
        
        dialog = tk.Toplevel(self)
        dialog.title("Quantité")
        dialog.geometry("300x150")
        dialog.configure(bg=COLORS['light'])
        dialog.transient(self)
        # Pas de grab_set pour éviter le blocage
        # dialog.grab_set()
        dialog.focus_force()
        
        tk.Label(dialog, text=f"Quantité pour {plat} :", 
                font=('Arial', 10), bg=COLORS['light']).pack(pady=10)
        
        spinbox = ttk.Spinbox(dialog, from_=1, to=20, width=10)
        spinbox.set(1)
        spinbox.pack(pady=5)
        
        def confirmer():
            quantite = int(spinbox.get())
            dialog.destroy()
            self.ajouter_au_panier(plat, quantite)
        
        ttk.Button(dialog, text="Ajouter", command=confirmer, 
                  style='Accent.TButton').pack(pady=10)
        
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() - dialog.winfo_width()) // 2
        y = (dialog.winfo_screenheight() - dialog.winfo_height()) // 2
        dialog.geometry(f"+{x}+{y}")

    def ajouter_au_panier(self, plat, quantite):
        for i, (p, q) in enumerate(self.panier_items):
            if p == plat:
                self.panier_items[i] = (p, q + quantite)
                break
        else:
            self.panier_items.append((plat, quantite))
        
        self.actualiser_panier()
        self.selecteur_plat.set("")

    def actualiser_panier(self):
        for widget in self.panier_frame.winfo_children():
            widget.destroy()
        
        total_ht = 0
        for plat, quantite in self.panier_items:
            prix = MENU[plat] * quantite
            total_ht += prix
            
            ligne = tk.Frame(self.panier_frame, bg=COLORS['light'])
            ligne.pack(fill="x", pady=2)
            
            tk.Label(ligne, text=f"• {plat} x{quantite}", 
                    font=('Arial', 10), bg=COLORS['light']).pack(side="left", padx=5)
            tk.Label(ligne, text=f"={format_price(prix)}", 
                    font=('Arial', 10), bg=COLORS['light'], fg=COLORS['primary']).pack(side="left", padx=5)
            
            ttk.Button(ligne, text="✕", width=3,
                      command=lambda p=plat: self.supprimer_du_panier(p)).pack(side="right", padx=5)
        
        tva = total_ht * TVA
        total_ttc = total_ht + tva
        
        self.label_total_ht.config(text=f"Total HT : {format_price(total_ht)}")
        self.label_tva.config(text=f"TVA (18%) : {format_price(tva)}")
        self.label_total_ttc.config(text=f"Total TTC : {format_price(total_ttc)}")

    def supprimer_du_panier(self, plat):
        self.panier_items = [(p, q) for p, q in self.panier_items if p != plat]
        self.actualiser_panier()

    def vider_panier(self):
        if self.panier_items:
            if messagebox.askyesno("Confirmation", "Vider le panier ?"):
                self.panier_items = []
                self.actualiser_panier()

    def imprimer_recu_derniere_commande(self):
        if self.derniere_commande_info:
            afficher_apercu_recu(self.derniere_commande_info, self)
        else:
            messagebox.showwarning("Aucune commande", "Aucune commande récente à imprimer.")

    def valider_commande(self):
        nom_client = self.champ_client.get().strip()
        
        if not nom_client:
            messagebox.showwarning("Information manquante", "Merci d'indiquer le nom du client.")
            return
        
        if not self.panier_items:
            messagebox.showwarning("Panier vide", "Le panier est vide. Ajoutez des plats.")
            return
        
        paiement = self.combo_paiement.get()
        
        plats_affichage = []
        plats_commande = []
        total_ht = 0
        
        for plat, quantite in self.panier_items:
            if quantite > 1:
                plats_affichage.append(f"{plat} x{quantite}")
            else:
                plats_affichage.append(plat)
            plats_commande.extend([plat] * quantite)
            total_ht += MENU[plat] * quantite
        
        avis = self.combo_avis.get()
        
        nouvel_id, total_ht, tva, total_ttc = ajouter_commande_fichier(
            nom_client, plats_affichage, total_ht, avis, paiement
        )
        
        self.derniere_commande_info = {
            'id': str(nouvel_id),
            'date': date.today().strftime('%d/%m/%Y'),
            'heure': datetime.now().strftime('%H:%M'),
            'client': nom_client,
            'plats': plats_affichage,
            'avis': avis,
            'paiement': paiement
        }
        
        self.btn_imprimer_recu.config(state="normal")
        
        client = nom_client
        plats = plats_affichage
        total_ht_val = total_ht
        tva_val = tva
        total_ttc_val = total_ttc
        paiement_val = paiement
        avis_val = avis
        id_commande = nouvel_id
        
        self.champ_client.delete(0, tk.END)
        self.panier_items = []
        self.actualiser_panier()
        self.combo_avis.current(0)
        self.combo_paiement.current(0)
        self.selecteur_plat.set("")
        
        self.label_total_ht.config(text="Total HT : 0 FCFA")
        self.label_tva.config(text="TVA (18%) : 0 FCFA")
        self.label_total_ttc.config(text="Total TTC : 0 FCFA")
        
        messagebox.showinfo("Commande enregistree",
                            f"✅ Commande enregistree !\n\n"
                            f"N°: #{id_commande}\n"
                            f"Client : {client}\n"
                            f"Plats : {', '.join(plats)}\n"
                            f"Total HT : {format_price(total_ht_val)}\n"
                            f"TVA (18%) : {format_price(tva_val)}\n"
                            f"Total TTC : {format_price(total_ttc_val)}\n"
                            f"Moyen de paiement : {paiement_val}\n"
                            f"Avis : {avis_val}")
        
        if messagebox.askyesno("Reçu", "Voulez-vous imprimer un reçu pour cette commande ?"):
            afficher_apercu_recu(self.derniere_commande_info, self)
        
        self.appliquer_filtres_commandes()


if __name__ == "__main__":
    app = FenetreRestaurant()
    app.mainloop()