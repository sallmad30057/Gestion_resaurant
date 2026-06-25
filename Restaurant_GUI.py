"""
================================================================
INTERFACE GRAPHIQUE - Restaurant Chez Sall (version finale)
Avec dossier recus/, bouton imprimer, détails au clic, paiement, TVA
================================================================
"""

import os
import csv
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import date, datetime, timedelta
import subprocess
import platform

from Restaurant import Serveur, Caissier, Manager, Restaurant
from menu import MENU, TVA
from reçu import afficher_apercu_recu, generer_recu, imprimer_recu_depuis_commande, get_dossier_recus


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

        self.construire_onglet_commande()
        self.construire_onglet_commandes()
        self.construire_onglet_depenses()
        self.construire_onglet_bilan()

        self.bind("<Configure>", self.on_resize)
        
        # Variable pour stocker l'ID de la dernière commande
        self.derniere_commande_id = None
        self.derniere_commande_info = None
        self.selected_commande_id = None
        self.details_visible = False  # Pour savoir si les détails sont affichés

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

    def on_resize(self, event):
        """Gere le redimensionnement de la fenetre."""
        if hasattr(self, 'tableau_commandes'):
            largeur_totale = self.tableau_commandes.winfo_width()
            if largeur_totale > 100:
                largeurs = [40, 80, 60, 100, 150, 70, 70, 80, 80, 90]
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

    def ouvrir_dossier_recus(self):
        """Ouvre le dossier des reçus dans le gestionnaire de fichiers."""
        dossier = get_dossier_recus()
        if platform.system() == "Windows":
            os.startfile(dossier)
        elif platform.system() == "Darwin":  # macOS
            subprocess.run(["open", dossier])
        else:  # Linux
            subprocess.run(["xdg-open", dossier])

    # ==============================================================
    # ONGLET 1 : NOUVELLE COMMANDE
    # ==============================================================
    def construire_onglet_commande(self):
        cadre = self.onglet_commande
        cadre.configure(bg=COLORS['light'])
        
        # EN-TÊTE AVEC TITRE ET BOUTON RECU
        cadre_entete = tk.Frame(cadre, bg=COLORS['light'])
        cadre_entete.pack(fill="x", padx=20, pady=(10, 5))
        
        # Titre à gauche
        titre = tk.Label(cadre_entete, text="🛎️ Nouvelle commande", 
                        font=('Arial', 14, 'bold'), fg=COLORS['primary'], bg=COLORS['light'])
        titre.pack(side="left")
        
        # Bouton Reçu à droite (bien visible)
        self.btn_imprimer_recu = ttk.Button(
            cadre_entete, 
            text="🖨️ Imprimer le reçu", 
            command=self.imprimer_recu_derniere_commande,
            style='Print.TButton'
        )
        self.btn_imprimer_recu.pack(side="right", padx=5)
        self.btn_imprimer_recu.config(state="disabled")
        
        # Bouton pour ouvrir le dossier des reçus
        ttk.Button(
            cadre_entete, 
            text="📁 Voir les reçus", 
            command=self.ouvrir_dossier_recus,
            style='Accent.TButton'
        ).pack(side="right", padx=5)
        
        # Canvas avec scroll pour le reste
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
        
        # Liste des plats sélectionnés (panier)
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

        # Informations sur le total
        cadre_total = tk.Frame(cadre_contenu, bg=COLORS['light'])
        cadre_total.pack(anchor="w", pady=10, fill="x")
        
        self.label_total_ht = tk.Label(cadre_total, text="Total HT : 0.00€", 
                                       font=('Arial', 11, 'bold'), fg=COLORS['primary'], bg=COLORS['light'])
        self.label_total_ht.pack(anchor="w")
        
        self.label_tva = tk.Label(cadre_total, text="TVA (18%) : 0.00€", 
                                  font=('Arial', 11), fg=COLORS['warning'], bg=COLORS['light'])
        self.label_tva.pack(anchor="w")
        
        self.label_total_ttc = tk.Label(cadre_total, text="Total TTC : 0.00€", 
                                        font=('Arial', 14, 'bold'), fg=COLORS['success'], bg=COLORS['light'])
        self.label_total_ttc.pack(anchor="w", pady=(5, 0))

        # Moyen de paiement
        tk.Label(cadre_contenu, text="Moyen de paiement :", font=('Arial', 10), 
                bg=COLORS['light'], fg=COLORS['dark']).pack(anchor="w", pady=(10, 5))
        self.combo_paiement = ttk.Combobox(cadre_contenu, values=MOYENS_PAIEMENT, 
                                           state="readonly", width=20, font=('Arial', 10))
        self.combo_paiement.current(0)
        self.combo_paiement.pack(anchor="w", pady=(0, 10))

        # Avis
        tk.Label(cadre_contenu, text="Avis :", font=('Arial', 10), 
                bg=COLORS['light'], fg=COLORS['dark']).pack(anchor="w", pady=(10, 5))
        self.combo_avis = ttk.Combobox(cadre_contenu, values=["bon", "excellent", "pimenté", "parfait"], 
                                       state="readonly", width=20, font=('Arial', 10))
        self.combo_avis.current(0)
        self.combo_avis.pack(anchor="w", pady=(0, 20))

        cadre_boutons = tk.Frame(cadre_contenu, bg=COLORS['light'])
        cadre_boutons.pack(pady=10)
        
        ttk.Button(cadre_boutons, text="✅ Valider la commande", 
                  command=self.valider_commande, style='Accent.TButton').pack(side="left", padx=5)
        
        ttk.Button(cadre_boutons, text="🗑️ Vider le panier", 
                  command=self.vider_panier, style='Danger.TButton').pack(side="left", padx=5)
        
        tk.Frame(contenu, height=50, bg=COLORS['light']).pack()

    def ajouter_plat_selectionne(self, event=None):
        """Ajoute le plat sélectionné au panier."""
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
        dialog.grab_set()
        
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
        """Ajoute un plat au panier avec sa quantité."""
        for i, (p, q) in enumerate(self.panier_items):
            if p == plat:
                self.panier_items[i] = (p, q + quantite)
                break
        else:
            self.panier_items.append((plat, quantite))
        
        self.actualiser_panier()
        self.selecteur_plat.set("")

    def actualiser_panier(self):
        """Met à jour l'affichage du panier et les totaux."""
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
            tk.Label(ligne, text=f"={prix:.2f}€", 
                    font=('Arial', 10), bg=COLORS['light'], fg=COLORS['primary']).pack(side="left", padx=5)
            
            ttk.Button(ligne, text="✕", width=3,
                      command=lambda p=plat: self.supprimer_du_panier(p)).pack(side="right", padx=5)
        
        tva = total_ht * TVA
        total_ttc = total_ht + tva
        
        self.label_total_ht.config(text=f"Total HT : {total_ht:.2f}€")
        self.label_tva.config(text=f"TVA (18%) : {tva:.2f}€")
        self.label_total_ttc.config(text=f"Total TTC : {total_ttc:.2f}€")

    def supprimer_du_panier(self, plat):
        """Supprime un plat du panier."""
        self.panier_items = [(p, q) for p, q in self.panier_items if p != plat]
        self.actualiser_panier()

    def vider_panier(self):
        """Vide complètement le panier."""
        if self.panier_items:
            if messagebox.askyesno("Confirmation", "Vider le panier ?"):
                self.panier_items = []
                self.actualiser_panier()

    def imprimer_recu_derniere_commande(self):
        """Imprime le reçu de la dernière commande."""
        if self.derniere_commande_info:
            afficher_apercu_recu(self.derniere_commande_info, self)
        else:
            messagebox.showwarning("Aucune commande", "Aucune commande récente à imprimer.")

    def valider_commande(self):
        """Valide et enregistre la commande."""
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
        
        # Enregistrer la commande
        nouvel_id, tva, total_ttc = ajouter_commande_fichier(
            nom_client, plats_affichage, total_ht, avis, paiement
        )
        
        # Stocker les infos pour le reçu
        self.derniere_commande_info = {
            'id': str(nouvel_id),
            'date': date.today().strftime('%d/%m/%Y'),
            'heure': datetime.now().strftime('%H:%M'),
            'client': nom_client,
            'plats': plats_affichage,
            'avis': avis,
            'paiement': paiement
        }
        
        # Activer le bouton Reçu
        self.btn_imprimer_recu.config(state="normal")
        
        # Proposer d'imprimer le reçu
        if messagebox.askyesno("Reçu", "Voulez-vous imprimer un reçu pour cette commande ?"):
            afficher_apercu_recu(self.derniere_commande_info, self)
        
        messagebox.showinfo("Commande enregistree",
                            f"✅ Commande enregistree !\n\n"
                            f"N°: #{nouvel_id}\n"
                            f"Client : {nom_client}\n"
                            f"Plats : {', '.join(plats_affichage)}\n"
                            f"Total HT : {total_ht:.2f}€\n"
                            f"TVA (18%) : {tva:.2f}€\n"
                            f"Total TTC : {total_ttc:.2f}€\n"
                            f"Moyen de paiement : {paiement}\n"
                            f"Avis : {avis}")
        
        self.champ_client.delete(0, tk.END)
        self.panier_items = []
        self.actualiser_panier()
        self.combo_avis.current(0)
        self.combo_paiement.current(0)
        self.selecteur_plat.set("")
        
        self.appliquer_filtres_commandes()

    # ==============================================================
    # ONGLET 2 : COMMANDES AVEC DETAILS AU CLIC
    # ==============================================================
    def construire_onglet_commandes(self):
        # Frame principal avec PanedWindow pour redimensionnement
        self.paned = ttk.PanedWindow(self.onglet_commandes, orient='horizontal')
        self.paned.pack(fill="both", expand=True)
        
        # Partie gauche : Liste des commandes
        cadre_gauche = tk.Frame(self.paned, bg=COLORS['light'])
        self.paned.add(cadre_gauche, weight=1)
        
        # Partie droite : Détails (cachée par défaut)
        self.cadre_droite = tk.Frame(self.paned, bg=COLORS['white'], width=350)
        # Ne pas ajouter immédiatement - on l'ajoutera au clic
        self.details_pane_added = False

        # ===== PARTIE GAUCHE : LISTE DES COMMANDES =====
        cadre = cadre_gauche
        cadre.configure(bg=COLORS['light'])

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
        largeurs = [40, 80, 60, 100, 150, 60, 60, 70, 80, 90]
        for col, titre, largeur in zip(colonnes, titres, largeurs):
            self.tableau_commandes.heading(col, text=titre)
            self.tableau_commandes.column(col, width=largeur, minwidth=largeur//2)

        scroll_y.config(command=self.tableau_commandes.yview)
        scroll_x.config(command=self.tableau_commandes.xview)

        self.tableau_commandes.pack(side="left", fill="both", expand=True)
        scroll_y.pack(side="right", fill="y")
        scroll_x.pack(side="bottom", fill="x")
        
        # Bind pour la sélection - AFFICHAGE DES DETAILS UNIQUEMENT AU CLIC
        self.tableau_commandes.bind("<<TreeviewSelect>>", self.on_commande_selectionnee)

        cadre_bas = tk.Frame(contenu, bg=COLORS['light'])
        cadre_bas.pack(anchor="w", padx=10, pady=10, fill="x")
        
        self.label_resultat_commandes = tk.Label(cadre_bas, text="", font=('Arial', 10), 
                                                bg=COLORS['light'], fg=COLORS['primary'])
        self.label_resultat_commandes.pack(side="left")

        cadre_boutons = tk.Frame(cadre_bas, bg=COLORS['light'])
        cadre_boutons.pack(side="right")
        
        ttk.Button(cadre_boutons, text="🖨️ Reçu", 
                  command=self.imprimer_recu_selectionne,
                  style='Print.TButton').pack(side="right", padx=5)
        
        ttk.Button(cadre_boutons, text="🗑️ Supprimer", 
                  command=self.supprimer_commandes_selectionnees,
                  style='Danger.TButton').pack(side="right", padx=5)
        
        tk.Frame(contenu, height=50, bg=COLORS['light']).pack()

        # ===== PARTIE DROITE : DÉTAILS DE LA COMMANDE (cachée par défaut) =====
        self.construire_panneau_details()

        self.appliquer_filtres_commandes()

    def construire_panneau_details(self):
        """Construit le panneau des détails (caché par défaut)."""
        cadre = self.cadre_droite
        cadre.configure(bg=COLORS['white'])
        
        # Titre
        tk.Label(cadre, text="📄 Détails de la commande", 
                font=('Arial', 12, 'bold'), bg=COLORS['white'], fg=COLORS['primary']).pack(pady=(10, 5))
        
        # Frame pour les détails avec scroll
        details_canvas = tk.Canvas(cadre, bg='white', highlightthickness=0)
        details_scrollbar = ttk.Scrollbar(cadre, orient="vertical", command=details_canvas.yview)
        details_frame = tk.Frame(details_canvas, bg='white')
        
        details_frame.bind(
            "<Configure>",
            lambda e: details_canvas.configure(scrollregion=details_canvas.bbox("all"))
        )
        
        details_canvas.create_window((0, 0), window=details_frame, anchor="nw", width=details_canvas.winfo_width())
        details_canvas.configure(yscrollcommand=details_scrollbar.set)
        
        def _configure_details_canvas(event):
            details_canvas.itemconfig(1, width=event.width)
        
        details_canvas.bind("<Configure>", _configure_details_canvas)
        
        details_canvas.pack(side="left", fill="both", expand=True)
        details_scrollbar.pack(side="right", fill="y")
        
        # Widgets pour les détails
        self.details_text = tk.Text(details_frame, height=20, width=35, 
                                   font=('Arial', 9), bg='white', wrap='word')
        self.details_text.pack(fill="both", expand=True, padx=10, pady=5)
        self.details_text.config(state="disabled")
        
        # Message par défaut
        self.details_text.config(state="normal")
        self.details_text.insert("1.0", "\n\n\n   👆 Cliquez sur une commande\n   pour voir les détails ici")
        self.details_text.config(state="disabled")
        
        # Bouton pour imprimer depuis les détails
        btn_print_details = ttk.Button(cadre, text="🖨️ Imprimer ce reçu", 
                                       command=self.imprimer_recu_depuis_details,
                                       style='Print.TButton')
        btn_print_details.pack(pady=5)
        
        # Cacher le panneau par défaut
        self.cadre_droite.pack_forget()

    def on_commande_selectionnee(self, event):
        """Affiche les détails de la commande sélectionnée (UNIQUEMENT au clic)."""
        selection = self.tableau_commandes.selection()
        if not selection:
            return
        
        valeurs = self.tableau_commandes.item(selection[0], "values")
        if not valeurs:
            return
        
        commande_id = valeurs[0]
        
        # Récupérer les infos de la commande
        commandes = charger_commandes()
        for cmd in commandes:
            if str(cmd.get('ID', '')) == str(commande_id):
                # Ajouter le panneau des détails s'il n'est pas déjà affiché
                if not self.details_pane_added:
                    self.paned.add(self.cadre_droite, weight=0)
                    self.details_pane_added = True
                
                self.afficher_details_commande(cmd)
                self.selected_commande_id = commande_id
                
                # Forcer le redimensionnement du panneau
                self.paned.update_idletasks()
                return

    def afficher_details_commande(self, cmd):
        """Affiche les détails d'une commande dans le panneau de droite."""
        self.details_text.config(state="normal")
        self.details_text.delete("1.0", tk.END)
        
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
Total HT : {cmd.get('Total HT (€)', '0.00')}€
TVA (18%) : {cmd.get('TVA (€)', '0.00')}€
Total TTC : {cmd.get('Total TTC (€)', '0.00')}€

⭐ Avis : {cmd.get('Avis', 'Non spécifié')}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
        self.details_text.insert("1.0", details)
        self.details_text.config(state="disabled")

    def formater_plats(self, plats_str):
        """Formate la liste des plats pour l'affichage."""
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

    def imprimer_recu_depuis_details(self):
        """Imprime un reçu pour la commande affichée dans les détails."""
        if hasattr(self, 'selected_commande_id') and self.selected_commande_id:
            imprimer_recu_depuis_commande(self.selected_commande_id, self)
        else:
            messagebox.showwarning("Aucune commande", "Veuillez sélectionner une commande.")

    def imprimer_recu_selectionne(self):
        """Imprime un reçu pour la commande sélectionnée."""
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
        """Supprime toutes les commandes selectionnees."""
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
        
        # Cacher les détails si affichés
        if self.details_pane_added:
            self.paned.remove(self.cadre_droite)
            self.details_pane_added = False
        
        messagebox.showinfo("Succes", f"✅ {len(ids_a_supprimer)} commande(s) supprimee(s).")

    def appliquer_filtres_commandes(self):
        """Applique les filtres et affiche les commandes."""
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
                    f"{total_ht_cmd:.2f}",
                    f"{tva_cmd:.2f}",
                    f"{total_ttc_cmd:.2f}",
                    c.get("Avis", ""),
                    c.get("Paiement", "")
                ))
                total_ht += total_ht_cmd
                total_ttc += total_ttc_cmd
                nb += 1
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur lors du chargement : {str(e)}")

        self.label_resultat_commandes.config(
            text=f"📊 {nb} commande(s) - HT : {total_ht:.2f}€ - TTC : {total_ttc:.2f}€"
        )

    def reinitialiser_filtres_commandes(self):
        """Reinitialise tous les filtres."""
        self.filtre_client.delete(0, tk.END)
        self.filtre_plat.delete(0, tk.END)
        self.filtre_id.delete(0, tk.END)
        self.filtre_avis.current(0)
        self.filtre_periode_commande.current(0)
        self.appliquer_filtres_commandes()

    def exporter_commandes_csv(self):
        """Exporte les commandes filtrees dans un fichier CSV."""
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
    # ONGLET 3 : DEPENSES
    # ==============================================================
    def construire_onglet_depenses(self):
        """Construit l'onglet de gestion des depenses."""
        cadre = self.onglet_depenses
        cadre.configure(bg=COLORS['light'])

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

        def _configure_canvas(event):
            canvas.itemconfig(1, width=event.width)
        
        canvas.bind("<Configure>", _configure_canvas)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        contenu = scrollable_frame
        contenu.configure(bg=COLORS['light'])

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

        tk.Label(ligne_form, text="Montant (€) :", font=('Arial', 9), bg=COLORS['light']).pack(side="left", padx=5)
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
        titres = ["ID", "Date", "Type", "Description", "Montant (€)"]
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

    def ajouter_depense(self):
        """Ajoute une nouvelle depense."""
        type_depense = self.combo_type_depense.get()
        description = self.champ_description_depense.get().strip()
        try:
            montant = float(self.champ_montant_depense.get().strip())
        except ValueError:
            messagebox.showwarning("Montant invalide", "Le montant doit etre un nombre.")
            return

        ajouter_depense_fichier(type_depense, description, montant)
        messagebox.showinfo("Depense ajoutee", f"✅ {type_depense} : {montant}€ ajoutee.")

        self.champ_description_depense.delete(0, tk.END)
        self.champ_montant_depense.delete(0, tk.END)
        self.appliquer_filtres_depenses()

    def appliquer_filtres_depenses(self):
        """Applique les filtres pour les depenses."""
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
                d.get("Montant (€)", "0")
            ))
            try:
                total_affiche += float(d.get("Montant (€)", "0"))
            except:
                pass
            nb += 1

        self.label_resultat_depenses.config(
            text=f"📊 {nb} depense(s) affichee(s) - Total : {total_affiche:.2f}€"
        )

    def reinitialiser_filtres_depenses(self):
        """Reinitialise les filtres des depenses."""
        self.filtre_type_depense.current(0)
        self.filtre_periode_depense.current(0)
        self.appliquer_filtres_depenses()

    def supprimer_depense_selectionnee(self):
        """Supprime une depense selectionnee."""
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
    # ONGLET 4 : BILAN
    # ==============================================================
    def construire_onglet_bilan(self):
        """Construit l'onglet de bilan financier."""
        cadre = self.onglet_bilan
        cadre.configure(bg=COLORS['light'])

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

        def _configure_canvas(event):
            canvas.itemconfig(1, width=event.width)
        
        canvas.bind("<Configure>", _configure_canvas)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        contenu = scrollable_frame
        contenu.configure(bg=COLORS['light'])

        cadre_entete = tk.Frame(contenu, bg=COLORS['light'])
        cadre_entete.pack(fill="x", padx=20, pady=(20, 10))

        titre = tk.Label(cadre_entete, text="📊 Bilan financier (TTC)", 
                        font=('Arial', 16, 'bold'), fg=COLORS['primary'], bg=COLORS['light'])
        titre.pack(side="left")

        cadre_solde = tk.Frame(cadre_entete, bg=COLORS['light'], relief='ridge', bd=2)
        cadre_solde.pack(side="right", padx=10)

        tk.Label(cadre_solde, text="SOLDE", 
                font=('Arial', 10, 'bold'), fg=COLORS['white'], 
                bg=COLORS['primary'], padx=15, pady=2).pack(fill="x")

        self.label_solde_principal = tk.Label(cadre_solde, text="0.00 €", 
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
                  style='Accent.TButton').pack(pady=10)

        cadre_resultats = ttk.LabelFrame(cadre_contenu, text="📈 Details", padding=15)
        cadre_resultats.pack(anchor="w", pady=10, fill="both", expand=True)

        grille_resultats = tk.Frame(cadre_resultats, bg=COLORS['light'])
        grille_resultats.pack(fill="x", pady=5)

        cadre_entrees = tk.Frame(grille_resultats, bg=COLORS['light'], relief='groove', bd=1)
        cadre_entrees.pack(side="left", fill="both", expand=True, padx=5)

        tk.Label(cadre_entrees, text="💰 Entrees (TTC)", 
                font=('Arial', 10, 'bold'), bg=COLORS['success'], fg=COLORS['white'],
                padx=10, pady=5).pack(fill="x")
        self.label_entrees = tk.Label(cadre_entrees, text="0.00 €", 
                                      font=('Arial', 14, 'bold'), 
                                      fg=COLORS['success'], bg=COLORS['light'],
                                      padx=10, pady=10)
        self.label_entrees.pack()

        cadre_sorties = tk.Frame(grille_resultats, bg=COLORS['light'], relief='groove', bd=1)
        cadre_sorties.pack(side="right", fill="both", expand=True, padx=5)

        tk.Label(cadre_sorties, text="💸 Sorties (depenses)", 
                font=('Arial', 10, 'bold'), bg=COLORS['danger'], fg=COLORS['white'],
                padx=10, pady=5).pack(fill="x")
        self.label_sorties = tk.Label(cadre_sorties, text="0.00 €", 
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
        
        self.calculer_et_afficher_bilan()

    def on_bilan_periode_changed(self, event=None):
        """Active ou desactive les dates personnalisees pour le bilan."""
        periode = self.combo_periode_bilan.get()
        etat = "normal" if periode == "Personnalisee" else "disabled"
        self.bilan_date_debut.config(state=etat)
        self.bilan_date_fin.config(state=etat)

    def calculer_et_afficher_bilan(self):
        """Calcule et affiche le bilan financier."""
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
        
        self.label_entrees.config(text=f"{entrees:.2f} €")
        self.label_sorties.config(text=f"{sorties:.2f} €")
        
        self.label_solde_principal.config(text=f"{solde:.2f} €")
        
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
                self.text_details_depenses.insert(tk.END, f"  • {type_dep}: {montant:.2f}€\n")
        else:
            self.text_details_depenses.insert(tk.END, "Aucune depense sur cette periode.")
        self.text_details_depenses.config(state="disabled")


if __name__ == "__main__":
    app = FenetreRestaurant()
    app.mainloop()