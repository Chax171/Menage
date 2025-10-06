import streamlit as st
import pandas as pd
import datetime as dt
import math
from streamlit import column_config as cc

# ============================================================
# MODE COMPAT iOS : désactive tout rendu Markdown/GFM
# ============================================================
st.sidebar.checkbox("Mode compat iOS (désactiver Markdown)", key="compat_ios", value=False)

def md(text: str):
    """Affiche un texte: Markdown normal ou texte brut si compat iOS."""
    if st.session_state.get("compat_ios"):
        st.text(text)
    else:
        st.markdown(text)

def ui_success(msg: str):
    if st.session_state.get("compat_ios"):
        st.write("✅ " + msg)
    else:
        st.success(msg)

def ui_info(msg: str):
    if st.session_state.get("compat_ios"):
        st.write("ℹ️ " + msg)
    else:
        st.info(msg)

def ui_warning(msg: str):
    if st.session_state.get("compat_ios"):
        st.write("⚠️ " + msg)
    else:
        st.warning(msg)

def ui_error(msg: str):
    if st.session_state.get("compat_ios"):
        st.write("❌ " + msg)
    else:
        st.error(msg)

# ============================================================
# CONSTANTES ET VARIABLES
# ============================================================
title = "Ajouter une tâche"

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

if 'Colita_points' not in st.session_state:
    st.session_state.Colita_points = 0
if 'Xav_points' not in st.session_state:
    st.session_state.Xav_points = 0
if 'Rosalia_points' not in st.session_state:
    st.session_state.Rosalia_points = 0
if 'Chin_points' not in st.session_state:
    st.session_state.Chin_points = 0

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

if 'due_dates' not in st.session_state:
    today0 = pd.Timestamp.today().normalize()
    st.session_state.due_dates = [
        (today0 + pd.Timedelta(days=d)).date() for d in st.session_state['echeances']
    ]

# ============================================================
# TITRE + TABS
# ============================================================
md("# 1100 Gilford clean up crew")
tab1, tab2, tab3 = st.tabs(["Tâches", "Historique", "Leaderboard"])

# ============================================================
# IDENTIFICATION
# ============================================================
choixLaveur = tab1.selectbox("Qui es-tu ?", ["Xav", "Rosalia", "Colita", "Chin"])

# ============================================================
# POPUP AJOUTER UNE TÂCHE
# ============================================================
ajouterTacheBouton = tab1.button("Ajouter une tâche", type="primary")

@st.dialog(title)
def popup():
    nomTache = st.text_input("Nom de la tâche")
    echeanceTache = st.number_input("Échéance (en jours)", min_value=0, max_value=30, value=1, step=1)
    nbPointsTache = st.number_input("Nombre de points", min_value=0, max_value=100, value=10, step=1)

    recurrence = st.checkbox("Récurrence")
    if recurrence:
        nbRecurrence = st.number_input("Récurrence (en jours)", min_value=1, max_value=30, value=7, step=1)
        today_date = pd.Timestamp.today().normalize().date()
        start_date = st.date_input("Date de départ (première occurrence)", value=today_date, format="DD/MM/YYYY")
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
        if nbRecurrence > 0 and start_date is not None:
            due = start_date
            if due < today:
                delta = (today - due).days
                steps = math.ceil(delta / nbRecurrence)
                due = due + dt.timedelta(days=steps * nbRecurrence)
            due_date = due
            echeance_effective = (due_date - today).days
        else:
            due_date = (today + dt.timedelta(days=int(echeanceTache)))
            echeance_effective = int(echeanceTache)

        st.session_state.taches.append(nomTache)
        st.session_state.echeances.append(int(echeance_effective))
        st.session_state.points.append(int(nbPointsTache))
        st.session_state.status.append(False)
        st.session_state.recurrences.append(int(nbRecurrence))
        st.session_state.due_dates.append(due_date)

        ui_success("Tâche ajoutée !")
        st.rerun()

if ajouterTacheBouton:
    popup()

# ============================================================
# TABLEAU DES TÂCHES
# ============================================================
today = pd.Timestamp.today().normalize()

taches = pd.DataFrame({
    'Tâches': st.session_state['taches'],
    'Échéance (jours)': st.session_state['echeances'],
    'Date due': st.session_state['due_dates'],
    'Points': st.session_state['points'],
    'Statut': st.session_state['status'],
    'Récurrence (jours)': st.session_state['recurrences']
})
taches['Jours restants'] = (pd.to_datetime(taches['Date due']) - today).dt.days
taches = taches.sort_values(['Jours restants', 'Points'], ascending=[True, False]).reset_index(drop=True)
taches['Supprimer'] = pd.Series([False] * len(taches), dtype=bool)

visible_cols = ["Tâches", "Jours restants", "Récurrence (jours)", "Points", "Statut", "Supprimer"]

tableauTaches = tab1.data_editor(
    taches[visible_cols],
    hide_index=True,
    num_rows="fixed",
    disabled=["Tâches", "Jours restants", "Récurrence (jours)", "Points"],
    column_config={
        "Tâches": cc.TextColumn("Tâches"),
        "Jours restants": cc.NumberColumn("Jours restants"),
        "Récurrence (jours)": cc.NumberColumn("Récurrence (jours)"),
        "Points": cc.NumberColumn("Points"),
        "Statut": cc.CheckboxColumn("Statut", help="Coche si la tâche est faite"),
        "Supprimer": cc.CheckboxColumn("Supprimer", help="Cocher pour supprimer définitivement la tâche"),
    },
    key="editor_taches"
)

# ============================================================
# VALIDATION DES TÂCHES
# ============================================================
validerTacheBouton = tab1.button("Valider les tâches effectuées", type="primary")

if validerTacheBouton:
    statuts = tableauTaches["Statut"].tolist()
    indices_a_valider = [i for i, done in enumerate(statuts) if done]

    if not indices_a_valider:
        ui_info("Aucune tâche cochée.")
    else:
        source = pd.DataFrame({
            'Tâches': st.session_state['taches'],
            'Échéance (jours)': st.session_state['echeances'],
            'Date due': st.session_state['due_dates'],
            'Points': st.session_state['points'],
            'Statut': st.session_state['status'],
            'Récurrence (jours)': st.session_state['recurrences'],
        })
        source['Jours restants'] = (pd.to_datetime(source['Date due']) - today).dt.days
        source_sorted = source.sort_values(['Jours restants', 'Points'], ascending=[True, False]).reset_index()
        idx_originaux = [int(source_sorted.loc[i, 'index']) for i in indices_a_valider]

        for idx in sorted(idx_originaux, reverse=True):
            pointsGagnes = st.session_state['points'][idx]
            laveur = choixLaveur
            if laveur == "Xav": st.session_state.Xav_points += pointsGagnes
            elif laveur == "Rosalia": st.session_state.Rosalia_points += pointsGagnes
            elif laveur == "Colita": st.session_state.Colita_points += pointsGagnes
            elif laveur == "Chin": st.session_state.Chin_points += pointsGagnes

            st.session_state.historiqueDf.append(st.session_state['taches'][idx])
            st.session_state.dateDf.append(pd.Timestamp.now().strftime("%d/%m/%Y"))
            st.session_state.pointsGagnesDf.append(pointsGagnes)
            st.session_state.laveurDf.append(laveur)
            st.session_state.supprimerDf.append(False)

            rec = int(st.session_state['recurrences'][idx])
            if rec > 0:
                old_due = pd.Timestamp(st.session_state['due_dates'][idx])
                base = max(old_due, today)
                st.session_state['due_dates'][idx] = (base + pd.Timedelta(days=rec)).date()
                st.session_state['echeances'][idx] = rec
                st.session_state['status'][idx] = False
            else:
                for key in ['taches','echeances','points','status','recurrences','due_dates']:
                    st.session_state[key].pop(idx)

        ui_success("Tâche(s) validée(s) !")
        st.rerun()

# ============================================================
# SUPPRESSION DE TÂCHES
# ============================================================
supprimerTachesBtn = tab1.button("Supprimer les tâches sélectionnées", type="secondary")

if supprimerTachesBtn:
    sup_list = tableauTaches["Supprimer"].fillna(False).astype(bool).tolist()
    idx_sorted_view = [i for i, s in enumerate(sup_list) if s]
    if not idx_sorted_view:
        ui_warning("Aucune tâche à supprimer n'est sélectionnée.")
    else:
        source = pd.DataFrame({
            'Tâches': st.session_state['taches'],
            'Échéance (jours)': st.session_state['echeances'],
            'Date due': st.session_state['due_dates'],
            'Points': st.session_state['points'],
            'Statut': st.session_state['status'],
            'Récurrence (jours)': st.session_state['recurrences'],
        })
        source['Jours restants'] = (pd.to_datetime(source['Date due']) - today).dt.days
        source_sorted = source.sort_values(['Jours restants', 'Points'], ascending=[True, False]).reset_index()
        idx_originaux = [int(source_sorted.loc[i, 'index']) for i in idx_sorted_view]

        for idx in sorted(idx_originaux, reverse=True):
            for key in ['taches','echeances','points','status','recurrences','due_dates']:
                st.session_state[key].pop(idx)
        ui_success("Tâche(s) supprimée(s) avec succès.")
        st.rerun()

# ============================================================
# LEADERBOARD
# ============================================================
points = pd.DataFrame({
    'Points': [st.session_state.Colita_points, st.session_state.Xav_points,
               st.session_state.Rosalia_points, st.session_state.Chin_points],
    'Laveur': ['Colita', 'Xav', 'Rosalia', 'Chin']
})
tab3.bar_chart(points, x='Laveur', y='Points', use_container_width=True)

# ============================================================
# HISTORIQUE
# ============================================================
historique = pd.DataFrame({
    'Tâches': st.session_state['historiqueDf'],
    'Date': st.session_state['dateDf'],
    'Points gagnés': st.session_state['pointsGagnesDf'],
    'Laveur': st.session_state['laveurDf'],
})
historique['Supprimer'] = pd.Series([False] * len(historique), dtype=bool)

tableauHistorique = tab2.data_editor(
    historique,
    hide_index=True,
    num_rows="fixed",
    disabled=['Tâches','Date','Points gagnés','Laveur'],
    column_config={
        "Tâches": cc.TextColumn("Tâches"),
        "Date": cc.TextColumn("Date"),
        "Points gagnés": cc.NumberColumn("Points gagnés"),
        "Laveur": cc.TextColumn("Laveur"),
        "Supprimer": cc.CheckboxColumn("Supprimer",
            help="Cocher pour retirer la ligne et reprendre les points")
    },
    key="editor_historique"
)

supprimerHistoriqueBtn = tab2.button("Supprimer les tâches cochées de l'historique", type="secondary")
if supprimerHistoriqueBtn:
    sup_list = tableauHistorique['Supprimer'].fillna(False).astype(bool).tolist()
    idx_to_delete = [i for i,s in enumerate(sup_list) if s]
    if not idx_to_delete:
        ui_warning("Aucune tâche à supprimer n'est sélectionnée.")
    else:
        for idx in sorted(idx_to_delete, reverse=True):
            laveur = st.session_state.laveurDf[idx]
            pts = int(st.session_state.pointsGagnesDf[idx])
            if laveur == "Xav": st.session_state.Xav_points -= pts
            elif laveur == "Rosalia": st.session_state.Rosalia_points -= pts
            elif laveur == "Colita": st.session_state.Colita_points -= pts
            elif laveur == "Chin": st.session_state.Chin_points -= pts
            for k in ['historiqueDf','dateDf','pointsGagnesDf','laveurDf']:
                st.session_state[k].pop(idx)
        ui_success("Ligne(s) supprimée(s) et points repris avec succès.")
        st.rerun()
