"""
main.py — Application de comptabilité SYSCOHADA autonome (Tkinter).

Navigation par menu (SAISIE, COMMERCE, PRODUCTION, ENGAGEMENTS-PROJETS,
ÉTATS ET RAPPORTS) : un seul panneau de contenu, qui change selon le menu
choisi. Les données sont stockées localement dans un fichier SQLite
(%LOCALAPPDATA%\\SaisieComptable\\comptabilite.db sous Windows).
"""
import tkinter as tk
from tkinter import ttk, messagebox, filedialog, simpledialog
from datetime import date

import core


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Saisie Comptable SYSCOHADA")
        self.geometry("1200x720")
        self.conn = core.get_connection()

        # ---- Barre d'exercice comptable (toujours visible, en haut) ----
        top_bar = ttk.Frame(self, relief="raised", padding=4)
        top_bar.pack(fill="x", side="top")
        ttk.Label(top_bar, text="EXERCICE COMPTABLE :", font=("Segoe UI", 9, "bold")).pack(side="left", padx=(6, 4))
        self.exercice_var = tk.StringVar(value=core.get_current_exercice(self.conn))
        self.exercice_combo = ttk.Combobox(top_bar, textvariable=self.exercice_var, width=10, state="readonly")
        self.exercice_combo.pack(side="left", padx=4)
        self.exercice_combo.bind("<<ComboboxSelected>>", self._on_exercice_changed)
        ttk.Button(top_bar, text="+ Nouvel exercice", command=self._new_exercice).pack(side="left", padx=8)
        self.exercice_status_var = tk.StringVar()
        ttk.Label(top_bar, textvariable=self.exercice_status_var, foreground="#B00020",
                  font=("Segoe UI", 9, "bold")).pack(side="left", padx=12)
        self._refresh_exercice_list()

        self.content = ttk.Frame(self)
        self.content.pack(fill="both", expand=True)
        self.content.grid_rowconfigure(0, weight=1)
        self.content.grid_columnconfigure(0, weight=1)

        self.pages = {}

        def register(key, cls, *args):
            w = cls(self.content, self.conn, *args)
            w.grid(row=0, column=0, sticky="nsew")
            self.pages[key] = w
            return w

        # ---- Instanciation de toutes les pages (une seule fois) ----
        register("saisie", SaisieTab)
        register("ouverture", OpeningBalancesTab)
        register("exercices", ExercicesTab, self)
        register("plan_comptable", PlanComptableTab)
        register("plan_analytique", PlanAnalytiqueTab)
        register("plan_budgetaire", PlanBudgetaireTab)
        register("plan_bailleur", PlanBailleurTab)
        register("stocks", StocksTab)
        register("production", ProductionTab)
        register("cr", CompteResultatTab)
        register("tft", TftTab)
        register("situation_financiere", SituationFinanciereTab)
        register("grand_livre", GrandLivreTab)
        register("balance", BalanceTab)
        register("bilan", BilanTab)
        register("liasse", LiasseFiscaleTab)
        register("ventes", VentesTab)
        register("clients", ClientsTab)
        register("recouvrement", RecouvrementTab)
        register("facturation", FacturationTab)
        register("marges", MargesTab)
        register("achats", AchatsTab)
        register("fournisseurs", FournisseursTab)
        register("factures_frs", FacturesFrsTab)
        register("contrats", ContratsTab)
        register("budget_exec", PlaceholderTab,
                 "Tableaux d'exécution budgétaire",
                 "Suivi budget prévisionnel vs réalisé, par ligne budgétaire et par projet.")
        register("impots", PlaceholderTab,
                 "Impôts", "Calcul et suivi des impôts (IS, TVA due/récupérable, retenues à la source...).")
        register("declarations_sociales", PlaceholderTab,
                 "Déclarations sociales", "Préparation des déclarations CNSS et assimilées.")
        register("rapprochements", PlaceholderTab,
                 "Rapprochements bancaires",
                 "Comparaison des relevés bancaires avec les comptes de trésorerie (521000/531000/570000).")

        # ---- Barre de menu ----
        menubar = tk.Menu(self)
        bold = ("Segoe UI", 9, "bold")

        def add_top_menu(label, items):
            m = tk.Menu(menubar, tearoff=0)
            for item_label, key in items:
                m.add_command(label=item_label, command=lambda k=key: self.show(k))
            menubar.add_cascade(label=label, menu=m)
            menubar.entryconfig(menubar.index("end"), font=bold)

        add_top_menu("SAISIE", [
            ("Saisie des écritures", "saisie"),
            ("Soldes d'ouverture", "ouverture"),
        ])
        add_top_menu("COMMERCE", [
            ("Ventes", "ventes"),
            ("Clients", "clients"),
            ("Recouvrement", "recouvrement"),
            ("Facturation", "facturation"),
            ("Stocks", "stocks"),
            ("Marges bénéficiaires", "marges"),
        ])
        add_top_menu("PRODUCTION", [
            ("Matières premières", "stocks"),
            ("Fabrication", "production"),
            ("Produits finis", "stocks"),
        ])
        add_top_menu("ENGAGEMENTS-PROJETS", [
            ("Achats", "achats"),
            ("Fournisseurs", "fournisseurs"),
            ("Factures frs", "factures_frs"),
            ("Contrats", "contrats"),
        ])
        add_top_menu("ÉTATS ET RAPPORTS", [
            ("Grand livre", "grand_livre"),
            ("Balance", "balance"),
            ("Bilan", "bilan"),
            ("Compte de résultat", "cr"),
            ("TFT", "tft"),
            ("Situation financière", "situation_financiere"),
            ("Liasse fiscale", "liasse"),
            ("Tableaux d'exécution budgétaire", "budget_exec"),
            ("Impôts", "impots"),
            ("Déclarations sociales", "declarations_sociales"),
            ("Rapprochements bancaires", "rapprochements"),
        ])
        add_top_menu("PARAMÈTRES", [
            ("Exercices comptables (clôture)", "exercices"),
            ("Plan comptable", "plan_comptable"),
            ("Plan analytique", "plan_analytique"),
            ("Plan budgétaire", "plan_budgetaire"),
            ("Plan bailleurs de fonds", "plan_bailleur"),
        ])
        self.config(menu=menubar)

        self.show("saisie")

    def _refresh_exercice_list(self):
        exercices = core.list_exercices(self.conn)
        values = [e["exercice"] + (" (clôturé)" if e["cloture"] else "") for e in exercices]
        self.exercice_combo["values"] = values
        current = core.get_current_exercice(self.conn)
        match = next((v for v in values if v.startswith(current)), current)
        self.exercice_var.set(match)
        if core.is_exercice_cloture(self.conn, current):
            self.exercice_status_var.set("⚠ Cet exercice est clôturé (lecture seule).")
        else:
            self.exercice_status_var.set("")

    def _on_exercice_changed(self, event=None):
        raw = self.exercice_var.get().split(" ")[0]
        core.set_current_exercice(self.conn, raw)
        self._refresh_exercice_list()
        self.refresh_current_page()

    def _new_exercice(self):
        current = core.get_current_exercice(self.conn)
        suggestion = str(int(current) + 1)
        new_ex = simpledialog.askstring("Nouvel exercice", "Année de l'exercice (AAAA) :",
                                         initialvalue=suggestion, parent=self)
        if not new_ex:
            return
        core.set_current_exercice(self.conn, new_ex.strip())
        self._refresh_exercice_list()
        self.refresh_current_page()

    def refresh_current_page(self):
        for page in self.pages.values():
            if hasattr(page, "refresh"):
                try:
                    page.refresh()
                except Exception:
                    pass

    def show(self, key):
        page = self.pages[key]
        page.tkraise()
        if hasattr(page, "refresh"):
            page.refresh()


class SaisieTab(ttk.Frame):
    def __init__(self, parent, conn):
        super().__init__(parent)
        self.conn = conn
        self.selected_id = None
        self.pending_piece = None
        self._build()
        self.refresh()

    def _default_date(self):
        """Aujourd'hui si son année correspond à l'exercice courant, sinon le
        1er janvier de l'exercice courant."""
        exercice = core.get_current_exercice(self.conn)
        today = date.today()
        if str(today.year) == exercice:
            return today.strftime("%d/%m/%Y")
        return f"01/01/{exercice}"

    def _open_dropdown(self, event=None):
        """Ouvre automatiquement la liste déroulante d'un Combobox au clic,
        pour permettre de faire défiler et choisir sans avoir à taper."""
        widget = event.widget if event else None
        if widget is not None:
            widget.event_generate("<Down>")

    def _build(self):
        form = ttk.LabelFrame(self, text="Écriture (partie double : compte débiteur ET compte créditeur obligatoires)")
        form.pack(fill="x", padx=8, pady=8)

        labels = ["Date (JJ/MM/AAAA)", "N° Pièce", "Journal",
                  "Compte débiteur", "Compte créditeur", "Montant",
                  "Tiers", "Libellé", "Fournisseur",
                  "Code analytique (ex: AN-FAB)", "Code budgétaire", "Code bailleur", "Quantité", "Client"]
        self.vars = {k: tk.StringVar() for k in labels}
        self.vars["Date (JJ/MM/AAAA)"].set(self._default_date())

        for i, lbl in enumerate(labels):
            r, c = divmod(i, 3)
            ttk.Label(form, text=lbl).grid(row=r * 2, column=c, sticky="w", padx=4, pady=(4, 0))
            if lbl == "Compte débiteur":
                widget = ttk.Combobox(form, textvariable=self.vars[lbl], width=22)
                widget.grid(row=r * 2 + 1, column=c, sticky="we", padx=4, pady=(0, 4))
                widget.bind("<KeyRelease>", lambda e: self._on_compte_keyrelease("Compte débiteur"))
                widget.bind("<<ComboboxSelected>>", lambda e: (
                    self._show_account_labels(), self._validate_compte_field("Compte débiteur")))
                widget.bind("<FocusOut>", lambda e: self._validate_compte_field("Compte débiteur"))
                widget.bind("<Return>", lambda e: self._validate_compte_field("Compte débiteur"))
                widget.bind("<Tab>", lambda e: self._validate_compte_field("Compte débiteur"))
                widget.bind("<Button-1>", self._open_dropdown)
                self.compte_debit_combo = widget
            elif lbl == "Compte créditeur":
                widget = ttk.Combobox(form, textvariable=self.vars[lbl], width=22)
                widget.grid(row=r * 2 + 1, column=c, sticky="we", padx=4, pady=(0, 4))
                widget.bind("<KeyRelease>", lambda e: self._on_compte_keyrelease("Compte créditeur"))
                widget.bind("<<ComboboxSelected>>", lambda e: (
                    self._show_account_labels(), self._validate_compte_field("Compte créditeur")))
                widget.bind("<FocusOut>", lambda e: self._validate_compte_field("Compte créditeur"))
                widget.bind("<Return>", lambda e: self._validate_compte_field("Compte créditeur"))
                widget.bind("<Tab>", lambda e: self._validate_compte_field("Compte créditeur"))
                widget.bind("<Button-1>", self._open_dropdown)
                self.compte_credit_combo = widget
            elif lbl == "Journal":
                widget = ttk.Combobox(form, textvariable=self.vars[lbl], width=22,
                                       values=["AC", "VE", "OD", "BQ", "CA"])
                widget.grid(row=r * 2 + 1, column=c, sticky="we", padx=4, pady=(0, 4))
                widget.bind("<Button-1>", self._open_dropdown)
            elif lbl == "Fournisseur":
                widget = ttk.Combobox(form, textvariable=self.vars[lbl], width=22)
                widget.grid(row=r * 2 + 1, column=c, sticky="we", padx=4, pady=(0, 4))
                widget.bind("<KeyRelease>", self._on_fournisseur_keyrelease)
                widget.bind("<FocusOut>", lambda e: self._validate_fournisseur_field())
                widget.bind("<Button-1>", self._open_dropdown)
                self.fournisseur_combo = widget
                self._refresh_fournisseur_values()
            elif lbl == "Client":
                widget = ttk.Combobox(form, textvariable=self.vars[lbl], width=22)
                widget.grid(row=r * 2 + 1, column=c, sticky="we", padx=4, pady=(0, 4))
                widget.bind("<KeyRelease>", self._on_client_keyrelease)
                widget.bind("<FocusOut>", lambda e: self._validate_client_field())
                widget.bind("<Button-1>", self._open_dropdown)
                self.client_combo = widget
                self._refresh_client_values()
            elif lbl == "Code analytique (ex: AN-FAB)":
                widget = ttk.Combobox(form, textvariable=self.vars[lbl], width=22)
                widget.grid(row=r * 2 + 1, column=c, sticky="we", padx=4, pady=(0, 4))
                widget.bind("<FocusOut>", lambda e: self._validate_plan_field(
                    "Code analytique (ex: AN-FAB)", "analytique"))
                widget.bind("<Button-1>", self._open_dropdown)
                self.analytique_combo = widget
                self._refresh_plan_values("analytique")
            elif lbl == "Code budgétaire":
                widget = ttk.Combobox(form, textvariable=self.vars[lbl], width=22)
                widget.grid(row=r * 2 + 1, column=c, sticky="we", padx=4, pady=(0, 4))
                widget.bind("<FocusOut>", lambda e: self._validate_plan_field(
                    "Code budgétaire", "budgetaire"))
                widget.bind("<Button-1>", self._open_dropdown)
                self.budgetaire_combo = widget
                self._refresh_plan_values("budgetaire")
            elif lbl == "Code bailleur":
                widget = ttk.Combobox(form, textvariable=self.vars[lbl], width=22)
                widget.grid(row=r * 2 + 1, column=c, sticky="we", padx=4, pady=(0, 4))
                widget.bind("<FocusOut>", lambda e: self._validate_plan_field(
                    "Code bailleur", "bailleur"))
                widget.bind("<Button-1>", self._open_dropdown)
                self.bailleur_combo = widget
                self._refresh_plan_values("bailleur")
            else:
                widget = ttk.Entry(form, textvariable=self.vars[lbl], width=24)
                widget.grid(row=r * 2 + 1, column=c, sticky="we", padx=4, pady=(0, 4))

        self.account_label_var = tk.StringVar()
        ttk.Label(form, textvariable=self.account_label_var, foreground="#1F4E78").grid(
            row=10, column=0, columnspan=3, sticky="w", padx=4)

        self.balance_var = tk.StringVar()
        self.balance_label = ttk.Label(form, textvariable=self.balance_var, foreground="#B00020",
                                        font=("Segoe UI", 9, "bold"), wraplength=1000)
        self.balance_label.grid(row=10, column=1, columnspan=2, sticky="w", padx=4)

        btns = ttk.Frame(form)
        btns.grid(row=11, column=0, columnspan=3, sticky="w", pady=6, padx=4)
        ttk.Button(btns, text="Ajouter (écriture équilibrée)", command=self.add_entry).pack(side="left", padx=2)
        ttk.Button(btns, text="Enregistrer modification", command=self.update_entry).pack(side="left", padx=2)
        ttk.Button(btns, text="Supprimer", command=self.delete_entry).pack(side="left", padx=2)
        ttk.Button(btns, text="Effacer le formulaire", command=self.clear_form).pack(side="left", padx=2)

        import_bar = ttk.Frame(self)
        import_bar.pack(fill="x", padx=8, pady=(0, 4))
        ttk.Button(import_bar, text="Importer des écritures (.xlsx)", command=self.import_xlsx).pack(side="left", padx=2)
        ttk.Button(import_bar, text="Télécharger un modèle (.xlsx)", command=self.download_template).pack(side="left", padx=2)
        ttk.Label(import_bar, text=(
            "Pour les volumes importants : préparez un fichier avec les colonnes Date, N° Pièce, "
            "Journal, N° Compte, Tiers, Libellé, Débit, Crédit, Quantité, Code analytique, Code "
            "budgétaire, Code bailleur (l'ordre n'a pas d'importance), puis importez-le d'un coup. "
            "(L'import accepte un compte par ligne comme avant ; c'est le formulaire ci-dessus qui "
            "impose désormais la paire débit/crédit.)"
        ), foreground="#595959", wraplength=850).pack(side="left", padx=10)

        cols = ("id", "date", "piece", "journal", "compte", "libelle_compte",
                "tiers", "libelle", "debit", "credit", "quantite", "analytique", "budget", "bailleur",
                "fournisseur", "client")
        self.tree = ttk.Treeview(self, columns=cols, show="headings", height=15)
        headers = ["ID", "Date", "Pièce", "Journal", "Compte", "Libellé du compte",
                   "Tiers", "Libellé écriture", "Débit", "Crédit", "Qté", "Analytique", "Budget", "Bailleur",
                   "Fournisseur", "Client"]
        widths = [40, 90, 80, 60, 70, 160, 85, 140, 70, 70, 50, 75, 75, 75, 95, 95]
        for c, h, w in zip(cols, headers, widths):
            self.tree.heading(c, text=h)
            self.tree.column(c, width=w, anchor="w")
        self.tree.pack(fill="both", expand=True, padx=8, pady=(0, 8))
        self.tree.bind("<<TreeviewSelect>>", self._on_select)

        totals = ttk.Frame(self)
        totals.pack(fill="x", padx=8, pady=(0, 8))
        self.totals_var = tk.StringVar()
        ttk.Label(totals, textvariable=self.totals_var, font=("Segoe UI", 10, "bold")).pack(side="left")

        self._refresh_compte_values()

    def _refresh_compte_values(self):
        """Peuple les listes déroulantes Compte débiteur/créditeur avec un
        premier lot de comptes, pour qu'un simple clic affiche déjà une
        liste à faire défiler (sans avoir à taper au clavier)."""
        accounts = core.search_accounts(self.conn, "", limit=300)
        values = [f"{a['code']} — {a['label']}" for a in accounts]
        self.compte_debit_combo["values"] = values
        self.compte_credit_combo["values"] = values

    def _extract_code(self, raw):
        raw = (raw or "").strip()
        return raw.split(" — ", 1)[0].strip() if " — " in raw else raw

    def _on_compte_keyrelease(self, field, event=None):
        combo = self.compte_debit_combo if field == "Compte débiteur" else self.compte_credit_combo
        query = self._extract_code(self.vars[field].get())
        if query:
            matches = core.search_accounts(self.conn, query, limit=30)
            combo["values"] = [f"{m['code']} — {m['label']}" for m in matches]
        self._show_account_labels()

    def _validate_compte_field(self, field):
        """Force un compte valide : propose de créer le compte ou de choisir dans la liste.
        Pour TOUT compte commençant par la racine 40 (Fournisseurs) ou 41 (Clients) —
        qu'il s'agisse de la racine elle-même (40, 41) ou d'un compte de détail
        (401000, 411000, 412000...) — impose de choisir le tiers auxiliaire concerné."""
        code = self._extract_code(self.vars[field].get())
        if not code:
            return
        if code in (core.RACINE_FOURNISSEURS, core.RACINE_CLIENTS):
            # Racine seule (40 ou 41) : pas un compte de détail postable, on
            # bascule sur le compte usuel avant de forcer le choix du tiers.
            kind = "fournisseur" if code == core.RACINE_FOURNISSEURS else "client"
            default_compte = "401000" if kind == "fournisseur" else "411000"
            if not core.account_exists(self.conn, default_compte):
                default_compte = code
            self.vars[field].set(default_compte)
            code = default_compte
        elif not core.account_exists(self.conn, code):
            if messagebox.askyesno(
                "Compte introuvable",
                f"Le compte « {code} » n'existe pas dans le Plan comptable.\n\n"
                f"Voulez-vous le créer maintenant ? (Non pour effacer et choisir un compte existant)"
            ):
                label = simpledialog.askstring("Nouveau compte", f"Libellé du compte « {code} » :", parent=self)
                if not label:
                    self.vars[field].set("")
                    return
                core.add_account(self.conn, code, label)
            else:
                self.vars[field].set("")
                return

        racine = core.account_racine(code)
        if racine == core.RACINE_FOURNISSEURS:
            self._force_tiers_selection(field, "fournisseur", code)
        elif racine == core.RACINE_CLIENTS:
            self._force_tiers_selection(field, "client", code)
        self._show_account_labels()

    def _force_tiers_selection(self, field, kind, code):
        """kind = 'fournisseur' ou 'client'. Impose de choisir le tiers auxiliaire
        pour tout compte de la racine 40/41 (pas seulement la racine elle-même)."""
        tiers_var_key = "Fournisseur" if kind == "fournisseur" else "Client"
        tiers_var = self.vars[tiers_var_key]
        if self._extract_code(tiers_var.get()):
            return  # déjà renseigné, rien à faire
        messagebox.showwarning(
            "Sélection du tiers obligatoire",
            f"Le compte « {code} » relève de la racine "
            f"{core.RACINE_FOURNISSEURS if kind == 'fournisseur' else core.RACINE_CLIENTS} "
            f"({'Fournisseurs' if kind == 'fournisseur' else 'Clients'}).\n\n"
            f"Choisissez le {kind} concerné dans le champ « {tiers_var_key} » ci-dessous "
            f"(il doit déjà exister dans le plan auxiliaire, ex. CL0001 — sinon créez-le d'abord "
            f"dans l'onglet {'Fournisseurs' if kind == 'fournisseur' else 'Clients'}). "
            f"C'est obligatoire pour valider l'écriture."
        )
        combo = self.fournisseur_combo if kind == "fournisseur" else self.client_combo
        combo.focus_set()

    def _show_account_labels(self, event=None):
        d = self._extract_code(self.vars["Compte débiteur"].get())
        c = self._extract_code(self.vars["Compte créditeur"].get())
        parts = []
        if d:
            parts.append(f"Débit {d} : {core.get_account_label(self.conn, d)}")
        if c:
            parts.append(f"Crédit {c} : {core.get_account_label(self.conn, c)}")
        self.account_label_var.set("   |   ".join(parts))

    def _refresh_fournisseur_values(self):
        items = core.list_fournisseurs(self.conn)
        self.fournisseur_combo["values"] = [f"{f['code']} — {f['raison_sociale']}" for f in items]

    def _on_fournisseur_keyrelease(self, event=None):
        query = self._extract_code(self.vars["Fournisseur"].get())
        if query:
            items = core.list_fournisseurs(self.conn, query)
            self.fournisseur_combo["values"] = [f"{f['code']} — {f['raison_sociale']}" for f in items]

    def _validate_fournisseur_field(self):
        code = self._extract_code(self.vars["Fournisseur"].get())
        if not code or core.fournisseur_exists(self.conn, code):
            return
        if messagebox.askyesno(
            "Fournisseur introuvable",
            f"Le fournisseur « {code} » n'existe pas.\n\n"
            f"Voulez-vous le créer maintenant ? (Non pour effacer et choisir dans la liste existante)"
        ):
            raison = simpledialog.askstring("Nouveau fournisseur", f"Raison sociale pour « {code} » :", parent=self)
            if not raison:
                self.vars["Fournisseur"].set("")
                return
            core.add_fournisseur(self.conn, code, raison)
            self._refresh_fournisseur_values()
        else:
            self.vars["Fournisseur"].set("")

    def _refresh_client_values(self):
        items = core.list_clients(self.conn)
        self.client_combo["values"] = [f"{c['code']} — {c['raison_sociale']}" for c in items]

    def _on_client_keyrelease(self, event=None):
        query = self._extract_code(self.vars["Client"].get())
        if query:
            items = core.list_clients(self.conn, query)
            self.client_combo["values"] = [f"{c['code']} — {c['raison_sociale']}" for c in items]

    def _validate_client_field(self):
        code = self._extract_code(self.vars["Client"].get())
        if not code or core.client_exists(self.conn, code):
            return
        if messagebox.askyesno(
            "Client introuvable",
            f"Le client « {code} » n'existe pas.\n\n"
            f"Voulez-vous le créer maintenant ? (Non pour effacer et choisir dans la liste existante)"
        ):
            raison = simpledialog.askstring("Nouveau client", f"Raison sociale pour « {code} » :", parent=self)
            if not raison:
                self.vars["Client"].set("")
                return
            core.add_client(self.conn, code, raison)
            self._refresh_client_values()
        else:
            self.vars["Client"].set("")

    def _refresh_plan_values(self, plan):
        if plan == "analytique":
            items = core.list_analytic_codes(self.conn)
            self.analytique_combo["values"] = [f"{i['code']} — {i['label']}" for i in items]
        elif plan == "budgetaire":
            items = core.list_budget_codes(self.conn)
            self.budgetaire_combo["values"] = [f"{i['code']} — {i['label']}" for i in items]
        elif plan == "bailleur":
            items = core.list_donor_codes(self.conn)
            self.bailleur_combo["values"] = [f"{i['code']} — {i['label']}" for i in items]

    def _validate_plan_field(self, var_key, plan):
        raw = self.vars[var_key].get().strip()
        code = raw.split(" — ", 1)[0].strip() if " — " in raw else raw
        if not code:
            return
        exists_fn = {"analytique": core.analytic_code_exists,
                     "budgetaire": core.budget_code_exists,
                     "bailleur": core.donor_code_exists}[plan]
        if exists_fn(self.conn, code):
            return
        plan_name = {"analytique": "Plan analytique", "budgetaire": "Plan budgétaire",
                     "bailleur": "Plan bailleurs de fonds"}[plan]
        if messagebox.askyesno(
            "Code introuvable",
            f"Le code « {code} » n'existe pas dans le {plan_name}.\n\n"
            f"Voulez-vous le créer maintenant ? (Non pour effacer et choisir dans la liste existante)"
        ):
            label = simpledialog.askstring("Nouveau code", f"Libellé pour « {code} » :", parent=self)
            if not label:
                self.vars[var_key].set("")
                return
            if plan == "analytique":
                core.add_analytic_code(self.conn, code, label)
            elif plan == "budgetaire":
                core.add_budget_code(self.conn, code, label)
            elif plan == "bailleur":
                core.add_donor_code(self.conn, code, label)
            self.vars[var_key].set(code)
            self._refresh_plan_values(plan)
        else:
            self.vars[var_key].set("")

    def _get_form(self):
        try:
            montant = float(self.vars["Montant"].get() or 0)
            quantite = float(self.vars["Quantité"].get() or 0)
        except ValueError:
            messagebox.showerror("Erreur", "Montant et Quantité doivent être des nombres.")
            return None
        return dict(
            date_str=core.to_iso_date(self.vars["Date (JJ/MM/AAAA)"].get().strip()),
            piece=self.vars["N° Pièce"].get().strip(),
            journal=self.vars["Journal"].get().strip(),
            compte_debit=self._extract_code(self.vars["Compte débiteur"].get()),
            compte_credit=self._extract_code(self.vars["Compte créditeur"].get()),
            montant=montant,
            tiers=self.vars["Tiers"].get().strip(),
            libelle=self.vars["Libellé"].get().strip(),
            analytic_code=self._extract_code(self.vars["Code analytique (ex: AN-FAB)"].get()),
            budget_code=self._extract_code(self.vars["Code budgétaire"].get()),
            donor_code=self._extract_code(self.vars["Code bailleur"].get()),
            fournisseur_code=self._extract_code(self.vars["Fournisseur"].get()),
            client_code=self._extract_code(self.vars["Client"].get()),
            quantite=quantite,
        )

    def add_entry(self):
        data = self._get_form()
        if not data:
            return
        missing = []
        if not data["date_str"]:
            missing.append("Date")
        if not data["piece"]:
            missing.append("N° Pièce")
        if not data["compte_debit"]:
            missing.append("Compte débiteur")
        if not data["compte_credit"]:
            missing.append("Compte créditeur")
        if not data["montant"] or data["montant"] <= 0:
            missing.append("Montant (> 0)")
        if missing:
            messagebox.showwarning(
                "Champs manquants",
                "Le principe de la partie double impose de renseigner ensemble le compte "
                "débiteur ET le compte créditeur pour un même montant.\n\n"
                "Champs manquants : " + ", ".join(missing)
            )
            return
        if not core.account_exists(self.conn, data["compte_debit"]):
            messagebox.showerror("Compte invalide", f"Le compte débiteur « {data['compte_debit']} » "
                                                      f"n'existe pas dans le Plan comptable. Créez-le d'abord "
                                                      f"(quittez le champ pour être invité à le créer).")
            return
        if not core.account_exists(self.conn, data["compte_credit"]):
            messagebox.showerror("Compte invalide", f"Le compte créditeur « {data['compte_credit']} » "
                                                      f"n'existe pas dans le Plan comptable. Créez-le d'abord "
                                                      f"(quittez le champ pour être invité à le créer).")
            return
        for cote, code in (("débiteur", data["compte_debit"]), ("créditeur", data["compte_credit"])):
            if core.account_racine(code) == core.RACINE_FOURNISSEURS and not data["fournisseur_code"]:
                messagebox.showwarning(
                    "Fournisseur obligatoire",
                    f"Le compte {cote} « {code} » relève de la racine 40 (Fournisseurs) : "
                    f"le champ « Fournisseur » est obligatoire pour cette écriture."
                )
                self.fournisseur_combo.focus_set()
                return
            if core.account_racine(code) == core.RACINE_CLIENTS and not data["client_code"]:
                messagebox.showwarning(
                    "Client obligatoire",
                    f"Le compte {cote} « {code} » relève de la racine 41 (Clients) : "
                    f"le champ « Client » est obligatoire pour cette écriture."
                )
                self.client_combo.focus_set()
                return
        try:
            core.add_balanced_entry(
                self.conn, data["date_str"], data["piece"], data["journal"],
                data["compte_debit"], data["compte_credit"], data["montant"],
                data["tiers"], data["libelle"],
                analytic_code=data["analytic_code"], budget_code=data["budget_code"],
                donor_code=data["donor_code"], quantite=data["quantite"],
                fournisseur_code=data["fournisseur_code"], client_code=data["client_code"],
            )
        except ValueError as exc:
            messagebox.showerror("Erreur", str(exc))
            return
        self.refresh()
        self.balance_var.set("")
        piece = self.vars["N° Pièce"].get().strip()
        for k in ("Compte débiteur", "Compte créditeur", "Montant", "Tiers", "Libellé", "Fournisseur", "Client",
                  "Code analytique (ex: AN-FAB)", "Code budgétaire", "Code bailleur", "Quantité"):
            self.vars[k].set("")
        self.vars["N° Pièce"].set(piece)  # facilite l'ajout d'autres paires sur la même pièce
        self.account_label_var.set("")
        self.selected_id = None
        self.compte_debit_combo.focus_set()

    def update_entry(self):
        if self.selected_id is None:
            messagebox.showinfo("Info", "Sélectionnez d'abord une ligne dans le tableau.")
            return
        debit_code = self._extract_code(self.vars["Compte débiteur"].get())
        credit_code = self._extract_code(self.vars["Compte créditeur"].get())
        if debit_code and credit_code:
            messagebox.showwarning(
                "Une seule ligne à la fois",
                "Pour modifier une écriture existante, ne renseignez que le compte du côté "
                "concerné (Débit OU Crédit), pas les deux — chaque ligne du tableau est une "
                "moitié d'une écriture en partie double."
            )
            return
        try:
            montant = float(self.vars["Montant"].get() or 0)
            quantite = float(self.vars["Quantité"].get() or 0)
        except ValueError:
            messagebox.showerror("Erreur", "Montant et Quantité doivent être des nombres.")
            return
        if debit_code:
            if not core.account_exists(self.conn, debit_code):
                messagebox.showerror("Compte invalide", f"Le compte « {debit_code} » n'existe pas.")
                return
            fields = dict(compte=debit_code, debit=montant, credit=0)
        elif credit_code:
            if not core.account_exists(self.conn, credit_code):
                messagebox.showerror("Compte invalide", f"Le compte « {credit_code} » n'existe pas.")
                return
            fields = dict(compte=credit_code, debit=0, credit=montant)
        else:
            messagebox.showwarning("Champ manquant", "Renseignez le compte (débiteur ou créditeur) de cette ligne.")
            return
        fields.update(
            date=core.to_iso_date(self.vars["Date (JJ/MM/AAAA)"].get().strip()),
            piece=self.vars["N° Pièce"].get().strip(),
            journal=self.vars["Journal"].get().strip(),
            tiers=self.vars["Tiers"].get().strip(),
            libelle=self.vars["Libellé"].get().strip(),
            analytic_code=self._extract_code(self.vars["Code analytique (ex: AN-FAB)"].get()),
            budget_code=self._extract_code(self.vars["Code budgétaire"].get()),
            donor_code=self._extract_code(self.vars["Code bailleur"].get()),
            fournisseur_code=self._extract_code(self.vars["Fournisseur"].get()),
            client_code=self._extract_code(self.vars["Client"].get()),
            quantite=quantite,
        )
        try:
            core.update_entry(self.conn, self.selected_id, **fields)
        except ValueError as exc:
            messagebox.showerror("Erreur", str(exc))
            return
        self.clear_form()
        self.refresh()

    def delete_entry(self):
        if self.selected_id is None:
            messagebox.showinfo("Info", "Sélectionnez d'abord une ligne dans le tableau.")
            return
        if messagebox.askyesno("Confirmer", "Supprimer cette écriture ?"):
            try:
                core.delete_entry(self.conn, self.selected_id)
            except ValueError as exc:
                messagebox.showerror("Erreur", str(exc))
                return
            self.clear_form()
            self.refresh()

    def clear_form(self):
        self.selected_id = None
        self.pending_piece = None
        self.balance_var.set("")
        for k, v in self.vars.items():
            v.set("" if k != "Date (JJ/MM/AAAA)" else self._default_date())
        self.account_label_var.set("")

    def download_template(self):
        path = filedialog.asksaveasfilename(
            defaultextension=".xlsx",
            filetypes=[("Classeur Excel", "*.xlsx")],
            initialfile="Modele_import_ecritures.xlsx",
            title="Enregistrer le modèle d'import",
        )
        if not path:
            return
        try:
            core.export_import_template(path)
        except Exception as exc:
            messagebox.showerror("Erreur", f"Échec de la création du modèle : {exc}")
            return
        messagebox.showinfo("Modèle créé", f"Modèle enregistré :\n{path}")

    def import_xlsx(self):
        path = filedialog.askopenfilename(
            filetypes=[("Classeur Excel", "*.xlsx")],
            title="Importer des écritures",
        )
        if not path:
            return
        try:
            imported, warnings = core.import_entries_from_xlsx(self.conn, path)
        except Exception as exc:
            messagebox.showerror("Erreur", f"Échec de l'import : {exc}")
            return
        self.refresh()
        if warnings:
            preview = "\n".join(warnings[:25])
            more = f"\n... et {len(warnings) - 25} autre(s)." if len(warnings) > 25 else ""
            messagebox.showwarning(
                "Import terminé avec avertissements",
                f"{imported} écriture(s) importée(s).\n\nAvertissements :\n{preview}{more}",
            )
        else:
            messagebox.showinfo("Import terminé", f"{imported} écriture(s) importée(s) avec succès.")

    def _on_select(self, event=None):
        sel = self.tree.selection()
        if not sel:
            return
        values = self.tree.item(sel[0], "values")
        self.selected_id = int(values[0])
        self.vars["Date (JJ/MM/AAAA)"].set(values[1])
        self.vars["N° Pièce"].set(values[2])
        self.vars["Journal"].set(values[3])
        compte = values[4]
        debit_val = values[8]
        credit_val = values[9]
        self.vars["Compte débiteur"].set("")
        self.vars["Compte créditeur"].set("")
        if debit_val:
            self.vars["Compte débiteur"].set(compte)
            self.vars["Montant"].set(debit_val)
        else:
            self.vars["Compte créditeur"].set(compte)
            self.vars["Montant"].set(credit_val)
        self.vars["Tiers"].set(values[6])
        self.vars["Libellé"].set(values[7])
        self.vars["Quantité"].set(values[10])
        self.vars["Code analytique (ex: AN-FAB)"].set(values[11])
        self.vars["Code budgétaire"].set(values[12])
        self.vars["Code bailleur"].set(values[13])
        self.vars["Fournisseur"].set(values[14])
        self.vars["Client"].set(values[15])
        self._show_account_labels()

    def refresh(self):
        self._refresh_compte_values()
        for row in self.tree.get_children():
            self.tree.delete(row)
        entries = core.list_entries(self.conn, exercice=core.get_current_exercice(self.conn))
        total_d = total_c = 0.0
        for e in entries:
            label = core.get_account_label(self.conn, e["compte"])
            self.tree.insert("", "end", values=(
                e["id"], core.to_display_date(e["date"]), e["piece"] or "", e["journal"] or "", e["compte"], label,
                e["tiers"] or "", e["libelle"] or "",
                f"{e['debit']:.2f}" if e["debit"] else "",
                f"{e['credit']:.2f}" if e["credit"] else "",
                f"{e['quantite']:g}" if e["quantite"] else "",
                e["analytic_code"] or "",
                e["budget_code"] or "",
                e["donor_code"] or "",
                e["fournisseur_code"] or "",
                e["client_code"] or "",
            ))
            total_d += e["debit"]
            total_c += e["credit"]
        equilibre = "Équilibré ✓" if abs(total_d - total_c) < 0.01 else "NON ÉQUILIBRÉ ✗"
        self.totals_var.set(f"TOTAUX — Débit : {total_d:,.2f}   Crédit : {total_c:,.2f}   {equilibre}")


class BalanceTab(ttk.Frame):
    def __init__(self, parent, conn):
        super().__init__(parent)
        self.conn = conn
        cols = ("compte", "libelle", "ouverture", "cumul_debit", "cumul_credit", "solde_debit", "solde_credit")
        self.tree = ttk.Treeview(self, columns=cols, show="headings")
        headers = ["N° Compte", "Libellé du compte", "Solde Ouverture", "Cumul Débit", "Cumul Crédit",
                   "Solde Débit", "Solde Crédit"]
        widths = [90, 260, 110, 110, 110, 110, 110]
        for c, h, w in zip(cols, headers, widths):
            self.tree.heading(c, text=h)
            self.tree.column(c, width=w, anchor="w")
        self.tree.tag_configure("classe_total", background="#DCE6F1", font=("Segoe UI", 9, "bold"))
        self.tree.tag_configure("grand_total", background="#1F4E78", foreground="white", font=("Segoe UI", 10, "bold"))
        self.tree.pack(fill="both", expand=True, padx=8, pady=8)
        ttk.Button(self, text="Actualiser", command=self.refresh).pack(pady=(0, 8))
        self.refresh()

    def refresh(self):
        for row in self.tree.get_children():
            self.tree.delete(row)
        data = core.compute_balance_detaillee(self.conn)
        for c in data["classes"]:
            for l in c["lignes"]:
                self.tree.insert("", "end", values=(
                    l["code"], l["label"], f"{l['solde_ouverture']:,.2f}",
                    f"{l['cumul_debit']:,.2f}", f"{l['cumul_credit']:,.2f}",
                    f"{l['solde_debit']:,.2f}" if l["solde_debit"] else "",
                    f"{l['solde_credit']:,.2f}" if l["solde_credit"] else "",
                ))
            st = c["sous_total"]
            self.tree.insert("", "end", tags=("classe_total",), values=(
                "", f"TOTAL CLASSE {c['classe']}", "",
                f"{st['cumul_debit']:,.2f}", f"{st['cumul_credit']:,.2f}",
                f"{st['solde_debit']:,.2f}", f"{st['solde_credit']:,.2f}",
            ))
        gt = data["grand_total"]
        self.tree.insert("", "end", tags=("grand_total",), values=(
            "", "TOTAL BALANCE", "",
            f"{gt['cumul_debit']:,.2f}", f"{gt['cumul_credit']:,.2f}",
            f"{gt['solde_debit']:,.2f}", f"{gt['solde_credit']:,.2f}",
        ))


class CompteResultatTab(ttk.Frame):
    """Compte de résultat selon les Soldes Intermédiaires de Gestion (SIG),
    présenté selon le modèle officiel, avec une couleur par section.
    Calculé à partir de compute_liasse_resultat() — la même fonction que la
    Liasse fiscale et la Situation financière — donc toujours cohérent avec
    la Balance, le Bilan, le TFT et la Situation financière."""

    SECTIONS = {
        "commerciale": "#D9EAD3",   # vert clair — activité commerciale
        "ca": "#CFE2F3",            # bleu clair — chiffre d'affaires
        "va": "#FFF2CC",            # jaune clair — valeur ajoutée
        "ebe": "#D9D2E9",           # violet clair — EBE / résultat exploitation
        "financier": "#FCE5CD",     # orange clair — résultat financier
        "hao": "#F4CCCC",           # rouge/rose clair — HAO / résultat net
        "total": "#1F4E78",
    }

    def __init__(self, parent, conn):
        super().__init__(parent)
        self.conn = conn
        cols = ("libelle", "montant")
        self.tree = ttk.Treeview(self, columns=cols, show="headings", height=30)
        self.tree.heading("libelle", text="Rubrique")
        self.tree.heading("montant", text="Montant")
        self.tree.column("libelle", width=480, anchor="w")
        self.tree.column("montant", width=160, anchor="e")
        for key, color in self.SECTIONS.items():
            fg = "white" if key == "total" else "black"
            tree_font = ("Segoe UI", 9, "bold") if key == "total" else ("Segoe UI", 9)
            self.tree.tag_configure(key, background=color, foreground=fg, font=tree_font)
            self.tree.tag_configure(key + "_header", background=color, foreground=fg, font=("Segoe UI", 9, "bold"))
        self.tree.pack(fill="both", expand=True, padx=8, pady=8)
        ttk.Label(self, text=(
            "Calculé à partir de la même fonction que la Liasse fiscale, la Situation financière et "
            "le TFT (compute_liasse_resultat) — toujours cohérent avec la Balance et le Bilan."
        ), foreground="#595959").pack(anchor="w", padx=8)
        ttk.Button(self, text="Actualiser", command=self.refresh).pack(pady=8)
        self.refresh()

    def _row(self, tag, label, val):
        self.tree.insert("", "end", tags=(tag,), values=(f"  {label}", f"{val:,.2f}"))

    def _header(self, tag, titre):
        self.tree.insert("", "end", tags=(tag + "_header",), values=(titre, ""))

    def refresh(self):
        for row in self.tree.get_children():
            self.tree.delete(row)
        cr = core.compute_liasse_resultat(self.conn)

        self._header("commerciale", "ACTIVITÉ COMMERCIALE")
        self._row("commerciale", "+ Vente de marchandises (A)", cr["TA"])
        self._row("commerciale", "- Coût d'achat des marchandises vendues", cr["RA"])
        self._row("commerciale", "- Variation de stocks de marchandises", cr["RA_STOCK"])
        self._row("commerciale", "MARGE COMMERCIALE", cr["XA"])

        self._header("ca", "CHIFFRE D'AFFAIRES")
        self._row("ca", "+ Vente de produits fabriqués (B)", cr["TB"])
        self._row("ca", "+ Travaux, services vendus (C)", cr["TC"])
        self._row("ca", "+ Produits accessoires (D)", cr["TD"])
        self._row("ca", "CHIFFRE D'AFFAIRES (A+B+C+D)", cr["XB"])

        self._header("va", "VALEUR AJOUTÉE")
        self._row("va", "+ Production stockée", cr["TE"])
        self._row("va", "+ Subvention d'exploitation", cr["TG"])
        self._row("va", "+ Autres produits", cr["TH"])
        self._row("va", "- Achats de matières premières (+ variation de stocks)", cr["RC"])
        self._row("va", "- Autres achats (+ variation de stocks)", cr["RE"])
        self._row("va", "- Transport", cr["RG"])
        self._row("va", "- Services extérieurs", cr["RH"])
        self._row("va", "- Impôts et taxes", cr["RI"])
        self._row("va", "- Autres charges", cr["RJ"])
        self._row("va", "VALEUR AJOUTÉE", cr["XC"])

        self._header("ebe", "EXCÉDENT BRUT D'EXPLOITATION ET RÉSULTAT D'EXPLOITATION")
        self._row("ebe", "- Charges de personnel", cr["RK"])
        self._row("ebe", "EXCÉDENT BRUT D'EXPLOITATION (EBE)", cr["XD"])
        self._row("ebe", "- Dotations aux amortissements et provisions", cr["RL"])
        self._row("ebe", "RÉSULTAT D'EXPLOITATION", cr["XE"])

        self._header("financier", "RÉSULTAT FINANCIER")
        self._row("financier", "+ Produits financiers", cr["TK"])
        self._row("financier", "- Frais financiers et charges assimilées", cr["RM"])
        self._row("financier", "RÉSULTAT FINANCIER", cr["XF"])
        self._row("financier", "RÉSULTAT DES ACTIVITÉS ORDINAIRES", cr["XG"])

        self._header("hao", "RÉSULTAT HORS ACTIVITÉS ORDINAIRES ET RÉSULTAT NET")
        self._row("hao", "RÉSULTAT HAO", cr["XH"])
        self._row("hao", "- Participation des salariés", cr["RQ"])
        self._row("hao", "- Impôts sur les bénéfices", cr["RS"])
        self.tree.insert("", "end", tags=("total",), values=("RÉSULTAT NET COMPTABLE", f"{cr['XI']:,.2f}"))


class BilanTab(ttk.Frame):
    """Bilan présenté en deux colonnes (Passif à gauche, Actif à droite),
    avec une couleur distincte par masse (Immobilisations, Stocks,
    Créances, Trésorerie, Capitaux propres, Dettes...), comme un bilan
    comptable classique. Calculé à partir de la même Balance générale que
    l'onglet Balance — toujours cohérent avec elle."""

    MASSES = {
        "immo": "#D9EAD3",      # vert clair — Immobilisations
        "stocks": "#FFF2CC",    # jaune clair — Stocks
        "creances": "#CFE2F3",  # bleu clair — Créances
        "treso": "#D9D2E9",     # violet clair — Trésorerie
        "capital": "#D9EAD3",   # vert clair — Capitaux propres
        "dettes_fin": "#FCE5CD",   # orange clair — Dettes financières
        "dettes_circ": "#F4CCCC",  # rouge/rose clair — Dettes circulantes
        "total": "#1F4E78",     # bandeau total
    }

    def __init__(self, parent, conn):
        super().__init__(parent)
        self.conn = conn

        ttk.Label(self, text="BILAN", font=("Segoe UI", 14, "bold")).pack(anchor="w", padx=8, pady=(8, 0))
        ttk.Label(self, text=(
            "Calculé à partir de la même Balance générale que l'onglet Balance (États et rapports) "
            "— les deux sont donc toujours cohérents."
        ), foreground="#595959").pack(anchor="w", padx=8, pady=(0, 8))

        columns_frame = ttk.Frame(self)
        columns_frame.pack(fill="both", expand=True, padx=8, pady=(0, 4))
        columns_frame.columnconfigure(0, weight=1)
        columns_frame.columnconfigure(1, weight=1)

        ttk.Label(columns_frame, text="ACTIF", font=("Segoe UI", 12, "bold")).grid(row=0, column=0, sticky="w")
        ttk.Label(columns_frame, text="PASSIF", font=("Segoe UI", 12, "bold")).grid(row=0, column=1, sticky="w")

        cols = ("libelle", "montant")
        self.tree_passif = ttk.Treeview(columns_frame, columns=cols, show="headings", height=22)
        self.tree_actif = ttk.Treeview(columns_frame, columns=cols, show="headings", height=22)
        for tree in (self.tree_passif, self.tree_actif):
            tree.heading("libelle", text="Libellé")
            tree.heading("montant", text="Montant")
            tree.column("libelle", width=280, anchor="w")
            tree.column("montant", width=140, anchor="e")
            for key, color in self.MASSES.items():
                fg = "white" if key == "total" else "black"
                font = ("Segoe UI", 9, "bold") if key == "total" else ("Segoe UI", 9)
                tree.tag_configure(key, background=color, foreground=fg, font=font)
                tree.tag_configure(key + "_header", background=color, foreground=fg, font=("Segoe UI", 9, "bold"))
        self.tree_actif.grid(row=1, column=0, sticky="nsew", padx=(0, 4))
        self.tree_passif.grid(row=1, column=1, sticky="nsew", padx=(4, 0))
        columns_frame.rowconfigure(1, weight=1)

        self.ecart_var = tk.StringVar()
        ttk.Label(self, textvariable=self.ecart_var, font=("Segoe UI", 10, "bold")).pack(anchor="w", padx=8, pady=8)
        ttk.Button(self, text="Actualiser", command=self.refresh).pack(pady=(0, 8))
        self.refresh()

    @staticmethod
    def _add_masse(tree, titre, key, lignes, total_label, total_val):
        """lignes: liste de (libellé, montant) ; masse ignorée si tout est à 0."""
        if not any(v for _, v in lignes) and not total_val:
            return
        tree.insert("", "end", tags=(key + "_header",), values=(titre, ""))
        for label, val in lignes:
            if val:
                tree.insert("", "end", tags=(key,), values=(f"   {label}", f"{val:,.2f}"))
        tree.insert("", "end", tags=(key,), values=(f"  {total_label}", f"{total_val:,.2f}"))
        tree.insert("", "end", values=("", ""))  # ligne vide de séparation

    def refresh(self):
        for tree in (self.tree_passif, self.tree_actif):
            for row in tree.get_children():
                tree.delete(row)

        liasse = core.compute_liasse_bilan(self.conn)
        b = liasse["totaux"]
        ad = liasse["actif_detail"]
        acd = liasse["actif_circulant_detail"]
        pdet = liasse["passif_detail"]
        stocks_detail = core.compute_stocks_detail(self.conn)
        treso_lignes, _ = core.compute_tresorerie_detail(self.conn)

        # ---- ACTIF (colonne de droite) ----
        self._add_masse(self.tree_actif, "IMMOBILISATIONS", "immo",
                         [(k, v["net"]) for k, v in ad.items()],
                         "Immobilisations nettes", b["actif"]["Immobilisations nettes"])
        self._add_masse(self.tree_actif, "STOCKS", "stocks",
                         [(f"{s['code']} {s['label']}", s["stock_final"]) for s in stocks_detail],
                         "Total stocks", b["actif"]["Stocks"])
        self._add_masse(self.tree_actif, "CRÉANCES", "creances",
                         [("Avances versées sur commandes", acd["BH"]), ("Clients", acd["BI"])],
                         "Total créances", b["actif"]["Créances et emplois assimilés"])
        self._add_masse(self.tree_actif, "TRÉSORERIE ACTIF", "treso",
                         [(f"{t['code']} {t['label']}", t["solde_cloture"]) for t in treso_lignes
                          if t["solde_cloture"] > 0],
                         "Total trésorerie actif", b["actif"]["Trésorerie actif"])
        self.tree_actif.insert("", "end", tags=("total",), values=("TOTAL ACTIF", f"{b['total_actif']:,.2f}"))

        # ---- PASSIF (colonne de gauche) ----
        capitaux_lignes = [(k, v) for k, v in pdet.items()
                            if k not in ("DA", "DB", "DC", "DJ", "DH_avances", "DK", "DM")]
        self._add_masse(self.tree_passif, "CAPITAUX PROPRES", "capital",
                         capitaux_lignes + [("Résultat net de l'exercice", b["passif"]["Résultat net de l'exercice"])],
                         "Total capitaux propres", b["passif"]["Capital et réserves"] + b["passif"]["Résultat net de l'exercice"])
        self._add_masse(self.tree_passif, "DETTES FINANCIÈRES", "dettes_fin",
                         [("Emprunts et dettes financières", pdet["DA"])],
                         "Total dettes financières", b["passif"]["Dettes financières"])
        self._add_masse(self.tree_passif, "DETTES CIRCULANTES", "dettes_circ",
                         [("Fournisseurs et comptes rattachés", pdet["DJ"]),
                          ("Avances reçues des fournisseurs", pdet["DH_avances"]),
                          ("Dettes fiscales et sociales", pdet["DK"]),
                          ("Autres dettes", pdet["DM"])],
                         "Total dettes circulantes", b["passif"]["Dettes circulantes"])
        self._add_masse(self.tree_passif, "TRÉSORERIE PASSIF", "treso",
                         [(f"{t['code']} {t['label']}", -t["solde_cloture"]) for t in treso_lignes
                          if t["solde_cloture"] < 0],
                         "Total trésorerie passif", b["passif"]["Trésorerie passif"])
        self.tree_passif.insert("", "end", tags=("total",), values=("TOTAL PASSIF", f"{b['total_passif']:,.2f}"))

        ecart = b["ecart"]
        couleur = "#B00020" if abs(ecart) >= 1 else "#1F7A1F"
        self.ecart_var.set(f"Écart Actif - Passif : {ecart:,.2f}"
                            + (" ✓ équilibré" if abs(ecart) < 1 else " ⚠ à corriger (soldes d'ouverture ?)"))


class GrandLivreTab(ttk.Frame):
    def __init__(self, parent, conn):
        super().__init__(parent)
        self.conn = conn

        bar = ttk.Frame(self)
        bar.pack(fill="x", padx=8, pady=8)
        ttk.Label(bar, text="N° Compte :").pack(side="left")
        self.compte_var = tk.StringVar()
        self.compte_combo = ttk.Combobox(bar, textvariable=self.compte_var, width=30)
        self.compte_combo.pack(side="left", padx=4)
        self.compte_combo.bind("<KeyRelease>", self._on_compte_keyrelease)
        self.compte_combo.bind("<<ComboboxSelected>>", lambda e: self.refresh())
        ttk.Label(bar, text="Tiers (optionnel) :").pack(side="left", padx=(12, 0))
        self.tiers_var = tk.StringVar()
        ttk.Entry(bar, textvariable=self.tiers_var, width=18).pack(side="left", padx=4)
        ttk.Button(bar, text="Afficher", command=self.refresh).pack(side="left", padx=12)
        self.label_var = tk.StringVar()
        ttk.Label(bar, textvariable=self.label_var, foreground="#1F4E78").pack(side="left", padx=8)

        cols = ("date", "piece", "journal", "tiers", "libelle", "debit", "credit", "solde")
        self.tree = ttk.Treeview(self, columns=cols, show="headings")
        headers = ["Date", "Pièce", "Journal", "Tiers", "Libellé", "Débit", "Crédit", "Solde cumulé"]
        widths = [90, 80, 60, 140, 260, 90, 90, 100]
        for c, h, w in zip(cols, headers, widths):
            self.tree.heading(c, text=h)
            self.tree.column(c, width=w, anchor="w")
        self.tree.pack(fill="both", expand=True, padx=8, pady=(0, 8))

    def _extract_compte_code(self):
        raw = self.compte_var.get().strip()
        if " — " in raw:
            return raw.split(" — ", 1)[0].strip()
        return raw

    def _on_compte_keyrelease(self, event=None):
        if event is not None and event.keysym in ("Up", "Down", "Return", "Tab"):
            return
        query = self._extract_compte_code()
        if query:
            matches = core.search_accounts(self.conn, query, limit=30)
            self.compte_combo["values"] = [f"{m['code']} — {m['label']}" for m in matches]

    def refresh(self):
        for row in self.tree.get_children():
            self.tree.delete(row)
        compte = self._extract_compte_code()
        if not compte:
            self.label_var.set("")
            return
        self.label_var.set(core.get_account_label(self.conn, compte))
        for r in core.compute_grand_livre(self.conn, compte, self.tiers_var.get().strip() or None):
            self.tree.insert("", "end", values=(
                core.to_display_date(r["date"]), r["piece"] or "", r["journal"] or "", r["tiers"] or "", r["libelle"] or "",
                f"{r['debit']:.2f}" if r["debit"] else "",
                f"{r['credit']:.2f}" if r["credit"] else "",
                f"{r['solde_cumule']:,.2f}",
            ))


class OpeningBalancesTab(ttk.Frame):
    """Soldes d'ouverture (report à nouveau) : un solde signé par compte, saisi
    une fois en début d'exercice. Débiteur = positif, créditeur = négatif."""

    def __init__(self, parent, conn):
        super().__init__(parent)
        self.conn = conn

        ttk.Label(self, text=(
            "Saisissez ici le solde de report à nouveau de chaque compte de bilan au 1er jour de "
            "l'exercice (= solde de clôture de l'exercice précédent). Convention : solde débiteur = "
            "positif, solde créditeur = négatif (ex. Capital social créditeur de 5 000 000 → -5000000). "
            "La « Balance de clôture » (onglet Balance) et le Bilan intègrent automatiquement ces soldes."
        ), foreground="#595959", wraplength=1000).pack(anchor="w", padx=8, pady=(8, 4))

        import_bar = ttk.Frame(self)
        import_bar.pack(fill="x", padx=8, pady=(0, 4))
        ttk.Button(import_bar, text="Importer la balance N-1 (.xlsx) — ÉCRASE la balance actuelle",
                   command=self.import_xlsx).pack(side="left", padx=2)
        ttk.Button(import_bar, text="Exporter la balance N-1 (.xlsx)", command=self.export_xlsx).pack(side="left", padx=2)
        ttk.Label(import_bar, text="(Colonnes attendues : N° Compte, Libellé, Solde — l'écrasement "
                                    "ne concerne que l'exercice comptable actuellement sélectionné.)",
                  foreground="#595959").pack(side="left", padx=10)

        form = ttk.Frame(self)
        form.pack(fill="x", padx=8, pady=4)
        ttk.Label(form, text="N° Compte :").pack(side="left")
        self.compte_var = tk.StringVar()
        self.compte_combo = ttk.Combobox(form, textvariable=self.compte_var, width=34)
        self.compte_combo.pack(side="left", padx=4)
        self.compte_combo.bind("<KeyRelease>", self._on_compte_keyrelease)
        ttk.Label(form, text="Solde d'ouverture :").pack(side="left", padx=(12, 0))
        self.solde_var = tk.StringVar()
        ttk.Entry(form, textvariable=self.solde_var, width=16).pack(side="left", padx=4)
        ttk.Button(form, text="Enregistrer", command=self.save).pack(side="left", padx=6)

        cols = ("code", "label", "solde")
        self.tree = ttk.Treeview(self, columns=cols, show="headings")
        headers = ["N° Compte", "Libellé", "Solde d'ouverture"]
        widths = [90, 400, 140]
        for c, h, w in zip(cols, headers, widths):
            self.tree.heading(c, text=h)
            self.tree.column(c, width=w, anchor="w")
        self.tree.pack(fill="both", expand=True, padx=8, pady=8)
        self.tree.bind("<<TreeviewSelect>>", self._on_select)

        bottom = ttk.Frame(self)
        bottom.pack(fill="x", padx=8, pady=(0, 8))
        self.total_var = tk.StringVar()
        ttk.Label(bottom, textvariable=self.total_var, font=("Segoe UI", 10, "bold")).pack(side="left")
        self.refresh()

    def _extract_compte_code(self):
        raw = self.compte_var.get().strip()
        if " — " in raw:
            return raw.split(" — ", 1)[0].strip()
        return raw

    def _on_compte_keyrelease(self, event=None):
        if event is not None and event.keysym in ("Up", "Down", "Return", "Tab"):
            return
        query = self._extract_compte_code()
        if query:
            matches = core.search_accounts(self.conn, query, limit=30)
            self.compte_combo["values"] = [f"{m['code']} — {m['label']}" for m in matches]

    def _on_select(self, event=None):
        sel = self.tree.selection()
        if not sel:
            return
        values = self.tree.item(sel[0], "values")
        self.compte_var.set(values[0])
        self.solde_var.set(values[2])

    def save(self):
        code = self._extract_compte_code()
        if not code:
            messagebox.showinfo("Info", "Choisissez d'abord un compte.")
            return
        try:
            value = float(self.solde_var.get() or 0)
        except ValueError:
            messagebox.showerror("Erreur", "Le solde d'ouverture doit être un nombre.")
            return
        core.set_opening_balance(self.conn, code, value)
        self.compte_var.set("")
        self.solde_var.set("")
        self.refresh()

    def refresh(self):
        for row in self.tree.get_children():
            self.tree.delete(row)
        total = 0.0
        for b in core.list_opening_balances(self.conn):
            self.tree.insert("", "end", values=(b["code"], b["label"], f"{b['solde']:,.2f}"))
            total += b["solde"]
        equilibre = "Équilibré ✓" if abs(total) < 0.01 else "NON ÉQUILIBRÉ ✗ (la somme des soldes d'ouverture doit être nulle)"
        self.total_var.set(f"Somme des soldes d'ouverture : {total:,.2f}   {equilibre}")

    def export_xlsx(self):
        path = filedialog.asksaveasfilename(
            defaultextension=".xlsx", filetypes=[("Classeur Excel", "*.xlsx")],
            initialfile="Balance_ouverture.xlsx", title="Exporter la balance d'ouverture",
        )
        if not path:
            return
        core.export_opening_balances_xlsx(self.conn, path)
        messagebox.showinfo("Export terminé", f"Balance d'ouverture exportée :\n{path}")

    def import_xlsx(self):
        path = filedialog.askopenfilename(filetypes=[("Classeur Excel", "*.xlsx")],
                                           title="Importer une balance d'ouverture (N-1)")
        if not path:
            return
        exercice = core.get_current_exercice(self.conn)
        if not messagebox.askyesno(
            "Confirmer l'écrasement",
            f"Importer ce fichier va ÉCRASER complètement les soldes d'ouverture de l'exercice "
            f"{exercice} actuellement sélectionné. Cette action est irréversible. Continuer ?"
        ):
            return
        try:
            n, warnings = core.import_opening_balances_xlsx(self.conn, path)
        except Exception as exc:
            messagebox.showerror("Erreur", f"Échec de l'import : {exc}")
            return
        self.refresh()
        msg = f"{n} solde(s) importé(s) pour l'exercice {exercice}. La balance précédente a été remplacée."
        if warnings:
            msg += "\n\nAvertissements :\n" + "\n".join(warnings[:20])
        messagebox.showinfo("Import terminé", msg)


class StocksTab(ttk.Frame):
    def __init__(self, parent, conn):
        super().__init__(parent)
        self.conn = conn
        inner = ttk.Notebook(self)
        inner.pack(fill="both", expand=True)
        self.synthese_tab = StocksSyntheseTab(inner, conn)
        self.mouvements_tab = StocksMouvementsTab(inner, conn)
        inner.add(self.synthese_tab, text="Synthèse par compte")
        inner.add(self.mouvements_tab, text="Mouvements comptables (classe 3)")

    def refresh(self):
        self.synthese_tab.refresh()
        self.mouvements_tab.refresh()


class StocksSyntheseTab(ttk.Frame):
    def __init__(self, parent, conn):
        super().__init__(parent)
        self.conn = conn
        ttk.Label(self, text=(
            "Détail RÉEL de chaque compte de stock utilisé (pas seulement les comptes centralisateurs "
            "310000/320000/331000/360000) : tout sous-compte 31x/32x/33x/36x ayant un mouvement ou un "
            "stock initial apparaît ici (ex. 321001 CLINKER). Cliquez une ligne, modifiez la valeur puis "
            "« Enregistrer ». La quantité de mouvement provient du champ « Quantité » saisi sur chaque "
            "écriture (onglet Saisie) — elle permet de calculer un coût unitaire moyen réel."
        ), foreground="#595959", wraplength=1050).pack(anchor="w", padx=8, pady=(8, 0))

        filt = ttk.Frame(self)
        filt.pack(fill="x", padx=8, pady=4)
        ttk.Label(filt, text="Catégorie :").pack(side="left")
        self.categorie_var = tk.StringVar(value="Toutes")
        ttk.Combobox(filt, textvariable=self.categorie_var, width=28, state="readonly", values=[
            "Toutes", "31 — Marchandises", "32 — Matières premières",
            "33 — Autres approvisionnements", "36 — Produits finis",
        ]).pack(side="left", padx=4)
        ttk.Button(filt, text="Filtrer", command=self.refresh).pack(side="left", padx=8)

        ttk.Label(filt, text="Marge de valorisation des produits finis par défaut (%) :").pack(side="left", padx=(24, 4))
        self.marge_defaut_var = tk.StringVar(value=str(core.get_setting(conn, "marge_production_defaut", 30.0)))
        ttk.Entry(filt, textvariable=self.marge_defaut_var, width=6).pack(side="left", padx=2)
        ttk.Button(filt, text="Enregistrer la marge", command=self.save_marge_defaut).pack(side="left", padx=4)

        edit_bar = ttk.Frame(self)
        edit_bar.pack(fill="x", padx=8, pady=4)
        ttk.Label(edit_bar, text="Stock initial (valeur) du compte sélectionné :").pack(side="left")
        self.initial_var = tk.StringVar()
        ttk.Entry(edit_bar, textvariable=self.initial_var, width=14).pack(side="left", padx=4)
        ttk.Button(edit_bar, text="Enregistrer la valeur", command=self.save_initial).pack(side="left", padx=4)
        ttk.Label(edit_bar, text="Quantité initiale :").pack(side="left", padx=(16, 0))
        self.qte_initial_var = tk.StringVar()
        ttk.Entry(edit_bar, textvariable=self.qte_initial_var, width=14).pack(side="left", padx=4)
        ttk.Button(edit_bar, text="Enregistrer la quantité", command=self.save_qte_initial).pack(side="left", padx=4)
        ttk.Label(edit_bar, text="(pour un nouveau compte : tapez son n° ci-dessus dans le champ, puis "
                                  "enregistrez — il apparaîtra dans la liste)", foreground="#595959").pack(side="left", padx=8)

        cols = ("code", "label", "initial", "entrees", "sorties", "final",
                "qte_initiale", "qte_entrees", "qte_sorties", "qte_finale", "cump")
        self.tree = ttk.Treeview(self, columns=cols, show="headings")
        headers = ["N° Compte", "Libellé", "Stock initial", "Entrées (Débit)", "Sorties (Crédit)", "Stock final",
                   "Qté initiale", "Qté entrées", "Qté sorties", "Qté finale", "Coût unit. moyen"]
        widths = [90, 190, 100, 100, 100, 100, 80, 80, 80, 80, 110]
        for c, h, w in zip(cols, headers, widths):
            self.tree.heading(c, text=h)
            self.tree.column(c, width=w, anchor="w")
        self.tree.pack(fill="both", expand=True, padx=8, pady=8)
        self.tree.bind("<<TreeviewSelect>>", self._on_select)
        self.selected_code = None
        self.refresh()

    def _on_select(self, event=None):
        sel = self.tree.selection()
        if not sel:
            return
        values = self.tree.item(sel[0], "values")
        self.selected_code = values[0]
        self.initial_var.set(values[2])
        self.qte_initial_var.set(values[6])

    def save_marge_defaut(self):
        try:
            value = float(self.marge_defaut_var.get() or 0)
        except ValueError:
            messagebox.showerror("Erreur", "La marge doit être un nombre.")
            return
        core.set_setting(self.conn, "marge_production_defaut", value)
        messagebox.showinfo("Enregistré", "Marge de valorisation par défaut enregistrée.")

    def save_initial(self):
        if not self.selected_code:
            messagebox.showinfo("Info", "Sélectionnez d'abord un compte de stock dans le tableau "
                                         "(ou saisissez son code dans le champ ci-dessus après l'avoir tapé).")
            return
        try:
            value = float(self.initial_var.get() or 0)
        except ValueError:
            messagebox.showerror("Erreur", "Le stock initial doit être un nombre.")
            return
        core.set_stock_initial(self.conn, self.selected_code, value)
        self.refresh()

    def save_qte_initial(self):
        if not self.selected_code:
            messagebox.showinfo("Info", "Sélectionnez d'abord un compte de stock dans le tableau.")
            return
        try:
            value = float(self.qte_initial_var.get() or 0)
        except ValueError:
            messagebox.showerror("Erreur", "La quantité initiale doit être un nombre.")
            return
        core.set_stock_qte_initiale(self.conn, self.selected_code, value)
        self.refresh()

    def refresh(self):
        for row in self.tree.get_children():
            self.tree.delete(row)
        cat = self.categorie_var.get()
        prefixes = None
        if cat != "Toutes":
            prefixes = [cat.split(" — ")[0].strip()]
        for s in core.compute_stocks_detail(self.conn, prefixes=prefixes):
            cump = f"{s['cout_unitaire_moyen']:,.2f}" if s["cout_unitaire_moyen"] is not None else "—"
            self.tree.insert("", "end", values=(
                s["code"], s["label"], f"{s['stock_initial']:,.2f}",
                f"{s['entrees']:,.2f}", f"{s['sorties']:,.2f}", f"{s['stock_final']:,.2f}",
                f"{s['qte_initiale']:g}", f"{s['qte_entrees']:g}", f"{s['qte_sorties']:g}",
                f"{s['qte_finale']:g}", cump,
            ))


class StocksMouvementsTab(ttk.Frame):
    """Détail de toutes les écritures comptables sur les comptes de stock
    (classe 3), avec leur origine : générées automatiquement par la
    Facturation (ventes) ou les Factures frs (achats), ou saisies
    manuellement dans l'onglet Saisie."""

    def __init__(self, parent, conn):
        super().__init__(parent)
        self.conn = conn
        ttk.Label(self, text=(
            "Tous les mouvements comptables des comptes de stock (310000, 320000, 331000, 360000) "
            "de l'exercice en cours, y compris ceux générés automatiquement par la validation d'une "
            "facture de vente (Commerce → Facturation) ou d'une facture d'achat (Engagements-projets "
            "→ Factures frs)."
        ), foreground="#595959", wraplength=1050).pack(anchor="w", padx=8, pady=(8, 4))

        filt = ttk.Frame(self)
        filt.pack(fill="x", padx=8, pady=4)
        ttk.Label(filt, text="Filtrer par origine :").pack(side="left")
        self.origine_var = tk.StringVar(value="Toutes")
        ttk.Combobox(filt, textvariable=self.origine_var, width=18, state="readonly",
                     values=["Toutes", "Facturation", "Facture frs", "Saisie directe (auto)", "Saisie manuelle"]).pack(side="left", padx=4)
        ttk.Button(filt, text="Filtrer", command=self.refresh).pack(side="left", padx=8)

        cols = ("date", "piece", "compte", "compte_label", "libelle", "debit", "credit", "quantite",
                "qte_cumulee", "valeur_cumulee", "origine")
        self.tree = ttk.Treeview(self, columns=cols, show="headings")
        headers = ["Date", "Pièce", "Compte", "Libellé du compte", "Libellé écriture",
                   "Débit (valeur)", "Crédit (valeur)", "Qté mvt", "Qté cumulée", "Valeur cumulée", "Origine"]
        widths = [90, 80, 80, 150, 190, 90, 90, 70, 90, 100, 110]
        for c, h, w in zip(cols, headers, widths):
            self.tree.heading(c, text=h)
            self.tree.column(c, width=w, anchor="w")
        self.tree.tag_configure("auto", foreground="#1F4E78")
        self.tree.pack(fill="both", expand=True, padx=8, pady=8)

        self.totals_var = tk.StringVar()
        ttk.Label(self, textvariable=self.totals_var, font=("Segoe UI", 10, "bold")).pack(anchor="w", padx=8, pady=(0, 8))
        self.refresh()

    def refresh(self):
        for row in self.tree.get_children():
            self.tree.delete(row)
        mouvements = core.compute_mouvements_stocks(self.conn)
        filtre = self.origine_var.get()
        total_d = total_c = 0.0
        for m in mouvements:
            if filtre != "Toutes" and m["origine"] != filtre:
                continue
            tags = ("auto",) if m["origine"] != "Saisie manuelle" else ()
            self.tree.insert("", "end", tags=tags, values=(
                core.to_display_date(m["date"]), m["piece"] or "", m["compte"], m["compte_label"],
                m["libelle"] or "", f"{m['debit']:,.2f}" if m["debit"] else "",
                f"{m['credit']:,.2f}" if m["credit"] else "", f"{m['quantite']:g}" if m["quantite"] else "",
                f"{m['qte_cumulee']:g}", f"{m['valeur_cumulee']:,.2f}",
                m["origine"],
            ))
            total_d += m["debit"]
            total_c += m["credit"]
        self.totals_var.set(f"TOTAL — Débit : {total_d:,.2f}   Crédit : {total_c:,.2f}")


class CoutsFabricationPeriodeTab(ttk.Frame):
    """Coûts de fabrication réels de la période (écritures taguées AN-FAB)."""

    def __init__(self, parent, conn):
        super().__init__(parent)
        self.conn = conn
        ttk.Label(self, text=(
            "Pour qu'une charge remonte ici, saisissez le code analytique « AN-FAB » "
            "sur la ligne correspondante dans l'onglet Saisie."
        ), foreground="#595959").pack(anchor="w", padx=8, pady=(8, 0))
        self.text = tk.Text(self, font=("Consolas", 11), wrap="none")
        self.text.pack(fill="both", expand=True, padx=8, pady=8)
        ttk.Button(self, text="Actualiser", command=self.refresh).pack(pady=(0, 8))
        self.refresh()

    def refresh(self):
        p = core.compute_production(self.conn)
        lines = ["PRODUCTION DE L'EXERCICE", "=" * 60,
                 f"  {'Ventes (produits finis, travaux, services)':<50} {p['ventes']:>12,.2f}",
                 f"  {'Production stockée (variation stock 360000)':<50} {p['production_stockee']:>12,.2f}",
                 f"  {'VALEUR DE LA PRODUCTION':<50} {p['valeur_production']:>12,.2f}",
                 "", "COÛTS DE FABRICATION (axe AN-FAB)", "=" * 60]
        for poste in p["postes_cout"]:
            lines.append(f"  {poste['label']:<50} {poste['montant']:>12,.2f}")
        lines += [f"  {'COÛT DE PRODUCTION':<50} {p['cout_production']:>12,.2f}", "",
                  f"MARGE SUR COÛT DE PRODUCTION{'':<34}{p['marge']:>12,.2f}"]
        self.text.delete("1.0", "end")
        self.text.insert("1.0", "\n".join(lines))


class RecetteFabricationTab(ttk.Frame):
    """Nomenclature de fabrication (BOM) : combine matières premières (coût
    réel des stocks), main-d'œuvre et énergie pour calculer le coût de
    production d'un produit fini, puis le prix de vente suggéré (+ marge)."""

    def __init__(self, parent, conn):
        super().__init__(parent)
        self.conn = conn
        self.selected_produit = None

        top = ttk.Frame(self)
        top.pack(fill="x", padx=12, pady=8)
        ttk.Label(top, text="Produit fini :").pack(side="left")
        self.produit_var = tk.StringVar()
        self.produit_combo = ttk.Combobox(top, textvariable=self.produit_var, width=30, state="readonly")
        self.produit_combo.pack(side="left", padx=4)
        self.produit_combo.bind("<<ComboboxSelected>>", self._on_produit_selected)
        ttk.Button(top, text="Nouveau produit fini", command=self._new_produit).pack(side="left", padx=8)
        ttk.Button(top, text="Supprimer ce produit", command=self._delete_produit).pack(side="left", padx=2)

        params = ttk.Frame(self)
        params.pack(fill="x", padx=12, pady=(0, 8))
        ttk.Label(params, text="Quantité produite par recette :").pack(side="left")
        self.qte_produite_var = tk.StringVar()
        ttk.Entry(params, textvariable=self.qte_produite_var, width=8).pack(side="left", padx=4)
        ttk.Label(params, text="Marge (%) :").pack(side="left", padx=(16, 0))
        self.marge_var = tk.StringVar()
        ttk.Entry(params, textvariable=self.marge_var, width=8).pack(side="left", padx=4)
        ttk.Label(params, text="Compte stock produit fini (classe 36) :").pack(side="left", padx=(16, 0))
        self.compte_stock_pf_var = tk.StringVar()
        self.compte_stock_pf_combo = ttk.Combobox(params, textvariable=self.compte_stock_pf_var, width=26)
        self.compte_stock_pf_combo.pack(side="left", padx=4)
        self.compte_stock_pf_combo.bind("<KeyRelease>", self._on_compte_pf_keyrelease)
        self._refresh_compte_pf_values()
        ttk.Button(params, text="Enregistrer ces paramètres", command=self._save_params).pack(side="left", padx=8)

        form = ttk.LabelFrame(self, text="Ajouter un composant à la recette")
        form.pack(fill="x", padx=12, pady=4)
        ttk.Label(form, text="Type :").grid(row=0, column=0, sticky="w", padx=4, pady=4)
        self.type_var = tk.StringVar(value="matiere")
        type_combo = ttk.Combobox(form, textvariable=self.type_var, width=22, state="readonly",
                                   values=list(core.LIGNE_TYPES.values()))
        type_combo.set(core.LIGNE_TYPES["matiere"])
        type_combo.grid(row=0, column=1, padx=4)
        type_combo.bind("<<ComboboxSelected>>", self._on_type_changed)
        self.type_combo = type_combo

        ttk.Label(form, text="Libellé :").grid(row=0, column=2, sticky="w", padx=(12, 4))
        self.libelle_var = tk.StringVar()
        ttk.Entry(form, textvariable=self.libelle_var, width=22).grid(row=0, column=3, padx=4)

        self.compte_label = ttk.Label(form, text="Compte de stock :")
        self.compte_label.grid(row=0, column=4, sticky="w", padx=(12, 4))
        self.compte_var = tk.StringVar()
        self.compte_combo = ttk.Combobox(form, textvariable=self.compte_var, width=26, state="readonly")
        self.compte_combo.grid(row=0, column=5, padx=4)
        self._refresh_stock_accounts()

        ttk.Label(form, text="Quantité :").grid(row=1, column=0, sticky="w", padx=4, pady=4)
        self.ligne_qte_var = tk.StringVar()
        ttk.Entry(form, textvariable=self.ligne_qte_var, width=10).grid(row=1, column=1, padx=4, sticky="w")

        self.cout_label = ttk.Label(form, text="Coût unitaire (si pas de compte de stock) :")
        self.cout_label.grid(row=1, column=2, sticky="w", padx=(12, 4))
        self.ligne_cout_var = tk.StringVar()
        self.cout_entry = ttk.Entry(form, textvariable=self.ligne_cout_var, width=12)
        self.cout_entry.grid(row=1, column=3, padx=4, sticky="w")

        ttk.Button(form, text="Ajouter le composant", command=self.add_ligne).grid(row=1, column=5, padx=4, pady=4)

        cols = ("id", "type", "libelle", "compte", "quantite", "cout_unitaire", "source", "montant")
        self.tree = ttk.Treeview(self, columns=cols, show="headings", height=8)
        headers = ["ID", "Type", "Libellé", "Compte", "Quantité", "Coût unitaire", "Origine du coût", "Montant"]
        widths = [40, 90, 180, 90, 80, 110, 170, 110]
        for c, h, w in zip(cols, headers, widths):
            self.tree.heading(c, text=h)
            self.tree.column(c, width=w, anchor="w")
        self.tree.pack(fill="both", expand=True, padx=12, pady=8)
        self.tree.bind("<<TreeviewSelect>>", self._on_ligne_select)
        ttk.Button(self, text="Supprimer le composant sélectionné", command=self.delete_ligne).pack(
            anchor="w", padx=12)

        self.result_text = tk.Text(self, font=("Consolas", 11), height=8, wrap="none")
        self.result_text.pack(fill="x", padx=12, pady=8)

        ttk.Button(self, text="Valider la fabrication (comptabiliser)", command=self.valider_fabrication).pack(
            anchor="w", padx=12, pady=(0, 8))

        self._on_type_changed()
        self.refresh_produits()

    def _refresh_stock_accounts(self):
        stocks = core.compute_stocks_detail(self.conn, prefixes=["31", "32", "33", "36"])
        self.compte_combo["values"] = [f"{s['code']} — {s['label']}" for s in stocks]

    def _refresh_compte_pf_values(self):
        stocks = core.compute_stocks_detail(self.conn, prefixes=["36"])
        values = [f"{s['code']} — {s['label']}" for s in stocks]
        if "360000 — PRODUITS FINIS" not in values and core.account_exists(self.conn, "360000"):
            values.insert(0, f"360000 — {core.get_account_label(self.conn, '360000')}")
        self.compte_stock_pf_combo["values"] = values

    def _on_compte_pf_keyrelease(self, event=None):
        query = self._extract_code(self.compte_stock_pf_var.get())
        if query:
            items = [a for a in core.search_accounts(self.conn, query, limit=50)
                     if a["code"].startswith("36")]
            self.compte_stock_pf_combo["values"] = [f"{a['code']} — {a['label']}" for a in items]

    def _on_type_changed(self, event=None):
        is_matiere = self.type_combo.get() == core.LIGNE_TYPES["matiere"]
        state_compte = "readonly" if is_matiere else "disabled"
        self.compte_combo.configure(state=state_compte)
        if not is_matiere:
            self.compte_var.set("")

    @staticmethod
    def _extract_code(raw):
        raw = (raw or "").strip()
        return raw.split(" — ", 1)[0].strip() if " — " in raw else raw

    def _type_key(self):
        label = self.type_combo.get()
        for key, val in core.LIGNE_TYPES.items():
            if val == label:
                return key
        return "autre"

    def refresh_produits(self):
        produits = core.list_produits_finis(self.conn)
        self.produit_combo["values"] = [f"{p['code']} — {p['nom']}" for p in produits]
        if produits and not self.selected_produit:
            self.selected_produit = produits[0]["code"]
            self.produit_var.set(f"{produits[0]['code']} — {produits[0]['nom']}")
        self.refresh()

    def _on_produit_selected(self, event=None):
        self.selected_produit = self._extract_code(self.produit_var.get())
        self.refresh()

    def _new_produit(self):
        code = simpledialog.askstring("Nouveau produit fini", "Code du produit :", parent=self)
        if not code:
            return
        nom = simpledialog.askstring("Nouveau produit fini", "Nom du produit :", parent=self)
        if not nom:
            return
        marge_defaut = core.get_setting(self.conn, "marge_production_defaut", 30.0)
        core.add_produit_fini(self.conn, code.strip(), nom.strip(), marge_pourcentage=marge_defaut)
        self.selected_produit = code.strip()
        self.refresh_produits()

    def _delete_produit(self):
        if not self.selected_produit:
            return
        if messagebox.askyesno("Confirmer", f"Supprimer le produit « {self.selected_produit} » et sa recette ?"):
            core.delete_produit_fini(self.conn, self.selected_produit)
            self.selected_produit = None
            self.refresh_produits()

    def _save_params(self):
        if not self.selected_produit:
            return
        produit = core.get_produit_fini(self.conn, self.selected_produit)
        try:
            qte = float(self.qte_produite_var.get() or 1)
            marge = float(self.marge_var.get() or 0)
        except ValueError:
            messagebox.showerror("Erreur", "Quantité produite et marge doivent être des nombres.")
            return
        compte_stock = self._extract_code(self.compte_stock_pf_var.get()) or "360000"
        if not core.account_exists(self.conn, compte_stock):
            messagebox.showerror("Compte invalide", f"Le compte « {compte_stock} » n'existe pas.")
            return
        core.add_produit_fini(self.conn, self.selected_produit, produit["nom"], produit["description"] or "",
                               qte, marge, compte_stock)
        self.refresh()

    def _on_ligne_select(self, event=None):
        pass

    def add_ligne(self):
        if not self.selected_produit:
            messagebox.showinfo("Info", "Créez ou sélectionnez d'abord un produit fini.")
            return
        libelle = self.libelle_var.get().strip()
        if not libelle:
            messagebox.showwarning("Champ manquant", "Le libellé du composant est obligatoire.")
            return
        try:
            qte = float(self.ligne_qte_var.get() or 0)
        except ValueError:
            messagebox.showerror("Erreur", "La quantité doit être un nombre.")
            return
        type_key = self._type_key()
        compte = self._extract_code(self.compte_var.get()) if type_key == "matiere" else None
        cout_unitaire = None
        if self.ligne_cout_var.get().strip():
            try:
                cout_unitaire = float(self.ligne_cout_var.get())
            except ValueError:
                messagebox.showerror("Erreur", "Le coût unitaire doit être un nombre.")
                return
        if type_key == "matiere" and not compte and cout_unitaire is None:
            messagebox.showwarning("Champ manquant",
                                    "Choisissez un compte de stock ou saisissez un coût unitaire manuel.")
            return
        core.add_recette_ligne(self.conn, self.selected_produit, type_key, libelle, qte, compte, cout_unitaire)
        self.libelle_var.set("")
        self.ligne_qte_var.set("")
        self.ligne_cout_var.set("")
        self.refresh()

    def delete_ligne(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showinfo("Info", "Sélectionnez d'abord un composant dans le tableau.")
            return
        ligne_id = int(self.tree.item(sel[0], "values")[0])
        core.delete_recette_ligne(self.conn, ligne_id)
        self.refresh()

    def refresh(self):
        self._refresh_stock_accounts()
        for row in self.tree.get_children():
            self.tree.delete(row)
        self.result_text.delete("1.0", "end")
        if not self.selected_produit or not core.get_produit_fini(self.conn, self.selected_produit):
            return
        produit = core.get_produit_fini(self.conn, self.selected_produit)
        self.qte_produite_var.set(str(produit["quantite_produite"]))
        self.marge_var.set(str(produit["marge_pourcentage"]))
        self._refresh_compte_pf_values()
        label_pf = core.get_account_label(self.conn, produit["compte_stock"])
        self.compte_stock_pf_var.set(f"{produit['compte_stock']} — {label_pf}")

        resultat = core.compute_cout_production(self.conn, self.selected_produit)
        for l in resultat["lignes"]:
            self.tree.insert("", "end", values=(
                l["id"], core.LIGNE_TYPES.get(l["type_ligne"], l["type_ligne"]), l["libelle"],
                l["compte"] or "", f"{l['quantite']:g}", f"{l['cout_unitaire_utilise']:,.2f}",
                l["source_cout"], f"{l['montant']:,.2f}",
            ))
        lines = [
            f"COÛT DE PRODUCTION — {produit['nom']} ({self.selected_produit})", "=" * 70,
            f"  {'Coût de production total (recette)':<45} {resultat['cout_production_total']:>15,.2f}",
            f"  {'Quantité produite':<45} {resultat['quantite_produite']:>15,g}",
            f"  {'COÛT DE PRODUCTION UNITAIRE':<45} {resultat['cout_unitaire_produit']:>15,.2f}", "",
            f"  {'Marge appliquée':<45} {resultat['marge_pourcentage']:>14,g} %",
            f"  {'PRIX DE VENTE UNITAIRE SUGGÉRÉ':<45} {resultat['prix_vente_unitaire']:>15,.2f}",
            f"  {'dont marge unitaire':<45} {resultat['marge_unitaire']:>15,.2f}",
        ]
        self.result_text.insert("1.0", "\n".join(lines))

    def valider_fabrication(self):
        if not self.selected_produit:
            messagebox.showinfo("Info", "Sélectionnez d'abord un produit fini.")
            return
        self._save_params()
        resultat = core.compute_cout_production(self.conn, self.selected_produit)
        if not resultat["lignes"]:
            messagebox.showwarning("Recette vide", "Ajoutez au moins un composant à la recette avant de valider.")
            return
        if not messagebox.askyesno(
            "Confirmer la validation de la fabrication",
            f"Valider la fabrication de « {resultat['produit']['nom']} » ?\n\n"
            f"Coût de production : {resultat['cout_production_total']:,.2f}\n"
            f"Quantité produite : {resultat['quantite_produite']:g}\n"
            f"Valeur du produit fini mis en stock (coût + marge {resultat['marge_pourcentage']:g}%) : "
            f"{resultat['prix_vente_total']:,.2f}\n\n"
            f"Cette action va DIMINUER les matières premières consommées (quantité et valeur) et "
            f"AUGMENTER le stock de produit fini, avec envoi des écritures dans le menu SAISIE. "
            f"Cette action est définitive."
        ):
            return
        try:
            _, warnings = core.valider_fabrication(self.conn, self.selected_produit)
        except ValueError as exc:
            messagebox.showerror("Erreur", str(exc))
            return
        msg = "Fabrication validée. Les matières premières ont été décrémentées et le produit fini mis en stock."
        if warnings:
            msg += "\n\nAvertissements :\n" + "\n".join(warnings)
        messagebox.showinfo("Validation terminée", msg)
        self.refresh()


class ProductionTab(ttk.Frame):
    """Regroupe la nomenclature de fabrication (coût de production, prix de
    vente) et le suivi des coûts réels de fabrication de la période."""

    def __init__(self, parent, conn):
        super().__init__(parent)
        self.conn = conn
        inner = ttk.Notebook(self)
        inner.pack(fill="both", expand=True)
        self.recette_tab = RecetteFabricationTab(inner, conn)
        self.periode_tab = CoutsFabricationPeriodeTab(inner, conn)
        inner.add(self.recette_tab, text="Recettes / Coût de production")
        inner.add(self.periode_tab, text="Coûts de fabrication (période)")

    def refresh(self):
        self.recette_tab.refresh_produits()
        self.periode_tab.refresh()


class TftIndirectTab(ttk.Frame):
    """TFT selon la méthode indirecte SYSCOHADA (avec CAFG), présenté selon le
    modèle officiel avec une couleur par section. Calculé à partir de
    compute_balance() et compute_liasse_resultat() — donc toujours cohérent
    avec la Balance et le Bilan. La ligne CONTRÔLE compare la trésorerie
    calculée à la trésorerie réelle de la Balance : un écart signale un
    mouvement mal classé."""

    SECTIONS = {
        "ouverture": "#D9D2E9",   # violet clair — trésorerie
        "cafg": "#D9EAD3",        # vert clair — CAFG / exploitation
        "invest": "#FCE5CD",      # orange clair — investissement
        "finance": "#CFE2F3",     # bleu clair — financement
        "controle": "#F4CCCC",    # rouge/rose clair — contrôle
        "total": "#1F4E78",       # bandeau total
    }

    def __init__(self, parent, conn):
        super().__init__(parent)
        self.conn = conn
        cols = ("libelle", "montant")
        self.tree = ttk.Treeview(self, columns=cols, show="headings", height=28)
        self.tree.heading("libelle", text="Rubrique")
        self.tree.heading("montant", text="Montant")
        self.tree.column("libelle", width=480, anchor="w")
        self.tree.column("montant", width=160, anchor="e")
        for key, color in self.SECTIONS.items():
            fg = "white" if key == "total" else "black"
            tree_font = ("Segoe UI", 9, "bold") if key == "total" else ("Segoe UI", 9)
            self.tree.tag_configure(key, background=color, foreground=fg, font=tree_font)
            self.tree.tag_configure(key + "_header", background=color, foreground=fg, font=("Segoe UI", 9, "bold"))
        self.tree.pack(fill="both", expand=True, padx=8, pady=8)
        self.ecart_var = tk.StringVar()
        ttk.Label(self, textvariable=self.ecart_var, font=("Segoe UI", 10, "bold")).pack(anchor="w", padx=8)
        ttk.Button(self, text="Actualiser", command=self.refresh).pack(pady=8)
        self.refresh()

    def _row(self, tag, label, val):
        self.tree.insert("", "end", tags=(tag,), values=(f"  {label}", f"{val:,.2f}"))

    def _header(self, tag, titre):
        self.tree.insert("", "end", tags=(tag + "_header",), values=(titre, ""))

    def refresh(self):
        for row in self.tree.get_children():
            self.tree.delete(row)
        t = core.compute_tft_indirect(self.conn)

        self._header("ouverture", "A — TRÉSORERIE NETTE AU 1ER JANVIER")
        self._row("ouverture", "Trésorerie d'ouverture", t["treso_ouverture"])

        self._header("cafg", "DÉTERMINATION DE LA CAFG")
        self._row("cafg", "Excédent Brut d'Exploitation (EBE)", t["ebe"])
        self._row("cafg", "+ Revenus financiers", t["revenus_financiers"])
        self._row("cafg", "- Frais financiers", t["frais_financiers"])
        self._row("cafg", "CAPACITÉ D'AUTOFINANCEMENT GLOBALE (CAFG)", t["cafg"])
        self._row("cafg", "- Variation des stocks", t["variation_stocks"])
        self._row("cafg", "- Variation des créances", t["variation_creances"])
        self._row("cafg", "+ Variation du passif circulant (dettes)", t["variation_dettes_circulantes"])
        self._row("cafg", "FLUX DES ACTIVITÉS OPÉRATIONNELLES (A)", t["flux_operationnel"])

        self._header("invest", "FLUX DES ACTIVITÉS D'INVESTISSEMENT")
        self._row("invest", "- Acquisitions d'immobilisations incorporelles", t["acquisitions_incorp"])
        self._row("invest", "- Acquisitions d'immobilisations corporelles", t["acquisitions_corp"])
        self._row("invest", "- Acquisitions d'immobilisations financières", t["acquisitions_fin"])
        self._row("invest", "+ Cessions d'immobilisations incorporelles", t["cessions_incorp"])
        self._row("invest", "+ Cessions d'immobilisations corporelles", t["cessions_corp"])
        self._row("invest", "+ Cessions d'immobilisations financières", t["cessions_fin"])
        self._row("invest", "FLUX DES ACTIVITÉS D'INVESTISSEMENT (B)", t["flux_investissement"])

        self._header("finance", "FLUX DES ACTIVITÉS DE FINANCEMENT")
        self._row("finance", "+ Augmentation de capital par apports nouveaux", t["augmentation_capital"])
        self._row("finance", "+ Subventions d'investissement reçues", t["subventions_recues"])
        self._row("finance", "- Prélèvements sur le capital", t["prelevements_capital"])
        self._row("finance", "- Dividendes versés", t["dividendes_verses"])
        self._row("finance", "Flux de trésorerie provenant des capitaux propres", t["flux_capitaux_propres"])
        self._row("finance", "+ Emprunts nouveaux", t["emprunts_nouveaux"])
        self._row("finance", "- Remboursements des emprunts", t["remboursements_emprunts"])
        self._row("finance", "Flux de trésorerie provenant des capitaux étrangers", t["flux_capitaux_etrangers"])
        self._row("finance", "FLUX DES ACTIVITÉS DE FINANCEMENT (C)", t["flux_financement"])

        self._header("controle", "VARIATION ET CONTRÔLE")
        self._row("controle", "VARIATION DE LA TRÉSORERIE NETTE (A+B+C)", t["variation_treso_nette"])
        self._row("controle", "Trésorerie nette calculée au 31/12/N", t["treso_cloture_calculee"])
        self._row("controle", "Contrôle — Trésorerie réelle (Balance, classe 5)", t["treso_cloture_reelle"])
        self._row("controle", "ÉCART", t["ecart"])
        self.tree.insert("", "end", tags=("total",), values=(
            "TRÉSORERIE NETTE DE CLÔTURE", f"{t['treso_cloture_reelle']:,.2f}"))

        if abs(t["ecart"]) < 1:
            self.ecart_var.set("✓ La trésorerie calculée correspond exactement à la trésorerie de la Balance.")
        else:
            self.ecart_var.set(
                f"⚠ Écart de {t['ecart']:,.2f} — un mouvement de trésorerie n'est peut-être pas "
                f"correctement classé (comptes d'immobilisations, capital ou emprunts)."
            )


class TftDirectTab(ttk.Frame):
    """Ancienne méthode (directe, par code flux EXP/INV/FIN) — conservée pour
    référence ; la méthode indirecte (CAFG) est désormais la vue principale."""

    def __init__(self, parent, conn):
        super().__init__(parent)
        self.conn = conn

        bar = ttk.Frame(self)
        bar.pack(fill="x", padx=8, pady=8)
        ttk.Label(bar, text="Trésorerie d'ouverture (auto., ou forcez une valeur) :").pack(side="left")
        self.ouverture_var = tk.StringVar()
        ttk.Entry(bar, textvariable=self.ouverture_var, width=14).pack(side="left", padx=4)
        ttk.Button(bar, text="Forcer cette valeur", command=self.save_and_refresh).pack(side="left", padx=4)
        ttk.Button(bar, text="Revenir à l'automatique", command=self.reset_auto).pack(side="left", padx=4)
        ttk.Label(bar, text=(
            "Par défaut = somme des soldes d'ouverture des comptes de trésorerie (onglet « Soldes "
            "d'ouverture »). Les mouvements se classent par nature via le code flux EXP/INV/FIN saisi "
            "dans l'onglet Saisie."
        ), foreground="#595959", wraplength=550).pack(side="left", padx=12)

        self.text = tk.Text(self, font=("Consolas", 11), wrap="none")
        self.text.pack(fill="both", expand=True, padx=8, pady=8)
        self.refresh()

    def save_and_refresh(self):
        try:
            value = float(self.ouverture_var.get() or 0)
        except ValueError:
            messagebox.showerror("Erreur", "La trésorerie d'ouverture doit être un nombre.")
            return
        core.set_setting(self.conn, "treso_ouverture_override", value)
        core.set_setting(self.conn, "treso_ouverture_use_override", 1)
        self.refresh()

    def reset_auto(self):
        core.set_setting(self.conn, "treso_ouverture_use_override", 0)
        self.refresh()

    def refresh(self):
        use_override = core.get_setting(self.conn, "treso_ouverture_use_override", 0.0)
        ouverture_override = core.get_setting(self.conn, "treso_ouverture_override", 0.0) if use_override else None
        t = core.compute_tft(self.conn, treso_ouverture=ouverture_override)
        self.ouverture_var.set(str(t["ouverture"]))
        label_ouv = "Trésorerie d'ouverture"
        label_inv = "Flux liés aux activités d'investissement (INV)"
        label_clot = "TRÉSORERIE DE CLÔTURE"
        lines = [
            "TABLEAU DES FLUX DE TRÉSORERIE (méthode directe)", "=" * 60,
            f"  {label_ouv:<50} {t['ouverture']:>12,.2f}", "",
            f"  {'Flux liés aux activités opérationnelles (EXP)':<50} {t['exploitation']:>12,.2f}",
            f"  {label_inv:<50} {t['investissement']:>12,.2f}",
            f"  {'Flux liés aux activités de financement (FIN)':<50} {t['financement']:>12,.2f}",
            f"  {'Flux non classés (à coder)':<50} {t['non_classes']:>12,.2f}",
            f"  {'VARIATION NETTE DE TRÉSORERIE':<50} {t['variation']:>12,.2f}", "",
            f"{label_clot:<52} {t['cloture']:>12,.2f}",
        ]
        self.text.delete("1.0", "end")
        self.text.insert("1.0", "\n".join(lines))


class SituationFinanciereTab(ttk.Frame):
    """Situation financière (FR - BFR - TN), présentée selon le modèle
    officiel, avec une couleur par section. Entièrement recalculée à partir
    de compute_bilan(), compute_liasse_resultat() et compute_tft_indirect()
    — donc toujours cohérente avec la Balance, le Bilan et le TFT."""

    SECTIONS = {
        "cafg": "#D9EAD3",       # vert clair — CAFG / rentabilité
        "fr": "#CFE2F3",         # bleu clair — Fonds de roulement
        "bfr": "#FFF2CC",        # jaune clair — Besoin en fonds de roulement
        "tn": "#D9D2E9",         # violet clair — Trésorerie nette
        "flux": "#FCE5CD",       # orange clair — Flux de la période
        "endettement": "#F4CCCC",  # rouge/rose clair — Endettement
        "total": "#1F4E78",
    }

    def __init__(self, parent, conn):
        super().__init__(parent)
        self.conn = conn
        cols = ("libelle", "montant")
        self.tree = ttk.Treeview(self, columns=cols, show="headings", height=30)
        self.tree.heading("libelle", text="Rubrique")
        self.tree.heading("montant", text="Montant")
        self.tree.column("libelle", width=480, anchor="w")
        self.tree.column("montant", width=160, anchor="e")
        for key, color in self.SECTIONS.items():
            fg = "white" if key == "total" else "black"
            tree_font = ("Segoe UI", 9, "bold") if key == "total" else ("Segoe UI", 9)
            self.tree.tag_configure(key, background=color, foreground=fg, font=tree_font)
            self.tree.tag_configure(key + "_header", background=color, foreground=fg, font=("Segoe UI", 9, "bold"))
        self.tree.pack(fill="both", expand=True, padx=8, pady=8)
        self.ecart_var = tk.StringVar()
        ttk.Label(self, textvariable=self.ecart_var, font=("Segoe UI", 10, "bold")).pack(anchor="w", padx=8)
        ttk.Button(self, text="Actualiser", command=self.refresh).pack(pady=8)
        self.refresh()

    def _row(self, tag, label, val, pct=False):
        suffix = " %" if pct else ""
        self.tree.insert("", "end", tags=(tag,), values=(f"  {label}", f"{val:,.2f}{suffix}"))

    def _header(self, tag, titre):
        self.tree.insert("", "end", tags=(tag + "_header",), values=(titre, ""))

    def refresh(self):
        for row in self.tree.get_children():
            self.tree.delete(row)
        s = core.compute_situation_financiere(self.conn)

        self._header("cafg", "RÉSULTAT ET CAPACITÉ D'AUTOFINANCEMENT")
        self._row("cafg", "Résultat net comptable", s["resultat_net_comptable"])
        self._row("cafg", "Excédent Brut d'Exploitation (EBE)", s["ebe"])
        self._row("cafg", "+ Revenus financiers", s["revenus_financiers"])
        self._row("cafg", "- Frais financiers", s["frais_financiers"])
        self._row("cafg", "CAPACITÉ D'AUTOFINANCEMENT GLOBALE (CAFG)", s["cafg"])
        self._row("cafg", "- Dividendes versés durant l'exercice", s["dividendes_verses"])
        self._row("cafg", "AUTOFINANCEMENT", s["autofinancement"])
        self._row("cafg", "Rentabilité économique (Résultat exploit. / Cap. propres)", s["rentabilite_economique"], pct=True)
        self._row("cafg", "Rentabilité financière (Résultat net / Cap. propres)", s["rentabilite_financiere"], pct=True)

        self._header("fr", "FONDS DE ROULEMENT (FR)")
        self._row("fr", "Capitaux propres et ressources assimilées", s["capitaux_propres_ressources"])
        self._row("fr", "+ Dettes financières", s["dettes_financieres"])
        self._row("fr", "= RESSOURCES STABLES", s["ressources_stables"])
        self._row("fr", "- Actifs immobilisés", s["actifs_immobilises"])
        self._row("fr", "= FONDS DE ROULEMENT (FR)", s["fonds_de_roulement"])

        self._header("bfr", "BESOIN EN FONDS DE ROULEMENT (BFR)")
        self._row("bfr", "+ Actif circulant d'exploitation", s["actif_circulant_exploitation"])
        self._row("bfr", "- Passif circulant d'exploitation", s["passif_circulant_exploitation"])
        self._row("bfr", "= BESOIN DE FINANCEMENT D'EXPLOITATION", s["besoin_financement_exploitation"])
        self._row("bfr", "+ Actif circulant HAO", s["actif_circulant_hao"])
        self._row("bfr", "- Passif circulant HAO", s["passif_circulant_hao"])
        self._row("bfr", "= BESOIN DE FINANCEMENT HAO", s["besoin_financement_hao"])
        self._row("bfr", "= BESOIN DE FINANCEMENT GLOBAL (BFR)", s["besoin_financement_global"])

        self._header("tn", "TRÉSORERIE NETTE (TN = FR - BFR)")
        self._row("tn", "TRÉSORERIE NETTE (FR - BFR)", s["tresorerie_nette"])
        self._row("tn", "Contrôle — Trésorerie réelle (Balance, classe 5)", s["controle_treso_reelle"])
        self._row("tn", "ÉCART", s["controle_ecart"])

        self._header("flux", "FLUX DE TRÉSORERIE DE LA PÉRIODE (cf. onglet TFT)")
        self._row("flux", "+ Flux des activités opérationnelles", s["flux_operationnel"])
        self._row("flux", "- Flux des activités d'investissement", s["flux_investissement"])
        self._row("flux", "+ Flux des activités de financement", s["flux_financement"])
        self._row("flux", "VARIATION DE LA TRÉSORERIE NETTE DE LA PÉRIODE", s["variation_treso_nette"])

        self._header("endettement", "ENDETTEMENT FINANCIER")
        self._row("endettement", "Endettement financier brut (dettes fin. + trésorerie passif)", s["endettement_financier_brut"])
        self._row("endettement", "- Trésorerie actif", s["treso_actif"])
        self._row("endettement", "= ENDETTEMENT FINANCIER NET", s["endettement_financier_net"])

        self.tree.insert("", "end", tags=("total",), values=(
            "TRÉSORERIE NETTE", f"{s['controle_treso_reelle']:,.2f}"))

        if abs(s["controle_ecart"]) < 1:
            self.ecart_var.set("✓ La trésorerie nette (FR - BFR) correspond exactement à la Balance.")
        else:
            self.ecart_var.set(
                f"⚠ Écart de {s['controle_ecart']:,.2f} — vérifiez que les soldes d'ouverture de tous "
                f"les comptes (onglet Soldes d'ouverture) sont complets et s'équilibrent à zéro."
            )


class TftTab(ttk.Frame):
    def __init__(self, parent, conn):
        super().__init__(parent)
        self.conn = conn
        inner = ttk.Notebook(self)
        inner.pack(fill="both", expand=True)
        self.indirect_tab = TftIndirectTab(inner, conn)
        self.direct_tab = TftDirectTab(inner, conn)
        inner.add(self.indirect_tab, text="TFT (méthode indirecte — CAFG)")
        inner.add(self.direct_tab, text="TFT (méthode directe — ancien)")

    def refresh(self):
        self.indirect_tab.refresh()
        self.direct_tab.refresh()


class LiasseFiscaleTab(ttk.Frame):
    def __init__(self, parent, conn):
        super().__init__(parent)
        self.conn = conn

        info = ttk.LabelFrame(self, text="Identification de l'entité (SYSCOHADA / DGI)")
        info.pack(fill="x", padx=8, pady=8)

        self.vars = {}
        for i, (key, label) in enumerate(core.COMPANY_FIELDS.items()):
            r, c = divmod(i, 2)
            ttk.Label(info, text=label + " :").grid(row=r * 2, column=c, sticky="w", padx=4, pady=(4, 0))
            var = tk.StringVar(value=core.get_company_value(conn, key))
            ttk.Entry(info, textvariable=var, width=40).grid(row=r * 2 + 1, column=c, sticky="we", padx=4, pady=(0, 6))
            self.vars[key] = var
        ttk.Button(info, text="Enregistrer les informations", command=self.save_info).grid(
            row=6, column=0, sticky="w", padx=4, pady=6)

        params = ttk.LabelFrame(self, text="Paramètres d'export")
        params.pack(fill="x", padx=8, pady=(0, 8))
        ttk.Label(params, text="Stock initial total (cf. onglet Stocks) :").grid(row=0, column=0, sticky="w", padx=4, pady=4)
        self.stock_initial_var = tk.StringVar(value="0")
        ttk.Entry(params, textvariable=self.stock_initial_var, width=16).grid(row=0, column=1, sticky="w", padx=4)
        ttk.Label(params, text="(complément optionnel — utilisez plutôt l'onglet « Soldes d'ouverture »)",
                  foreground="#595959").grid(row=0, column=2, sticky="w", padx=(10, 4))

        note = ttk.Label(self, wraplength=900, foreground="#595959", text=(
            "Génère un classeur .xlsx COMPLET reprenant les 92 pages du modèle SYSCOHADA système "
            "normal (mêmes dimensions, mêmes codes officiels) : COUVERTURE, BILAN, RESULTAT, TFT, "
            "39 notes annexes, ~20 tableaux fiscaux DGI. BILAN et RESULTAT sont calculés automatiquement "
            "depuis vos écritures (soldes de clôture = solde d'ouverture + mouvements de l'exercice, "
            "cf. onglet « Soldes d'ouverture »). Le TFT officiel (méthode indirecte, CAFG) est laissé "
            "vierge — un onglet « TFT (simplifie) » calculé en méthode directe est ajouté à titre "
            "indicatif. Toutes les autres pages gardent leur mise en page et leurs dimensions exactes, "
            "mais leurs valeurs sont vidées (ce ne sont pas vos chiffres) pour être complétées "
            "manuellement — le détail des lignes du Bilan (AE à AN, CA à CM, DA à DM) est une "
            "répartition indicative par plage de comptes. À faire vérifier par un expert-comptable "
            "avant tout dépôt officiel auprès de la DGI."
        ))
        note.pack(fill="x", padx=8, pady=(0, 8))

        ttk.Button(self, text="Exporter la liasse fiscale complète (.xlsx)", command=self.export).pack(padx=8, pady=8, anchor="w")
        self.status_var = tk.StringVar()
        ttk.Label(self, textvariable=self.status_var, foreground="#1F4E78").pack(padx=8, anchor="w")

    def save_info(self):
        for key, var in self.vars.items():
            core.set_company_value(self.conn, key, var.get().strip())
        self.status_var.set("Informations enregistrées.")

    def export(self):
        self.save_info()
        try:
            stock_initial = float(self.stock_initial_var.get() or 0)
        except ValueError:
            messagebox.showerror("Erreur", "Le complément de stock initial doit être un nombre.")
            return
        path = filedialog.asksaveasfilename(
            defaultextension=".xlsx",
            filetypes=[("Classeur Excel", "*.xlsx")],
            initialfile="Liasse_fiscale.xlsx",
            title="Enregistrer la liasse fiscale",
        )
        if not path:
            return
        try:
            core.export_liasse_fiscale_complete(self.conn, path, stock_initial=stock_initial)
        except Exception as exc:
            messagebox.showerror("Erreur", f"Échec de l'export : {exc}")
            return
        self.status_var.set(f"Export réussi : {path}")
        messagebox.showinfo("Export terminé", f"Liasse fiscale enregistrée :\n{path}")


class PlaceholderTab(ttk.Frame):
    """Page pas encore développée : structure de menu en place, contenu à venir."""

    def __init__(self, parent, conn, title, description):
        super().__init__(parent)
        ttk.Label(self, text=title, font=("Segoe UI", 14, "bold")).pack(anchor="w", padx=24, pady=(24, 8))
        ttk.Label(self, text=description, wraplength=900, foreground="#595959").pack(anchor="w", padx=24)
        ttk.Label(self, text="Fonctionnalité pas encore développée — dites-moi si vous voulez que je "
                              "la construise en priorité.", foreground="#B00020").pack(anchor="w", padx=24, pady=(16, 0))


class VentesTab(ttk.Frame):
    """Soldes des opérations avec chaque client, total par client,
    avec filtre sur une plage de dates."""

    def __init__(self, parent, conn):
        super().__init__(parent)
        self.conn = conn
        ttk.Label(self, text="VENTES — SOLDES PAR CLIENT", font=("Segoe UI", 14, "bold")).pack(
            anchor="w", padx=16, pady=(16, 4))
        ttk.Label(self, text=(
            "Solde = Débit − Crédit sur les comptes clients (411xxx) taggés à chaque client dans "
            "la Saisie. Positif = montant restant dû par le client (à recouvrer)."
        ), foreground="#595959", wraplength=1000).pack(anchor="w", padx=16, pady=(0, 8))

        filt = ttk.Frame(self)
        filt.pack(fill="x", padx=16, pady=4)
        ttk.Label(filt, text="Du (JJ/MM/AAAA) :").pack(side="left")
        self.date_from_var = tk.StringVar()
        ttk.Entry(filt, textvariable=self.date_from_var, width=12).pack(side="left", padx=4)
        ttk.Label(filt, text="Au (JJ/MM/AAAA) :").pack(side="left", padx=(12, 0))
        self.date_to_var = tk.StringVar()
        ttk.Entry(filt, textvariable=self.date_to_var, width=12).pack(side="left", padx=4)
        ttk.Button(filt, text="Filtrer", command=self.refresh).pack(side="left", padx=8)
        ttk.Button(filt, text="Réinitialiser", command=self._reset_filter).pack(side="left", padx=2)

        cols = ("code", "raison_sociale", "debit", "credit", "solde")
        self.tree = ttk.Treeview(self, columns=cols, show="headings")
        headers = ["Code", "Client", "Total Débit", "Total Crédit", "Solde (dû si positif)"]
        widths = [90, 320, 120, 120, 160]
        for c, h, w in zip(cols, headers, widths):
            self.tree.heading(c, text=h)
            self.tree.column(c, width=w, anchor="w")
        self.tree.pack(fill="both", expand=True, padx=16, pady=8)
        self.total_var = tk.StringVar()
        ttk.Label(self, textvariable=self.total_var, font=("Segoe UI", 10, "bold")).pack(anchor="w", padx=16, pady=(0, 12))
        self.refresh()

    def _reset_filter(self):
        self.date_from_var.set("")
        self.date_to_var.set("")
        self.refresh()

    def refresh(self):
        for row in self.tree.get_children():
            self.tree.delete(row)
        date_from = core.to_iso_date(self.date_from_var.get()) if self.date_from_var.get().strip() else None
        date_to = core.to_iso_date(self.date_to_var.get()) if self.date_to_var.get().strip() else None
        ventes, total_debit, total_credit = core.compute_ventes_par_client(
            self.conn, date_from=date_from, date_to=date_to)
        for v in ventes:
            self.tree.insert("", "end", values=(
                v["code"], v["raison_sociale"], f"{v['debit']:,.2f}", f"{v['credit']:,.2f}", f"{v['solde']:,.2f}"
            ))
        self.total_var.set(
            f"TOTAL — Débit : {total_debit:,.2f}   Crédit : {total_credit:,.2f}   "
            f"Solde global à recouvrer : {total_debit - total_credit:,.2f}"
        )


class AchatsTab(ttk.Frame):
    """Soldes des opérations avec chaque fournisseur, total par fournisseur,
    avec filtre sur une plage de dates."""

    def __init__(self, parent, conn):
        super().__init__(parent)
        self.conn = conn
        ttk.Label(self, text="ACHATS — SOLDES PAR FOURNISSEUR", font=("Segoe UI", 14, "bold")).pack(
            anchor="w", padx=16, pady=(16, 4))
        ttk.Label(self, text=(
            "Solde = Débit − Crédit sur les comptes fournisseurs (401xxx/408xxx) taggés à chaque "
            "fournisseur dans la Saisie. Négatif = montant restant dû au fournisseur."
        ), foreground="#595959", wraplength=1000).pack(anchor="w", padx=16, pady=(0, 8))

        filt = ttk.Frame(self)
        filt.pack(fill="x", padx=16, pady=4)
        ttk.Label(filt, text="Du (JJ/MM/AAAA) :").pack(side="left")
        self.date_from_var = tk.StringVar()
        ttk.Entry(filt, textvariable=self.date_from_var, width=12).pack(side="left", padx=4)
        ttk.Label(filt, text="Au (JJ/MM/AAAA) :").pack(side="left", padx=(12, 0))
        self.date_to_var = tk.StringVar()
        ttk.Entry(filt, textvariable=self.date_to_var, width=12).pack(side="left", padx=4)
        ttk.Button(filt, text="Filtrer", command=self.refresh).pack(side="left", padx=8)
        ttk.Button(filt, text="Réinitialiser", command=self._reset_filter).pack(side="left", padx=2)

        cols = ("code", "raison_sociale", "debit", "credit", "solde")
        self.tree = ttk.Treeview(self, columns=cols, show="headings")
        headers = ["Code", "Fournisseur", "Total Débit", "Total Crédit", "Solde (dû si négatif)"]
        widths = [90, 320, 120, 120, 160]
        for c, h, w in zip(cols, headers, widths):
            self.tree.heading(c, text=h)
            self.tree.column(c, width=w, anchor="w")
        self.tree.pack(fill="both", expand=True, padx=16, pady=8)
        self.total_var = tk.StringVar()
        ttk.Label(self, textvariable=self.total_var, font=("Segoe UI", 10, "bold")).pack(anchor="w", padx=16, pady=(0, 12))
        self.refresh()

    def _reset_filter(self):
        self.date_from_var.set("")
        self.date_to_var.set("")
        self.refresh()

    def refresh(self):
        for row in self.tree.get_children():
            self.tree.delete(row)
        date_from = core.to_iso_date(self.date_from_var.get()) if self.date_from_var.get().strip() else None
        date_to = core.to_iso_date(self.date_to_var.get()) if self.date_to_var.get().strip() else None
        achats, total_debit, total_credit = core.compute_achats_par_fournisseur(
            self.conn, date_from=date_from, date_to=date_to)
        for a in achats:
            self.tree.insert("", "end", values=(
                a["code"], a["raison_sociale"], f"{a['debit']:,.2f}", f"{a['credit']:,.2f}", f"{a['solde']:,.2f}"
            ))
        self.total_var.set(
            f"TOTAL — Débit : {total_debit:,.2f}   Crédit : {total_credit:,.2f}   "
            f"Solde global : {total_debit - total_credit:,.2f}"
        )


class MargesTab(ttk.Frame):
    """Marge commerciale et valeur ajoutée, calculées comme dans la Liasse fiscale."""

    def __init__(self, parent, conn):
        super().__init__(parent)
        self.conn = conn
        self.text = tk.Text(self, font=("Consolas", 11), wrap="none")
        self.text.pack(fill="both", expand=True, padx=16, pady=16)
        self.refresh()

    def refresh(self):
        cr = core.compute_liasse_resultat(self.conn)
        label_ca = "Chiffre d'affaires (XB)"
        label_re = "Résultat d'exploitation (XE)"
        lines = [
            "MARGES BÉNÉFICIAIRES", "=" * 60, "",
            f"  {'Ventes de marchandises (TA)':<45} {cr['TA']:>14,.2f}",
            f"  {'Achats de marchandises (RA)':<45} {-cr['RA']:>14,.2f}",
            f"  {'MARGE COMMERCIALE (XA)':<45} {cr['XA']:>14,.2f}", "",
            f"  {label_ca:<45} {cr['XB']:>14,.2f}",
            f"  {'VALEUR AJOUTÉE (XC)':<45} {cr['XC']:>14,.2f}",
            f"  {label_re:<45} {cr['XE']:>14,.2f}",
            f"  {'RÉSULTAT NET (XI)':<45} {cr['XI']:>14,.2f}",
        ]
        self.text.delete("1.0", "end")
        self.text.insert("1.0", "\n".join(lines))


class ClientsTab(ttk.Frame):
    """Liste auxiliaire des clients : créer / modifier / importer."""

    def __init__(self, parent, conn):
        super().__init__(parent)
        self.conn = conn
        ttk.Label(self, text="CLIENTS (LISTE AUXILIAIRE)", font=("Segoe UI", 14, "bold")).pack(
            anchor="w", padx=16, pady=(16, 8))
        ttk.Label(self, text=(
            "Ces fiches sont rattachées à la racine 41 (Clients et comptes rattachés) du Plan "
            "comptable — les écritures qui les taguent doivent utiliser un compte 41xxxx."
        ), foreground="#595959").pack(anchor="w", padx=16, pady=(0, 4))

        form = ttk.Frame(self)
        form.pack(fill="x", padx=16, pady=4)
        labels = ["Code", "Raison sociale", "Contact", "Téléphone", "Adresse", "Délai paiement (jours)"]
        self.vars = {k: tk.StringVar() for k in labels}
        for i, lbl in enumerate(labels):
            r, c = divmod(i, 4)
            ttk.Label(form, text=lbl + " :").grid(row=r * 2, column=c, sticky="w", padx=4, pady=(4, 0))
            ttk.Entry(form, textvariable=self.vars[lbl], width=22).grid(
                row=r * 2 + 1, column=c, sticky="we", padx=4, pady=(0, 4))
        btns = ttk.Frame(form)
        btns.grid(row=2, column=0, columnspan=4, sticky="w", pady=6)
        ttk.Button(btns, text="Créer / Modifier", command=self.save).pack(side="left", padx=2)
        ttk.Button(btns, text="Supprimer", command=self.delete).pack(side="left", padx=2)
        ttk.Button(btns, text="Effacer le formulaire", command=self.clear_form).pack(side="left", padx=2)

        import_bar = ttk.Frame(self)
        import_bar.pack(fill="x", padx=16, pady=(4, 4))
        ttk.Button(import_bar, text="Importer des clients (.xlsx)", command=self.import_xlsx).pack(side="left", padx=2)
        ttk.Button(import_bar, text="Télécharger un modèle (.xlsx)", command=self.download_template).pack(side="left", padx=2)

        search_bar = ttk.Frame(self)
        search_bar.pack(fill="x", padx=16, pady=4)
        ttk.Label(search_bar, text="Rechercher :").pack(side="left")
        self.search_var = tk.StringVar()
        se = ttk.Entry(search_bar, textvariable=self.search_var, width=30)
        se.pack(side="left", padx=6)
        se.bind("<KeyRelease>", lambda e: self.refresh())

        cols = ("code", "raison_sociale", "contact", "telephone", "adresse", "dp")
        self.tree = ttk.Treeview(self, columns=cols, show="headings")
        headers = ["Code", "Raison sociale", "Contact", "Téléphone", "Adresse", "Délai paiement (j)"]
        widths = [90, 220, 130, 110, 220, 130]
        for c, h, w in zip(cols, headers, widths):
            self.tree.heading(c, text=h)
            self.tree.column(c, width=w, anchor="w")
        self.tree.pack(fill="both", expand=True, padx=16, pady=8)
        self.tree.bind("<<TreeviewSelect>>", self._on_select)
        self.refresh()

    def _on_select(self, event=None):
        sel = self.tree.selection()
        if not sel:
            return
        v = self.tree.item(sel[0], "values")
        self.vars["Code"].set(v[0])
        self.vars["Raison sociale"].set(v[1])
        self.vars["Contact"].set(v[2])
        self.vars["Téléphone"].set(v[3])
        self.vars["Adresse"].set(v[4])
        self.vars["Délai paiement (jours)"].set(v[5])

    def clear_form(self):
        for v in self.vars.values():
            v.set("")

    def save(self):
        code = self.vars["Code"].get().strip()
        raison = self.vars["Raison sociale"].get().strip()
        if not code or not raison:
            messagebox.showwarning("Champs manquants", "Code et Raison sociale sont obligatoires.")
            return
        try:
            dp = int(self.vars["Délai paiement (jours)"].get() or 30)
        except ValueError:
            messagebox.showerror("Erreur", "Le délai de paiement doit être un nombre entier de jours.")
            return
        core.add_client(self.conn, code, raison, self.vars["Contact"].get().strip(),
                         self.vars["Téléphone"].get().strip(), self.vars["Adresse"].get().strip(), dp)
        self.refresh()

    def delete(self):
        code = self.vars["Code"].get().strip()
        if not code:
            messagebox.showinfo("Info", "Sélectionnez d'abord un client.")
            return
        if messagebox.askyesno("Confirmer", f"Supprimer le client {code} ?"):
            core.delete_client(self.conn, code)
            self.clear_form()
            self.refresh()

    def download_template(self):
        path = filedialog.asksaveasfilename(
            defaultextension=".xlsx", filetypes=[("Classeur Excel", "*.xlsx")],
            initialfile="Modele_clients.xlsx", title="Enregistrer le modèle",
        )
        if not path:
            return
        core.export_clients_template(path)
        messagebox.showinfo("Modèle créé", f"Modèle enregistré :\n{path}")

    def import_xlsx(self):
        path = filedialog.askopenfilename(filetypes=[("Classeur Excel", "*.xlsx")],
                                           title="Importer des clients")
        if not path:
            return
        try:
            imported, warnings = core.import_clients_from_xlsx(self.conn, path)
        except Exception as exc:
            messagebox.showerror("Erreur", f"Échec de l'import : {exc}")
            return
        self.refresh()
        msg = f"{imported} client(s) importé(s)."
        if warnings:
            msg += "\n\nAvertissements :\n" + "\n".join(warnings[:20])
        messagebox.showinfo("Import terminé", msg)

    def refresh(self):
        for row in self.tree.get_children():
            self.tree.delete(row)
        for c in core.list_clients(self.conn, self.search_var.get().strip() or None):
            self.tree.insert("", "end", values=(
                c["code"], c["raison_sociale"], c["contact"] or "", c["telephone"] or "",
                c["adresse"] or "", c["delai_paiement_jours"],
            ))


class FournisseursTab(ttk.Frame):
    """Liste auxiliaire des fournisseurs : créer / modifier / importer."""

    def __init__(self, parent, conn):
        super().__init__(parent)
        self.conn = conn
        ttk.Label(self, text="FOURNISSEURS (LISTE AUXILIAIRE)", font=("Segoe UI", 14, "bold")).pack(
            anchor="w", padx=16, pady=(16, 8))
        ttk.Label(self, text=(
            "Ces fiches sont rattachées à la racine 40 (Fournisseurs et comptes rattachés) du Plan "
            "comptable — les écritures qui les taguent doivent utiliser un compte 40xxxx."
        ), foreground="#595959").pack(anchor="w", padx=16, pady=(0, 4))

        form = ttk.Frame(self)
        form.pack(fill="x", padx=16, pady=4)
        labels = ["Code", "Raison sociale", "Contact", "Téléphone", "Adresse",
                  "Délai paiement (jours)", "Délai livraison (jours)"]
        self.vars = {k: tk.StringVar() for k in labels}
        for i, lbl in enumerate(labels):
            r, c = divmod(i, 4)
            ttk.Label(form, text=lbl + " :").grid(row=r * 2, column=c, sticky="w", padx=4, pady=(4, 0))
            ttk.Entry(form, textvariable=self.vars[lbl], width=22).grid(
                row=r * 2 + 1, column=c, sticky="we", padx=4, pady=(0, 4))
        btns = ttk.Frame(form)
        btns.grid(row=4, column=0, columnspan=4, sticky="w", pady=6)
        ttk.Button(btns, text="Créer / Modifier", command=self.save).pack(side="left", padx=2)
        ttk.Button(btns, text="Supprimer", command=self.delete).pack(side="left", padx=2)
        ttk.Button(btns, text="Effacer le formulaire", command=self.clear_form).pack(side="left", padx=2)

        import_bar = ttk.Frame(self)
        import_bar.pack(fill="x", padx=16, pady=(4, 4))
        ttk.Button(import_bar, text="Importer des fournisseurs (.xlsx)", command=self.import_xlsx).pack(side="left", padx=2)
        ttk.Button(import_bar, text="Télécharger un modèle (.xlsx)", command=self.download_template).pack(side="left", padx=2)

        search_bar = ttk.Frame(self)
        search_bar.pack(fill="x", padx=16, pady=4)
        ttk.Label(search_bar, text="Rechercher :").pack(side="left")
        self.search_var = tk.StringVar()
        se = ttk.Entry(search_bar, textvariable=self.search_var, width=30)
        se.pack(side="left", padx=6)
        se.bind("<KeyRelease>", lambda e: self.refresh())

        cols = ("code", "raison_sociale", "contact", "telephone", "adresse", "dp", "dl")
        self.tree = ttk.Treeview(self, columns=cols, show="headings")
        headers = ["Code", "Raison sociale", "Contact", "Téléphone", "Adresse",
                   "Délai paiement (j)", "Délai livraison (j)"]
        widths = [90, 220, 130, 110, 200, 110, 110]
        for c, h, w in zip(cols, headers, widths):
            self.tree.heading(c, text=h)
            self.tree.column(c, width=w, anchor="w")
        self.tree.pack(fill="both", expand=True, padx=16, pady=8)
        self.tree.bind("<<TreeviewSelect>>", self._on_select)
        self.refresh()

    def _on_select(self, event=None):
        sel = self.tree.selection()
        if not sel:
            return
        v = self.tree.item(sel[0], "values")
        self.vars["Code"].set(v[0])
        self.vars["Raison sociale"].set(v[1])
        self.vars["Contact"].set(v[2])
        self.vars["Téléphone"].set(v[3])
        self.vars["Adresse"].set(v[4])
        self.vars["Délai paiement (jours)"].set(v[5])
        self.vars["Délai livraison (jours)"].set(v[6])

    def clear_form(self):
        for v in self.vars.values():
            v.set("")

    def save(self):
        code = self.vars["Code"].get().strip()
        raison = self.vars["Raison sociale"].get().strip()
        if not code or not raison:
            messagebox.showwarning("Champs manquants", "Code et Raison sociale sont obligatoires.")
            return
        try:
            dp = int(self.vars["Délai paiement (jours)"].get() or 30)
            dl = int(self.vars["Délai livraison (jours)"].get() or 15)
        except ValueError:
            messagebox.showerror("Erreur", "Les délais doivent être des nombres entiers de jours.")
            return
        core.add_fournisseur(self.conn, code, raison, self.vars["Contact"].get().strip(),
                              self.vars["Téléphone"].get().strip(), self.vars["Adresse"].get().strip(),
                              dp, dl)
        self.refresh()

    def delete(self):
        code = self.vars["Code"].get().strip()
        if not code:
            messagebox.showinfo("Info", "Sélectionnez d'abord un fournisseur.")
            return
        if messagebox.askyesno("Confirmer", f"Supprimer le fournisseur {code} ?"):
            core.delete_fournisseur(self.conn, code)
            self.clear_form()
            self.refresh()

    def download_template(self):
        path = filedialog.asksaveasfilename(
            defaultextension=".xlsx", filetypes=[("Classeur Excel", "*.xlsx")],
            initialfile="Modele_fournisseurs.xlsx", title="Enregistrer le modèle",
        )
        if not path:
            return
        core.export_fournisseurs_template(path)
        messagebox.showinfo("Modèle créé", f"Modèle enregistré :\n{path}")

    def import_xlsx(self):
        path = filedialog.askopenfilename(filetypes=[("Classeur Excel", "*.xlsx")],
                                           title="Importer des fournisseurs")
        if not path:
            return
        try:
            imported, warnings = core.import_fournisseurs_from_xlsx(self.conn, path)
        except Exception as exc:
            messagebox.showerror("Erreur", f"Échec de l'import : {exc}")
            return
        self.refresh()
        msg = f"{imported} fournisseur(s) importé(s)."
        if warnings:
            msg += "\n\nAvertissements :\n" + "\n".join(warnings[:20])
        messagebox.showinfo("Import terminé", msg)

    def refresh(self):
        for row in self.tree.get_children():
            self.tree.delete(row)
        for f in core.list_fournisseurs(self.conn, self.search_var.get().strip() or None):
            self.tree.insert("", "end", values=(
                f["code"], f["raison_sociale"], f["contact"] or "", f["telephone"] or "",
                f["adresse"] or "", f["delai_paiement_jours"], f["delai_livraison_jours"],
            ))


class FacturationTab(ttk.Frame):
    """Facturation clients : présente directement une facture (entête, lignes de
    vente liées à un compte 70x, TVA paramétrable, pied de page), et sa
    validation envoie les écritures comptables en Saisie — avec sortie de stock
    automatique pour les lignes liées aux marchandises (31) ou produits finis (36)."""

    def __init__(self, parent, conn):
        super().__init__(parent)
        self.conn = conn
        self.current_facture_id = None

        # ---- Barre du haut : liste des factures ----
        top = ttk.Frame(self)
        top.pack(fill="x", padx=12, pady=8)
        ttk.Label(top, text="Facture n° :").pack(side="left")
        self.facture_combo = ttk.Combobox(top, width=40, state="readonly")
        self.facture_combo.pack(side="left", padx=4)
        self.facture_combo.bind("<<ComboboxSelected>>", self._on_facture_selected)
        ttk.Button(top, text="Nouvelle facture", command=self.new_facture).pack(side="left", padx=8)
        ttk.Button(top, text="Supprimer cette facture", command=self.delete_facture).pack(side="left", padx=2)
        self.statut_var = tk.StringVar()
        ttk.Label(top, textvariable=self.statut_var, font=("Segoe UI", 10, "bold")).pack(side="left", padx=16)

        # ---- Entête modifiable ----
        ttk.Label(self, text="En-tête de la facture (modifiable) :").pack(anchor="w", padx=12)
        self.entete_text = tk.Text(self, height=3, font=("Segoe UI", 10))
        self.entete_text.pack(fill="x", padx=12, pady=(0, 8))

        # ---- Champs d'en-tête structurés ----
        info = ttk.Frame(self)
        info.pack(fill="x", padx=12, pady=4)
        ttk.Label(info, text="N° Facture :").grid(row=0, column=0, sticky="w", padx=4)
        self.numero_var = tk.StringVar()
        ttk.Entry(info, textvariable=self.numero_var, width=16).grid(row=0, column=1, padx=4)
        ttk.Label(info, text="Date (JJ/MM/AAAA) :").grid(row=0, column=2, sticky="w", padx=(12, 4))
        self.date_var = tk.StringVar(value=date.today().strftime("%d/%m/%Y"))
        ttk.Entry(info, textvariable=self.date_var, width=14).grid(row=0, column=3, padx=4)
        ttk.Label(info, text="Client (compte 41) :").grid(row=0, column=4, sticky="w", padx=(12, 4))
        self.client_var = tk.StringVar()
        self.client_combo = ttk.Combobox(info, textvariable=self.client_var, width=26)
        self.client_combo.grid(row=0, column=5, padx=4)
        self.client_combo.bind("<KeyRelease>", self._on_client_keyrelease)
        self._refresh_client_values()
        ttk.Label(info, text="TVA % (compte 44) :").grid(row=0, column=6, sticky="w", padx=(12, 4))
        self.tva_var = tk.StringVar(value=str(core.get_setting(conn, "tva_taux_defaut", core.TVA_TAUX_DEFAUT)))
        ttk.Entry(info, textvariable=self.tva_var, width=6).grid(row=0, column=7, padx=4)

        # ---- Lignes ----
        form = ttk.LabelFrame(self, text="Ajouter une ligne (produit/service vendu — compte 70x)")
        form.pack(fill="x", padx=12, pady=6)
        ttk.Label(form, text="Compte de vente :").grid(row=0, column=0, sticky="w", padx=4, pady=4)
        self.ligne_compte_var = tk.StringVar()
        self.ligne_compte_combo = ttk.Combobox(form, textvariable=self.ligne_compte_var, width=34)
        self.ligne_compte_combo.grid(row=0, column=1, padx=4)
        self.ligne_compte_combo.bind("<KeyRelease>", self._on_ligne_compte_keyrelease)
        self._refresh_ligne_compte_values()
        ttk.Label(form, text="Libellé :").grid(row=0, column=2, sticky="w", padx=(12, 4))
        self.ligne_libelle_var = tk.StringVar()
        ttk.Entry(form, textvariable=self.ligne_libelle_var, width=26).grid(row=0, column=3, padx=4)
        ttk.Label(form, text="Quantité :").grid(row=1, column=0, sticky="w", padx=4, pady=4)
        self.ligne_qte_var = tk.StringVar(value="1")
        ttk.Entry(form, textvariable=self.ligne_qte_var, width=10).grid(row=1, column=1, sticky="w", padx=4)
        ttk.Label(form, text="Prix unitaire :").grid(row=1, column=2, sticky="w", padx=(12, 4))
        self.ligne_prix_var = tk.StringVar()
        ttk.Entry(form, textvariable=self.ligne_prix_var, width=14).grid(row=1, column=3, sticky="w", padx=4)
        ttk.Button(form, text="Ajouter la ligne", command=self.add_ligne).grid(row=1, column=4, padx=12)

        cols = ("id", "compte", "libelle", "type_stock", "qte", "prix", "montant")
        self.tree = ttk.Treeview(self, columns=cols, show="headings", height=6)
        headers = ["ID", "Compte", "Libellé", "Impact stock", "Qté", "Prix unit.", "Montant HT"]
        widths = [40, 90, 220, 110, 70, 100, 110]
        for c, h, w in zip(cols, headers, widths):
            self.tree.heading(c, text=h)
            self.tree.column(c, width=w, anchor="w")
        self.tree.pack(fill="both", expand=True, padx=12, pady=6)
        ttk.Button(self, text="Supprimer la ligne sélectionnée", command=self.delete_ligne).pack(anchor="w", padx=12)

        self.totals_var = tk.StringVar()
        ttk.Label(self, textvariable=self.totals_var, font=("Segoe UI", 11, "bold")).pack(anchor="w", padx=12, pady=(8, 0))

        # ---- Pied de page modifiable ----
        ttk.Label(self, text="Pied de page de la facture (modifiable) :").pack(anchor="w", padx=12, pady=(8, 0))
        self.pied_text = tk.Text(self, height=3, font=("Segoe UI", 10))
        self.pied_text.pack(fill="x", padx=12, pady=(0, 8))

        # ---- Validation ----
        btns = ttk.Frame(self)
        btns.pack(fill="x", padx=12, pady=8)
        ttk.Button(btns, text="Enregistrer (brouillon)", command=self.save_facture).pack(side="left", padx=2)
        ttk.Button(btns, text="Valider et envoyer en Saisie", command=self.valider).pack(side="left", padx=2)

        self.refresh_factures_list()

    # -- Client --
    def _refresh_client_values(self):
        items = core.list_clients(self.conn)
        self.client_combo["values"] = [f"{c['code']} — {c['raison_sociale']}" for c in items]

    def _on_client_keyrelease(self, event=None):
        query = self._extract_code(self.client_var.get())
        if query:
            items = core.list_clients(self.conn, query)
            self.client_combo["values"] = [f"{c['code']} — {c['raison_sociale']}" for c in items]

    # -- Compte de vente --
    def _refresh_ligne_compte_values(self):
        items = core.search_accounts(self.conn, "7", limit=100)
        items = [a for a in items if a["classe"] == "7"]
        self.ligne_compte_combo["values"] = [f"{a['code']} — {a['label']}" for a in items]

    def _on_ligne_compte_keyrelease(self, event=None):
        query = self._extract_code(self.ligne_compte_var.get())
        if query:
            items = [a for a in core.search_accounts(self.conn, query, limit=50) if a["classe"] == "7"]
            self.ligne_compte_combo["values"] = [f"{a['code']} — {a['label']}" for a in items]

    @staticmethod
    def _extract_code(raw):
        raw = (raw or "").strip()
        return raw.split(" — ", 1)[0].strip() if " — " in raw else raw

    # -- Gestion des factures --
    def refresh_factures_list(self):
        factures = core.list_factures_vente(self.conn)
        values = [f"{f['numero']} — {f['raison_sociale']} — {f['statut']}" for f in factures]
        self.facture_combo["values"] = values
        self._factures_cache = factures
        if self.current_facture_id is None and factures:
            self.current_facture_id = factures[0]["id"]
            self.facture_combo.current(0)
        self.load_facture()

    def new_facture(self):
        numero = simpledialog.askstring("Nouvelle facture", "N° de facture :", parent=self)
        if not numero:
            return
        client_code = self._extract_code(self.client_var.get())
        if not client_code or not core.client_exists(self.conn, client_code):
            messagebox.showinfo("Client requis", "Choisissez d'abord un client existant dans le champ Client.")
            return
        date_str = core.to_iso_date(self.date_var.get().strip()) or date.today().strftime("%Y-%m-%d")
        fid = core.create_facture_vente(self.conn, numero, date_str, client_code)
        self.current_facture_id = fid
        self.refresh_factures_list()

    def _on_facture_selected(self, event=None):
        idx = self.facture_combo.current()
        if 0 <= idx < len(self._factures_cache):
            self.current_facture_id = self._factures_cache[idx]["id"]
        self.load_facture()

    def load_facture(self):
        for row in self.tree.get_children():
            self.tree.delete(row)
        self.entete_text.delete("1.0", "end")
        self.pied_text.delete("1.0", "end")
        if not self.current_facture_id:
            self.statut_var.set("Aucune facture — créez-en une nouvelle.")
            self.totals_var.set("")
            return
        f = core.get_facture_vente(self.conn, self.current_facture_id)
        if not f:
            self.current_facture_id = None
            self.statut_var.set("")
            return
        self.numero_var.set(f["numero"])
        self.date_var.set(core.to_display_date(f["date_facture"]))
        client = core.get_client(self.conn, f["client_code"])
        self.client_var.set(f"{f['client_code']} — {client['raison_sociale']}" if client else f["client_code"])
        self.tva_var.set(str(f["tva_taux"]))
        self.entete_text.insert("1.0", f["entete"] or "")
        self.pied_text.insert("1.0", f["pied_page"] or "")
        statut_label = "VALIDÉE (écritures envoyées en Saisie)" if f["statut"] == "validee" else "Brouillon"
        self.statut_var.set(f"Statut : {statut_label}")

        editable = f["statut"] != "validee"
        state = "normal" if editable else "disabled"
        for w in (self.entete_text, self.pied_text):
            w.configure(state="normal")
        if not editable:
            self.entete_text.configure(state="disabled")
            self.pied_text.configure(state="disabled")

        lignes = core.list_lignes_facture_vente(self.conn, self.current_facture_id)
        for l in lignes:
            impact = {"marchandise": "Stock marchandises (31)", "produit_fini": "Stock produits finis (36)"}.get(
                l["type_stock"], "Aucun (service)")
            self.tree.insert("", "end", values=(
                l["id"], l["compte_vente"], l["libelle"], impact,
                f"{l['quantite']:g}", f"{l['prix_unitaire']:,.2f}", f"{l['montant_ht']:,.2f}",
            ))
        totals = core.compute_facture_totals(self.conn, self.current_facture_id)
        self.totals_var.set(
            f"TOTAL HT : {totals['total_ht']:,.2f}    TVA ({totals['tva_taux']:g}%) : "
            f"{totals['tva_montant']:,.2f}    TOTAL TTC : {totals['total_ttc']:,.2f}"
        )

    def _ensure_facture(self):
        if not self.current_facture_id:
            messagebox.showinfo("Info", "Créez d'abord une nouvelle facture.")
            return None
        f = core.get_facture_vente(self.conn, self.current_facture_id)
        if f and f["statut"] == "validee":
            messagebox.showwarning("Facture validée", "Cette facture est déjà validée et ne peut plus être modifiée.")
            return None
        return f

    def add_ligne(self):
        f = self._ensure_facture()
        if not f:
            return
        compte = self._extract_code(self.ligne_compte_var.get())
        if not compte:
            messagebox.showwarning("Champ manquant", "Choisissez un compte de vente (classe 70).")
            return
        if not core.account_exists(self.conn, compte) or core.account_racine(compte) != "7":
            messagebox.showerror("Compte invalide", "Le compte de vente doit être un compte existant de la classe 7.")
            return
        libelle = self.ligne_libelle_var.get().strip()
        if not libelle:
            messagebox.showwarning("Champ manquant", "Le libellé de la ligne est obligatoire.")
            return
        try:
            qte = float(self.ligne_qte_var.get() or 0)
            prix = float(self.ligne_prix_var.get() or 0)
        except ValueError:
            messagebox.showerror("Erreur", "Quantité et Prix unitaire doivent être des nombres.")
            return
        core.add_ligne_facture_vente(self.conn, self.current_facture_id, compte, libelle, qte, prix)
        self.ligne_libelle_var.set("")
        self.ligne_qte_var.set("1")
        self.ligne_prix_var.set("")
        self.load_facture()

    def delete_ligne(self):
        f = self._ensure_facture()
        if not f:
            return
        sel = self.tree.selection()
        if not sel:
            messagebox.showinfo("Info", "Sélectionnez d'abord une ligne.")
            return
        ligne_id = int(self.tree.item(sel[0], "values")[0])
        core.delete_ligne_facture_vente(self.conn, ligne_id)
        self.load_facture()

    def save_facture(self):
        f = self._ensure_facture()
        if not f:
            return
        client_code = self._extract_code(self.client_var.get())
        if not client_code or not core.client_exists(self.conn, client_code):
            messagebox.showerror("Client invalide", "Choisissez un client existant.")
            return
        date_str = core.to_iso_date(self.date_var.get().strip())
        try:
            tva = float(self.tva_var.get() or 0)
        except ValueError:
            messagebox.showerror("Erreur", "Le taux de TVA doit être un nombre.")
            return
        core.update_facture_vente(
            self.conn, self.current_facture_id,
            numero=self.numero_var.get().strip(), date_facture=date_str, client_code=client_code,
            entete=self.entete_text.get("1.0", "end").strip(),
            pied_page=self.pied_text.get("1.0", "end").strip(),
            tva_taux=tva,
        )
        core.set_setting(self.conn, "tva_taux_defaut", tva)
        messagebox.showinfo("Enregistré", "Facture enregistrée (brouillon).")
        self.refresh_factures_list()

    def valider(self):
        f = self._ensure_facture()
        if not f:
            return
        self.save_facture()
        if messagebox.askyesno(
            "Confirmer la validation",
            "Valider cette facture ? Les écritures comptables seront envoyées dans le menu SAISIE "
            "(débit client, crédit ventes, TVA, et sortie de stock automatique pour les lignes "
            "marchandises/produits finis). Cette action est définitive."
        ):
            try:
                warnings = core.valider_facture_vente(self.conn, self.current_facture_id)
            except ValueError as exc:
                messagebox.showerror("Erreur", str(exc))
                return
            msg = "Facture validée et écritures envoyées en Saisie."
            if warnings:
                msg += "\n\nAvertissements :\n" + "\n".join(warnings)
            messagebox.showinfo("Validation terminée", msg)
            self.refresh_factures_list()

    def delete_facture(self):
        if not self.current_facture_id:
            return
        if messagebox.askyesno("Confirmer", "Supprimer cette facture ?"):
            try:
                core.delete_facture_vente(self.conn, self.current_facture_id)
            except ValueError as exc:
                messagebox.showerror("Erreur", str(exc))
                return
            self.current_facture_id = None
            self.refresh_factures_list()

    def refresh(self):
        self._refresh_client_values()
        self._refresh_ligne_compte_values()
        self.refresh_factures_list()


class RecouvrementTab(ttk.Frame):
    """Journal des factures clients : suivi des retards de paiement (recouvrement)."""

    def __init__(self, parent, conn):
        super().__init__(parent)
        self.conn = conn
        ttk.Label(self, text="RECOUVREMENT — SUIVI DES RETARDS DE PAIEMENT CLIENTS",
                  font=("Segoe UI", 14, "bold")).pack(anchor="w", padx=16, pady=(16, 4))
        ttk.Label(self, text=(
            "Enregistrez ici chaque facture émise à un client. L'échéance de paiement est calculée "
            "automatiquement à partir du délai par défaut du client (modifiable dans l'onglet "
            "Clients), à la date de facture. Renseignez ensuite la date réelle de paiement au fur "
            "et à mesure des encaissements — les retards sont signalés automatiquement."
        ), foreground="#595959", wraplength=1050).pack(anchor="w", padx=16, pady=(0, 8))

        form = ttk.LabelFrame(self, text="Nouvelle facture")
        form.pack(fill="x", padx=16, pady=4)
        ttk.Label(form, text="Client :").grid(row=0, column=0, sticky="w", padx=4, pady=4)
        self.client_var = tk.StringVar()
        self.client_combo = ttk.Combobox(form, textvariable=self.client_var, width=28)
        self.client_combo.grid(row=0, column=1, padx=4)
        self.client_combo.bind("<KeyRelease>", self._on_client_keyrelease)
        self._refresh_client_values()

        ttk.Label(form, text="N° Pièce :").grid(row=0, column=2, sticky="w", padx=(12, 4))
        self.piece_var = tk.StringVar()
        ttk.Entry(form, textvariable=self.piece_var, width=14).grid(row=0, column=3, padx=4)

        ttk.Label(form, text="Libellé :").grid(row=0, column=4, sticky="w", padx=(12, 4))
        self.libelle_var = tk.StringVar()
        ttk.Entry(form, textvariable=self.libelle_var, width=26).grid(row=0, column=5, padx=4)

        ttk.Label(form, text="Montant :").grid(row=1, column=0, sticky="w", padx=4, pady=4)
        self.montant_var = tk.StringVar()
        ttk.Entry(form, textvariable=self.montant_var, width=16).grid(row=1, column=1, padx=4)

        ttk.Label(form, text="Date facture (JJ/MM/AAAA) :").grid(row=1, column=2, sticky="w", padx=(12, 4))
        self.date_facture_var = tk.StringVar(value=date.today().strftime("%d/%m/%Y"))
        ttk.Entry(form, textvariable=self.date_facture_var, width=14).grid(row=1, column=3, padx=4)

        ttk.Button(form, text="Créer la facture (échéance auto)", command=self.add_facture).grid(
            row=1, column=4, columnspan=2, sticky="w", padx=12, pady=4)

        update_frame = ttk.LabelFrame(self, text="Mettre à jour la facture sélectionnée")
        update_frame.pack(fill="x", padx=16, pady=(8, 4))
        ttk.Label(update_frame, text="Date paiement réel (JJ/MM/AAAA) :").grid(row=0, column=0, sticky="w", padx=4, pady=4)
        self.paiement_reel_var = tk.StringVar()
        ttk.Entry(update_frame, textvariable=self.paiement_reel_var, width=14).grid(row=0, column=1, padx=4)
        ttk.Button(update_frame, text="Enregistrer le paiement", command=self.save_paiement).grid(
            row=0, column=2, padx=8)
        ttk.Button(update_frame, text="Supprimer la facture sélectionnée", command=self.delete_facture).grid(
            row=0, column=3, padx=20)

        cols = ("id", "client", "piece", "libelle", "montant", "date_facture",
                "echeance_paiement", "statut_paiement")
        self.tree = ttk.Treeview(self, columns=cols, show="headings")
        headers = ["ID", "Client", "Pièce", "Libellé", "Montant", "Date facture",
                   "Échéance paiement", "Statut paiement"]
        widths = [40, 180, 90, 200, 110, 110, 130, 160]
        for c, h, w in zip(cols, headers, widths):
            self.tree.heading(c, text=h)
            self.tree.column(c, width=w, anchor="w")
        self.tree.tag_configure("depasse", foreground="#B00020")
        self.tree.pack(fill="both", expand=True, padx=16, pady=8)
        self.tree.bind("<<TreeviewSelect>>", self._on_select)
        self.selected_id = None
        self.refresh()

    def _refresh_client_values(self):
        items = core.list_clients(self.conn)
        self.client_combo["values"] = [f"{c['code']} — {c['raison_sociale']}" for c in items]

    def _on_client_keyrelease(self, event=None):
        query = self._extract_code(self.client_var.get())
        if query:
            items = core.list_clients(self.conn, query)
            self.client_combo["values"] = [f"{c['code']} — {c['raison_sociale']}" for c in items]

    @staticmethod
    def _extract_code(raw):
        raw = (raw or "").strip()
        return raw.split(" — ", 1)[0].strip() if " — " in raw else raw

    def _on_select(self, event=None):
        sel = self.tree.selection()
        if not sel:
            return
        values = self.tree.item(sel[0], "values")
        self.selected_id = int(values[0])

    def add_facture(self):
        code = self._extract_code(self.client_var.get())
        if not code:
            messagebox.showwarning("Champ manquant", "Choisissez un client.")
            return
        if not core.client_exists(self.conn, code):
            messagebox.showerror("Client invalide", f"Le client « {code} » n'existe pas. "
                                                      f"Créez-le d'abord dans l'onglet Clients.")
            return
        try:
            montant = float(self.montant_var.get() or 0)
        except ValueError:
            messagebox.showerror("Erreur", "Le montant doit être un nombre.")
            return
        date_facture = core.to_iso_date(self.date_facture_var.get().strip())
        if not date_facture:
            messagebox.showwarning("Champ manquant", "La date de facture est obligatoire.")
            return
        core.add_facture(self.conn, code, self.piece_var.get().strip(), self.libelle_var.get().strip(),
                          montant, date_facture)
        self.piece_var.set("")
        self.libelle_var.set("")
        self.montant_var.set("")
        self.refresh()

    def save_paiement(self):
        if self.selected_id is None:
            messagebox.showinfo("Info", "Sélectionnez d'abord une facture dans le tableau.")
            return
        d = core.to_iso_date(self.paiement_reel_var.get().strip())
        if not d:
            messagebox.showwarning("Champ manquant", "Saisissez la date de paiement réel.")
            return
        core.update_facture(self.conn, self.selected_id, date_paiement_reel=d)
        self.paiement_reel_var.set("")
        self.refresh()

    def delete_facture(self):
        if self.selected_id is None:
            messagebox.showinfo("Info", "Sélectionnez d'abord une facture.")
            return
        if messagebox.askyesno("Confirmer", "Supprimer cette facture ?"):
            core.delete_facture(self.conn, self.selected_id)
            self.selected_id = None
            self.refresh()

    def refresh(self):
        self._refresh_client_values()
        for row in self.tree.get_children():
            self.tree.delete(row)
        for f in core.list_factures(self.conn):
            tags = ("depasse",) if f["depassement"] else ()
            self.tree.insert("", "end", tags=tags, values=(
                f["id"], f["raison_sociale"], f["piece"] or "", f["libelle"] or "",
                f"{f['montant']:,.2f}", core.to_display_date(f["date_facture"]),
                core.to_display_date(f["date_echeance_paiement"]), f["statut_paiement"],
            ))


class FacturesFrsTab(ttk.Frame):
    """Factures fournisseurs (achats) : présente directement une facture (entête,
    lignes d'achat liées à un compte 6x, retenue fiscale à la source paramétrable,
    pied de page), et sa validation envoie les écritures comptables en Saisie —
    avec entrée de stock automatique pour les lignes liées aux marchandises (31)
    ou matières premières (32)."""

    def __init__(self, parent, conn):
        super().__init__(parent)
        self.conn = conn
        self.current_facture_id = None

        top = ttk.Frame(self)
        top.pack(fill="x", padx=12, pady=8)
        ttk.Label(top, text="Facture n° :").pack(side="left")
        self.facture_combo = ttk.Combobox(top, width=40, state="readonly")
        self.facture_combo.pack(side="left", padx=4)
        self.facture_combo.bind("<<ComboboxSelected>>", self._on_facture_selected)
        ttk.Button(top, text="Nouvelle facture", command=self.new_facture).pack(side="left", padx=8)
        ttk.Button(top, text="Supprimer cette facture", command=self.delete_facture).pack(side="left", padx=2)
        self.statut_var = tk.StringVar()
        ttk.Label(top, textvariable=self.statut_var, font=("Segoe UI", 10, "bold")).pack(side="left", padx=16)

        ttk.Label(self, text="En-tête de la facture (modifiable) :").pack(anchor="w", padx=12)
        self.entete_text = tk.Text(self, height=3, font=("Segoe UI", 10))
        self.entete_text.pack(fill="x", padx=12, pady=(0, 8))

        info = ttk.Frame(self)
        info.pack(fill="x", padx=12, pady=4)
        ttk.Label(info, text="N° Facture :").grid(row=0, column=0, sticky="w", padx=4)
        self.numero_var = tk.StringVar()
        ttk.Entry(info, textvariable=self.numero_var, width=16).grid(row=0, column=1, padx=4)
        ttk.Label(info, text="Date (JJ/MM/AAAA) :").grid(row=0, column=2, sticky="w", padx=(12, 4))
        self.date_var = tk.StringVar(value=date.today().strftime("%d/%m/%Y"))
        ttk.Entry(info, textvariable=self.date_var, width=14).grid(row=0, column=3, padx=4)
        ttk.Label(info, text="Fournisseur (compte 40) :").grid(row=0, column=4, sticky="w", padx=(12, 4))
        self.fournisseur_var = tk.StringVar()
        self.fournisseur_combo = ttk.Combobox(info, textvariable=self.fournisseur_var, width=26)
        self.fournisseur_combo.grid(row=0, column=5, padx=4)
        self.fournisseur_combo.bind("<KeyRelease>", self._on_fournisseur_keyrelease)
        self._refresh_fournisseur_values()

        ttk.Label(info, text="Retenue % :").grid(row=1, column=0, sticky="w", padx=4, pady=(6, 0))
        self.retenue_taux_var = tk.StringVar(
            value=str(core.get_setting(conn, "retenue_taux_defaut", core.RETENUE_TAUX_DEFAUT)))
        ttk.Entry(info, textvariable=self.retenue_taux_var, width=6).grid(row=1, column=1, sticky="w", padx=4, pady=(6, 0))
        ttk.Label(info, text="Compte retenue (classe 44) :").grid(row=1, column=2, sticky="w", padx=(12, 4), pady=(6, 0))
        self.retenue_compte_var = tk.StringVar(
            value=core.get_text_setting(conn, "retenue_compte_defaut", core.COMPTE_RETENUE_DEFAUT))
        self.retenue_compte_combo = ttk.Combobox(info, textvariable=self.retenue_compte_var, width=30)
        self.retenue_compte_combo.grid(row=1, column=3, columnspan=2, sticky="w", padx=4, pady=(6, 0))
        self.retenue_compte_combo.bind("<KeyRelease>", self._on_retenue_compte_keyrelease)
        self._refresh_retenue_compte_values()

        form = ttk.LabelFrame(self, text="Ajouter une ligne (produit/service acheté — compte 6x)")
        form.pack(fill="x", padx=12, pady=6)
        ttk.Label(form, text="Compte d'achat :").grid(row=0, column=0, sticky="w", padx=4, pady=4)
        self.ligne_compte_var = tk.StringVar()
        self.ligne_compte_combo = ttk.Combobox(form, textvariable=self.ligne_compte_var, width=34)
        self.ligne_compte_combo.grid(row=0, column=1, padx=4)
        self.ligne_compte_combo.bind("<KeyRelease>", self._on_ligne_compte_keyrelease)
        self._refresh_ligne_compte_values()
        ttk.Label(form, text="Libellé :").grid(row=0, column=2, sticky="w", padx=(12, 4))
        self.ligne_libelle_var = tk.StringVar()
        ttk.Entry(form, textvariable=self.ligne_libelle_var, width=26).grid(row=0, column=3, padx=4)
        ttk.Label(form, text="Quantité :").grid(row=1, column=0, sticky="w", padx=4, pady=4)
        self.ligne_qte_var = tk.StringVar(value="1")
        ttk.Entry(form, textvariable=self.ligne_qte_var, width=10).grid(row=1, column=1, sticky="w", padx=4)
        ttk.Label(form, text="Prix unitaire :").grid(row=1, column=2, sticky="w", padx=(12, 4))
        self.ligne_prix_var = tk.StringVar()
        ttk.Entry(form, textvariable=self.ligne_prix_var, width=14).grid(row=1, column=3, sticky="w", padx=4)
        ttk.Button(form, text="Ajouter la ligne", command=self.add_ligne).grid(row=1, column=4, padx=12)

        cols = ("id", "compte", "libelle", "type_stock", "qte", "prix", "montant")
        self.tree = ttk.Treeview(self, columns=cols, show="headings", height=6)
        headers = ["ID", "Compte", "Libellé", "Impact stock", "Qté", "Prix unit.", "Montant HT"]
        widths = [40, 90, 220, 110, 70, 100, 110]
        for c, h, w in zip(cols, headers, widths):
            self.tree.heading(c, text=h)
            self.tree.column(c, width=w, anchor="w")
        self.tree.pack(fill="both", expand=True, padx=12, pady=6)
        ttk.Button(self, text="Supprimer la ligne sélectionnée", command=self.delete_ligne).pack(anchor="w", padx=12)

        self.totals_var = tk.StringVar()
        ttk.Label(self, textvariable=self.totals_var, font=("Segoe UI", 11, "bold")).pack(anchor="w", padx=12, pady=(8, 0))

        ttk.Label(self, text="Pied de page de la facture (modifiable) :").pack(anchor="w", padx=12, pady=(8, 0))
        self.pied_text = tk.Text(self, height=3, font=("Segoe UI", 10))
        self.pied_text.pack(fill="x", padx=12, pady=(0, 8))

        btns = ttk.Frame(self)
        btns.pack(fill="x", padx=12, pady=8)
        ttk.Button(btns, text="Enregistrer (brouillon)", command=self.save_facture).pack(side="left", padx=2)
        ttk.Button(btns, text="Valider et envoyer en Saisie", command=self.valider).pack(side="left", padx=2)

        self.refresh_factures_list()

    # -- Fournisseur --
    def _refresh_fournisseur_values(self):
        items = core.list_fournisseurs(self.conn)
        self.fournisseur_combo["values"] = [f"{f['code']} — {f['raison_sociale']}" for f in items]

    def _on_fournisseur_keyrelease(self, event=None):
        query = self._extract_code(self.fournisseur_var.get())
        if query:
            items = core.list_fournisseurs(self.conn, query)
            self.fournisseur_combo["values"] = [f"{f['code']} — {f['raison_sociale']}" for f in items]

    # -- Compte de retenue (classe 44) --
    def _refresh_retenue_compte_values(self):
        items = [a for a in core.search_accounts(self.conn, "44", limit=100) if core.account_racine(a["code"]) == "44"]
        self.retenue_compte_combo["values"] = [f"{a['code']} — {a['label']}" for a in items]

    def _on_retenue_compte_keyrelease(self, event=None):
        query = self._extract_code(self.retenue_compte_var.get())
        if query:
            items = [a for a in core.search_accounts(self.conn, query, limit=50)
                     if core.account_racine(a["code"]) == "44"]
            self.retenue_compte_combo["values"] = [f"{a['code']} — {a['label']}" for a in items]

    # -- Compte d'achat (classe 6) --
    def _refresh_ligne_compte_values(self):
        items = [a for a in core.search_accounts(self.conn, "6", limit=100) if a["classe"] == "6"]
        self.ligne_compte_combo["values"] = [f"{a['code']} — {a['label']}" for a in items]

    def _on_ligne_compte_keyrelease(self, event=None):
        query = self._extract_code(self.ligne_compte_var.get())
        if query:
            items = [a for a in core.search_accounts(self.conn, query, limit=50) if a["classe"] == "6"]
            self.ligne_compte_combo["values"] = [f"{a['code']} — {a['label']}" for a in items]

    @staticmethod
    def _extract_code(raw):
        raw = (raw or "").strip()
        return raw.split(" — ", 1)[0].strip() if " — " in raw else raw

    # -- Gestion des factures --
    def refresh_factures_list(self):
        factures = core.list_factures_achat(self.conn)
        values = [f"{f['numero']} — {f['raison_sociale']} — {f['statut']}" for f in factures]
        self.facture_combo["values"] = values
        self._factures_cache = factures
        if self.current_facture_id is None and factures:
            self.current_facture_id = factures[0]["id"]
            self.facture_combo.current(0)
        self.load_facture()

    def new_facture(self):
        numero = simpledialog.askstring("Nouvelle facture", "N° de facture :", parent=self)
        if not numero:
            return
        fournisseur_code = self._extract_code(self.fournisseur_var.get())
        if not fournisseur_code or not core.fournisseur_exists(self.conn, fournisseur_code):
            messagebox.showinfo("Fournisseur requis", "Choisissez d'abord un fournisseur existant dans le champ Fournisseur.")
            return
        date_str = core.to_iso_date(self.date_var.get().strip()) or date.today().strftime("%Y-%m-%d")
        try:
            retenue_taux = float(self.retenue_taux_var.get() or 0)
        except ValueError:
            retenue_taux = 0
        retenue_compte = self._extract_code(self.retenue_compte_var.get()) or core.COMPTE_RETENUE_DEFAUT
        fid = core.create_facture_achat(self.conn, numero, date_str, fournisseur_code,
                                         retenue_taux=retenue_taux, retenue_compte=retenue_compte)
        self.current_facture_id = fid
        self.refresh_factures_list()

    def _on_facture_selected(self, event=None):
        idx = self.facture_combo.current()
        if 0 <= idx < len(self._factures_cache):
            self.current_facture_id = self._factures_cache[idx]["id"]
        self.load_facture()

    def load_facture(self):
        for row in self.tree.get_children():
            self.tree.delete(row)
        self.entete_text.delete("1.0", "end")
        self.pied_text.delete("1.0", "end")
        if not self.current_facture_id:
            self.statut_var.set("Aucune facture — créez-en une nouvelle.")
            self.totals_var.set("")
            return
        f = core.get_facture_achat(self.conn, self.current_facture_id)
        if not f:
            self.current_facture_id = None
            self.statut_var.set("")
            return
        self.numero_var.set(f["numero"])
        self.date_var.set(core.to_display_date(f["date_facture"]))
        fournisseur = core.get_fournisseur(self.conn, f["fournisseur_code"])
        self.fournisseur_var.set(
            f"{f['fournisseur_code']} — {fournisseur['raison_sociale']}" if fournisseur else f["fournisseur_code"])
        self.retenue_taux_var.set(str(f["retenue_taux"]))
        self.retenue_compte_var.set(f["retenue_compte"])
        self.entete_text.insert("1.0", f["entete"] or "")
        self.pied_text.insert("1.0", f["pied_page"] or "")
        statut_label = "VALIDÉE (écritures envoyées en Saisie)" if f["statut"] == "validee" else "Brouillon"
        self.statut_var.set(f"Statut : {statut_label}")

        lignes = core.list_lignes_facture_achat(self.conn, self.current_facture_id)
        for l in lignes:
            impact = {"marchandise": "Stock marchandises (31)", "matiere_premiere": "Stock matières (32)"}.get(
                l["type_stock"], "Aucun (service)")
            self.tree.insert("", "end", values=(
                l["id"], l["compte_achat"], l["libelle"], impact,
                f"{l['quantite']:g}", f"{l['prix_unitaire']:,.2f}", f"{l['montant_ht']:,.2f}",
            ))
        totals = core.compute_facture_achat_totals(self.conn, self.current_facture_id)
        self.totals_var.set(
            f"TOTAL HT : {totals['total_ht']:,.2f}    Retenue ({totals['retenue_taux']:g}%) : "
            f"{totals['retenue_montant']:,.2f}    NET À PAYER : {totals['net_a_payer']:,.2f}"
        )

    def _ensure_facture(self):
        if not self.current_facture_id:
            messagebox.showinfo("Info", "Créez d'abord une nouvelle facture.")
            return None
        f = core.get_facture_achat(self.conn, self.current_facture_id)
        if f and f["statut"] == "validee":
            messagebox.showwarning("Facture validée", "Cette facture est déjà validée et ne peut plus être modifiée.")
            return None
        return f

    def add_ligne(self):
        f = self._ensure_facture()
        if not f:
            return
        compte = self._extract_code(self.ligne_compte_var.get())
        if not compte:
            messagebox.showwarning("Champ manquant", "Choisissez un compte d'achat (classe 6).")
            return
        if not core.account_exists(self.conn, compte) or core.account_racine(compte) != "6":
            messagebox.showerror("Compte invalide", "Le compte d'achat doit être un compte existant de la classe 6.")
            return
        libelle = self.ligne_libelle_var.get().strip()
        if not libelle:
            messagebox.showwarning("Champ manquant", "Le libellé de la ligne est obligatoire.")
            return
        try:
            qte = float(self.ligne_qte_var.get() or 0)
            prix = float(self.ligne_prix_var.get() or 0)
        except ValueError:
            messagebox.showerror("Erreur", "Quantité et Prix unitaire doivent être des nombres.")
            return
        core.add_ligne_facture_achat(self.conn, self.current_facture_id, compte, libelle, qte, prix)
        self.ligne_libelle_var.set("")
        self.ligne_qte_var.set("1")
        self.ligne_prix_var.set("")
        self.load_facture()

    def delete_ligne(self):
        f = self._ensure_facture()
        if not f:
            return
        sel = self.tree.selection()
        if not sel:
            messagebox.showinfo("Info", "Sélectionnez d'abord une ligne.")
            return
        ligne_id = int(self.tree.item(sel[0], "values")[0])
        core.delete_ligne_facture_achat(self.conn, ligne_id)
        self.load_facture()

    def save_facture(self):
        f = self._ensure_facture()
        if not f:
            return
        fournisseur_code = self._extract_code(self.fournisseur_var.get())
        if not fournisseur_code or not core.fournisseur_exists(self.conn, fournisseur_code):
            messagebox.showerror("Fournisseur invalide", "Choisissez un fournisseur existant.")
            return
        date_str = core.to_iso_date(self.date_var.get().strip())
        try:
            retenue_taux = float(self.retenue_taux_var.get() or 0)
        except ValueError:
            messagebox.showerror("Erreur", "Le taux de retenue doit être un nombre.")
            return
        retenue_compte = self._extract_code(self.retenue_compte_var.get()) or core.COMPTE_RETENUE_DEFAUT
        core.update_facture_achat(
            self.conn, self.current_facture_id,
            numero=self.numero_var.get().strip(), date_facture=date_str, fournisseur_code=fournisseur_code,
            entete=self.entete_text.get("1.0", "end").strip(),
            pied_page=self.pied_text.get("1.0", "end").strip(),
            retenue_taux=retenue_taux, retenue_compte=retenue_compte,
        )
        core.set_setting(self.conn, "retenue_taux_defaut", retenue_taux)
        core.set_setting(self.conn, "retenue_compte_defaut", retenue_compte)
        messagebox.showinfo("Enregistré", "Facture enregistrée (brouillon).")
        self.refresh_factures_list()

    def valider(self):
        f = self._ensure_facture()
        if not f:
            return
        self.save_facture()
        if messagebox.askyesno(
            "Confirmer la validation",
            "Valider cette facture ? Les écritures comptables seront envoyées dans le menu SAISIE "
            "(débit achats, crédit fournisseur, retenue à la source, et entrée de stock automatique "
            "pour les lignes marchandises/matières premières). Cette action est définitive."
        ):
            try:
                warnings = core.valider_facture_achat(self.conn, self.current_facture_id)
            except ValueError as exc:
                messagebox.showerror("Erreur", str(exc))
                return
            msg = "Facture validée et écritures envoyées en Saisie."
            if warnings:
                msg += "\n\nAvertissements :\n" + "\n".join(warnings)
            messagebox.showinfo("Validation terminée", msg)
            self.refresh_factures_list()

    def delete_facture(self):
        if not self.current_facture_id:
            return
        if messagebox.askyesno("Confirmer", "Supprimer cette facture ?"):
            try:
                core.delete_facture_achat(self.conn, self.current_facture_id)
            except ValueError as exc:
                messagebox.showerror("Erreur", str(exc))
                return
            self.current_facture_id = None
            self.refresh_factures_list()

    def refresh(self):
        self._refresh_fournisseur_values()
        self._refresh_ligne_compte_values()
        self._refresh_retenue_compte_values()
        self.refresh_factures_list()


class ContratsTab(ttk.Frame):
    """Journal des commandes/contrats fournisseurs : délais de paiement et de
    livraison, avec détection des dépassements."""

    def __init__(self, parent, conn):
        super().__init__(parent)
        self.conn = conn
        ttk.Label(self, text="CONTRATS FOURNISSEURS — SUIVI DES DÉLAIS",
                  font=("Segoe UI", 14, "bold")).pack(anchor="w", padx=16, pady=(16, 4))
        ttk.Label(self, text=(
            "Enregistrez ici chaque commande/contrat passé avec un fournisseur. Les échéances de "
            "livraison et de paiement sont calculées automatiquement à partir des délais par défaut "
            "du fournisseur (modifiables dans l'onglet Fournisseurs), à la date de commande. "
            "Renseignez ensuite les dates réelles de livraison/paiement au fur et à mesure — les "
            "dépassements sont signalés automatiquement."
        ), foreground="#595959", wraplength=1050).pack(anchor="w", padx=16, pady=(0, 8))

        form = ttk.LabelFrame(self, text="Nouvelle commande / contrat")
        form.pack(fill="x", padx=16, pady=4)
        ttk.Label(form, text="Fournisseur :").grid(row=0, column=0, sticky="w", padx=4, pady=4)
        self.fournisseur_var = tk.StringVar()
        self.fournisseur_combo = ttk.Combobox(form, textvariable=self.fournisseur_var, width=28)
        self.fournisseur_combo.grid(row=0, column=1, padx=4)
        self.fournisseur_combo.bind("<KeyRelease>", self._on_fournisseur_keyrelease)
        self._refresh_fournisseur_values()

        ttk.Label(form, text="N° Pièce :").grid(row=0, column=2, sticky="w", padx=(12, 4))
        self.piece_var = tk.StringVar()
        ttk.Entry(form, textvariable=self.piece_var, width=14).grid(row=0, column=3, padx=4)

        ttk.Label(form, text="Libellé :").grid(row=0, column=4, sticky="w", padx=(12, 4))
        self.libelle_var = tk.StringVar()
        ttk.Entry(form, textvariable=self.libelle_var, width=26).grid(row=0, column=5, padx=4)

        ttk.Label(form, text="Montant :").grid(row=1, column=0, sticky="w", padx=4, pady=4)
        self.montant_var = tk.StringVar()
        ttk.Entry(form, textvariable=self.montant_var, width=16).grid(row=1, column=1, padx=4)

        ttk.Label(form, text="Date commande (JJ/MM/AAAA) :").grid(row=1, column=2, sticky="w", padx=(12, 4))
        self.date_commande_var = tk.StringVar(value=date.today().strftime("%d/%m/%Y"))
        ttk.Entry(form, textvariable=self.date_commande_var, width=14).grid(row=1, column=3, padx=4)

        ttk.Button(form, text="Créer la commande (échéances auto)", command=self.add_commande).grid(
            row=1, column=4, columnspan=2, sticky="w", padx=12, pady=4)

        update_frame = ttk.LabelFrame(self, text="Mettre à jour la commande sélectionnée (dates réelles)")
        update_frame.pack(fill="x", padx=16, pady=(8, 4))
        ttk.Label(update_frame, text="Date livraison réelle (JJ/MM/AAAA) :").grid(row=0, column=0, sticky="w", padx=4, pady=4)
        self.livraison_reelle_var = tk.StringVar()
        ttk.Entry(update_frame, textvariable=self.livraison_reelle_var, width=14).grid(row=0, column=1, padx=4)
        ttk.Button(update_frame, text="Enregistrer la livraison", command=self.save_livraison).grid(
            row=0, column=2, padx=8)
        ttk.Label(update_frame, text="Date paiement réel (JJ/MM/AAAA) :").grid(row=0, column=3, sticky="w", padx=(20, 4))
        self.paiement_reel_var = tk.StringVar()
        ttk.Entry(update_frame, textvariable=self.paiement_reel_var, width=14).grid(row=0, column=4, padx=4)
        ttk.Button(update_frame, text="Enregistrer le paiement", command=self.save_paiement).grid(
            row=0, column=5, padx=8)
        ttk.Button(update_frame, text="Supprimer la commande sélectionnée", command=self.delete_commande).grid(
            row=0, column=6, padx=20)

        cols = ("id", "fournisseur", "piece", "libelle", "montant", "date_commande",
                "livraison_prevue", "statut_livraison", "echeance_paiement", "statut_paiement")
        self.tree = ttk.Treeview(self, columns=cols, show="headings")
        headers = ["ID", "Fournisseur", "Pièce", "Libellé", "Montant", "Date commande",
                   "Livraison prévue", "Statut livraison", "Échéance paiement", "Statut paiement"]
        widths = [40, 160, 80, 160, 100, 100, 100, 140, 110, 140]
        for c, h, w in zip(cols, headers, widths):
            self.tree.heading(c, text=h)
            self.tree.column(c, width=w, anchor="w")
        self.tree.tag_configure("depasse", foreground="#B00020")
        self.tree.pack(fill="both", expand=True, padx=16, pady=8)
        self.tree.bind("<<TreeviewSelect>>", self._on_select)
        self.selected_id = None
        self.refresh()

    def _refresh_fournisseur_values(self):
        items = core.list_fournisseurs(self.conn)
        self.fournisseur_combo["values"] = [f"{f['code']} — {f['raison_sociale']}" for f in items]

    def _on_fournisseur_keyrelease(self, event=None):
        query = self._extract_code(self.fournisseur_var.get())
        if query:
            items = core.list_fournisseurs(self.conn, query)
            self.fournisseur_combo["values"] = [f"{f['code']} — {f['raison_sociale']}" for f in items]

    @staticmethod
    def _extract_code(raw):
        raw = (raw or "").strip()
        return raw.split(" — ", 1)[0].strip() if " — " in raw else raw

    def _on_select(self, event=None):
        sel = self.tree.selection()
        if not sel:
            return
        values = self.tree.item(sel[0], "values")
        self.selected_id = int(values[0])

    def add_commande(self):
        code = self._extract_code(self.fournisseur_var.get())
        if not code:
            messagebox.showwarning("Champ manquant", "Choisissez un fournisseur.")
            return
        if not core.fournisseur_exists(self.conn, code):
            messagebox.showerror("Fournisseur invalide", f"Le fournisseur « {code} » n'existe pas. "
                                                           f"Créez-le d'abord dans l'onglet Fournisseurs.")
            return
        try:
            montant = float(self.montant_var.get() or 0)
        except ValueError:
            messagebox.showerror("Erreur", "Le montant doit être un nombre.")
            return
        date_commande = core.to_iso_date(self.date_commande_var.get().strip())
        if not date_commande:
            messagebox.showwarning("Champ manquant", "La date de commande est obligatoire.")
            return
        core.add_commande(self.conn, code, self.piece_var.get().strip(), self.libelle_var.get().strip(),
                           montant, date_commande)
        self.piece_var.set("")
        self.libelle_var.set("")
        self.montant_var.set("")
        self.refresh()

    def save_livraison(self):
        if self.selected_id is None:
            messagebox.showinfo("Info", "Sélectionnez d'abord une commande dans le tableau.")
            return
        d = core.to_iso_date(self.livraison_reelle_var.get().strip())
        if not d:
            messagebox.showwarning("Champ manquant", "Saisissez la date de livraison réelle.")
            return
        core.update_commande(self.conn, self.selected_id, date_livraison_reelle=d)
        self.livraison_reelle_var.set("")
        self.refresh()

    def save_paiement(self):
        if self.selected_id is None:
            messagebox.showinfo("Info", "Sélectionnez d'abord une commande dans le tableau.")
            return
        d = core.to_iso_date(self.paiement_reel_var.get().strip())
        if not d:
            messagebox.showwarning("Champ manquant", "Saisissez la date de paiement réel.")
            return
        core.update_commande(self.conn, self.selected_id, date_paiement_reel=d)
        self.paiement_reel_var.set("")
        self.refresh()

    def delete_commande(self):
        if self.selected_id is None:
            messagebox.showinfo("Info", "Sélectionnez d'abord une commande.")
            return
        if messagebox.askyesno("Confirmer", "Supprimer cette commande ?"):
            core.delete_commande(self.conn, self.selected_id)
            self.selected_id = None
            self.refresh()

    def refresh(self):
        self._refresh_fournisseur_values()
        for row in self.tree.get_children():
            self.tree.delete(row)
        for c in core.list_commandes(self.conn):
            tags = ("depasse",) if (c["depassement_livraison"] or c["depassement_paiement"]) else ()
            self.tree.insert("", "end", tags=tags, values=(
                c["id"], c["raison_sociale"], c["piece"] or "", c["libelle"] or "",
                f"{c['montant']:,.2f}", core.to_display_date(c["date_commande"]),
                core.to_display_date(c["date_livraison_prevue"]), c["statut_livraison"],
                core.to_display_date(c["date_echeance_paiement"]), c["statut_paiement"],
            ))


class ExercicesTab(ttk.Frame):
    """Liste des exercices comptables et clôture annuelle."""

    def __init__(self, parent, conn, app):
        super().__init__(parent)
        self.conn = conn
        self.app = app
        ttk.Label(self, text="EXERCICES COMPTABLES", font=("Segoe UI", 14, "bold")).pack(anchor="w", padx=16, pady=(16, 4))
        ttk.Label(self, text=(
            "La clôture calcule le solde de clôture de chaque compte de bilan (classes 1 à 5) de "
            "l'exercice sélectionné, l'intègre au résultat net dans le compte 121000 (Report à "
            "nouveau créditeur), et reporte le tout comme solde d'ouverture de l'exercice suivant. "
            "Un exercice clôturé passe en lecture seule : impossible d'y ajouter, modifier ou "
            "supprimer une écriture."
        ), foreground="#595959", wraplength=1000).pack(anchor="w", padx=16, pady=(0, 8))

        cols = ("exercice", "statut")
        self.tree = ttk.Treeview(self, columns=cols, show="headings", height=10)
        self.tree.heading("exercice", text="Exercice")
        self.tree.heading("statut", text="Statut")
        self.tree.column("exercice", width=100, anchor="w")
        self.tree.column("statut", width=150, anchor="w")
        self.tree.pack(fill="x", padx=16, pady=8)
        self.tree.bind("<<TreeviewSelect>>", self._on_select)

        self.selected_exercice = None
        btns = ttk.Frame(self)
        btns.pack(fill="x", padx=16, pady=4)
        ttk.Button(btns, text="Basculer sur cet exercice", command=self._switch).pack(side="left", padx=2)
        ttk.Button(btns, text="Clôturer l'exercice sélectionné", command=self._close).pack(side="left", padx=2)

        self.refresh()

    def _on_select(self, event=None):
        sel = self.tree.selection()
        if sel:
            self.selected_exercice = self.tree.item(sel[0], "values")[0]

    def _switch(self):
        if not self.selected_exercice:
            messagebox.showinfo("Info", "Sélectionnez d'abord un exercice.")
            return
        core.set_current_exercice(self.conn, self.selected_exercice)
        self.app._refresh_exercice_list()
        self.app.refresh_current_page()

    def _close(self):
        if not self.selected_exercice:
            messagebox.showinfo("Info", "Sélectionnez d'abord un exercice.")
            return
        ex = self.selected_exercice
        if core.is_exercice_cloture(self.conn, ex):
            messagebox.showinfo("Info", f"L'exercice {ex} est déjà clôturé.")
            return
        bilan = core.compute_bilan(self.conn, exercice=ex)
        if abs(bilan["ecart"]) >= 1:
            if not messagebox.askyesno(
                "Bilan non équilibré",
                f"Le Bilan de l'exercice {ex} n'est pas équilibré (écart de {bilan['ecart']:,.2f}). "
                f"Clôturer quand même ?"
            ):
                return
        resultat_net = bilan['passif']["Résultat net de l'exercice"]
        if not messagebox.askyesno(
            "Confirmer la clôture",
            f"Clôturer définitivement l'exercice {ex} ?\n\n"
            f"Résultat net : {resultat_net:,.2f}\n"
            f"Cette action reporte les soldes de clôture comme soldes d'ouverture de l'exercice "
            f"suivant et verrouille l'exercice {ex} en lecture seule."
        ):
            return
        try:
            next_ex = core.close_exercice(self.conn, ex)
        except ValueError as exc:
            messagebox.showerror("Erreur", str(exc))
            return
        messagebox.showinfo("Clôture effectuée",
                             f"Exercice {ex} clôturé. Les soldes d'ouverture de {next_ex} ont été calculés.")
        core.set_current_exercice(self.conn, next_ex)
        self.app._refresh_exercice_list()
        self.app.refresh_current_page()
        self.refresh()

    def refresh(self):
        for row in self.tree.get_children():
            self.tree.delete(row)
        for e in core.list_exercices(self.conn):
            statut = "Clôturé" if e["cloture"] else "Ouvert"
            self.tree.insert("", "end", values=(e["exercice"], statut))


class PlanComptableTab(ttk.Frame):
    """Créer / modifier / supprimer des comptes du Plan comptable."""

    def __init__(self, parent, conn):
        super().__init__(parent)
        self.conn = conn
        ttk.Label(self, text="PLAN COMPTABLE", font=("Segoe UI", 14, "bold")).pack(anchor="w", padx=16, pady=(16, 4))
        ttk.Label(self, text=(
            "Chaque compte est rattaché à une racine : 1 chiffre pour les classes 1, 2, 3, 5, 6, 7, 8, 9 ; "
            "2 chiffres pour la classe 4 (comptes de tiers), qui se subdivise en 40 (Fournisseurs), "
            "41 (Clients), 42 (Personnel), 43 (Organismes sociaux), 44 (État), 45 (Organismes "
            "internationaux), 46 (Associés/Groupe), 47 (Débiteurs/créditeurs divers), 48 "
            "(Régularisations), 49 (Dépréciations sur tiers). Les fiches auxiliaires créées dans "
            "l'onglet Fournisseurs sont rattachées à la racine 40, celles de l'onglet Clients à la "
            "racine 41 — c'est ce qui permet au Bilan de classer correctement les créances et les dettes."
        ), foreground="#595959", wraplength=1050).pack(anchor="w", padx=16, pady=(0, 8))

        search_bar = ttk.Frame(self)
        search_bar.pack(fill="x", padx=16, pady=4)
        ttk.Label(search_bar, text="Rechercher (code ou libellé) :").pack(side="left")
        self.search_var = tk.StringVar()
        search_entry = ttk.Entry(search_bar, textvariable=self.search_var, width=30)
        search_entry.pack(side="left", padx=6)
        search_entry.bind("<KeyRelease>", lambda e: self.refresh())

        import_bar = ttk.Frame(self)
        import_bar.pack(fill="x", padx=16, pady=4)
        ttk.Button(import_bar, text="Importer un plan (.xlsx) — ÉCRASE le plan actuel",
                   command=self.import_xlsx).pack(side="left", padx=2)
        ttk.Button(import_bar, text="Exporter le plan actuel (.xlsx)", command=self.export_xlsx).pack(side="left", padx=2)

        form = ttk.Frame(self)
        form.pack(fill="x", padx=16, pady=6)
        ttk.Label(form, text="N° Compte :").grid(row=0, column=0, sticky="w")
        self.code_var = tk.StringVar()
        ttk.Entry(form, textvariable=self.code_var, width=16).grid(row=0, column=1, padx=6)
        ttk.Label(form, text="Libellé :").grid(row=0, column=2, sticky="w", padx=(16, 0))
        self.label_var = tk.StringVar()
        ttk.Entry(form, textvariable=self.label_var, width=45).grid(row=0, column=3, padx=6)
        ttk.Button(form, text="Créer / Modifier", command=self.save).grid(row=0, column=4, padx=6)
        ttk.Button(form, text="Supprimer le compte sélectionné", command=self.delete).grid(row=0, column=5, padx=6)

        cols = ("code", "label", "classe", "racine", "racine_label")
        self.tree = ttk.Treeview(self, columns=cols, show="headings")
        headers = ["N° Compte", "Libellé", "Classe", "Racine", "Libellé de la racine"]
        widths = [100, 420, 60, 70, 260]
        for c, h, w in zip(cols, headers, widths):
            self.tree.heading(c, text=h)
            self.tree.column(c, width=w, anchor="w")
        self.tree.pack(fill="both", expand=True, padx=16, pady=8)
        self.tree.bind("<<TreeviewSelect>>", self._on_select)
        self.refresh()

    def _on_select(self, event=None):
        sel = self.tree.selection()
        if not sel:
            return
        values = self.tree.item(sel[0], "values")
        self.code_var.set(values[0])
        self.label_var.set(values[1])

    def save(self):
        code = self.code_var.get().strip()
        label = self.label_var.get().strip()
        if not code or not label:
            messagebox.showwarning("Champs manquants", "N° Compte et Libellé sont obligatoires.")
            return
        core.add_account(self.conn, code, label)
        self.refresh()

    def delete(self):
        code = self.code_var.get().strip()
        if not code:
            messagebox.showinfo("Info", "Sélectionnez d'abord un compte.")
            return
        if messagebox.askyesno("Confirmer", f"Supprimer le compte {code} ?"):
            core.delete_account(self.conn, code)
            self.code_var.set("")
            self.label_var.set("")
            self.refresh()

    def refresh(self):
        for row in self.tree.get_children():
            self.tree.delete(row)
        for a in core.search_accounts(self.conn, self.search_var.get(), limit=200):
            racine = core.account_racine(a["code"])
            racine_label = core.RACINE_LABELS.get(racine, "")
            self.tree.insert("", "end", values=(a["code"], a["label"], a["classe"], racine, racine_label))

    def export_xlsx(self):
        path = filedialog.asksaveasfilename(
            defaultextension=".xlsx", filetypes=[("Classeur Excel", "*.xlsx")],
            initialfile="Plan_comptable.xlsx", title="Exporter le Plan comptable",
        )
        if not path:
            return
        core.export_plan_comptable_xlsx(self.conn, path)
        messagebox.showinfo("Export terminé", f"Plan comptable exporté :\n{path}")

    def import_xlsx(self):
        path = filedialog.askopenfilename(filetypes=[("Classeur Excel", "*.xlsx")],
                                           title="Importer un Plan comptable")
        if not path:
            return
        if not messagebox.askyesno(
            "Confirmer l'écrasement",
            "Importer ce fichier va ÉCRASER complètement le Plan comptable actuel (tous les comptes "
            "existants seront supprimés et remplacés par ceux du fichier). Cette action est "
            "irréversible. Continuer ?"
        ):
            return
        try:
            n = core.import_plan_comptable_xlsx(self.conn, path)
        except Exception as exc:
            messagebox.showerror("Erreur", f"Échec de l'import : {exc}")
            return
        self.refresh()
        messagebox.showinfo("Import terminé", f"{n} compte(s) importé(s). Le plan précédent a été remplacé.")


class _SimplePlanTab(ttk.Frame):
    """Base pour les plans Code + Libellé (analytique, bailleurs)."""
    TITLE = ""
    CODE_LABEL = "Code"

    def list_fn(self, conn):
        raise NotImplementedError

    def add_fn(self, conn, code, label):
        raise NotImplementedError

    def delete_fn(self, conn, code):
        raise NotImplementedError

    def export_fn(self, conn, path):
        raise NotImplementedError

    def import_fn(self, conn, path):
        raise NotImplementedError

    def __init__(self, parent, conn):
        super().__init__(parent)
        self.conn = conn
        ttk.Label(self, text=self.TITLE, font=("Segoe UI", 14, "bold")).pack(anchor="w", padx=16, pady=(16, 4))

        import_bar = ttk.Frame(self)
        import_bar.pack(fill="x", padx=16, pady=(0, 4))
        ttk.Button(import_bar, text="Importer (.xlsx) — ÉCRASE le plan actuel",
                   command=self.import_xlsx).pack(side="left", padx=2)
        ttk.Button(import_bar, text="Exporter (.xlsx)", command=self.export_xlsx).pack(side="left", padx=2)

        form = ttk.Frame(self)
        form.pack(fill="x", padx=16, pady=6)
        ttk.Label(form, text=self.CODE_LABEL + " :").grid(row=0, column=0, sticky="w")
        self.code_var = tk.StringVar()
        ttk.Entry(form, textvariable=self.code_var, width=20).grid(row=0, column=1, padx=6)
        ttk.Label(form, text="Libellé :").grid(row=0, column=2, sticky="w", padx=(16, 0))
        self.label_var = tk.StringVar()
        ttk.Entry(form, textvariable=self.label_var, width=45).grid(row=0, column=3, padx=6)
        ttk.Button(form, text="Créer / Modifier", command=self.save).grid(row=0, column=4, padx=6)
        ttk.Button(form, text="Supprimer", command=self.delete).grid(row=0, column=5, padx=6)

        cols = ("code", "label")
        self.tree = ttk.Treeview(self, columns=cols, show="headings")
        for c, h, w in zip(cols, [self.CODE_LABEL, "Libellé"], [140, 500]):
            self.tree.heading(c, text=h)
            self.tree.column(c, width=w, anchor="w")
        self.tree.pack(fill="both", expand=True, padx=16, pady=8)
        self.tree.bind("<<TreeviewSelect>>", self._on_select)
        self.refresh()

    def _on_select(self, event=None):
        sel = self.tree.selection()
        if not sel:
            return
        values = self.tree.item(sel[0], "values")
        self.code_var.set(values[0])
        self.label_var.set(values[1])

    def save(self):
        code = self.code_var.get().strip()
        label = self.label_var.get().strip()
        if not code or not label:
            messagebox.showwarning("Champs manquants", f"{self.CODE_LABEL} et Libellé sont obligatoires.")
            return
        self.add_fn(self.conn, code, label)
        self.refresh()

    def delete(self):
        code = self.code_var.get().strip()
        if not code:
            messagebox.showinfo("Info", "Sélectionnez d'abord une ligne.")
            return
        if messagebox.askyesno("Confirmer", f"Supprimer « {code} » ?"):
            self.delete_fn(self.conn, code)
            self.code_var.set("")
            self.label_var.set("")
            self.refresh()

    def refresh(self):
        for row in self.tree.get_children():
            self.tree.delete(row)
        for item in self.list_fn(self.conn):
            self.tree.insert("", "end", values=(item["code"], item["label"]))

    def export_xlsx(self):
        path = filedialog.asksaveasfilename(
            defaultextension=".xlsx", filetypes=[("Classeur Excel", "*.xlsx")],
            initialfile=f"{self.TITLE.title().replace(' ', '_')}.xlsx", title=f"Exporter {self.TITLE}",
        )
        if not path:
            return
        self.export_fn(self.conn, path)
        messagebox.showinfo("Export terminé", f"Plan exporté :\n{path}")

    def import_xlsx(self):
        path = filedialog.askopenfilename(filetypes=[("Classeur Excel", "*.xlsx")],
                                           title=f"Importer {self.TITLE}")
        if not path:
            return
        if not messagebox.askyesno(
            "Confirmer l'écrasement",
            f"Importer ce fichier va ÉCRASER complètement le {self.TITLE.lower()} actuel. "
            f"Cette action est irréversible. Continuer ?"
        ):
            return
        try:
            n = self.import_fn(self.conn, path)
        except Exception as exc:
            messagebox.showerror("Erreur", f"Échec de l'import : {exc}")
            return
        self.refresh()
        messagebox.showinfo("Import terminé", f"{n} ligne(s) importée(s). Le plan précédent a été remplacé.")


class PlanAnalytiqueTab(_SimplePlanTab):
    TITLE = "PLAN ANALYTIQUE"
    CODE_LABEL = "Code analytique"

    def list_fn(self, conn):
        return core.list_analytic_codes(conn)

    def add_fn(self, conn, code, label):
        core.add_analytic_code(conn, code, label)

    def delete_fn(self, conn, code):
        core.delete_analytic_code(conn, code)

    def export_fn(self, conn, path):
        core.export_analytic_codes_xlsx(conn, path)

    def import_fn(self, conn, path):
        return core.import_analytic_codes_xlsx(conn, path)


class PlanBailleurTab(_SimplePlanTab):
    TITLE = "PLAN BAILLEURS DE FONDS"
    CODE_LABEL = "Code bailleur"

    def list_fn(self, conn):
        return core.list_donor_codes(conn)

    def add_fn(self, conn, code, label):
        core.add_donor_code(conn, code, label)

    def delete_fn(self, conn, code):
        core.delete_donor_code(conn, code)

    def export_fn(self, conn, path):
        core.export_donor_codes_xlsx(conn, path)

    def import_fn(self, conn, path):
        return core.import_donor_codes_xlsx(conn, path)


class PlanBudgetaireTab(ttk.Frame):
    """Plan budgétaire : Code + Libellé + Montant prévu."""

    def __init__(self, parent, conn):
        super().__init__(parent)
        self.conn = conn
        ttk.Label(self, text="PLAN BUDGÉTAIRE", font=("Segoe UI", 14, "bold")).pack(anchor="w", padx=16, pady=(16, 4))

        import_bar = ttk.Frame(self)
        import_bar.pack(fill="x", padx=16, pady=(0, 4))
        ttk.Button(import_bar, text="Importer (.xlsx) — ÉCRASE le plan actuel",
                   command=self.import_xlsx).pack(side="left", padx=2)
        ttk.Button(import_bar, text="Exporter (.xlsx)", command=self.export_xlsx).pack(side="left", padx=2)

        form = ttk.Frame(self)
        form.pack(fill="x", padx=16, pady=6)
        ttk.Label(form, text="Code budgétaire :").grid(row=0, column=0, sticky="w")
        self.code_var = tk.StringVar()
        ttk.Entry(form, textvariable=self.code_var, width=16).grid(row=0, column=1, padx=6)
        ttk.Label(form, text="Libellé :").grid(row=0, column=2, sticky="w", padx=(16, 0))
        self.label_var = tk.StringVar()
        ttk.Entry(form, textvariable=self.label_var, width=35).grid(row=0, column=3, padx=6)
        ttk.Label(form, text="Montant prévu :").grid(row=0, column=4, sticky="w", padx=(16, 0))
        self.montant_var = tk.StringVar()
        ttk.Entry(form, textvariable=self.montant_var, width=16).grid(row=0, column=5, padx=6)
        ttk.Button(form, text="Créer / Modifier", command=self.save).grid(row=0, column=6, padx=6)
        ttk.Button(form, text="Supprimer", command=self.delete).grid(row=0, column=7, padx=6)

        cols = ("code", "label", "montant")
        self.tree = ttk.Treeview(self, columns=cols, show="headings")
        for c, h, w in zip(cols, ["Code budgétaire", "Libellé", "Montant prévu"], [120, 400, 130]):
            self.tree.heading(c, text=h)
            self.tree.column(c, width=w, anchor="w")
        self.tree.pack(fill="both", expand=True, padx=16, pady=8)
        self.tree.bind("<<TreeviewSelect>>", self._on_select)
        self.refresh()

    def _on_select(self, event=None):
        sel = self.tree.selection()
        if not sel:
            return
        values = self.tree.item(sel[0], "values")
        self.code_var.set(values[0])
        self.label_var.set(values[1])
        self.montant_var.set(values[2])

    def save(self):
        code = self.code_var.get().strip()
        label = self.label_var.get().strip()
        try:
            montant = float(self.montant_var.get() or 0)
        except ValueError:
            messagebox.showerror("Erreur", "Le montant prévu doit être un nombre.")
            return
        if not code or not label:
            messagebox.showwarning("Champs manquants", "Code budgétaire et Libellé sont obligatoires.")
            return
        core.add_budget_code(self.conn, code, label, montant)
        self.refresh()

    def delete(self):
        code = self.code_var.get().strip()
        if not code:
            messagebox.showinfo("Info", "Sélectionnez d'abord une ligne.")
            return
        if messagebox.askyesno("Confirmer", f"Supprimer « {code} » ?"):
            core.delete_budget_code(self.conn, code)
            self.code_var.set("")
            self.label_var.set("")
            self.montant_var.set("")
            self.refresh()

    def refresh(self):
        for row in self.tree.get_children():
            self.tree.delete(row)
        for item in core.list_budget_codes(self.conn):
            self.tree.insert("", "end", values=(item["code"], item["label"], f"{item['montant']:,.2f}"))

    def export_xlsx(self):
        path = filedialog.asksaveasfilename(
            defaultextension=".xlsx", filetypes=[("Classeur Excel", "*.xlsx")],
            initialfile="Plan_budgetaire.xlsx", title="Exporter le Plan budgétaire",
        )
        if not path:
            return
        core.export_budget_codes_xlsx(self.conn, path)
        messagebox.showinfo("Export terminé", f"Plan budgétaire exporté :\n{path}")

    def import_xlsx(self):
        path = filedialog.askopenfilename(filetypes=[("Classeur Excel", "*.xlsx")],
                                           title="Importer un Plan budgétaire")
        if not path:
            return
        if not messagebox.askyesno(
            "Confirmer l'écrasement",
            "Importer ce fichier va ÉCRASER complètement le Plan budgétaire actuel. "
            "Cette action est irréversible. Continuer ?"
        ):
            return
        try:
            n = core.import_budget_codes_xlsx(self.conn, path)
        except Exception as exc:
            messagebox.showerror("Erreur", f"Échec de l'import : {exc}")
            return
        self.refresh()
        messagebox.showinfo("Import terminé", f"{n} ligne(s) importée(s). Le plan précédent a été remplacé.")


if __name__ == "__main__":
    App().mainloop()
