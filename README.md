# Saisie Comptable SYSCOHADA — application Windows autonome

## 🔄 RÉSUMÉ DE REPRISE (à lire en premier par toute nouvelle conversation Claude)

**Contexte** : application de comptabilité SYSCOHADA développée sur
plusieurs longues sessions avec Claude. Le code est **volumineux et déjà
très abouti** (`core.py` ~180 Ko, `main.py` ~210 Ko) — avant toute
modification, lis intégralement les fichiers concernés plutôt que de les
régénérer ou de les réécrire à partir d'une supposition. Une réécriture
depuis zéro **casserait** des dizaines de fonctionnalités déjà construites
et testées.

**Dépôt GitHub** : build automatique via GitHub Actions (le `.exe` ne peut
pas être compilé directement par Claude, environnement Linux). Voir section
suivante pour le processus de mise à jour.

**Ce qui existe déjà (ne pas reconstruire, juste modifier/étendre)** :
- Menu à 6 entrées : SAISIE, COMMERCE, PRODUCTION, ENGAGEMENTS-PROJETS,
  ÉTATS ET RAPPORTS, PARAMÈTRES (navigation par menu déroulant, pas
  d'onglets classiques — voir `class App` dans `main.py`)
- **Saisie** : partie double forcée (Compte débiteur + Compte créditeur
  obligatoires ensemble), validation des comptes/tiers en temps réel,
  liste déroulante automatique au clic, sélection multiple + Ctrl+A +
  suppression groupée (transaction unique, pas de commit par ligne)
- **Exercices comptables** : multi-exercices avec clôture annuelle
  (report des soldes + résultat net vers le compte 121000), verrouillage
  des exercices clôturés
- **Plan comptable** : 1591 comptes (import Sage), comptes racines
  (1 chiffre, ou 40-49 pour la classe 4), rattachement obligatoire des
  écritures 40xxx/41xxx à un fournisseur/client
- **Commerce** : Ventes, Clients, Recouvrement, Facturation (avec sortie de
  stock automatique et TVA), Stocks, Marges
- **Engagements-projets** : Achats, Fournisseurs, Factures frs (entrée de
  stock automatique + retenue à la source), Contrats
- **Production** : Fabrication avec nomenclature (BOM), coût de production,
  validation qui décrémente les matières et valorise le produit fini
- **États et rapports** : Grand livre complet (tous comptes, bandes de
  couleur), Balance (sous-totaux par classe), **Bilan « avec détails »**
  (Actif gauche en Brut/Amortissements/Net, Passif droite en Montant,
  détail compte par compte — immobilisations, stocks, créances, dettes,
  trésorerie banque par banque —, toujours équilibré par construction,
  exportable en .xlsx ; voir section « Bilan « avec détails » » plus bas),
  Compte de résultat (SIG), TFT (méthode indirecte CAFG), Situation
  financière (FR-BFR-TN), Liasse fiscale (export 92 pages, cohérente avec
  tous les écrans ci-dessus)
- **Paramètres** : gestion des 4 plans (comptable/analytique/budgétaire/
  bailleurs) avec import/export xlsx (écrase à l'import)

**Pièges déjà rencontrés (pour ne pas les refaire)** :
- Les f-strings avec apostrophe échappée (`f"{'d\\'accord'}"`) plantent en
  Python < 3.12 — toujours extraire la chaîne dans une variable avant.
- Toujours utiliser `account_racine()`/préfixes (pas le code exact à 6
  chiffres) pour agréger des comptes — le vrai plan comptable de
  l'utilisateur est plein de sous-comptes détaillés (602101, 521120...).
- Chaque `conn.commit()` coûte cher en boucle — grouper en une transaction
  pour les opérations multiples.
- Toujours tester avec `python3 -m py_compile` et un scénario réel
  (`core.get_connection('t.db')` puis nettoyer) avant de livrer.
- Vérifier la cohérence Balance ↔ Bilan ↔ TFT ↔ Situation financière ↔
  Liasse fiscale : ils partagent tous `compute_balance()` **et, depuis la
  correction de l'équilibre du Bilan, le même `compute_resultat_net_complet()`
  pour le résultat net.**
- **Ne jamais calculer un total de Bilan (résultat net, capitaux propres,
  stocks...) à partir d'une liste de comptes codée en dur** (ex.
  `COMPTES_CAPITAL = ["101","118","121"]`) : le vrai plan comptable de
  l'utilisateur (1591 comptes Sage) contient forcément des comptes hors de
  toute liste pré-définie, qui disparaîtraient alors silencieusement du
  Total Actif/Passif et casseraient l'équilibre. Pour un TOTAL, toujours
  sommer la classe entière (`_sum_class(balance, "1")` etc.) ; les listes de
  comptes codées en dur ne sont acceptables que pour un DÉTAIL affiché à
  titre indicatif, avec une ligne « Autres » qui absorbe le reliquat pour
  que le détail somme exactement au vrai total.

**Ce qui reste à construire/imparfait** : Contrats (module vide),
Tableaux d'exécution budgétaire, Impôts, Déclarations sociales,
Rapprochements bancaires (tous encore des placeholders) ; les lignes
d'investissement/financement de la vraie feuille TFT officielle dans la
Liasse fiscale (seules ZA/FA-FE sont mappées, positions FF+ à confirmer).

**Les données réelles de l'utilisateur (`comptabilite.db`) ne sont PAS ici**
— uniquement sur son PC Windows local
(`%LOCALAPPDATA%\SaisieComptable\`). Ne jamais supposer leur contenu.

---

Application de bureau (Tkinter) qui reproduit les fonctions essentielles
du classeur Excel : Saisie des écritures, Balance, Compte de résultat et
Bilan, calculés automatiquement. Aucune installation d'Excel n'est requise :
une fois compilée, c'est un simple `.exe`.

Le plan comptable intégré (`plan_comptable.json`) est celui importé depuis
votre export Sage (1591 comptes).

## Important : je ne peux pas produire le .exe moi-même

Un `.exe` est un binaire Windows. Je travaille dans un environnement Linux
qui ne peut pas compiler de binaire Windows. La solution ci-dessous utilise
**GitHub Actions** : GitHub compile lui-même le `.exe` sur une machine
Windows à chaque fois que vous poussez du code — c'est la manière standard
et fiable de faire, sans avoir besoin d'un PC Windows.

## Mise en ligne sur GitHub (une seule fois)

```bash
cd accounting-app
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin https://github.com/VOTRE-COMPTE/VOTRE-DEPOT.git
git push -u origin main
```

## Récupérer le .exe

1. Sur GitHub, ouvrez l'onglet **Actions** de votre dépôt : le workflow
   « Build Windows .exe » se déclenche automatiquement à chaque push sur
   `main` (ou lancez-le manuellement via **Run workflow**).
2. Une fois le job terminé (~2-3 minutes), ouvrez son résumé et téléchargez
   l'artifact **SaisieComptable-windows** : il contient `SaisieComptable.exe`.
3. Pour publier une **Release** téléchargeable en un clic (recommandé pour
   partager l'app), créez un tag :
   ```bash
   git tag v1.0
   git push origin v1.0
   ```
   Le `.exe` sera automatiquement attaché à la Release correspondante.

## Utilisation de l'application

- **Saisie** : formulaire d'ajout/modification/suppression d'écritures
  (Date, Pièce, Journal, Compte, Tiers, Libellé, Débit, Crédit, Code flux,
  Code analytique). Le champ **N° Compte** est une liste déroulante avec
  recherche : tapez un numéro ou un mot du libellé (ex. `clients`, `601`,
  `banque`) et choisissez le compte dans la liste qui s'affiche. Le
  **Journal** propose AC/VE/OD/BQ/CA (modifiable librement), et le
  **Code flux** est une liste fermée EXP/INV/FIN pour éviter les fautes de
  frappe. Le libellé du compte s'affiche automatiquement pendant la saisie.

  **Import massif (.xlsx)** *(nouveau)* : pour les volumes d'écritures
  importants, deux boutons sont disponibles au-dessus du tableau :
  - **« Télécharger un modèle (.xlsx) »** : génère un fichier vierge avec
    les bons en-têtes (Date, N° Pièce, Journal, N° Compte, Tiers, Libellé,
    Débit, Crédit, Code flux, Code analytique) et deux lignes d'exemple.
  - **« Importer des écritures (.xlsx) »** : sélectionnez votre fichier
    préparé (l'ordre des colonnes n'a pas d'importance, les en-têtes sont
    reconnus automatiquement) — toutes les lignes sont ajoutées à la
    Saisie en une fois. Les dates peuvent être au format texte (AAAA-MM-JJ)
    ou en dates Excel natives. Les lignes vides sont ignorées ; un compte
    absent du plan comptable ou un montant non numérique déclenche un
    avertissement (la ligne est quand même importée, avec le montant
    invalide remplacé par 0) plutôt que de faire échouer tout l'import.
- **Balance** : synthèse Débit/Crédit/Solde par compte, actualisée à la volée.
- **Compte de résultat** et **Bilan** : calculés automatiquement selon la
  même logique que le classeur Excel (mêmes regroupements de comptes).

Les données sont stockées localement dans :
`%LOCALAPPDATA%\SaisieComptable\comptabilite.db` (SQLite). Elles persistent
d'un lancement à l'autre de l'application.

## Développer / tester en local (optionnel)

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

## Navigation

L'application n'a plus d'onglets classiques : la navigation se fait
entièrement via **la barre de menu** en haut de la fenêtre, avec 5 menus
principaux (en gras) :

- **SAISIE** : Saisie des écritures, Soldes d'ouverture.
- **COMMERCE** : Ventes, Clients, Recouvrement, Facturation, Stocks, Marges bénéficiaires.

### Correction majeure : reconnaissance des sous-comptes détaillés (important)

**Bug signalé et corrigé** : un achat de matières premières saisi directement
dans l'onglet Saisie sur un **sous-compte détaillé** (ex. `602101 ACHAT
CLINKER`, au lieu du compte maître `602000`) ne mettait pas le stock à jour,
et — plus grave — **faussait le calcul du Résultat et du Bilan** (écart non
nul), car les comptes de résultat/trésorerie/capitaux propres n'étaient
reconnus que sur leur code exact à 6 chiffres.

**Deux corrections apportées :**
1. **Mise à jour automatique du stock désormais aussi en Saisie directe** :
   dès qu'une écriture équilibrée (Compte débiteur/Compte créditeur) touche
   un compte d'achat (601x/602x) ou de vente (701x/702x) lié à un stock,
   **avec une quantité renseignée**, l'entrée ou la sortie de stock
   correspondante est automatiquement comptabilisée — plus besoin de passer
   par Facturation/Factures frs pour que le stock se mette à jour. Ces
   écritures apparaissent dans l'onglet Stocks → Mouvements comptables sous
   l'origine **« Saisie directe (auto) »**.
2. **Rattachement par racine/préfixe (3 chiffres) partout** : tous les
   calculs qui agrègent des comptes (Résultat, Bilan, Trésorerie, Production)
   reconnaissent désormais **tous les sous-comptes** d'une racine donnée
   (ex. 602101, 602102... sont bien rattachés à 602 ; 521100, 521120...
   sont bien rattachés à 521), et pas seulement le compte maître à 6 chiffres
   se terminant par des zéros.

Testé : le scénario exact du bug (achat de 4 500 000 sur le compte 602101,
quantité 100) met maintenant bien à jour le stock matières premières
(4 500 000 / 100 unités) **et** le Bilan reste parfaitement équilibré (écart
= 0) — vérifié aussi après un cycle complet de clôture d'exercice et dans
l'export de la Liasse fiscale.

### Onglet Stocks — mouvements comptables détaillés (nouveau)

L'onglet **Stocks** (menu COMMERCE, aussi accessible depuis PRODUCTION →
Matières premières/Produits finis) a maintenant deux sous-onglets :
- **« Synthèse par compte »** : le tableau existant (stock initial, entrées,
  sorties, stock final, coût unitaire moyen).
- **« Mouvements comptables (classe 3) »** *(nouveau)* : le détail
  chronologique de **toutes** les écritures sur les comptes de stock
  (310000, 320000, 331000, 360000) de l'exercice en cours, avec un filtre
  par origine :
  - **Facturation** : sorties de stock générées automatiquement par la
    validation d'une facture de vente.
  - **Facture frs** : entrées de stock générées automatiquement par la
    validation d'une facture d'achat.
  - **Saisie manuelle** : toute écriture sur un compte de stock passée
    directement dans l'onglet Saisie.

  Chaque ligne affiche à la fois le **mouvement** (Débit/Crédit en valeur,
  Qté mvt) et le **cumul** après ce mouvement (**Qté cumulée** et **Valeur
  cumulée**), en partant du stock initial de l'exercice — comme une vraie
  fiche de stock. Les lignes générées automatiquement sont affichées en
  bleu. Testé : une facture d'achat (+20 unités) puis une vente (-10
  unités) sur un stock initial de 100 unités / 300 000 donnent bien un
  cumul de 120 puis 110 unités, avec la valeur qui suit correctement.

### Module Facturation (nouveau)

L'onglet **Facturation** présente directement une facture éditable :
- **En-tête modifiable** et **pied de page modifiable** (texte libre).
- **N° Facture**, **Date**, **Client** (obligatoirement rattaché à un compte
  racine 41, avec la même recherche/validation que dans le reste de l'app).
- **Taux de TVA paramétrable** (compte 44 — 443100 « T.V.A. facturée sur
  ventes »), avec une valeur par défaut mémorisée d'une facture à l'autre.
- **Lignes de vente** liées à un compte de classe **70** (Ventes) : chaque
  ligne a un compte, un libellé, une quantité et un prix unitaire ; le
  montant HT est calculé automatiquement.

**Bouton « Valider et envoyer en Saisie »** : génère automatiquement les
écritures comptables équilibrées dans l'onglet Saisie :
- Débit **Client** (411000) pour le montant TTC.
- Crédit chaque **compte de vente** (70x) pour le HT de sa ligne.
- Crédit **TVA facturée** (443100) pour la taxe.
- **Mise à jour automatique des stocks** : les comptes 701000 (marchandises,
  stock 310000) et 702000 (produits finis, stock 360000) déclenchent en plus
  une sortie de stock au coût unitaire moyen réel (Débit 603100 ou 736000 /
  Crédit le compte de stock correspondant) — les comptes de services
  (ex. 706000) n'impactent aucun stock. Ce mapping compte-de-vente ↔ stock
  est défini dans `core.VENTE_STOCK_MAPPING` (extensible).

Une fois validée, une facture est **verrouillée** (plus de modification
possible, cohérent avec le fait que ses écritures existent déjà en Saisie).

**Bug de calcul du Résultat corrigé au passage** : les comptes de variation
de stock (603100 pour les marchandises, 736000 pour les produits finis)
n'étaient référencés dans aucune formule du Compte de résultat, ce qui
créait un écart Actif/Passif après une vente de marchandises ou de produits
finis. Testé et corrigé : un scénario complet (service + marchandise +
produit fini + TVA) donne désormais un Bilan parfaitement équilibré et un
Résultat net exact (vérifié à l'unité près sur plusieurs cas).

- **PRODUCTION** : Matières premières, Fabrication, Produits finis.

### Reconfiguration majeure : Stocks au détail réel + Fabrication qui consomme les matières (mise à jour)

**Onglet Stocks → Synthèse par compte** : affiche désormais le **détail réel
de chaque compte** de stock utilisé (ex. `321001 CLINKER`, `321002 GYPSE`),
et non plus seulement les 4 comptes centralisateurs (310000/320000/331000/
360000). Un filtre par catégorie (31 Marchandises / 32 Matières premières /
33 Autres approvisionnements / 36 Produits finis) est disponible, ainsi
qu'un nouveau champ **« Marge de valorisation des produits finis par défaut
(%) »**, utilisé comme marge par défaut pour tout nouveau produit créé dans
Fabrication.

**Onglet Fabrication → Recettes / Coût de production** reconfiguré :
- Le sélecteur **« Compte de stock »** des lignes matière propose désormais
  tous les comptes détaillés réellement utilisés dans Stocks (pas seulement
  les 4 comptes centralisateurs) — vous pouvez donc combiner clinker, gypse,
  calcaire... chacun avec son propre coût réel.
- Chaque produit fini a maintenant un **compte de stock configurable**
  (classe 36) où il sera placé une fois fabriqué.
- **Nouveau bouton « Valider la fabrication (comptabiliser) »** : envoie les
  écritures comptables dans le menu SAISIE —
  1. **Consommation des matières premières** : chaque matière utilisée dans
     la recette est diminuée en **quantité et en valeur** sur son compte
     réel (ex. 321001), avec pour contrepartie le compte de variation de
     stock approprié (603200 pour les matières premières, 603100 pour les
     marchandises...).
  2. **Entrée du produit fini** : le compte de stock du produit (classe 36)
     est augmenté en **quantité et en valeur**, valorisé au **coût de
     production + la marge paramétrée**, avec pour contrepartie le compte
     736000.

**Trois bugs trouvés et corrigés pendant les tests** (tous liés à la
reconnaissance des sous-comptes réels) : (1) le calcul du coût de
production ne cherchait le coût unitaire que parmi les 4 comptes maîtres —
corrigé ; (2) la fabrication était datée du jour au lieu d'une date dans
l'exercice actif par défaut — corrigé ; (3) le total des stocks au Bilan
utilisait des préfixes à 3 chiffres qui ratent les sous-comptes détaillés —
corrigé avec de vrais préfixes de catégorie à 2 chiffres.

Testé de bout en bout (clinker + gypse + main-d'œuvre + énergie → ciment,
marge 25 %) : consommation exacte des matières (quantité et valeur),
production de 10 unités de ciment valorisées à 250 000, **Bilan
parfaitement équilibré**, sans régression sur les scénarios précédents.

### Module Fabrication — nomenclature et coût de production (nouveau)

L'onglet **Fabrication** contient maintenant deux sous-onglets :

**« Recettes / Coût de production »** *(nouveau)* — un calculateur de coût de
revient (nomenclature / BOM) :
- Créez un **produit fini** (code, nom).
- Ajoutez ses composants : **matières premières** (choisies parmi les
  comptes de stock — le coût unitaire réel est repris automatiquement du
  **coût unitaire moyen** calculé dans l'onglet Stocks, donc directement
  depuis vos achats comptabilisés), **main-d'œuvre** et **énergie** (coût
  unitaire saisi manuellement), avec une quantité pour chacun.
- Le **coût de production total**, le **coût de production unitaire**
  (divisé par la quantité produite par la recette) sont calculés
  automatiquement.
- Réglez une **marge (%)** : le **prix de vente unitaire suggéré** est
  calculé automatiquement (coût de production × (1 + marge)).

Testé avec un cas concret : achat de 100 unités de matière première pour
500 000 (coût unitaire réel 5 000, repris automatiquement des stocks) → une
recette combinant 2 unités de cette matière + main-d'œuvre (3 000) +
énergie (500) donne un coût de production de 13 500, et un prix de vente
suggéré de 18 900 à 40 % de marge.

**« Coûts de fabrication (période) »** — l'ancien contenu de l'onglet
Fabrication (coûts réels de la période via l'axe analytique AN-FAB),
inchangé et toujours disponible.

- **ENGAGEMENTS-PROJETS** : Achats, Fournisseurs, Factures frs, Contrats.

### Module Factures frs (nouveau)

Le pendant achats du module Facturation. L'onglet **Factures frs** présente
directement une facture d'achat éditable :
- **En-tête** et **pied de page modifiables**.
- **N° Facture**, **Date**, **Fournisseur** (obligatoirement rattaché à un
  compte racine 40).
- **Retenue fiscale à la source paramétrable** : taux (%) et **compte de
  retenue au choix parmi la classe 44** (ex. 447810 « RETENUE 5% OPÉRÉE »),
  avec valeurs par défaut mémorisées d'une facture à l'autre.
- **Lignes d'achat** liées à un compte de classe **6** (charges) : compte,
  libellé, quantité, prix unitaire — montant HT calculé automatiquement.

**Bouton « Valider et envoyer en Saisie »** génère les écritures :
- Débit chaque **compte d'achat** (6x) pour le HT de sa ligne.
- Crédit **Fournisseur** (401000) pour le **net à payer** (HT − retenue).
- Crédit le **compte de retenue** choisi, si un taux est renseigné.
- **Mise à jour automatique des stocks** : les comptes 601000 (marchandises,
  stock 310000) et 602000 (matières premières, stock 320000) déclenchent en
  plus une **entrée de stock** (Débit le compte de stock / Crédit
  603100 ou 603200) — les comptes de service (ex. 622000 Locations)
  n'impactent aucun stock. Mapping défini dans `core.ACHAT_STOCK_MAPPING`
  (extensible).

Une fois validée, une facture est **verrouillée**. Testé de bout en bout
(service + marchandise + matière première + retenue 5%) : Bilan
parfaitement équilibré, stocks correctement augmentés, solde fournisseur
exact, et cohérence vérifiée aussi dans l'export de la Liasse fiscale.


### Module Commerce — Clients / Ventes / Recouvrement (nouveau)

- **Clients** : liste auxiliaire (fiche par client : raison sociale, contact,
  délai de paiement par défaut en jours). Créer / modifier / supprimer, ou
  **importer en masse (.xlsx)** avec un modèle téléchargeable.
- **Ventes** : soldes des opérations avec chaque client (Débit − Crédit sur
  les comptes 411xxx qui lui sont tagués), **total par client**, avec un
  **filtre de plage de dates** (Du / Au). Positif = montant restant dû par
  le client (à recouvrer).
- **Recouvrement** : journal des factures émises à chaque client. À la
  création, l'échéance de **paiement** est calculée automatiquement (date
  de facture + délai par défaut du client). Renseignez ensuite la date
  réelle de paiement au fur et à mesure des encaissements : les **retards
  sont détectés et affichés en rouge** (« EN RETARD (n j) » si l'échéance
  est dépassée sans paiement enregistré, ou « Payé (retard n j) » une fois
  la date réelle enregistrée après l'échéance).

**Saisie** : un nouveau champ **« Client »** (liste déroulante avec
recherche, proposition de création si le code n'existe pas) permet de taguer
chaque écriture — c'est ce qui alimente automatiquement les modules Ventes
et Recouvrement.

### Module Engagements-Projets (nouveau, remplace les placeholders)

- **Fournisseurs** : liste auxiliaire (fiche par fournisseur : raison sociale,
  contact, délais par défaut de paiement et de livraison en jours). Créer /
  modifier / supprimer, ou **importer en masse (.xlsx)** avec un modèle
  téléchargeable.
- **Achats** : soldes des opérations avec chaque fournisseur (Débit − Crédit
  sur les comptes 401xxx/408xxx qui lui sont tagués), **total par
  fournisseur**, avec un **filtre de plage de dates** (Du / Au).
- **Contrats** : journal des commandes passées avec chaque fournisseur. À la
  création, les échéances de **livraison** et de **paiement** sont calculées
  automatiquement (date de commande + délais par défaut du fournisseur).
  Renseignez ensuite les dates réelles de livraison/paiement au fur et à
  mesure : les **dépassements sont détectés et affichés en rouge**
  (« EN RETARD (n j) » si la date prévue est dépassée sans qu'une date
  réelle ait été saisie, ou « Livré/Payé (retard n j) » une fois la date
  réelle enregistrée après l'échéance).

**Saisie** : un nouveau champ **« Fournisseur »** (liste déroulante avec
recherche, proposition de création si le code n'existe pas) permet de taguer
chaque écriture — c'est ce qui alimente automatiquement les modules Achats
et Contrats.

- **ÉTATS ET RAPPORTS** : Grand livre, Balance, Bilan, Compte de résultat,
  TFT, Liasse fiscale, Tableaux d'exécution budgétaire, Impôts,
  Déclarations sociales, Rapprochements bancaires.

Cliquer sur un menu ouvre la liste de ses pages ; cliquer sur une page
l'affiche dans la fenêtre (un seul panneau à la fois).

### Saisie : nouveaux champs (mise à jour)

Le champ « Code flux » a été retiré du formulaire de Saisie. À la place,
chaque écriture propose désormais : **Code analytique**, **Code
budgétaire**, **Code bailleur** (texte libre, pour le suivi par projet/
bailleur de fonds) et **Quantité** (pour la valorisation des stocks — voir
ci-dessous). Le tableau et l'import massif (.xlsx) ont été mis à jour en
conséquence.

⚠️ Le TFT (Tableau des flux de trésorerie) utilisait le Code flux pour
classer les mouvements de trésorerie en EXP/INV/FIN. Ce champ n'étant plus
saisissable, les nouveaux mouvements apparaîtront tous en « Flux non
classés ». Dites-moi si vous voulez qu'on prévoie un autre moyen de les
classer.

**Stocks** (mise à jour) : suivi désormais en **valeur ET en quantité**.
Renseignez la quantité sur chaque écriture touchant un compte de stock
(Saisie), et une quantité initiale (bouton dédié dans l'onglet Stocks) —
l'application calcule alors le **coût unitaire moyen** (valeur du stock
final / quantité finale) pour chaque compte.

### Partie double vraiment forcée (mise à jour majeure)

Le formulaire de Saisie a changé de logique : au lieu d'une ligne à la fois
(un compte + Débit ou Crédit), il demande maintenant **ensemble** :
**Compte débiteur**, **Compte créditeur** et **Montant**. Cliquer sur
« Ajouter » crée automatiquement les deux lignes en une seule opération —
**il est structurellement impossible de créer une écriture déséquilibrée**
par ce formulaire (le compte débiteur doit être différent du compte
créditeur, le montant doit être positif, sinon le logiciel refuse).

Les deux champs comptes sont des listes déroulantes avec recherche ; si
vous quittez le champ avec un code qui n'existe pas dans le Plan comptable,
l'application vous demande de le créer (avec un libellé) avant de continuer
— impossible d'enregistrer une écriture sur un compte invalide.

**Modifier une ligne existante** : sélectionnez-la dans le tableau (chaque
ligne du tableau reste une moitié débit ou crédit, comme avant) — le
formulaire ne pré-remplit alors que le côté concerné ; ne renseignez que ce
compte-là pour la modifier.

**Pour les écritures à plus de 2 comptes** (ex. une facture avec TVA
répartie sur 3 lignes) : ajoutez plusieurs paires successives sur la même
pièce (le N° Pièce reste rempli après chaque « Ajouter » pour faciliter
l'enchaînement) — chaque paire est déjà équilibrée, donc la pièce entière
le reste automatiquement.

### Exercices comptables et clôture annuelle (nouveau)

Une barre en haut de la fenêtre affiche en permanence l'**exercice
comptable en cours** (ex. 2025), avec un sélecteur pour basculer entre
exercices et un bouton **« + Nouvel exercice »**.

Tous les calculs (Saisie, Balance, Bilan, Compte de résultat, TFT, Stocks,
Production, Liasse fiscale) sont désormais **scopés à l'exercice
sélectionné** : seules les écritures datées de cet exercice sont prises en
compte pour les mouvements, et les soldes d'ouverture sont ceux enregistrés
pour cet exercice précis.

**Clôture annuelle** (menu PARAMÈTRES → Exercices comptables) :
- calcule le solde de clôture de chaque compte de bilan (classes 1 à 5) de
  l'exercice sélectionné ;
- intègre le résultat net de l'exercice dans le compte **121000** (Report à
  nouveau créditeur) ;
- reporte ces soldes comme **soldes d'ouverture de l'exercice suivant**
  (créé automatiquement s'il n'existait pas) ;
- **verrouille l'exercice clôturé** : impossible d'ajouter, modifier ou
  supprimer une écriture datée de cet exercice tant qu'il reste clôturé.

Testé avec un cycle complet : exercice 2024 (capital, ventes, achats) →
clôture → exercice 2025 hérite automatiquement des bons soldes d'ouverture
(clients, fournisseurs, banque, report à nouveau incluant le résultat 2024)
et le Bilan reste équilibré, y compris après de nouveaux mouvements en 2025.

### Menu PARAMÈTRES (remplace les plans dans SAISIE)

Les 4 écrans de gestion des plans (Plan comptable, Plan analytique, Plan
budgétaire, Plan bailleurs de fonds) ainsi que les **Exercices comptables**
sont désormais regroupés dans le menu **PARAMÈTRES**.

### Grand livre complet avec bandes de couleur (mise à jour majeure)

L'onglet **Grand livre** affiche désormais **tous les comptes de
l'exercice par défaut**, groupés par compte puis par classe, exactement
comme un grand livre papier classique :
- Bandeau **bleu** pour l'en-tête de chaque compte, et pour son
  sous-total (« TOTAL COMPTE XXXXXX — Solde débiteur/créditeur »).
- Bandeau **orange** pour le total de chaque classe.
- La ligne « À-nouveaux au 01/01 » (solde d'ouverture) s'affiche si non
  nulle, puis le détail chronologique des écritures avec solde cumulé.

Un filtre optionnel (compte et/ou tiers) permet de se recentrer sur un
compte précis si besoin — bouton « Réinitialiser » pour revenir à la vue
complète. Testé sur le scénario exact de votre capture (emprunt WBI/Vista) :
le solde cumulé calculé correspond au FCFA près (-14 595 375 000 puis
-13 849 250 000, identiques à votre grand livre de référence).

### Grand livre : corrigé (n'affichait rien tant qu'on n'avait pas tapé)

**Cause** : le champ « N° Compte » n'avait aucune liste par défaut et ne
s'ouvrait pas au clic (il fallait taper au clavier pour voir apparaître des
résultats) — d'où l'impression que l'écran « n'affiche rien ». Corrigé,
même comportement que dans Saisie : liste des 300 premiers comptes
préchargée, clic = ouverture automatique de la liste déroulante, message
d'aide affiché tant qu'aucun compte n'est choisi (et message clair si le
compte tapé n'existe pas). Le calcul lui-même a été testé et fonctionne
correctement.

### Diagnostic de l'écart de Balance (analyse de votre fichier)

**Comparaison faite entre votre Balance PDF (exercice 2024, autre logiciel)
et notre export (exercice 2026)** : les **soldes de clôture** (colonnes
Solde Débit/Crédit) correspondent **exactement** entre les deux systèmes
là où c'est comparable (ex. TOTAL CLASSE 1 : 20 055 904 / 27 576 434 184
identiques des deux côtés) — la formule de calcul du solde est donc
correcte.

L'écart que vous observez sur les **Cumul Débit/Crédit** vient d'un
mélange de deux facteurs, pas d'un bug de calcul :
1. **Ce ne sont pas les mêmes exercices** (PDF = 2024, export = 2026) : les
   mouvements de la période ne peuvent pas être identiques entre deux
   années différentes.
2. **Des opérations semblent avoir été saisies comme solde d'ouverture au
   lieu d'écritures de la période** (ex. le compte 162020 « EMPRUNT VISTA »
   : votre solde d'ouverture 2026 est déjà de -15 000 000 000, alors que le
   PDF 2024 montre ce même emprunt DÉCAISSÉ pendant l'année — crédité 15
   milliards en cours d'exercice). Le solde final est identique dans les
   deux cas, mais le détail des mouvements de la période diffère forcément
   selon où l'opération a été enregistrée.

L'indicateur d'écart ajouté sur la Balance (message précédent) devrait déjà
vous signaler ce type de situation. Si un écart de **Cumul Débit/Crédit
total** subsiste sur l'exercice 2026 lui-même (pas en comparaison avec
2024), c'est probablement dû à un import massif d'écritures déséquilibré —
dites-le-moi si c'est le cas et je regarderai les données précises.

### Balance : export ajouté + diagnostic du déséquilibre (correction)

**Bouton d'export manquant** : l'onglet Balance n'avait effectivement pas
de bouton d'export — corrigé, un bouton **« Exporter (.xlsx) »** génère
maintenant un fichier avec les mêmes sous-totaux par classe et le total
général que l'écran.

**Sur la formule elle-même** : testée avec des données garanties
équilibrées, elle est correcte (Cumul Débit = Cumul Crédit, Solde Débit =
Solde Crédit à l'euro près). Le déséquilibre visible sur votre capture
vient très probablement de **données important déséquilibrées** — deux
causes possibles, maintenant détectées automatiquement :
1. **Écart sur le Cumul Débit/Crédit** → une ou plusieurs écritures de la
   période ne sont pas équilibrées. Cela ne peut arriver que via l'**import
   massif d'écritures (.xlsx)**, qui n'imposait pas l'équilibre global du
   fichier — **corrigé** : cet import affiche désormais un avertissement
   explicite si le fichier importé n'est pas équilibré dans son ensemble
   (testé et reproduit : Débit 5 000 ≠ Crédit 3 000 → avertissement déclenché).
2. **Écart sur le Solde Débit/Crédit** → soldes d'ouverture incomplets
   (déjà signalé dans le Bilan).

L'onglet Balance affiche maintenant un **indicateur d'écart en bas du
tableau** (vert si équilibré, rouge avec explication sinon) pour repérer
ces situations immédiatement, sans avoir à comparer les totaux à la main.

### Ctrl+A pour tout sélectionner dans Saisie (nouveau)

Dans le tableau de l'onglet Saisie, **Ctrl+A sélectionne désormais toutes
les lignes visibles** (comme dans l'Explorateur Windows), ce qui permet
ensuite de les supprimer toutes d'un coup avec le bouton « Supprimer
(sélection multiple possible) ».

### Correction de lenteur : suppression groupée trop lente (bug corrigé)

**Cause trouvée** : `core.delete_entry()` fait un `commit()` (écriture
synchrone sur disque) **à chaque ligne** — en boucle sur plusieurs lignes
sélectionnées, ça multiplie les accès disque et ralentit fortement,
surtout avec beaucoup de lignes.

**Corrigé** : nouvelle fonction `delete_entries_bulk()` qui supprime tout
le lot dans **une seule transaction** (un seul `commit()` à la fin).
Mesuré : 300 lignes supprimées en 0,003 s avec la nouvelle méthode, contre
0,068 s pour seulement 100 lignes avec l'ancienne — un gain d'environ 20×.

### Suppression groupée dans Saisie (nouveau)

Le tableau de l'onglet Saisie accepte désormais la **sélection multiple**
(Ctrl+clic ou Maj+clic, comme dans l'Explorateur Windows). Le bouton
**« Supprimer (sélection multiple possible) »** supprime alors toutes les
lignes sélectionnées d'un coup, avec une seule confirmation — un exercice
clôturé bloque toujours la suppression des lignes qu'il concerne (message
détaillé si certaines lignes n'ont pas pu être supprimées). Testé :
suppression groupée de 4 écritures en un clic.

### Modèle téléchargeable pour la balance N-1 (nouveau)

Ajout d'un bouton **« Télécharger un modèle (.xlsx) »** dans l'onglet
Soldes d'ouverture, avant les boutons Importer/Exporter — génère un fichier
vierge avec les bons en-têtes et **un exemple équilibré** (4 comptes dont
la somme fait 0), à remplir puis réimporter directement. Testé : le modèle
généré s'importe sans le moindre avertissement (round-trip complet).

### Import de la balance N-1 rendu plus tolérant (correction de bug)

**Bug signalé** : l'import échouait avec « Colonnes obligatoires
introuvables » sur un fichier réel. Corrigé — l'import reconnaît maintenant
plusieurs formats courants :
- Une colonne **« Solde »** signée (notre format par défaut).
- **Deux colonnes séparées « Solde débit » / « Solde crédit »** (comme une
  balance générale classique — le solde est recalculé automatiquement en
  Débit − Crédit).
- Simplement **« Débit » / « Crédit »**.
- Un **en-tête décalé** (titre ou lignes vides au-dessus) — la ligne
  d'en-têtes est désormais recherchée dans les 10 premières lignes, pas
  seulement la ligne 1.

Si le fichier ne correspond toujours à aucun format reconnu, le **message
d'erreur affiche maintenant les en-têtes réellement détectés** dans le
fichier, pour vous aider à comprendre ce qui ne correspond pas.

Testé avec 3 formats différents (solde signé, débit/crédit séparés,
en-tête décalé avec titre) : tous s'importent correctement.

### Import/Export xlsx pour tous les plans + balance N-1, et liste déroulante automatique en Saisie

**Import/Export .xlsx avec écrasement** (menu PARAMÈTRES) :
- **Plan comptable** : boutons Importer/Exporter dans l'onglet. Importer un
  fichier **écrase entièrement** le plan actuel (les comptes non présents
  dans le fichier disparaissent), puis réinsère automatiquement les comptes
  racines (1, 2, 3, 5, 6, 7, 8, 9, 40-49).
- **Plan analytique, Plan budgétaire, Plan bailleurs** : même principe
  (Importer écrase, Exporter génère un .xlsx avec les bons en-têtes).

**Balance d'ouverture (N-1)** (menu SAISIE → Soldes d'ouverture) : mêmes
boutons Importer/Exporter. L'import **écrase les soldes d'ouverture de
l'exercice actuellement sélectionné uniquement** (les autres exercices ne
sont pas affectés) — un compte absent du Plan comptable déclenche un
avertissement mais est importé quand même.

Testé pour les 5 imports : écrasement confirmé dans chaque cas (les
anciennes données disparaissent, remplacées par le contenu du fichier).

**Liste déroulante automatique en Saisie** : un simple **clic** dans les
champs Compte débiteur/créditeur, Journal, Fournisseur, Client, Code
analytique/budgétaire/bailleur ouvre désormais directement la liste
déroulante pour faire défiler et choisir — plus besoin de taper au clavier.
Les champs Compte débiteur/créditeur sont préchargés avec les 300 premiers
comptes dès l'ouverture de l'onglet.

### NOTE 34 (Liasse fiscale) remplie + liens externes cassés supprimés

**Cause identifiée** : le bandeau "IMPOSSIBLE D'ACTUALISER... valeurs
depuis un classeur lié" venait de **liens externes cassés** dans le modèle
(référence vers l'ancien classeur de l'entité GCM, absent). La feuille
**NOTE 34** (Fiche de synthèse des indicateurs financiers — SIG) contenait
en plus d'anciennes valeurs littérales (pas des formules), donc mon
nettoyage général les vidait sans les remplacer, d'où l'écran vide.

**Deux corrections** :
1. **Les liens externes cassés sont maintenant supprimés** à l'export —
   testé, le bandeau d'erreur ne devrait plus apparaître à l'ouverture.
2. **NOTE 34 est remplie automatiquement** (Chiffre d'affaires, Marge
   commerciale, Valeur ajoutée, EBE, Résultat d'exploitation, Résultat
   financier, Résultat des activités ordinaires, Résultat HAO, Résultat
   net), avec les mêmes données que l'onglet Compte de résultat — colonne
   « Année N-1 » remplie aussi si l'exercice précédent existe dans
   l'application.

### Compte de résultat en Soldes Intermédiaires de Gestion (SIG) (mise à jour)

L'onglet **Compte de résultat** suit désormais exactement la structure
officielle SIG (Soldes Intermédiaires de Gestion) de votre modèle, avec une
couleur par section :
- **Activité commerciale** (vert) : Marge commerciale
- **Chiffre d'affaires** (bleu) : A+B+C+D
- **Valeur ajoutée** (jaune) : tous les achats et charges externes détaillés
- **EBE et Résultat d'exploitation** (violet)
- **Résultat financier** (orange) et Résultat des activités ordinaires
- **HAO et Résultat net** (rouge/rose)

Calculé à partir de **`compute_liasse_resultat()`** — la même fonction que
la Liasse fiscale, le TFT et la Situation financière — donc toujours
cohérent avec la Balance et le Bilan. Vérifié : le Résultat net affiché
correspond exactement à celui utilisé par le Bilan (`compute_compte_resultat`
et `compute_liasse_resultat` donnent la même valeur, testé sur plusieurs
scénarios y compris avec variation de stock).

### TFT : la vraie feuille officielle est maintenant remplie (mise à jour)

Grâce à une capture de votre feuille TFT officielle, j'ai pu identifier
précisément les cellules à remplir : **ZA** (trésorerie d'ouverture, ligne
10), **FA** (CAFG, ligne 12), **FB** (variation actif circulant HAO, ligne
13), **FC** (variation des stocks, ligne 14), **FD** (variation des
créances, ligne 15), **FE** (variation du passif circulant, ligne 16) —
toutes en colonne I (Exercice N), calculées depuis vos écritures.

Testé : les valeurs injectées dans la vraie feuille TFT correspondent
exactement à celles de l'onglet TFT de l'application (flux opérationnel
cohérent entre les deux, écart 0).

⚠️ **Les lignes d'investissement et de financement (à partir de FF) ne sont
pas encore automatisées** dans la vraie feuille officielle — je n'ai pas
encore de confirmation visuelle de leur position exacte dans votre modèle,
et je préfère ne pas deviner au risque d'écrire au mauvais endroit sur un
document officiel. **Envoyez-moi une capture des lignes suivantes de la
feuille TFT** (après la ligne 19) pour que je complète le reste. En
attendant, le calcul complet (avec investissement et financement) reste
disponible dans l'onglet supplémentaire « TFT (méthode indirecte - CAFG) »
du même fichier exporté.

### Liasse fiscale : mêmes données que Balance/Bilan/TFT/Situation financière

L'export de la Liasse fiscale utilise désormais **exactement les mêmes
fonctions de calcul** que les onglets de l'application :
- **BILAN** et **RESULTAT** : déjà basés sur `compute_liasse_bilan()` et
  `compute_liasse_resultat()` (comme les onglets Bilan et Compte de
  résultat) — inchangé, déjà cohérent.
- **TFT** *(corrigé)* : l'onglet supplémentaire calculé automatiquement
  utilisait encore l'ancienne méthode directe (`compute_tft`) — remplacé
  par `compute_tft_indirect()`, la **méthode indirecte avec CAFG**,
  identique à l'onglet TFT de l'application (renommé « TFT (méthode
  indirecte - CAFG) » dans le fichier exporté).
- **Nouvelle feuille « SITUATION FIN. (FR-BFR-TN) »** *(nouveau)* : ajoutée
  à l'export, avec les mêmes données que l'onglet Situation financière
  (CAFG, rentabilité, Fonds de Roulement, Besoin en Fonds de Roulement,
  Trésorerie Nette avec contrôle).

Testé : export complet sans erreur ni avertissement (noms d'onglets
raccourcis pour respecter la limite Excel de 31 caractères), Bilan
équilibré (31 000 000 = 31 000 000), TFT et Situation financière remplis
avec les bonnes valeurs.

### Corrections TFT + Bilan, et nouveau module Situation financière

**TFT** : ajout des **bandes de couleur par section** qui manquaient (Text
brut remplacé par un Treeview coloré — trésorerie d'ouverture en violet,
CAFG/exploitation en vert, investissement en orange, financement en bleu,
contrôle en rouge/rose).

**Bilan** : **Actif à gauche, Passif à droite** (inversé par rapport à la
précédente version, sur votre demande).

**Nouveau : Situation financière (FR-BFR-TN)** (menu ÉTATS ET RAPPORTS),
présentée selon le modèle officiel que vous avez fourni, avec une couleur
par section :
- Résultat net, CAFG, autofinancement, ratios de rentabilité économique et
  financière (vert)
- **Fonds de Roulement (FR)** = Ressources stables − Actifs immobilisés (bleu)
- **Besoin en Fonds de Roulement (BFR)** = exploitation + HAO (jaune)
- **Trésorerie Nette (TN) = FR − BFR**, avec contrôle face à la trésorerie
  réelle de la Balance (violet)
- Flux de la période (rappel du TFT, orange) et endettement financier net
  (rouge/rose)

Entièrement calculée à partir de `compute_bilan()`, `compute_liasse_resultat()`
et `compute_tft_indirect()` — donc toujours cohérente avec la Balance, le
Bilan et le TFT. **Un bug a été détecté et corrigé pendant les tests** : un
premier essai montrait un écart de 5 000 000 entre la trésorerie nette
calculée (FR−BFR) et la trésorerie réelle — l'investigation a révélé qu'il
s'agissait en fait d'un **Bilan lui-même déséquilibré** dans le scénario de
test (solde d'ouverture d'un emprunt saisi sans sa contrepartie), et non
d'un défaut de la formule. Une fois les soldes d'ouverture complets et
équilibrés, la Situation financière se réconcilie exactement avec la
Balance (testé : écart 0 sur plusieurs scénarios).

### TFT en méthode indirecte — CAFG (nouveau, cohérent avec la Balance)

L'onglet **TFT** contient maintenant deux sous-onglets :

**« TFT (méthode indirecte — CAFG) »** *(nouveau, vue principale)* : suit
exactement la structure du modèle officiel SYSCOHADA que vous avez fourni —
trésorerie d'ouverture, détermination de la **Capacité d'Autofinancement
Globale (CAFG)** à partir de l'EBE, des revenus et frais financiers, puis
variation du BFR (stocks, créances, dettes circulantes) pour obtenir le
flux des activités opérationnelles ; flux d'investissement (acquisitions/
cessions d'immobilisations incorporelles, corporelles, financières) ; flux
de financement (capital, subventions, emprunts).

Entièrement calculé à partir de **la même `compute_balance()`** que les
onglets Balance et Bilan — une ligne **CONTRÔLE** compare la trésorerie
recalculée par la méthode indirecte à la trésorerie réelle de la Balance
(classe 5) ; l'**écart doit être nul**, ce qui garantit la cohérence entre
les trois états. Testé avec plusieurs scénarios (vente à crédit, achat de
stock au comptant, encaissement partiel, remboursement d'emprunt) : écart
toujours à 0, trésorerie calculée = trésorerie réelle au FCFA près.

**« TFT (méthode directe — ancien) »** : l'ancienne vue (basée sur le code
flux EXP/INV/FIN), conservée pour référence mais reléguée en second plan.

### Balance et Bilan reformatés (mise à jour, cohérence garantie entre eux)

**Balance** (États et rapports → Balance) : reformatée en **Balance
générale groupée par classe**, avec pour chaque compte les colonnes Solde
Ouverture, Cumul Débit, Cumul Crédit, **Solde Débit** et **Solde Crédit**
(séparés, comme une balance comptable classique), un **sous-total par
classe** (ligne bleutée « TOTAL CLASSE X ») et un **total général** en bas
(ligne foncée « TOTAL BALANCE »).

**Bilan** (États et rapports → Bilan) : présenté en **deux colonnes
côte à côte, PASSIF à gauche et ACTIF à droite**, avec une **couleur
distincte par masse** :
- Actif (droite) : Immobilisations (vert), Stocks détaillés par compte réel
  (jaune), Créances (bleu), Trésorerie détaillée par banque (violet).
- Passif (gauche) : Capitaux propres + résultat net (vert), Dettes
  financières (orange), Dettes circulantes détaillées — fournisseurs,
  avances, fiscal/social, autres — (rouge/rose), Trésorerie passif (violet).
- Une bande foncée en bas de chaque colonne pour le TOTAL ACTIF / TOTAL
  PASSIF, et l'écart Actif-Passif affiché en vert (équilibré) ou rouge
  (à corriger).

**Cohérence garantie entre les deux** : Balance et Bilan sont calculés à
partir de **la même fonction `compute_balance()`** — revérifié après cette
mise à jour visuelle (Total Actif = 14 700 000, cohérent avec la somme des
soldes débiteurs de la Balance sur les classes 1 à 5, aucune KeyError,
aucune régression).

### Balance et Bilan reformatés — première version (historique)

**Balance** (États et rapports → Balance) : reformatée en **Balance
générale groupée par classe**, avec pour chaque compte les colonnes Solde
Ouverture, Cumul Débit, Cumul Crédit, **Solde Débit** et **Solde Crédit**
(séparés, comme une balance comptable classique), un **sous-total par
classe** (ligne bleutée « TOTAL CLASSE X ») et un **total général** en bas
(ligne foncée « TOTAL BALANCE ») — structure proche de votre balance PDF de
référence.

**Bilan** (États et rapports → Bilan) : largement enrichi avec le détail
par poste :
- Immobilisations nettes détaillées par catégorie
- **Stocks détaillés par compte réel** (ex. 321001 CLINKER), pas seulement
  le total
- Créances détaillées (avances versées / clients)
- **Trésorerie détaillée par banque/caisse** (chaque compte 52x séparément,
  comme dans votre PDF)
- Dettes circulantes détaillées (fournisseurs / avances reçues / dettes
  fiscales et sociales / autres dettes)

**Cohérence garantie entre les deux** : Balance et Bilan sont désormais
calculés à partir de **la même fonction `compute_balance()`** — testé et
vérifié : le Total Actif du Bilan correspond exactement à la somme des
soldes débiteurs de la Balance sur les classes 1 à 5 (14 700 000 = 14 700
000 dans le scénario testé, avec plusieurs banques et sous-comptes de stock
détaillés). Aucune régression sur les scénarios précédents.

### Racines des comptes (nouveau)

Chaque compte du Plan comptable est désormais rattaché à une **racine**,
visible dans l'onglet Plan comptable (colonnes « Racine » et « Libellé de la
racine ») :
- **1 chiffre** pour les classes 1, 2, 3, 5, 6, 7, 8, 9.
- **2 chiffres pour la classe 4** (comptes de tiers), qui se subdivise en
  **40** (Fournisseurs et comptes rattachés), **41** (Clients et comptes
  rattachés), 42 (Personnel), 43 (Organismes sociaux), 44 (État), 45
  (Organismes internationaux), 46 (Associés/Groupe), 47 (Débiteurs/
  créditeurs divers), 48 (Régularisations), 49 (Dépréciations sur tiers).

**Les comptes racines existent désormais réellement dans le Plan comptable**
(1, 2, 3, 5, 6, 7, 8, 9, 40 à 49), avec un libellé entre tirets (ex. « —
Fournisseurs et comptes rattachés — ») pour les repérer facilement. Grâce au
tri alphabétique des codes, chaque racine **apparaît en tête de son groupe**
dans toutes les listes de comptes (ex. le compte « 1 » avant 101000, 101100,
etc. ; le compte « 40 » avant 400000, 401000, 401100...).

Les fiches auxiliaires créées dans **Fournisseurs** sont rattachées à la
racine **40**, celles créées dans **Clients** à la racine **41**.

**Sélection du tiers rendue obligatoire (nouveau)** : dans l'onglet Saisie,
si vous tapez directement le compte racine **40** ou **41** dans « Compte
débiteur »/« Compte créditeur », l'application vous avertit qu'on ne saisit
jamais directement sur une racine de regroupement, bascule automatiquement
sur le compte de détail usuel (401000/411000), et impose de choisir le
fournisseur ou le client dans le champ correspondant. Plus largement, **toute
écriture sur un compte de la racine 40 sans fournisseur renseigné (ou de la
racine 41 sans client renseigné) est bloquée** à l'enregistrement.

**Tous les calculs liés aux comptes de tiers ont été mis à jour en
conséquence** :
- Le **Bilan** classe désormais les comptes de tiers **par racine** plutôt
  que par simple signe du solde : la racine 41 (Clients) va toujours en
  Créances, la racine 40 (Fournisseurs) toujours en Dettes circulantes ; les
  autres racines (42 à 49) restent classées par signe, car leur nature
  actif/passif dépend réellement du solde.
- **Achats** et **Ventes** utilisent désormais la racine complète (`40%` et
  `41%`) au lieu de motifs partiels — un **bug a été corrigé au passage** :
  l'ancien filtre (401xxx/408xxx pour les fournisseurs, 411xxx pour les
  clients) ratait des comptes comme 402, 404, 409, 412, 413, 418, 419, qui
  sont maintenant bien pris en compte.

Testé de bout en bout : Bilan équilibré avec un compte fournisseur débiteur
(avance, compte 409xxx) et un compte client sur un effet à recevoir (compte
412xxx), tous deux désormais correctement classés ; comptes racines vérifiés
existants et correctement triés (« 1 » avant 101000, « 40 » avant 400000-
409xxx) ; écriture réelle avec fournisseur tagué toujours cohérente.

### Gestion des plans (détail des écrans)

Le menu **SAISIE** contient maintenant 4 écrans pour créer/modifier/
supprimer les référentiels utilisés lors de la saisie : **Plan comptable**,
**Plan analytique**, **Plan budgétaire** (avec montant prévu), **Plan
bailleurs de fonds**.

### (Ancien mécanisme remplacé)

L'équilibrage « après coup » ligne par ligne a été remplacé par le
formulaire Compte débiteur / Compte créditeur décrit plus haut, qui
équilibre chaque écriture dès sa création plutôt que de le vérifier après.

### Listes déroulantes avec proposition de création (nouveau)

Les champs **Code analytique**, **Code budgétaire** et **Code bailleur**
sont des listes déroulantes alimentées par leurs plans respectifs. Si vous
tapez un code qui n'existe pas encore, l'application vous demande de
confirmer sa création (avec un libellé) avant de passer à la cellule
suivante — impossible d'enregistrer un code orphelin par erreur de frappe.

### Ce qui est pleinement fonctionnel


Saisie, Soldes d'ouverture, Stocks (partagé entre Matières premières et
Produits finis pour l'instant), Fabrication, Compte de résultat, TFT, Grand
livre, Balance, Bilan, Liasse fiscale — ainsi que 3 nouvelles pages basées
sur vos écritures existantes :
- **Ventes** / **Achats** : synthèse des comptes de vente (classe 7) et
  d'achat (classe 6), hors éléments financiers.
- **Marges bénéficiaires** : marge commerciale, valeur ajoutée, résultat
  d'exploitation et résultat net (mêmes calculs que la Liasse fiscale).
- **Clients** / **Fournisseurs** : Grand livre pré-filtré sur les comptes
  411000 / 401000.

### Ce qui reste à construire

**Contrats**, **Tableaux d'exécution budgétaire**, **Impôts**,
**Déclarations sociales** et **Rapprochements bancaires** apparaissent dans
le menu mais affichent pour l'instant un message « fonctionnalité pas
encore développée » — ce sont de nouveaux modules à part entière (suivi de
contrats, calcul d'impôts, etc.) qui nécessitent d'être conçus et développés
spécifiquement. Dites-moi lesquels prioriser.

- **Soldes d'ouverture** *(nouveau)* : saisissez le solde de report à nouveau
  de chaque compte de bilan au 1er jour de l'exercice (= solde de clôture de
  l'exercice précédent). Convention : débiteur = positif, créditeur = négatif.
  La somme de tous les soldes d'ouverture doit être nulle (partie double) —
  un contrôle l'affiche en bas de l'onglet. **Tous les calculs (Balance,
  Bilan, TFT, Liasse fiscale) intègrent désormais automatiquement ces soldes
  d'ouverture** : Balance de clôture = Solde d'ouverture + Mouvements de
  l'exercice. C'est ce qui permet au Bilan de s'équilibrer même si ce n'est
  pas la première année d'activité.
- **Balance** *(mise à jour)* : affiche maintenant, pour chaque compte, le
  Solde d'ouverture, le Débit/Crédit/Solde de la période, et le **Solde de
  clôture**.
- **Stocks** : le stock initial saisi ici alimente désormais directement la
  table des soldes d'ouverture (même mécanisme que ci-dessus).
- **TFT** : la trésorerie d'ouverture est calculée **automatiquement** à
  partir des soldes d'ouverture des comptes de trésorerie (521000/531000/
  570000/585000) ; un bouton permet de la forcer manuellement si besoin.
  Codez `FLUX-EXP`, `FLUX-INV` ou `FLUX-FIN` dans le champ « Code flux » des
  écritures de trésorerie dans l'onglet Saisie pour classer les mouvements.
- **Grand livre** : tapez un N° Compte (liste déroulante avec recherche)
  puis « Afficher » pour voir le détail chronologique et le solde cumulé.
- **Production** : tapez `AN-FAB` dans le champ « Code analytique » de
  l'onglet Saisie sur les lignes de charges de fabrication pour qu'elles
  remontent dans l'onglet Production.

### Liasse fiscale *(mise à jour majeure)*

Renseignez l'identification de l'entité (dénomination, adresse, N° IFU,
exercice clos le...), puis « Exporter la liasse fiscale complète (.xlsx) ».

Le fichier généré reprend **les 92 pages et les mêmes dimensions exactes du
modèle SYSCOHADA système normal que vous avez fourni** (COUVERTURE, BILAN,
RESULTAT, TFT, 39 notes annexes NOTE 1 à NOTE 39, ~20 tableaux fiscaux DGI
SUPPL1 à SUPPL20, fiches R1-R4, etc.) :

- ✅ **BILAN et RESULTAT** : remplis automatiquement depuis vos écritures,
  avec les mêmes codes officiels (AD/AE/AI... côté actif, CA/CJ/DA... côté
  passif, TA/RA/XA... au compte de résultat). Les totaux et le Résultat net
  utilisent désormais la **balance de clôture** (soldes d'ouverture +
  mouvements) — le Bilan s'équilibre toujours, y compris les années
  suivantes une fois les soldes d'ouverture saisis.
- ✅ **TFT** : la page officielle (méthode indirecte avec CAFG) est laissée
  vierge — nous ne calculons pas la CAFG automatiquement. Un onglet
  supplémentaire **« TFT (simplifie) »** est ajouté avec un calcul en
  méthode directe (Ouverture, EXP/INV/FIN, Clôture), cohérent avec la
  Balance.
- ⚠️ **Détail des lignes du Bilan** (AE à AN, CA à CM, DA à DM) : réparti
  par plage de comptes, y compris une répartition proportionnelle des
  amortissements entre catégories — indicatif, à vérifier.
- 📄 **Toutes les autres pages** (39 notes, ~20 tableaux DGI) : conservées
  avec leur mise en page, leurs libellés et **leurs dimensions identiques**
  au modèle fourni, mais les montants qu'elles contenaient (qui sont les
  chiffres 2023 de l'entreprise du modèle, pas les vôtres) sont **effacés**
  pour éviter toute confusion — à compléter manuellement ou par votre
  expert-comptable.

**À faire vérifier par un expert-comptable avant tout dépôt officiel auprès
de la DGI** — cet export est une aide à la préparation, pas un dépôt
directement utilisable tel quel.

## Limites de cette version par rapport au classeur Excel

Cette version ne reprend pas encore le suivi budgétaire / analytique par
projet / par bailleur de fonds (feuille « Rapport d'exécution » du
classeur), ni les comptes auxiliaires Fournisseurs/Clients détaillés.
Dites-moi si vous voulez que je les ajoute — le moteur (`core.py`) est
structuré pour que ce soit un ajout incrémental, pas une réécriture.

### Bilan « avec détails » + correction de l'équilibre (mise à jour majeure)

**Cause racine de l'ancien déséquilibre du Bilan identifiée et corrigée** :
plusieurs calculs (résultat net dans `compute_bilan`, capitaux propres,
clôture d'exercice) s'appuyaient sur des **listes de comptes codées en dur**
(`COMPTES_PRODUITS_EXPL`, `COMPTES_CAPITAL`, etc.) qui ne couvrent qu'une
partie du vrai plan comptable de l'utilisateur (1591 comptes importés de
Sage). Tout compte hors de ces listes disparaissait purement et simplement
du Total Actif ou du Total Passif, d'où l'écart constaté.

**Correctif** : `compute_resultat_net_complet()` (nouveau, dans `core.py`)
calcule désormais le résultat net de façon exhaustive à partir de
**l'intégralité** des classes 6 (charges), 7 (produits) et 8 (HAO), sans
aucune liste de comptes partielle. `compute_bilan()` utilise l'intégralité
de la **classe 1** (au lieu de `COMPTES_CAPITAL`/`COMPTES_DETTES_FIN`...) et
l'intégralité de la **classe 3** (au lieu des 4 comptes maîtres de stock) —
chaque compte de la Balance est donc classé dans une case et une seule de
l'Actif ou du Passif, ce qui **garantit mathématiquement Actif = Passif**
(tant que la somme des soldes d'ouverture de l'exercice est nulle).
`compute_liasse_resultat()` (Compte de résultat officiel, TFT, Situation
financière, Liasse fiscale) est recalée sur cette même référence via une
ligne de réconciliation (repliée dans « Autres produits »/« Autres
charges ») — tous les états financiers partagent maintenant EXACTEMENT le
même résultat net. `close_exercice()` (clôture annuelle) utilise aussi ce
calcul exhaustif pour reporter le résultat sur le compte 121000.

**Nouvel onglet Bilan, présenté « avec détails »** (calqué sur le rapport
financier de référence fourni par l'utilisateur, pas sur les codes officiels
DGI de la Liasse fiscale) : `compute_bilan_detaille()` —
- **Actif** en colonnes Brut / Amortissements / Net : immobilisations par
  catégorie (charges immobilisées, terrains, bâtiments, installations,
  matériel, matériel de transport, avances sur immo, immobilisations
  financières — répartition de l'amortissement proportionnelle au brut de
  chaque catégorie, indicatif) ; stocks regroupés par préfixe à 2 chiffres
  (31 à 39, plus de compte de stock oublié) ; créances **compte par compte**
  (chaque client, chaque avance fournisseur, chaque compte 42 à 49 débiteur
  affiché séparément — pas juste un total) ; trésorerie **banque par
  banque**.
- **Passif** en Montant : capitaux propres et ressources durables **compte
  par compte** (capital, réserves, report à nouveau, emprunts... — classe 1
  entière) puis Résultat net de l'exercice ; dettes circulantes **compte par
  compte** (chaque fournisseur, et pour la classe 44 chaque compte distinct
  — IS, IMF, BIC, TVA facturée, TVA due, retenues... apparaissent
  automatiquement séparément dès lors qu'ils existent comme comptes distincts
  dans le plan comptable réel, sans codage en dur) ; trésorerie créditrice
  banque par banque.
- **Exportable en .xlsx** (bouton « Exporter (.xlsx) », `export_bilan_detaille_xlsx()`),
  dans une mise en page à deux colonnes proche du modèle papier fourni.

Testé de bout en bout avec des comptes volontairement absents des anciennes
listes codées en dur (105xxx, 163xxx, 380xxx stock, 84x/87x HAO...) : Bilan
et Bilan détaillé strictement équilibrés (écart = 0), Compte de résultat/TFT/
Situation financière cohérents avec ce même résultat net, clôture d'exercice
fonctionnelle.

**Point de vigilance non résolu** : la répartition Brut/Amortissements par
catégorie d'immobilisation reste **proportionnelle** (indicatif, comme déjà
signalé pour la Liasse fiscale) faute de connaître la correspondance exacte
entre chaque compte d'immobilisation et son compte d'amortissement dédié
dans le plan comptable réel de l'utilisateur — le Net par catégorie et le
Total Net restent, eux, exacts.
