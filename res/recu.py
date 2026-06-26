"""
================================================================
GESTION DES REÇUS - Restaurant Chez Sall
================================================================
"""

import os
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
from datetime import datetime
from reportlab.lib.pagesizes import A6, A5
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT

# Importer le menu pour les prix
try:
    from menu import MENU
except ImportError:
    MENU = {}

# TVA
TVA_RATE = 0.18

# Dossier pour les reçus
DOSSIER_RECUS = "recus"

def get_dossier_recus():
    """Retourne le chemin du dossier des reçus, le crée si nécessaire."""
    if not os.path.exists(DOSSIER_RECUS):
        os.makedirs(DOSSIER_RECUS)
    return DOSSIER_RECUS

def format_fcfa(amount):
    """
    Formate un montant en FCFA sans décimales, avec séparation des milliers par espace.
    Exemple: 23000 -> "23 000 FCFA"
    """
    try:
        amount = round(float(amount))
        return f"{amount:,}".replace(",", " ") + " FCFA"
    except:
        return "0 FCFA"

def generer_recu(commande_info, fichier_pdf=None):
    """
    Génère un reçu PDF pour une commande dans le dossier recus/.
    """
    # Créer le dossier si nécessaire
    dossier = get_dossier_recus()
    
    if fichier_pdf is None:
        # Générer un nom de fichier avec la date et l'ID
        date_str = datetime.now().strftime("%Y%m%d_%H%M%S")
        id_commande = commande_info.get('id', '0000')
        fichier_pdf = f"recu_{date_str}_#{id_commande}.pdf"
    
    # Chemin complet
    chemin_complet = os.path.join(dossier, fichier_pdf)
    
    doc = SimpleDocTemplate(chemin_complet, pagesize=A6,
                           rightMargin=8*mm, leftMargin=8*mm,
                           topMargin=8*mm, bottomMargin=8*mm)
    
    styles = getSampleStyleSheet()
    
    # Styles personnalisés
    style_titre = ParagraphStyle(
        'Titre',
        parent=styles['Title'],
        fontSize=14,
        alignment=TA_CENTER,
        textColor=colors.HexColor('#2c3e50'),
        spaceAfter=4
    )
    
    style_sous_titre = ParagraphStyle(
        'SousTitre',
        parent=styles['Normal'],
        fontSize=9,
        alignment=TA_CENTER,
        textColor=colors.HexColor('#7f8c8d'),
        spaceAfter=8
    )
    
    style_info = ParagraphStyle(
        'Info',
        parent=styles['Normal'],
        fontSize=8,
        alignment=TA_CENTER,
        spaceAfter=2
    )
    
    style_separateur = ParagraphStyle(
        'Separateur',
        parent=styles['Normal'],
        fontSize=8,
        alignment=TA_CENTER,
        textColor=colors.HexColor('#bdc3c7')
    )
    
    style_item = ParagraphStyle(
        'Item',
        parent=styles['Normal'],
        fontSize=9,
        spaceAfter=2
    )
    
    style_item_bold = ParagraphStyle(
        'ItemBold',
        parent=styles['Normal'],
        fontSize=9,
        spaceAfter=2,
        textColor=colors.HexColor('#2c3e50')
    )
    
    style_total = ParagraphStyle(
        'Total',
        parent=styles['Normal'],
        fontSize=12,
        alignment=TA_RIGHT,
        textColor=colors.HexColor('#27ae60'),
        spaceAfter=4
    )
    
    style_tva = ParagraphStyle(
        'TVA',
        parent=styles['Normal'],
        fontSize=8,
        alignment=TA_RIGHT,
        textColor=colors.HexColor('#f39c12'),
        spaceAfter=2
    )
    
    style_pied = ParagraphStyle(
        'Pied',
        parent=styles['Normal'],
        fontSize=7,
        alignment=TA_CENTER,
        textColor=colors.HexColor('#95a5a6'),
        spaceAfter=2
    )
    
    # Construction du contenu
    story = []
    
    # En-tête
    story.append(Paragraph("🏪 CHEZ SALL", style_titre))
    story.append(Paragraph("Restaurant - Traiteur", style_sous_titre))
    story.append(Paragraph("📞 +221 77 123 45 67", style_info))
    story.append(Paragraph("📍 Dakar, Sénégal", style_info))
    story.append(Paragraph("-" * 35, style_separateur))
    story.append(Spacer(1, 4))
    
    # Informations de la commande
    story.append(Paragraph(f"N° Commande: #{commande_info.get('id', '0000')}", style_item))
    story.append(Paragraph(f"Date: {commande_info.get('date', datetime.now().strftime('%d/%m/%Y'))}", style_item))
    story.append(Paragraph(f"Heure: {commande_info.get('heure', datetime.now().strftime('%H:%M'))}", style_item))
    story.append(Paragraph(f"Client: {commande_info.get('client', 'Client')}", style_item))
    story.append(Paragraph(f"Moyen de paiement: {commande_info.get('paiement', 'Non spécifié')}", style_item))
    story.append(Paragraph("-" * 35, style_separateur))
    story.append(Spacer(1, 4))
    
    # Liste des plats
    story.append(Paragraph("Détail de la commande :", style_item_bold))
    story.append(Spacer(1, 2))
    
    # Tableau des plats
    plats = commande_info.get('plats', [])
    if isinstance(plats, str):
        plats = [p.strip() for p in plats.split('+')]
    
    data = [["Article", "Prix"]]
    total_ht = 0
    
    for plat in plats:
        if ' x' in plat:
            nom, qte = plat.split(' x')
            nom = nom.strip()
            try:
                qte = int(qte.strip())
            except:
                qte = 1
            prix_unitaire = MENU.get(nom, 0)
            prix = prix_unitaire * qte
            data.append([f"{nom} x{qte}", format_fcfa(prix)])
            total_ht += prix
        else:
            plat_clean = plat.strip()
            prix = MENU.get(plat_clean, 0)
            data.append([plat_clean, format_fcfa(prix)])
            total_ht += prix
    
    if len(data) == 1:
        data.append(["Aucun plat", format_fcfa(0)])
    
    table = Table(data, colWidths=[70*mm, 25*mm])
    table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('GRID', (0, 0), (-1, 0), 0.5, colors.HexColor('#2c3e50')),
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#ecf0f1')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor('#2c3e50')),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    story.append(table)
    story.append(Spacer(1, 6))
    story.append(Paragraph("-" * 35, style_separateur))
    story.append(Spacer(1, 4))
    
    # Totaux
    tva = total_ht * TVA_RATE
    total_ttc = total_ht + tva
    
    story.append(Paragraph(f"Sous-total HT: {format_fcfa(total_ht)}", style_item))
    story.append(Paragraph(f"TVA (18%): {format_fcfa(tva)}", style_tva))
    story.append(Paragraph(f"<b>TOTAL TTC: {format_fcfa(total_ttc)}</b>", style_total))
    story.append(Spacer(1, 6))
    
    avis = commande_info.get('avis', '')
    if avis:
        story.append(Paragraph(f"⭐ Avis: {avis}", style_info))
    
    story.append(Paragraph("-" * 35, style_separateur))
    story.append(Spacer(1, 4))
    
    # Pied de page
    story.append(Paragraph("Merci de votre visite !", style_pied))
    story.append(Paragraph("À bientôt chez Chez Sall", style_pied))
    story.append(Paragraph(f"Imprimé le {datetime.now().strftime('%d/%m/%Y %H:%M')}", style_pied))
    
    # Générer le PDF
    doc.build(story)
    return chemin_complet

def afficher_apercu_recu(commande_info, parent=None):
    """
    Affiche un aperçu du reçu dans une fenêtre séparée avec scrollbar.
    """
    fenetre = tk.Toplevel(parent)
    fenetre.title("📄 Aperçu du reçu")
    fenetre.geometry("450x650")
    fenetre.configure(bg='white')
    fenetre.transient(parent)
    fenetre.grab_set()
    
    fenetre.focus_force()
    
    style = ttk.Style()
    style.theme_use('clam')
    
    main_frame = tk.Frame(fenetre, bg='white')
    main_frame.pack(fill="both", expand=True, padx=10, pady=10)
    
    canvas = tk.Canvas(main_frame, bg='white', highlightthickness=0)
    scrollbar = ttk.Scrollbar(main_frame, orient="vertical", command=canvas.yview)
    scrollable_frame = tk.Frame(canvas, bg='white')
    
    scrollable_frame.bind(
        "<Configure>",
        lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
    )
    
    canvas.create_window((0, 0), window=scrollable_frame, anchor="nw", width=canvas.winfo_width())
    canvas.configure(yscrollcommand=scrollbar.set)
    
    def _configure_canvas(event):
        canvas.itemconfig(1, width=event.width)
    
    canvas.bind("<Configure>", _configure_canvas)
    
    def _on_mousewheel(event):
        canvas.yview_scroll(int(-1*(event.delta/120)), "units")
    
    def _on_enter(event):
        canvas.bind_all("<MouseWheel>", _on_mousewheel)
    
    def _on_leave(event):
        canvas.unbind_all("<MouseWheel>")
    
    canvas.bind("<Enter>", _on_enter)
    canvas.bind("<Leave>", _on_leave)
    
    canvas.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")
    
    contenu = scrollable_frame
    contenu.configure(bg='white')
    
    # En-tête
    cadre_entete = tk.Frame(contenu, bg='white')
    cadre_entete.pack(fill='x', pady=(15, 5))
    
    tk.Label(cadre_entete, text="CHEZ SALL", font=('Arial', 18, 'bold'), 
            fg='#2c3e50', bg='white').pack()
    
    tk.Label(cadre_entete, text="Restaurant - Traiteur", 
            font=('Arial', 10), fg='#7f8c8d', bg='white').pack()
    
    tk.Label(cadre_entete, text="📞 +221 77 123 45 67  |  📍 Dakar", 
            font=('Arial', 8), fg='#95a5a6', bg='white').pack()
    
    tk.Label(contenu, text="─" * 40, font=('Arial', 8), 
            fg='#bdc3c7', bg='white').pack(pady=5)
    
    # Informations commande
    info_frame = tk.Frame(contenu, bg='white')
    info_frame.pack(fill='x', padx=10, pady=5)
    
    infos = [
        f"N° Commande: #{commande_info.get('id', '0000')}",
        f"Date: {commande_info.get('date', datetime.now().strftime('%d/%m/%Y'))}",
        f"Heure: {commande_info.get('heure', datetime.now().strftime('%H:%M'))}",
        f"Client: {commande_info.get('client', 'Client')}",
        f"Moyen de paiement: {commande_info.get('paiement', 'Non spécifié')}"
    ]
    
    for info in infos:
        tk.Label(info_frame, text=info, font=('Arial', 10), 
                bg='white', anchor='w').pack(fill='x', pady=1)
    
    tk.Label(contenu, text="─" * 40, font=('Arial', 8), 
            fg='#bdc3c7', bg='white').pack(pady=5)
    
    # Détail des plats
    tk.Label(contenu, text="DÉTAIL DE LA COMMANDE", 
            font=('Arial', 10, 'bold'), bg='white').pack(anchor='w', padx=10, pady=5)
    
    header = tk.Frame(contenu, bg='#ecf0f1')
    header.pack(fill='x', padx=10, pady=(0, 2))
    
    tk.Label(header, text="Article", font=('Arial', 9, 'bold'), 
            bg='#ecf0f1', width=25, anchor='w').pack(side='left', padx=5)
    tk.Label(header, text="Prix", font=('Arial', 9, 'bold'), 
            bg='#ecf0f1', width=10, anchor='e').pack(side='right', padx=5)
    
    plats = commande_info.get('plats', [])
    if isinstance(plats, str):
        plats = [p.strip() for p in plats.split('+')]
    
    total_ht = 0
    from menu import MENU
    
    for plat in plats:
        ligne = tk.Frame(contenu, bg='white')
        ligne.pack(fill='x', padx=10, pady=2)
        
        if ' x' in plat:
            nom, qte = plat.split(' x')
            nom = nom.strip()
            try:
                qte = int(qte.strip())
            except:
                qte = 1
            prix_unitaire = MENU.get(nom, 0)
            prix = prix_unitaire * qte
            tk.Label(ligne, text=f"{nom} x{qte}", font=('Arial', 9), 
                    bg='white', width=25, anchor='w').pack(side='left', padx=5)
            tk.Label(ligne, text=format_fcfa(prix), font=('Arial', 9), 
                    bg='white', width=10, anchor='e').pack(side='right', padx=5)
            total_ht += prix
        else:
            plat_clean = plat.strip()
            prix = MENU.get(plat_clean, 0)
            tk.Label(ligne, text=plat_clean, font=('Arial', 9), 
                    bg='white', width=25, anchor='w').pack(side='left', padx=5)
            tk.Label(ligne, text=format_fcfa(prix), font=('Arial', 9), 
                    bg='white', width=10, anchor='e').pack(side='right', padx=5)
            total_ht += prix
    
    tk.Label(contenu, text="─" * 40, font=('Arial', 8), 
            fg='#bdc3c7', bg='white').pack(pady=5)
    
    tva = total_ht * TVA_RATE
    total_ttc = total_ht + tva
    
    total_frame = tk.Frame(contenu, bg='white')
    total_frame.pack(fill='x', padx=10, pady=5)
    
    tk.Label(total_frame, text="Sous-total HT:", font=('Arial', 10), 
            bg='white').pack(anchor='e')
    tk.Label(total_frame, text=format_fcfa(total_ht), font=('Arial', 10), 
            bg='white').pack(anchor='e')
    
    tk.Label(total_frame, text="TVA (18%):", font=('Arial', 9), 
            fg='#f39c12', bg='white').pack(anchor='e')
    tk.Label(total_frame, text=format_fcfa(tva), font=('Arial', 9), 
            fg='#f39c12', bg='white').pack(anchor='e')
    
    tk.Label(total_frame, text="=" * 30, font=('Arial', 8), 
            fg='#bdc3c7', bg='white').pack(anchor='e', pady=2)
    
    tk.Label(total_frame, text="TOTAL TTC:", font=('Arial', 12, 'bold'), 
            fg='#27ae60', bg='white').pack(anchor='e')
    tk.Label(total_frame, text=format_fcfa(total_ttc), font=('Arial', 14, 'bold'), 
            fg='#27ae60', bg='white').pack(anchor='e')
    
    avis = commande_info.get('avis', '')
    if avis:
        tk.Label(contenu, text=f"⭐ Avis: {avis}", font=('Arial', 9), 
                fg='#7f8c8d', bg='white').pack(pady=5)
    
    tk.Label(contenu, text="─" * 40, font=('Arial', 8), 
            fg='#bdc3c7', bg='white').pack(pady=5)
    
    tk.Label(contenu, text="Merci de votre visite !", font=('Arial', 9, 'bold'), 
            fg='#2c3e50', bg='white').pack()
    tk.Label(contenu, text="À bientôt chez Chez Sall", font=('Arial', 9), 
            fg='#7f8c8d', bg='white').pack()
    tk.Label(contenu, text=f"Imprimé le {datetime.now().strftime('%d/%m/%Y %H:%M')}", 
            font=('Arial', 7), fg='#95a5a6', bg='white').pack(pady=5)
    
    boutons_frame = tk.Frame(contenu, bg='white')
    boutons_frame.pack(fill='x', padx=10, pady=10)
    
    def imprimer_pdf():
        try:
            fichier = generer_recu(commande_info)
            messagebox.showinfo("Succès", f"✅ Reçu généré avec succès !\n\nFichier: {fichier}")
            fenetre.destroy()
        except Exception as e:
            messagebox.showerror("Erreur", f"❌ Erreur lors de la génération du PDF : {str(e)}")
    
    ttk.Button(boutons_frame, text="🖨️ Imprimer PDF", 
              command=imprimer_pdf, style='Accent.TButton').pack(side='left', padx=5, expand=True, fill='x')
    
    ttk.Button(boutons_frame, text="❌ Fermer", 
              command=fenetre.destroy, style='Danger.TButton').pack(side='right', padx=5, expand=True, fill='x')

def imprimer_recu_depuis_commande(commande_id, parent=None):
    """
    Imprime un reçu à partir de l'ID de commande.
    """
    try:
        import sys
        sys.path.append(os.path.dirname(os.path.abspath(__file__)))
        from Restaurant_GUI import charger_commandes
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
                afficher_apercu_recu(commande_info, parent)
                return True
        
        messagebox.showerror("Erreur", f"❌ Commande n°{commande_id} non trouvée.")
        return False
    except Exception as e:
        messagebox.showerror("Erreur", f"❌ Erreur : {str(e)}")
        return False