import streamlit as st
import pandas as pd
import datetime as dt
import math
from streamlit import column_config as cc
import html as py_html  # échappement pour HTML brut

# ============================================================
# MODE COMPAT iOS : bypasse TOUT Markdown/GFM & labels
# ============================================================
if "compat_ios" not in st.session_state:
    # ON par défaut pour éviter le crash au 1er rendu sur Safari iOS
    st.session_state.compat_ios = True

def plain_text(s: str):
    """Affiche du texte brut (HTML échappé), sans Markdown/GFM."""
    safe = py_html.escape(s)
    if hasattr(st, "html"):  # Streamlit >= 1.36
        st.html(f"<div>{safe}</div>")
    else:
        st.markdown(f"<div>{safe}</div>", unsafe_allow_html=True)

def md(s: str):
    """Markdown normal, ou texte brut si compat iOS."""
    if st.session_state.get("compat_ios"):
        plain_text(s)
    else:
        st.markdown(s)

def ui_success(msg: str):
    plain_text("✅ " + msg) if st.session_state.get("compat_ios") else st.success(msg)

def ui_info(msg: str):
    plain_text("ℹ️ " + msg) if st.session_state.get("compat_ios") else st.info(msg)

def ui_warning(msg: str):
    plain_text("⚠️ " + msg) if st.session_state.get("compat_ios") else st.warning(msg)

def ui_error(msg: str):
    plain_text("❌ " + msg) if st.session_state.get("compat_ios") else st.error(msg)

# -------- Wrappers de widgets sans labels (compat iOS) --------
def sb_selectbox(label_text: str, options, key=None, **kwargs):
    if st.session_state.get("compat_ios"):
        plain_text(label_text)
        return st.selectbox("\u00A0", options, key=key, **kwargs)
    else:
        return st.selectbox(label_text, options, key=key, **kwargs)

def sb_button(label_text: str, key=None, **kwargs):
    if st.session_state.get("compat_ios"):
        c1, c2 = st.columns([1, 6])
        with c1:
            clicked = st.button("\u00A0", key=key, **kwargs)
        with c2:
            plain_text(label_text)
        return clicked
    else:
        return st.button(label_text, key=key, **kwargs)

def sb_text_input(label_text: str, key=None, **kwargs):
    if st.session_state.get("compat_ios"):
        plain_text(label_text)
        return st.text_input("\u00A0", key=key, **kwargs)
    else:
        return st.text_input(label_text, key=key, **kwargs)

def sb_number_input(label_text: str, key=None, **kwargs):
    if st.session_state.get("compat_ios"):
        plain_text(label_text)
        return st.number_input("\u00A0", key=key, **kwargs)
    else:
        return st.number_input(label_text, key=key, **kwargs)

def sb_checkbox(label_text: str, key=None, **kwargs):
    if st.session_state.get("compat_ios"):
        plain_text(label_text)
        return st.checkbox("\u00A0", key=key, **kwargs)
    else:
        return st.checkbox(label_text, key=key, **kwargs)

def sb_date_input(label_text: str, key=None, **kwargs):
    if st.session_state.get("compat_ios"):
        plain_text(label_text)
        return st.date_input("\u00A0", key=key, **kwargs)
    else:
        return st.date_input(label_text, key=key, **kwargs)

# Sidebar: libellé de la checkbox en HTML brut (pas Markdown)
with st.sidebar:
    plain_text("Mode compat iOS (désactiver Markdown/labels)")
    st.checkbox("\u00A0", key="compat_ios", value=st.session_state.compat_ios)

# ============================================================
# CONSTANTES / ÉTAT
# ============================================================
TITLE = "Ajouter une tâche"

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

# DATES D'ÉCHÉANCE
if 'due_dates' not in st.session_state:
    today0 = pd.Timestamp.today().normalize()
    st.session_state.due_dates = [(today0 + pd.Timedelta(days=d)).date()
                                  for d in st.session_state['echeances']]

# ============================================================
# TITRE
# ============================================================
md("# 1100 Gilford clean up crew")

# ============================================================
# POPUP AJOUTER UNE TÂCHE (titre neutre en compat)
# ============================================================
dialog_title = " " if st.session_state.get("compat_ios") else TITLE

@st.dialog(dialog_title)
def popup():
    nomTache = sb_text_input("Nom de la tâche")
    echeanceTache = sb_number_input("Échéance (en jours)", min_value=0, max_value=30, value=1, step=1)
    nbPointsTache = sb_number_input("Nombre de points", min_value=0, max_value=100, value=10, step=1)

    recurrence = sb_checkbox("Récurrence")
    if recurrence:
        nbRecurrence = sb_number_input("Récurrence (en jours)", min_value=1, max_value=30, value=7, step=1)
        today_date = pd.Timestamp.today().normalize().date()
        start_date = sb_date_input("Date de départ (première occurrence)", value=today_date, format="DD/MM/YYYY")
    else:
        nbRecurrence = 0
        start_date = None

    c1, c2 = st.columns(2)
    with c1:
        validerBouton = sb_button("Valider", key="btn_popup_valider", type="primary")
    with c2:
        _ = sb_button("Annuler", key="btn_popup_annuler", type="secondary")

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

# ============================================================
# RENDUS DES 3 PAGES (sans tabs en compat iOS)
# ============================================================
def render_page_taches():
    # Identification
    laveur = sb_selectbox("Qui es-tu ?", ["Xav", "Rosalia", "Colita", "Chin"], key="whoami")

    # Bouton Ajouter une tâche
    if sb_button("Ajouter une tâche", key="btn_add_task", type="primary"):
        popup()

    # Tableau des tâches
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
    tableauTaches = st.data_editor(
        taches[visible_cols],
        hide_index=True,
        num_rows="fixed",
        disabled=["Tâches", "Jours restants", "Récurrence (jours)", "Points"],
        column_config={
            "Tâches": cc.TextColumn("Tâches"),
            "Jours restants": cc.NumberColumn("Jours restants"),
            "Récurrence (jours)": cc.NumberColumn("Récurrence (jours)"),
            "Points": cc.NumberColumn("Points"),
            "Statut": cc.CheckboxColumn("Statut"),
            "Supprimer": cc.CheckboxColumn("Supprimer"),
        },
        key="editor_taches"
    )

    # Bouton SUPPRIMER
    if sb_button("Supprimer les tâches sélectionnées", key="btn_del_tasks", type="secondary"):
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

    # Bouton VALIDER
    if sb_button("Valider les tâches effectuées", key="btn_validate_tasks", type="primary"):
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
                if laveur == "Xav":
                    st.session_state.Xav_points += pointsGagnes
                elif laveur == "Rosalia":
                    st.session_state.Rosalia_points += pointsGagnes
                elif laveur == "Colita":
                    st.session_state.Colita_points += pointsGagnes
                elif laveur == "Chin":
                    st.session_state.Chin_points += pointsGagnes

                st.session_state.historiqueDf.append(st.session_state['taches'][idx])
                st.session_state.dateDf.append(pd.Timestamp.now().strftime("%d/%m/%Y"))
                st.session_state.pointsGagnesDf.append(pointsGagnes)
                st.session_state.laveurDf.append(laveur)

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

def render_page_historique():
    historique = pd.DataFrame({
        'Tâches': st.session_state['historiqueDf'],
        'Date': st.session_state['dateDf'],
        'Points gagnés': st.session_state['pointsGagnesDf'],
        'Laveur': st.session_state['laveurDf'],
    })
    historique['Supprimer'] = pd.Series([False] * len(historique), dtype=bool)

    table = st.data_editor(
        historique,
        hide_index=True,
        num_rows="fixed",
        disabled=['Tâches','Date','Points gagnés','Laveur'],
        column_config={
            "Tâches": cc.TextColumn("Tâches"),
            "Date": cc.TextColumn("Date"),
            "Points gagnés": cc.NumberColumn("Points gagnés"),
            "Laveur": cc.TextColumn("Laveur"),
            "Supprimer": cc.CheckboxColumn("Supprimer"),
        },
        key="editor_historique"
    )

    if sb_button("Supprimer les tâches cochées de l'historique", key="btn_del_history", type="secondary"):
        sup_list = table['Supprimer'].fillna(False).astype(bool).tolist() if len(table) else []
        idx_to_delete = [i for i,s in enumerate(sup_list) if s]
        if not idx_to_delete:
            ui_warning("Aucune tâche à supprimer n'est sélectionnée.")
        else:
            for idx in sorted(idx_to_delete, reverse=True):
                laveur = st.session_state.laveurDf[idx]
                pts = int(st.session_state.pointsGagnesDf[idx])
                if laveur == "Xav":
                    st.session_state.Xav_points -= pts
                elif laveur == "Rosalia":
                    st.session_state.Rosalia_points -= pts
                elif laveur == "Colita":
                    st.session_state.Colita_points -= pts
                elif laveur == "Chin":
                    st.session_state.Chin_points -= pts
                for k in ['historiqueDf','dateDf','pointsGagnesDf','laveurDf']:
                    st.session_state[k].pop(idx)
            ui_success("Ligne(s) supprimée(s) et points repris avec succès.")
            st.rerun()

def render_page_leaderboard():
    points = pd.DataFrame({
        'Points': [st.session_state.Colita_points, st.session_state.Xav_points,
                   st.session_state.Rosalia_points, st.session_state.Chin_points],
        'Laveur': ['Colita', 'Xav', 'Rosalia', 'Chin']
    })
    st.bar_chart(points, x='Laveur', y='Points', use_container_width=True)

# ============================================================
# ROUTAGE : tabs normaux (desktop) vs sélecteur (compat iOS)
# ============================================================
if st.session_state.get("compat_ios"):
    plain_text("Navigation")
    page = st.selectbox("\u00A0", ["Tâches", "Historique", "Leaderboard"], index=0, key="page_select")
    if page == "Tâches":
        render_page_taches()
    elif page == "Historique":
        render_page_historique()
    else:
        render_page_leaderboard()
else:
    tab1, tab2, tab3 = st.tabs(["Tâches", "Historique", "Leaderboard"])
    with tab1:
        render_page_taches()
    with tab2:
        render_page_historique()
    with tab3:
        render_page_leaderboard()
