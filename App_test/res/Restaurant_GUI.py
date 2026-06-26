"""
================================================================
INTERFACE GRAPHIQUE - Restaurant Chez Sall (version SQLite)
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
# IMPORTS SQLITE
# ============================================================
from database import init_db
from tables import GestionTables
from clients import GestionClients
from commandes_manager import GestionCommandes
from depenses_manager import GestionDepenses, charger_depenses, ajouter_depense_fichier, sauvegarder_depenses
import config.config as config


# ============================================================
# FONCTION DE FORMATAGE DES PRIX EN FCFA
# ============================================================

def format_price(amount):
    try:
        amount = round(float(amount))
        formatted = f"{amount:,}".replace(",", " ")
        return f"{formatted} FCFA"
    except:
        return "0 FCFA"

def format_price_table(amount):
    try:
        amount = round(float(amount))
        return f"{amount:,}".replace(",", " ")
    except:
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

serveur = Serveur("Alex")
caissier = Caissier("Lina")
manager = Manager("Paul")
restaurant = Restaurant("Chez Sall", MENU, {"serveur": serveur, "caissier": caissier, "manager": manager})


# ------------------------------------------------------------------
# OUTILS : DATES ET PERIODES
# ------------------------------------------------------------------
def date_dans_periode(date_texte, periode):
    if periode == "Toutes":
        return True
    try:
        d = datetime.strptime(date_texte, "%Y-%m-%d").date()
    except:
        return False
    aujourd = date.today()
    if periode == "Aujourd'hui":
        return d == aujourd
    if periode == "Cette semaine":
        debut = aujourd - timedelta(days=aujourd.weekday())
        fin = debut + timedelta(days=6)
        return debut <= d <= fin
    if periode == "Ce mois":
        return d.year == aujourd.year and d.month == aujourd.month
    if periode == "Ce trimestre":
        return d.year == aujourd.year and ((d.month-1)//3) == ((aujourd.month-1)//3)
    if periode == "Cette année":
        return d.year == aujourd.year
    return True


# ============================================================
# FENÊTRE DE CONNEXION
# ============================================================
class FenetreConnexion(tk.Toplevel):
    def __init__(self, parent, titre="Connexion", message="Entrez le mot de passe :"):
        super().__init__(parent)
        self.parent = parent
        self.mot_de_passe = None
        self.ok = False
        self.geometry("350x150")
        self.title(titre)
        self.configure(bg=COLORS['light'])
        self.transient(parent)
        self.focus_force()
        self.update_idletasks()
        x = (self.winfo_screenwidth() - self.winfo_width()) // 2
        y = (self.winfo_screenheight() - self.winfo_height()) // 2
        self.geometry(f"+{x}+{y}")

        tk.Label(self, text=message, font=('Arial', 10, 'bold'), bg=COLORS['light']).pack(pady=15)
        self.entry = ttk.Entry(self, show="*", width=25)
        self.entry.pack(pady=5)
        self.entry.bind("<Return>", lambda e: self.valider())
        self.entry.bind("<Control-v>", lambda e: self.entry.event_generate("<<Paste>>"))
        self.entry.bind("<Control-c>", lambda e: self.entry.event_generate("<<Copy>>"))
        self.entry.bind("<Control-x>", lambda e: self.entry.event_generate("<<Cut>>"))

        bouton_frame = tk.Frame(self, bg=COLORS['light'])
        bouton_frame.pack(pady=10)
        ttk.Button(bouton_frame, text="OK", command=self.valider, style='Accent.TButton').pack(side="left", padx=5)
        ttk.Button(bouton_frame, text="Annuler", command=self.annuler, style='Danger.TButton').pack(side="left", padx=5)

        self.entry.focus()
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

        get_dossier_recus()
        init_db()

        self.gestion_tables = GestionTables()
        self.gestion_clients = GestionClients()
        self.gestion_commandes = GestionCommandes()
        self.gestion_depenses = GestionDepenses()

        self.appliquer_style()

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

        self.derniere_commande_info = None
        self.commande_selectionnee_id = None
        self.tentatives_manager_bilan = 0
        self.tentatives_manager_depenses = 0
        self.acces_bilan = False
        self.acces_depenses = False
        self.bloque_bilan = False
        self.bloque_depenses = False

        self.verifier_acces_application()

    def appliquer_style(self):
        style = ttk.Style()
        style.theme_use('clam')
        style.configure('TNotebook', background=COLORS['light'])
        style.configure('TNotebook.Tab', padding=[15, 5], font=('Arial', 10, 'bold'))
        style.map('TNotebook.Tab',
                  background=[('selected', COLORS['primary']), ('active', COLORS['hover'])],
                  foreground=[('selected', COLORS['white']), ('active', COLORS['white'])])
        style.configure('Accent.TButton', background=COLORS['success'], foreground=COLORS['white'],
                        padding=10, font=('Arial', 10, 'bold'))
        style.map('Accent.TButton', background=[('active', '#2ecc71')])
        style.configure('Danger.TButton', background=COLORS['danger'], foreground=COLORS['white'],
                        padding=10)
        style.map('Danger.TButton', background=[('active', '#c0392b')])
        style.configure('Print.TButton', background=COLORS['warning'], foreground=COLORS['white'],
                        padding=10, font=('Arial', 10, 'bold'))
        style.map('Print.TButton', background=[('active', '#e67a2a')])
        style.configure('Treeview', background=COLORS['white'], foreground=COLORS['dark'],
                        rowheight=25, font=('Arial', 9))
        style.map('Treeview', background=[('selected', COLORS['hover'])],
                  foreground=[('selected', COLORS['white'])])
        style.configure('Treeview.Heading', background=COLORS['primary'],
                        foreground=COLORS['white'], font=('Arial', 9, 'bold'))

    def on_resize(self, event):
        if hasattr(self, 'tableau_commandes'):
            largeur = self.tableau_commandes.winfo_width()
            if largeur > 100:
                cols = ["id", "date", "heure", "client", "plats", "total_ht", "tva", "total_ttc", "avis", "paiement", "statut"]
                largeurs = [40, 80, 60, 100, 150, 80, 80, 80, 80, 90, 100]
                for col, w in zip(cols, largeurs):
                    self.tableau_commandes.column(col, width=w)
        if hasattr(self, 'tableau_depenses'):
            largeur = self.tableau_depenses.winfo_width()
            if largeur > 100:
                cols = ["id", "date", "type", "description", "montant"]
                largeurs = [40, 90, 120, int(largeur*0.3), 90]
                for col, w in zip(cols, largeurs):
                    self.tableau_depenses.column(col, width=w)

    def ouvrir_dossier_recus(self):
        dossier = get_dossier_recus()
        if platform.system() == "Windows":
            os.startfile(dossier)
        elif platform.system() == "Darwin":
            subprocess.run(["open", dossier])
        else:
            subprocess.run(["xdg-open", dossier])

    # ============================================================
    # VERIFICATION MOT DE PASSE APPLICATION
    # ============================================================
    def verifier_acces_application(self):
        while True:
            fenetre = FenetreConnexion(self, "Connexion à l'application", "Entrez le mot de passe de l'application :")
            self.wait_window(fenetre)
            if fenetre.ok and fenetre.mot_de_passe == MOT_DE_PASSE_APPLICATION:
                self.creer_interface()
                return
            elif fenetre.ok:
                messagebox.showerror("Accès refusé", "Mot de passe incorrect. Veuillez réessayer.")
            else:
                self.destroy()
                return

    def creer_interface(self):
        self.construire_onglet_commande()
        self.construire_onglet_commandes()
        self.construire_onglet_depenses()
        self.construire_onglet_bilan()
        self.bind("<Configure>", self.on_resize)

    # ============================================================
    # GESTION GENERIQUE ACCES MANAGER
    # ============================================================
    def demander_mot_de_passe_manager(self, nom_onglet):
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

        fenetre = FenetreConnexion(self, f"Accès Manager - {nom_onglet.capitalize()}",
                                   f"Entrez le mot de passe manager pour accéder à {nom_onglet.capitalize()} :")
        self.wait_window(fenetre)
        if fenetre.ok and fenetre.mot_de_passe == MOT_DE_PASSE_MANAGER:
            setattr(self, compteur_attr, 0)
            return True
        elif fenetre.ok:
            nouvelles = getattr(self, compteur_attr) + 1
            setattr(self, compteur_attr, nouvelles)
            restant = max_tentatives - nouvelles
            if restant <= 0:
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
                return self.demander_mot_de_passe_manager(nom_onglet)
        else:
            return False

    # ==============================================================
    # ONGLET 1 : NOUVELLE COMMANDE
    # ==============================================================
    def construire_onglet_commande(self):
        cadre = self.onglet_commande
        cadre.configure(bg=COLORS['light'])

        cadre_entete = tk.Frame(cadre, bg=COLORS['light'])
        cadre_entete.pack(fill="x", padx=20, pady=(10, 5))
        titre = tk.Label(cadre_entete, text="🛎️ Nouvelle commande",
                        font=('Arial', 14, 'bold'), fg=COLORS['primary'], bg=COLORS['light'])
        titre.pack(side="left")

        self.btn_imprimer_recu = ttk.Button(cadre_entete, text="🖨️ Imprimer le reçu",
                                            command=self.imprimer_recu_derniere_commande,
                                            style='Print.TButton')
        self.btn_imprimer_recu.pack(side="right", padx=5)
        self.btn_imprimer_recu.config(state="disabled")

        ttk.Button(cadre_entete, text="📁 Voir les reçus",
                   command=self.ouvrir_dossier_recus, style='Accent.TButton').pack(side="right", padx=5)

        # Canvas avec scroll
        canvas = tk.Canvas(cadre, bg=COLORS['light'], highlightthickness=0)
        scrollbar = ttk.Scrollbar(cadre, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg=COLORS['light'])
        scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
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

        # Sélecteur de plats
        tk.Label(cadre_contenu, text="🔽 Selectionner un plat :", font=('Arial', 10),
                bg=COLORS['light'], fg=COLORS['dark']).pack(anchor="w", pady=(0, 5))
        cadre_selecteur = tk.Frame(cadre_contenu, bg=COLORS['light'])
        cadre_selecteur.pack(anchor="w", pady=(0, 10), fill="x")
        self.selecteur_plat = ttk.Combobox(cadre_selecteur, values=sorted(MENU.keys()),
                                           width=30, font=('Arial', 10))
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
        panier_frame.bind("<Configure>", lambda e: canvas_panier.configure(scrollregion=canvas_panier.bbox("all")))
        canvas_panier.create_window((0, 0), window=panier_frame, anchor="nw", width=canvas_panier.winfo_width())
        canvas_panier.configure(yscrollcommand=scrollbar_panier.set)
        def _configure_panier(event):
            canvas_panier.itemconfig(1, width=event.width)
        canvas_panier.bind("<Configure>", _configure_panier)
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

        # Ligne paiement + boutons
        cadre_ligne_basse = tk.Frame(cadre_contenu, bg=COLORS['light'])
        cadre_ligne_basse.pack(anchor="w", pady=(10, 10), fill="x")
        cadre_gauche_paiement = tk.Frame(cadre_ligne_basse, bg=COLORS['light'])
        cadre_gauche_paiement.pack(side="left", fill="x", expand=True)
        tk.Label(cadre_gauche_paiement, text="Moyen de paiement :", font=('Arial', 10),
                bg=COLORS['light'], fg=COLORS['dark']).pack(side="left", padx=(0, 10))
        self.combo_paiement = ttk.Combobox(cadre_gauche_paiement, values=MOYENS_PAIEMENT,
                                           state="readonly", width=20, font=('Arial', 10))
        self.combo_paiement.current(0)
        self.combo_paiement.pack(side="left")
        cadre_droite_boutons = tk.Frame(cadre_ligne_basse, bg=COLORS['light'])
        cadre_droite_boutons.pack(side="right")
        ttk.Button(cadre_droite_boutons, text="✅ Valider la commande",
                   command=self.valider_commande, style='Accent.TButton').pack(side="left", padx=5)
        ttk.Button(cadre_droite_boutons, text="🗑️ Vider le panier",
                   command=self.vider_panier, style='Danger.TButton').pack(side="left", padx=5)

        # Avis
        tk.Label(cadre_contenu, text="Avis :", font=('Arial', 10),
                bg=COLORS['light'], fg=COLORS['dark']).pack(anchor="w", pady=(10, 5))
        self.combo_avis = ttk.Combobox(cadre_contenu, values=["bon", "excellent", "pimenté", "parfait"],
                                       state="readonly", width=20, font=('Arial', 10))
        self.combo_avis.current(0)
        self.combo_avis.pack(anchor="w", pady=(0, 20))

        tk.Frame(contenu, height=50, bg=COLORS['light']).pack()

    # ==============================================================
    # MÉTHODES PANIER
    # ==============================================================
    def ajouter_plat_selectionne(self, event=None):
        plat = self.selecteur_plat.get().strip()
        if not plat or plat not in MENU:
            messagebox.showwarning("Plat invalide", "Veuillez sélectionner un plat valide.")
            return
        dialog = tk.Toplevel(self)
        dialog.title("Quantité")
        dialog.geometry("300x150")
        dialog.configure(bg=COLORS['light'])
        dialog.transient(self)
        dialog.focus_force()
        tk.Label(dialog, text=f"Quantité pour {plat} :", font=('Arial', 10), bg=COLORS['light']).pack(pady=10)
        spinbox = ttk.Spinbox(dialog, from_=1, to=20, width=10)
        spinbox.set(1)
        spinbox.pack(pady=5)
        def confirmer():
            qte = int(spinbox.get())
            dialog.destroy()
            self.ajouter_au_panier(plat, qte)
        ttk.Button(dialog, text="Ajouter", command=confirmer, style='Accent.TButton').pack(pady=10)
        dialog.update_idletasks()
        x = (self.winfo_screenwidth() - dialog.winfo_width()) // 2
        y = (self.winfo_screenheight() - dialog.winfo_height()) // 2
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
        for plat, qte in self.panier_items:
            prix = MENU[plat] * qte
            total_ht += prix
            ligne = tk.Frame(self.panier_frame, bg=COLORS['light'])
            ligne.pack(fill="x", pady=2)
            tk.Label(ligne, text=f"• {plat} x{qte}", font=('Arial', 10), bg=COLORS['light']).pack(side="left", padx=5)
            tk.Label(ligne, text=f"={format_price(prix)}", font=('Arial', 10), bg=COLORS['light'], fg=COLORS['primary']).pack(side="left", padx=5)
            ttk.Button(ligne, text="✕", width=3, command=lambda p=plat: self.supprimer_du_panier(p)).pack(side="right", padx=5)
        tva = total_ht * TVA
        total_ttc = total_ht + tva
        self.label_total_ht.config(text=f"Total HT : {format_price(total_ht)}")
        self.label_tva.config(text=f"TVA (18%) : {format_price(tva)}")
        self.label_total_ttc.config(text=f"Total TTC : {format_price(total_ttc)}")

    def supprimer_du_panier(self, plat):
        self.panier_items = [(p, q) for p, q in self.panier_items if p != plat]
        self.actualiser_panier()

    def vider_panier(self):
        if self.panier_items and messagebox.askyesno("Confirmation", "Vider le panier ?"):
            self.panier_items = []
            self.actualiser_panier()

    # ==============================================================
    # VALIDER LA COMMANDE (SQLite)
    # ==============================================================
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
        for plat, qte in self.panier_items:
            if qte > 1:
                plats_affichage.append(f"{plat} x{qte}")
            else:
                plats_affichage.append(plat)
            plats_commande.extend([plat]*qte)
            total_ht += MENU[plat]*qte
        avis = self.combo_avis.get()
        plats_str = " + ".join(plats_affichage)

        tva = total_ht * TVA
        total_ttc = total_ht + tva

        gc = self.gestion_commandes
        commande_id = gc.ajouter_commande(
            client=nom_client,
            table=None,
            plats=plats_str,
            total_ht=total_ht,
            tva=tva,
            total_ttc=total_ttc,
            paiement=paiement,
            serveur="Alex",
            avis=avis
        )

        gc_clients = self.gestion_clients
        client_existant = gc_clients.get_client_par_nom(nom_client)
        if not client_existant:
            client_id = gc_clients.ajouter_client(nom_client)
        else:
            client_id = client_existant['id']
        gc_clients.enregistrer_commande_client(client_id, commande_id)
        gc_clients.ajouter_depense_client(client_id, total_ttc)

        self.derniere_commande_info = {
            'id': str(commande_id),
            'date': date.today().strftime('%d/%m/%Y'),
            'heure': datetime.now().strftime('%H:%M'),
            'client': nom_client,
            'plats': plats_affichage,
            'avis': avis,
            'paiement': paiement
        }
        self.btn_imprimer_recu.config(state="normal")

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
                            f"N°: #{commande_id}\n"
                            f"Client : {nom_client}\n"
                            f"Plats : {', '.join(plats_affichage)}\n"
                            f"Total HT : {format_price(total_ht)}\n"
                            f"TVA (18%) : {format_price(tva)}\n"
                            f"Total TTC : {format_price(total_ttc)}\n"
                            f"Moyen de paiement : {paiement}\n"
                            f"Avis : {avis}")
        if messagebox.askyesno("Reçu", "Voulez-vous imprimer un reçu pour cette commande ?"):
            afficher_apercu_recu(self.derniere_commande_info, self)
        self.appliquer_filtres_commandes()

    def imprimer_recu_derniere_commande(self):
        if self.derniere_commande_info:
            afficher_apercu_recu(self.derniere_commande_info, self)
        else:
            messagebox.showwarning("Aucune commande", "Aucune commande récente.")

    # ==============================================================
    # ONGLET 2 : COMMANDES
    # ==============================================================
    def construire_onglet_commandes(self):
        cadre = self.onglet_commandes
        cadre.configure(bg=COLORS['light'])

        canvas = tk.Canvas(cadre, bg=COLORS['light'], highlightthickness=0)
        scrollbar = ttk.Scrollbar(cadre, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg=COLORS['light'])
        scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
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
        canvas.bind("<Button-4>", lambda e: canvas.yview_scroll(-1, "units"))
        canvas.bind("<Button-5>", lambda e: canvas.yview_scroll(1, "units"))

        def _configure_canvas(event):
            canvas.itemconfig(1, width=event.width)
        canvas.bind("<Configure>", _configure_canvas)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        contenu = scrollable_frame
        contenu.configure(bg=COLORS['light'])

        tk.Label(contenu, text="📋 Liste des commandes",
                 font=('Arial', 14, 'bold'), fg=COLORS['primary'], bg=COLORS['light']).pack(anchor="w", padx=10, pady=(10, 10))

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
        colonnes = ("id", "date", "heure", "client", "plats", "total_ht", "tva", "total_ttc", "avis", "paiement", "statut")
        self.tableau_commandes = ttk.Treeview(cadre_tableau, columns=colonnes, show="headings",
                                              yscrollcommand=scroll_y.set, xscrollcommand=scroll_x.set,
                                              height=15, selectmode='extended')
        titres = ["ID", "Date", "Heure", "Client", "Plats", "HT", "TVA", "TTC", "Avis", "Paiement", "Statut"]
        largeurs = [40, 80, 60, 100, 150, 80, 80, 80, 80, 90, 100]
        for col, titre, w in zip(colonnes, titres, largeurs):
            self.tableau_commandes.heading(col, text=titre)
            self.tableau_commandes.column(col, width=w, minwidth=w//2)
        scroll_y.config(command=self.tableau_commandes.yview)
        scroll_x.config(command=self.tableau_commandes.xview)
        self.tableau_commandes.pack(side="left", fill="both", expand=True)
        scroll_y.pack(side="right", fill="y")
        scroll_x.pack(side="bottom", fill="x")

        self.tableau_commandes.bind("<<TreeviewSelect>>", self.on_commande_selectionnee)

        cadre_bas = tk.Frame(contenu, bg=COLORS['light'])
        cadre_bas.pack(anchor="w", padx=10, pady=10, fill="x")
        self.label_resultat_commandes = tk.Label(cadre_bas, text="", font=('Arial', 10),
                                                bg=COLORS['light'], fg=COLORS['primary'])
        self.label_resultat_commandes.pack(side="left")
        cadre_boutons = tk.Frame(cadre_bas, bg=COLORS['light'])
        cadre_boutons.pack(side="right")
        ttk.Button(cadre_boutons, text="🖨️ Recu", command=self.afficher_recu_selection,
                   style='Print.TButton').pack(side="right", padx=5)
        ttk.Button(cadre_boutons, text="🗑️ Supprimer", command=self.supprimer_commandes_selectionnees,
                   style='Danger.TButton').pack(side="right", padx=5)
        ttk.Button(cadre_boutons, text="📌 Changer statut", command=self.changer_statut_selection,
                   style='Accent.TButton').pack(side="right", padx=5)

        tk.Frame(contenu, height=50, bg=COLORS['light']).pack()
        self.appliquer_filtres_commandes()

    def on_commande_selectionnee(self, event):
        selection = self.tableau_commandes.selection()
        if not selection:
            self.commande_selectionnee_id = None
            return
        valeurs = self.tableau_commandes.item(selection[0], "values")
        self.commande_selectionnee_id = valeurs[0] if valeurs else None

    def afficher_recu_selection(self):
        if not self.commande_selectionnee_id:
            messagebox.showwarning("Aucune sélection", "Veuillez sélectionner une commande.")
            return
        self.ouvrir_details_commande(self.commande_selectionnee_id)

    def changer_statut_selection(self):
        if not self.commande_selectionnee_id:
            messagebox.showwarning("Aucune sélection", "Veuillez sélectionner une commande.")
            return

        dialog = tk.Toplevel(self)
        dialog.title("Changer le statut")
        dialog.geometry("300x200")
        dialog.configure(bg=COLORS['light'])
        dialog.transient(self)
        dialog.grab_set()
        dialog.focus_force()
        tk.Label(dialog, text="Sélectionnez le nouveau statut :",
                 font=('Arial', 11, 'bold'), bg=COLORS['light']).pack(pady=15)
        statuts = ["En attente", "En préparation", "Servie", "Payée", "Terminée"]
        combo_statut = ttk.Combobox(dialog, values=statuts, state="readonly", width=20)
        combo_statut.current(0)
        combo_statut.pack(pady=10)
        def valider():
            nouveau = combo_statut.get()
            if nouveau:
                gc = self.gestion_commandes
                try:
                    gc.changer_statut(self.commande_selectionnee_id, nouveau)
                    self.appliquer_filtres_commandes()
                    messagebox.showinfo("Succès", f"Statut mis à jour : {nouveau}")
                    dialog.destroy()
                except ValueError as e:
                    messagebox.showerror("Erreur", str(e))
        ttk.Button(dialog, text="Valider", command=valider, style='Accent.TButton').pack(pady=10)
        dialog.update_idletasks()
        x = (self.winfo_screenwidth() - dialog.winfo_width()) // 2
        y = (self.winfo_screenheight() - dialog.winfo_height()) // 2
        dialog.geometry(f"+{x}+{y}")

    def ouvrir_details_commande(self, commande_id):
        gc = self.gestion_commandes
        cmd = gc.get_commande(commande_id)
        if not cmd:
            messagebox.showerror("Erreur", "Commande non trouvée.")
            return

        fenetre = tk.Toplevel(self)
        fenetre.title(f"Détails de la commande #{commande_id}")
        fenetre.geometry("420x600")
        fenetre.configure(bg=COLORS['white'])
        fenetre.transient(self)
        fenetre.focus_force()
        fenetre.update_idletasks()
        x = (self.winfo_screenwidth() - fenetre.winfo_width()) // 2
        y = (self.winfo_screenheight() - fenetre.winfo_height()) // 2
        fenetre.geometry(f"+{x}+{y}")

        tk.Label(fenetre, text=f"📄 Détails de la commande n°{commande_id}",
                 font=('Arial', 14, 'bold'), bg=COLORS['white'], fg=COLORS['primary']).pack(pady=(15, 10))

        cadre_texte = tk.Frame(fenetre, bg=COLORS['white'])
        cadre_texte.pack(fill="both", expand=True, padx=15, pady=5)
        scrollbar = ttk.Scrollbar(cadre_texte)
        scrollbar.pack(side="right", fill="y")
        texte = tk.Text(cadre_texte, height=20, width=45, font=('Arial', 9),
                        wrap='word', yscrollcommand=scrollbar.set, bg='white')
        texte.pack(side="left", fill="both", expand=True)
        scrollbar.config(command=texte.yview)

        total_ht = cmd['total_ht']
        tva = cmd['tva']
        total_ttc = cmd['total_ttc']

        details = f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📋 COMMANDE N°{cmd['id']}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

👤 Client : {cmd['client'] or 'Non spécifié'}
📅 Date : {cmd['date']}
🕐 Heure : {cmd['heure']}
💳 Paiement : {cmd['paiement']}
📌 Statut : {cmd['statut']}
📋 Table : {cmd['table_num'] or 'Non assignée'}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🛒 PLATS COMMANDÉS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{self.formater_plats(cmd['plats'])}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
💰 TOTAUX
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Total HT : {format_price(total_ht)}
TVA (18%) : {format_price(tva)}
Total TTC : {format_price(total_ttc)}

⭐ Avis : {cmd['avis'] or 'Non spécifié'}
👨‍🍳 Serveur : {cmd['serveur'] or 'Non spécifié'}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
        texte.insert("1.0", details)
        texte.config(state="disabled")
        texte.update_idletasks()

        bouton_frame = tk.Frame(fenetre, bg=COLORS['white'])
        bouton_frame.pack(fill="x", pady=10, padx=15)
        ttk.Button(bouton_frame, text="🖨️ Aperçu",
                   command=lambda: self._imprimer_recu_par_id(commande_id, fenetre),
                   style='Print.TButton').pack(fill="x", pady=3)
        ttk.Button(bouton_frame, text="📄 Générer PDF",
                   command=lambda: self._generer_pdf_par_id(commande_id, fenetre),
                   style='Accent.TButton').pack(fill="x", pady=3)
        ttk.Button(bouton_frame, text="📁 Voir les reçus",
                   command=self.ouvrir_dossier_recus, style='Accent.TButton').pack(fill="x", pady=3)
        ttk.Button(bouton_frame, text="❌ Fermer",
                   command=fenetre.destroy, style='Danger.TButton').pack(fill="x", pady=3)

    def _imprimer_recu_par_id(self, commande_id, fenetre=None):
        if commande_id:
            imprimer_recu_depuis_commande(commande_id, self)
            if fenetre:
                fenetre.destroy()

    def _generer_pdf_par_id(self, commande_id, fenetre=None):
        if not commande_id:
            return
        try:
            gc = self.gestion_commandes
            cmd = gc.get_commande(commande_id)
            if cmd:
                commande_info = {
                    'id': cmd['id'],
                    'date': cmd['date'],
                    'heure': cmd['heure'],
                    'client': cmd['client'],
                    'plats': [p.strip() for p in cmd['plats'].split('+') if p.strip()],
                    'avis': cmd['avis'],
                    'paiement': cmd['paiement']
                }
                fichier = generer_recu(commande_info)
                messagebox.showinfo("Succès", f"✅ Reçu généré : {os.path.basename(fichier)}")
                if fenetre:
                    fenetre.destroy()
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur : {str(e)}")

    def formater_plats(self, plats_str):
        if not plats_str:
            return "Aucun plat"
        plats = [p.strip() for p in plats_str.split('+') if p.strip()]
        return "\n".join(f"   • {p}" for p in plats)

    def supprimer_commandes_selectionnees(self):
        selection = self.tableau_commandes.selection()
        if not selection:
            messagebox.showwarning("Aucune selection", "Selectionne d'abord une ou plusieurs commandes.")
            return
        ids = [self.tableau_commandes.item(item, "values")[0] for item in selection]
        if not ids:
            return
        if not messagebox.askyesno("Confirmation", f"⚠️ Supprimer {len(ids)} commande(s) ?"):
            return
        gc = self.gestion_commandes
        for cmd_id in ids:
            gc.supprimer_commande(cmd_id)
        self.appliquer_filtres_commandes()
        self.commande_selectionnee_id = None
        messagebox.showinfo("Succès", f"✅ {len(ids)} commande(s) supprimée(s).")

    def appliquer_filtres_commandes(self):
        client = self.filtre_client.get().strip().lower()
        plat = self.filtre_plat.get().strip().lower()
        id_f = self.filtre_id.get().strip()
        avis = self.filtre_avis.get()
        periode = self.filtre_periode_commande.get()

        for ligne in self.tableau_commandes.get_children():
            self.tableau_commandes.delete(ligne)

        gc = self.gestion_commandes
        if periode == "Toutes":
            commandes = gc.get_commandes_jour()
        elif periode == "Aujourd'hui":
            commandes = gc.get_commandes_jour()
        elif periode == "Cette semaine":
            commandes = gc.get_commandes_semaine()
        elif periode == "Ce mois":
            commandes = gc.get_commandes_mois()
        else:
            commandes = gc.get_commandes_jour()

        total_ht = 0
        total_ttc = 0
        nb = 0
        for c in commandes:
            c = dict(c)
            if id_f and str(c.get("ID", c.get("id", ""))) != id_f:
                continue
            if client and client not in c.get("Client", c.get("client", "")).lower():
                continue
            if plat and plat not in c.get("Plats", c.get("plats", "")).lower():
                continue
            if avis != "Tous" and c.get("Avis", c.get("avis", "")) != avis:
                continue

            total_ht_cmd = float(c.get("Total HT (€)", c.get("total_ht", 0)))
            tva_cmd = float(c.get("TVA (€)", c.get("tva", 0)))
            total_ttc_cmd = float(c.get("Total TTC (€)", c.get("total_ttc", 0)))

            self.tableau_commandes.insert("", "end", values=(
                c.get("ID", c.get("id", "")),
                c.get("Date", c.get("date", "")),
                c.get("Heure", c.get("heure", "")),
                c.get("Client", c.get("client", "")),
                c.get("Plats", c.get("plats", "")),
                format_price_table(total_ht_cmd),
                format_price_table(tva_cmd),
                format_price_table(total_ttc_cmd),
                c.get("Avis", c.get("avis", "")),
                c.get("Paiement", c.get("paiement", "")),
                c.get("statut", "En attente")
            ))
            total_ht += total_ht_cmd
            total_ttc += total_ttc_cmd
            nb += 1
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
        nom = f"export_commandes_{date.today().isoformat()}.csv"
        try:
            with open(nom, mode="w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(["ID", "Date", "Heure", "Client", "Plats", "Total HT (€)", "TVA (€)", "Total TTC (€)", "Avis", "Paiement", "Statut"])
                for ligne in self.tableau_commandes.get_children():
                    writer.writerow(self.tableau_commandes.item(ligne, "values"))
            messagebox.showinfo("Export réussi", f"✅ Fichier exporté : {nom}")
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur : {str(e)}")

    # ==============================================================
    # ONGLET 3 : DÉPENSES (CORRIGÉ)
    # ==============================================================
    def construire_onglet_depenses(self):
        cadre = self.onglet_depenses
        cadre.configure(bg=COLORS['light'])

        self.depenses_frame = tk.Frame(cadre, bg=COLORS['light'])
        self.depenses_frame.pack(fill="both", expand=True)
        self.afficher_verrou_depenses()

    def afficher_verrou_depenses(self):
        for widget in self.depenses_frame.winfo_children():
            widget.destroy()
        if self.bloque_depenses:
            tk.Label(self.depenses_frame,
                     text="🔒 Accès aux Dépenses définitivement bloqué\n\nTrop de tentatives échouées.",
                     font=('Arial', 14, 'bold'), bg=COLORS['light'], fg=COLORS['danger']).pack(pady=(100, 20))
            return
        tk.Label(self.depenses_frame,
                 text="🔒 Accès aux Dépenses\n\nCe service est protégé par le mot de passe manager.",
                 font=('Arial', 14, 'bold'), bg=COLORS['light'], fg=COLORS['danger']).pack(pady=(100, 20))
        self.btn_deverrouiller_depenses = ttk.Button(self.depenses_frame,
                                                     text="🔑 Déverrouiller",
                                                     command=self.demander_mot_de_passe_depenses,
                                                     style='Accent.TButton')
        self.btn_deverrouiller_depenses.pack(pady=10)
        self.acces_depenses = False

    def demander_mot_de_passe_depenses(self):
        if self.bloque_depenses:
            return
        if self.demander_mot_de_passe_manager("depenses"):
            self.acces_depenses = True
            self.afficher_contenu_depenses()
        else:
            self.afficher_verrou_depenses()

    def afficher_contenu_depenses(self):
        """Affiche le contenu réel des dépenses après déverrouillage."""
        for widget in self.depenses_frame.winfo_children():
            widget.destroy()

        # Créer un canvas avec scroll
        canvas = tk.Canvas(self.depenses_frame, bg=COLORS['light'], highlightthickness=0)
        scrollbar = ttk.Scrollbar(self.depenses_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg=COLORS['light'])

        # ===> FORCER LA LARGEUR DU CANVAS
        largeur = self.depenses_frame.winfo_width() or 800
        canvas.config(width=largeur)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw", width=largeur)
        canvas.configure(yscrollcommand=scrollbar.set)

        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        def _on_enter(event):
            canvas.bind_all("<MouseWheel>", _on_mousewheel)
        def _on_leave(event):
            canvas.unbind_all("<MouseWheel>")
        canvas.bind("<Enter>", _on_enter)
        canvas.bind("<Leave>", _on_leave)
        canvas.bind("<Button-4>", lambda e: canvas.yview_scroll(-1, "units"))
        canvas.bind("<Button-5>", lambda e: canvas.yview_scroll(1, "units"))

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        contenu = scrollable_frame
        contenu.configure(bg=COLORS['light'])

        # --- Contenu des dépenses ---
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
        for col, titre, w in zip(colonnes, titres, largeurs):
            self.tableau_depenses.heading(col, text=titre)
            self.tableau_depenses.column(col, width=w, minwidth=w//2)
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
                   command=self.supprimer_depense_selectionnee, style='Danger.TButton').pack(side="right", padx=5)

        tk.Frame(contenu, height=50, bg=COLORS['light']).pack()

        # ===> FORCER LA MISE À JOUR
        canvas.update_idletasks()
        self.appliquer_filtres_depenses()
        self.update()

    def ajouter_depense(self):
        type_dep = self.combo_type_depense.get()
        desc = self.champ_description_depense.get().strip()
        try:
            montant = float(self.champ_montant_depense.get().strip())
        except:
            messagebox.showwarning("Montant invalide", "Le montant doit être un nombre.")
            return
        gd = self.gestion_depenses
        gd.ajouter_depense(type_dep, desc, montant)
        messagebox.showinfo("Depense ajoutée", f"✅ {type_dep} : {format_price(montant)} ajoutée.")
        self.champ_description_depense.delete(0, tk.END)
        self.champ_montant_depense.delete(0, tk.END)
        self.appliquer_filtres_depenses()

    def appliquer_filtres_depenses(self):
        type_f = self.filtre_type_depense.get()
        periode = self.filtre_periode_depense.get()

        for ligne in self.tableau_depenses.get_children():
            self.tableau_depenses.delete(ligne)

        gd = self.gestion_depenses
        depenses = gd.get_depenses(type_f if type_f != "Tous" else None)

        total = 0
        nb = 0
        for d in depenses:
            d = dict(d)
            if not date_dans_periode(d['date'], periode):
                continue
            self.tableau_depenses.insert("", "end", values=(
                d['id'],
                d['date'],
                d['type'],
                d['description'],
                format_price_table(d['montant'])
            ))
            total += d['montant']
            nb += 1

        self.label_resultat_depenses.config(
            text=f"📊 {nb} depense(s) - Total : {format_price(total)}"
        )

    def reinitialiser_filtres_depenses(self):
        self.filtre_type_depense.current(0)
        self.filtre_periode_depense.current(0)
        self.appliquer_filtres_depenses()

    def supprimer_depense_selectionnee(self):
        selection = self.tableau_depenses.selection()
        if not selection:
            return
        id_dep = self.tableau_depenses.item(selection[0], "values")[0]
        if not messagebox.askyesno("Confirmation", f"⚠️ Supprimer la dépense n°{id_dep} ?"):
            return
        gd = self.gestion_depenses
        gd.supprimer_depense(id_dep)
        self.appliquer_filtres_depenses()
        messagebox.showinfo("Succès", "✅ Dépense supprimée.")

    # ==============================================================
    # ONGLET 4 : BILAN (CORRIGÉ)
    # ==============================================================
    def construire_onglet_bilan(self):
        cadre = self.onglet_bilan
        cadre.configure(bg=COLORS['light'])
        self.bilan_frame = tk.Frame(cadre, bg=COLORS['light'])
        self.bilan_frame.pack(fill="both", expand=True)
        self.afficher_verrou_bilan()

    def afficher_verrou_bilan(self):
        for widget in self.bilan_frame.winfo_children():
            widget.destroy()
        if self.bloque_bilan:
            tk.Label(self.bilan_frame,
                     text="🔒 Accès au Bilan définitivement bloqué\n\nTrop de tentatives échouées.",
                     font=('Arial', 14, 'bold'), bg=COLORS['light'], fg=COLORS['danger']).pack(pady=(100, 20))
            return
        tk.Label(self.bilan_frame,
                 text="🔒 Accès au Bilan Manager\n\nCe service est protégé par un mot de passe.",
                 font=('Arial', 14, 'bold'), bg=COLORS['light'], fg=COLORS['danger']).pack(pady=(100, 20))
        self.btn_deverrouiller_bilan = ttk.Button(self.bilan_frame,
                                                  text="🔑 Déverrouiller",
                                                  command=self.demander_mot_de_passe_bilan,
                                                  style='Accent.TButton')
        self.btn_deverrouiller_bilan.pack(pady=10)
        self.acces_bilan = False

    def demander_mot_de_passe_bilan(self):
        if self.bloque_bilan:
            return
        if self.demander_mot_de_passe_manager("bilan"):
            self.acces_bilan = True
            self.afficher_contenu_bilan()
        else:
            self.afficher_verrou_bilan()

    def afficher_contenu_bilan(self):
        """Affiche le contenu réel du bilan avec une barre de défilement."""
        for widget in self.bilan_frame.winfo_children():
            widget.destroy()

        # Créer un canvas avec scroll
        canvas = tk.Canvas(self.bilan_frame, bg=COLORS['light'], highlightthickness=0)
        scrollbar = ttk.Scrollbar(self.bilan_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg=COLORS['light'])

        # ===> FORCER LA LARGEUR DU CANVAS
        largeur = self.bilan_frame.winfo_width() or 800
        canvas.config(width=largeur)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw", width=largeur)
        canvas.configure(yscrollcommand=scrollbar.set)

        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        def _on_enter(event):
            canvas.bind_all("<MouseWheel>", _on_mousewheel)
        def _on_leave(event):
            canvas.unbind_all("<MouseWheel>")
        canvas.bind("<Enter>", _on_enter)
        canvas.bind("<Leave>", _on_leave)
        canvas.bind("<Button-4>", lambda e: canvas.yview_scroll(-1, "units"))
        canvas.bind("<Button-5>", lambda e: canvas.yview_scroll(1, "units"))

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        contenu = scrollable_frame
        contenu.configure(bg=COLORS['light'])

        # --- Contenu du bilan ---
        cadre_entete = tk.Frame(contenu, bg=COLORS['light'])
        cadre_entete.pack(fill="x", padx=20, pady=(20, 10))
        tk.Label(cadre_entete, text="📊 Bilan financier",
                 font=('Arial', 16, 'bold'), fg=COLORS['primary'], bg=COLORS['light']).pack(side="left")

        cadre_solde = tk.Frame(cadre_entete, bg=COLORS['light'], relief='ridge', bd=2)
        cadre_solde.pack(side="right", padx=10)
        tk.Label(cadre_solde, text="SOLDE", font=('Arial', 10, 'bold'), fg=COLORS['white'],
                 bg=COLORS['primary'], padx=15, pady=2).pack(fill="x")
        self.label_solde_principal = tk.Label(cadre_solde, text="0 FCFA", font=('Arial', 24, 'bold'),
                                              fg=COLORS['success'], bg=COLORS['white'], padx=20, pady=10)
        self.label_solde_principal.pack()
        self.label_status = tk.Label(cadre_solde, text="✅ Bénéfice", font=('Arial', 10, 'bold'),
                                     fg=COLORS['success'], bg=COLORS['white'], padx=15, pady=2)
        self.label_status.pack()

        cadre_contenu = tk.Frame(contenu, bg=COLORS['light'])
        cadre_contenu.pack(fill="both", expand=True, padx=20, pady=10)

        cadre_periode = ttk.LabelFrame(cadre_contenu, text="📅 Sélection de la période", padding=15)
        cadre_periode.pack(anchor="w", pady=10, fill="x")
        ligne1 = tk.Frame(cadre_periode, bg=COLORS['light'])
        ligne1.pack(fill="x", pady=5)
        tk.Label(ligne1, text="Période :", font=('Arial', 10), bg=COLORS['light']).pack(side="left", padx=5)
        self.combo_periode_bilan = ttk.Combobox(ligne1, values=PERIODES + ["Personnalisée"], state="readonly", width=18)
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
                   command=self.calculer_et_afficher_bilan, style='Accent.TButton').pack(pady=5)
        ttk.Button(cadre_periode, text="📊 Générer rapport PDF",
                   command=self.generer_rapport_bilan_pdf, style='Print.TButton').pack(pady=5)

        cadre_resultats = ttk.LabelFrame(cadre_contenu, text="📈 Détails", padding=15)
        cadre_resultats.pack(anchor="w", pady=10, fill="both", expand=True)

        grille = tk.Frame(cadre_resultats, bg=COLORS['light'])
        grille.pack(fill="x", pady=5)
        cadre_entrees = tk.Frame(grille, bg=COLORS['light'], relief='groove', bd=1)
        cadre_entrees.pack(side="left", fill="both", expand=True, padx=5)
        tk.Label(cadre_entrees, text="💰 Entrées", font=('Arial', 10, 'bold'),
                 bg=COLORS['success'], fg=COLORS['white'], padx=10, pady=5).pack(fill="x")
        self.label_entrees = tk.Label(cadre_entrees, text="0 FCFA", font=('Arial', 14, 'bold'),
                                      fg=COLORS['success'], bg=COLORS['light'], padx=10, pady=10)
        self.label_entrees.pack()

        cadre_sorties = tk.Frame(grille, bg=COLORS['light'], relief='groove', bd=1)
        cadre_sorties.pack(side="right", fill="both", expand=True, padx=5)
        tk.Label(cadre_sorties, text="💸 Sorties", font=('Arial', 10, 'bold'),
                 bg=COLORS['danger'], fg=COLORS['white'], padx=10, pady=5).pack(fill="x")
        self.label_sorties = tk.Label(cadre_sorties, text="0 FCFA", font=('Arial', 14, 'bold'),
                                      fg=COLORS['danger'], bg=COLORS['light'], padx=10, pady=10)
        self.label_sorties.pack()

        ttk.Separator(cadre_resultats, orient='horizontal').pack(fill='x', pady=10)
        tk.Label(cadre_resultats, text="📋 Détails des dépenses par type :",
                 font=('Arial', 11, 'bold'), bg=COLORS['light']).pack(anchor="w", pady=5)
        self.text_details_depenses = tk.Text(cadre_resultats, height=8, width=50,
                                             font=('Arial', 10), state="disabled")
        self.text_details_depenses.pack(anchor="w", fill="both", expand=True, pady=5)

        tk.Frame(contenu, height=50, bg=COLORS['light']).pack()

        # ===> FORCER LA MISE À JOUR
        canvas.update_idletasks()
        self.calculer_et_afficher_bilan()
        self.update()

    def on_bilan_periode_changed(self, event=None):
        periode = self.combo_periode_bilan.get()
        etat = "normal" if periode == "Personnalisée" else "disabled"
        self.bilan_date_debut.config(state=etat)
        self.bilan_date_fin.config(state=etat)

    def calculer_et_afficher_bilan(self):
        if not self.acces_bilan:
            return
        periode = self.combo_periode_bilan.get()
        date_debut = None
        date_fin = None
        if periode == "Personnalisée":
            date_debut = self.bilan_date_debut.get().strip()
            date_fin = self.bilan_date_fin.get().strip()
            if not date_debut or not date_fin:
                messagebox.showwarning("Dates manquantes", "Veuillez saisir les dates.")
                return

        gc = self.gestion_commandes
        gd = self.gestion_depenses

        if periode == "Toutes" or periode == "Personnalisée":
            commandes = gc.get_commandes_jour()  # ou toutes les commandes
        elif periode == "Aujourd'hui":
            commandes = gc.get_commandes_jour()
        elif periode == "Cette semaine":
            commandes = gc.get_commandes_semaine()
        elif periode == "Ce mois":
            commandes = gc.get_commandes_mois()
        else:
            commandes = gc.get_commandes_jour()

        depenses = gd.get_depenses_par_periode(date_debut, date_fin) if date_debut and date_fin else gd.get_depenses()

        entrees = sum(c['total_ttc'] for c in commandes)
        sorties = sum(d['montant'] for d in depenses)
        solde = entrees - sorties

        depenses_par_type = {}
        for d in depenses:
            depenses_par_type[d['type']] = depenses_par_type.get(d['type'], 0) + d['montant']

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
            self.text_details_depenses.insert(tk.END, "Aucune dépense sur cette période.")
        self.text_details_depenses.config(state="disabled")

    def generer_rapport_bilan_pdf(self):
        if not self.acces_bilan:
            return
        # Fonction simplifiée pour le test
        messagebox.showinfo("Rapport PDF", "Fonctionnalité de rapport PDF disponible dans la version complète.")


if __name__ == "__main__":
    app = FenetreRestaurant()
    app.mainloop()