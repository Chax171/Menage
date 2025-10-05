import streamlit as st
import pandas as pd
import datetime as dt
import math


#--------------------------------------------------------------
#CONSTANTES
#-------------------------------------------------------------

title = "Ajouter une tâche"

#--------------------------------------------------------------
#Variables stockées dans la session
#--------------------------------------------------------------
if 'taches' not in st.session_state:
    st.session_state.taches = ["test"]
if 'echeances' not in st.session_state:  
    st.session_state.echeances = [0]
if 'points' not in st.session_state:
    st.session_state.points = [0]
if 'status' not in st.session_state:
    st.session_state.status = [False]
if 'recurrences' not in st.session_state:
    st.session_state.recurrences = [0]

#POINTS
if 'Colita_points' not in st.session_state:
    st.session_state.Colita_points = 0
if 'Xav_points' not in st.session_state:
    st.session_state.Xav_points = 0
if 'Rosalia_points' not in st.session_state:
    st.session_state.Rosalia_points = 0
if 'Chin_points' not in st.session_state: 
    st.session_state.Chin_points = 0

#HISTORIQUE variables
if 'historiqueDf' not in st.session_state:
    st.session_state.historiqueDf = []
if 'dateDf' not in st.session_state:
    st.session_state.dateDf = []
if 'pointsGagnesDf' not in st.session_state:
    st.session_state.pointsGagnesDf = []
if 'laveurDf' not in st.session_state:
    st.session_state.laveurDf = []
if 'supprimerDf' not in st.session_state:
    st.session_state.supprimerDf = []

# DATES D'ÉCHÉANCE (une date par tâche)
if 'due_dates' not in st.session_state:
    # s'il y a déjà des tâches/echeances, on calcule les dates à partir d'aujourd'hui
    today = pd.Timestamp.today().normalize()
    st.session_state.due_dates = [
        (today + pd.Timedelta(days=d)).date() for d in st.session_state['echeances']
    ]


#TITRE DE LA PAGE
st.header("1100 Gilford clean up crew")


#TABS
tab1, tab2, tab3= st.tabs(["Tâches", "Historique", "Leaderboard"])


#IDENTIFIATION
choixLaveur = tab1.selectbox("Qui es-tu?",
 ["Xav", "Rosalia", "Colita", "Chin"])


#BOUTON AJOUTER UNE TACHE
ajouterTacheBouton = tab1.button("Ajouter une tâche",
    type = "primary")

#POPUP AJOUTER UNE TACHE
@st.dialog(title)
def popup():
    nomTache = st.text_input("Nom de la tâche")
    echeanceTache = st.number_input("Échéance (en jours)", min_value=0, max_value=30, value=1, step=1)
    nbPointsTache = st.number_input("Nombre de points", min_value=0, max_value=100, value=10, step=1)

    recurrence = st.checkbox("Récurrence")
    if recurrence:
        nbRecurrence = st.number_input("Récurrence (en jours)", min_value=1, max_value=30, value=7, step=1)
        # calendrier : date de départ (première occurrence)
        today_date = pd.Timestamp.today().normalize().date()
        start_date = st.date_input(
            "Date de départ (première occurrence)",
            value=today_date,  # tu peux mettre un jeudi par défaut si tu veux
            format="DD/MM/YYYY"
        )
    else:
        nbRecurrence = 0
        start_date = None

    col1, col2 = st.columns(2)
    with col1:
        validerBouton = st.button("Valider", type="primary")
    with col2:
        annulerBouton = st.button("Annuler", type="secondary")

    if validerBouton:
        today = pd.Timestamp.today().normalize().date()

        # Calcul de la date due et de l'échéance visible
        if nbRecurrence > 0 and start_date is not None:
            # première occurrence = start_date, mais si elle est passée, on pousse par pas de nbRecurrence
            due = start_date
            if due < today:
                delta = (today - due).days
                steps = math.ceil(delta / nbRecurrence)
                due = due + dt.timedelta(days=steps * nbRecurrence)
            due_date = due
            echeance_effective = (due_date - today).days  # pour remplir la colonne interne "Échéance (jours)"
        else:
            # tâche non récurrente : due = aujourd'hui + echeanceTache jours
            due_date = (today + dt.timedelta(days=int(echeanceTache)))
            echeance_effective = int(echeanceTache)

        # MAJ état
        st.session_state.taches.append(nomTache)
        st.session_state.echeances.append(int(echeance_effective))   # interne, peut être masquée à l’écran
        st.session_state.points.append(int(nbPointsTache))
        st.session_state.status.append(False)
        st.session_state.recurrences.append(int(nbRecurrence))
        st.session_state.due_dates.append(due_date)

        st.success("Tâche ajoutée !")
        st.rerun()



    
if ajouterTacheBouton:
    popup()



# --- DATAFRAME DES TÂCHES TRIÉ PAR URGENCE ---
today = pd.Timestamp.today().normalize()

taches = pd.DataFrame({
    'Tâches': st.session_state['taches'],
    'Échéance (jours)': st.session_state['echeances'],
    'Date due': st.session_state['due_dates'],
    'Points': st.session_state['points'],
    'Statut': st.session_state['status'],
    'Récurrence (jours)': st.session_state['recurrences']
})

# Jours restants = date_due - aujourd'hui
taches['Jours restants'] = (pd.to_datetime(taches['Date due']) - today).dt.days

# Tri: plus urgent en haut
taches = taches.sort_values(['Jours restants', 'Points'], ascending=[True, False]).reset_index(drop=True)

# Colonne UI "Supprimer" (bool pur, pas de NaN)
taches['Supprimer'] = pd.Series([False] * len(taches), dtype=bool)

# Colonnes visibles et ordre d’affichage
visible_cols = ["Tâches", "Jours restants", "Récurrence (jours)", "Points", "Statut", "Supprimer"]

tableauTaches = tab1.data_editor(
    taches[visible_cols],
    width="stretch",
    height="auto",
    hide_index=True,
    num_rows="fixed",
    disabled=['Tâches', 'Échéance (jours)', 'Points', 'Récurrence (jours)', 'Date due', 'Jours restants'],
    column_config={
        "Statut": st.column_config.CheckboxColumn("Statut", help="Coche si la tâche est faite"),
        "Supprimer": st.column_config.CheckboxColumn("Supprimer", help="Cocher pour supprimer définitivement la tâche"),
    },
    key="editor_taches")




#DATAFRAME DES POINTS
points = pd.DataFrame({
    'Points': [st.session_state.Colita_points, st.session_state.Xav_points, st.session_state.Rosalia_points, st.session_state.Chin_points],
    'Laveur': ['Colita', 'Xav', 'Rosalia', 'Chin']
})


# --- VALIDATION TACHES ---
validerTacheBouton = tab1.button("Valider les tâches effectuées", type="primary")

if validerTacheBouton:
    statuts = tableauTaches["Statut"].tolist()
    indices_a_valider = [i for i, done in enumerate(statuts) if done]

    if not indices_a_valider:
        st.info("Aucune tâche cochée.")
    else:
        # On repart de taches triées; il faut retrouver les index réels dans session_state.
        # Astuce: on reconstruit un mapping (valeurs triées -> index originaux) via une DataFrame source.
        source = pd.DataFrame({
            'Tâches': st.session_state['taches'],
            'Échéance (jours)': st.session_state['echeances'],
            'Date due': st.session_state['due_dates'],
            'Points': st.session_state['points'],
            'Statut': st.session_state['status'],
            'Récurrence (jours)': st.session_state['recurrences'],
        })
        source['Jours restants'] = (pd.to_datetime(source['Date due']) - today).dt.days
        source_sorted = source.sort_values(['Jours restants', 'Points'], ascending=[True, False]).reset_index()  # garde 'index' d'origine

        # Pour chaque ligne cochée dans l'éditeur (index trié), retrouve l'index original
        idx_originaux = [int(source_sorted.loc[i, 'index']) for i in indices_a_valider]

        # Traiter en ordre décroissant des index originaux si on supprime
        for idx in sorted(idx_originaux, reverse=True):
            pointsGagnes = st.session_state['points'][idx]

            # LEADERBOARD
            if choixLaveur == "Xav":
                st.session_state.Xav_points += pointsGagnes
            elif choixLaveur == "Rosalia":
                st.session_state.Rosalia_points += pointsGagnes
            elif choixLaveur == "Colita":
                st.session_state.Colita_points += pointsGagnes
            elif choixLaveur == "Chin":
                st.session_state.Chin_points += pointsGagnes

            # HISTORIQUE
            st.session_state.historiqueDf.append(st.session_state['taches'][idx])
            st.session_state.dateDf.append(pd.Timestamp.now().strftime("%d/%m/%Y"))
            st.session_state.pointsGagnesDf.append(pointsGagnes)
            st.session_state.laveurDf.append(choixLaveur)
            st.session_state.supprimerDf.append(False)

            # RÉCURRENCE : replanifier plutôt que supprimer
            rec = int(st.session_state['recurrences'][idx])
            if rec > 0:
                # nouvelle date due = ancienne date due + rec jours (ou max(aujourd'hui, date_due) + rec)
                old_due = pd.Timestamp(st.session_state['due_dates'][idx])
                base = max(old_due, today)  # si la tâche était en retard, on repart d'aujourd'hui
                new_due = (base + pd.Timedelta(days=rec)).date()

                st.session_state['due_dates'][idx] = new_due
                st.session_state['echeances'][idx] = rec  # l’échéance future = intervalle de récurrence
                st.session_state['status'][idx] = False   # décocher pour la prochaine occurrence
            else:
                # PAS DE RÉCURRENCE : suppression définitive
                st.session_state['taches'].pop(idx)
                st.session_state['echeances'].pop(idx)
                st.session_state['points'].pop(idx)
                st.session_state['status'].pop(idx)
                st.session_state['recurrences'].pop(idx)
                st.session_state['due_dates'].pop(idx)

        st.success("Tâche(s) validée(s) !")
        st.rerun()



# --- BOUTON SUPPRIMER ---
supprimerTachesBtn = tab1.button("Supprimer les tâches sélectionnées", type="secondary")

if supprimerTachesBtn:
    if len(tableauTaches) == 0:
        tab1.warning("Aucune tâche à supprimer n'est sélectionnée.")
    else:
        # Liste des cases cochées (côté tableau trié)
        sup_list = tableauTaches["Supprimer"].fillna(False).astype(bool).tolist()
        idx_sorted_view = [i for i, s in enumerate(sup_list) if s]

        if not idx_sorted_view:
            tab1.warning("Aucune tâche à supprimer n'est sélectionnée.")
        else:
            # --- Retrouver les index ORIGINELS dans session_state malgré le tri ---
            today = pd.Timestamp.today().normalize()
            source = pd.DataFrame({
                'Tâches': st.session_state['taches'],
                'Échéance (jours)': st.session_state['echeances'],
                'Date due': st.session_state['due_dates'],
                'Points': st.session_state['points'],
                'Statut': st.session_state['status'],
                'Récurrence (jours)': st.session_state['recurrences'],
            })
            source['Jours restants'] = (pd.to_datetime(source['Date due']) - today).dt.days

            source_sorted = source.sort_values(
                ['Jours restants', 'Points'], ascending=[True, False]
            ).reset_index()  # garde 'index' = index original

            # map des lignes cochées (dans la vue triée) vers les index originels
            idx_originaux = [int(source_sorted.loc[i, 'index']) for i in idx_sorted_view]

            # --- Supprimer proprement dans session_state (ordre décroissant) ---
            for idx in sorted(idx_originaux, reverse=True):
                st.session_state['taches'].pop(idx)
                st.session_state['echeances'].pop(idx)
                st.session_state['points'].pop(idx)
                st.session_state['status'].pop(idx)
                st.session_state['recurrences'].pop(idx)
                st.session_state['due_dates'].pop(idx)

            tab1.success("Tâche(s) supprimée(s) avec succès.")
            st.rerun()


#LEADERBOARD
tab3.bar_chart(data=points,
    x='Laveur',
    y='Points',
    width=0,
    height=0,
    use_container_width=True)

# --- DATAFRAME HISTORIQUE (reconstruit à chaque run) ---
historique = pd.DataFrame({
    'Tâches': st.session_state['historiqueDf'],
    'Date': st.session_state['dateDf'],
    'Points gagnés': st.session_state['pointsGagnesDf'],
    'Laveur': st.session_state['laveurDf'],
    'Supprimer': st.session_state['supprimerDf'],
})

# Ajouter la colonne "Supprimer" en booléen pur, sans NaN
historique['Supprimer'] = pd.Series([False] * len(historique), dtype=bool)

tableauHistorique = tab2.data_editor(
    historique,
    width="stretch",
    height="auto",
    hide_index=True,
    num_rows="fixed",
    # On rend TOUT éditable, puis on désactive les colonnes sauf "Supprimer"
    disabled=['Tâches', 'Date', 'Points gagnés', 'Laveur', 'Récupération'],
    column_config={
        "Supprimer": st.column_config.CheckboxColumn(
            "Supprimer",
            help="Cocher pour retirer la ligne et reprendre les points",
            default=False
        )
    },
    key="editor_historique"
)

# --- BOUTON SUPPRIMER ---
supprimerHistoriqueBtn = tab2.button(
    "Supprimer les tâches cochées de l'historique",
    type="secondary"
)

if supprimerHistoriqueBtn:
    if len(tableauHistorique) == 0:
        tab2.warning("Aucune tâche à supprimer n'est sélectionnée.")
    else:
        # Sécurise: convertir/compléter en bool (au cas où)
        sup_list = (
            tableauHistorique['Supprimer']
            .fillna(False)
            .astype(bool)
            .tolist()
        )

        idx_to_delete = [i for i, s in enumerate(sup_list) if s]

        if not idx_to_delete:
            tab2.warning("Aucune tâche à supprimer n'est sélectionnée.")
        else:
            for idx in sorted(idx_to_delete, reverse=True):
                laveur = st.session_state.laveurDf[idx]
                pts = int(st.session_state.pointsGagnesDf[idx])

                # Retirer les points
                if laveur == "Xav":
                    st.session_state.Xav_points -= pts
                elif laveur == "Rosalia":
                    st.session_state.Rosalia_points -= pts
                elif laveur == "Colita":
                    st.session_state.Colita_points -= pts
                elif laveur == "Chin":
                    st.session_state.Chin_points -= pts

                # (Optionnel) empêcher négatifs
                st.session_state.Xav_points = max(0, st.session_state.Xav_points)
                st.session_state.Rosalia_points = max(0, st.session_state.Rosalia_points)
                st.session_state.Colita_points = max(0, st.session_state.Colita_points)
                st.session_state.Chin_points = max(0, st.session_state.Chin_points)

                # Supprimer la ligne dans l'historique
                st.session_state.historiqueDf.pop(idx)
                st.session_state.dateDf.pop(idx)
                st.session_state.pointsGagnesDf.pop(idx)
                st.session_state.laveurDf.pop(idx)
                st.session_state.supprimerDf.pop(idx)

            tab2.success("Ligne(s) supprimée(s) et points repris avec succès.")
            st.rerun()
