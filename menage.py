# menage.py
# Streamlit ménage partagé entre colocs (SQLite)
# Lance: streamlit run menage.py

import sqlite3, threading
import pandas as pd
import streamlit as st
import datetime as dt
import math

# =========================
# BACKEND PARTAGÉ (SQLite)
# =========================
@st.cache_resource
def get_db():
    conn = sqlite3.connect("menage.db", check_same_thread=False)
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.row_factory = sqlite3.Row
    lock = threading.Lock()
    init_db(conn)
    return conn, lock

def init_db(conn):
    conn.executescript("""
    CREATE TABLE IF NOT EXISTS task(
      id INTEGER PRIMARY KEY,
      name TEXT NOT NULL,
      points INTEGER NOT NULL,
      recurrence_days INTEGER NOT NULL DEFAULT 0,
      due_date DATE NOT NULL,
      created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    CREATE TABLE IF NOT EXISTS history(
      id INTEGER PRIMARY KEY,
      task_name TEXT NOT NULL,
      points INTEGER NOT NULL,
      laveur TEXT NOT NULL,
      done_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    CREATE TABLE IF NOT EXISTS scores(
      laveur TEXT PRIMARY KEY,
      points INTEGER NOT NULL DEFAULT 0
    );
    """)
    conn.executemany("INSERT OR IGNORE INTO scores(laveur, points) VALUES (?,0)",
                     [("Xav",), ("Rosalia",), ("Colita",), ("Chin",)])
    conn.commit()

def fetch_tasks(conn):
    q = """
    SELECT id as ID,
           name as 'Tâches',
           points as 'Points',
           recurrence_days as 'Récurrence (jours)',
           due_date as 'Date due'
    FROM task
    ORDER BY date(due_date) ASC, points DESC
    """
    df = pd.read_sql_query(q, conn, parse_dates=["Date due"])
    today = pd.Timestamp.today().normalize()
    if not df.empty:
        df["Jours restants"] = (pd.to_datetime(df["Date due"]) - today).dt.days
    else:
        df = pd.DataFrame(columns=["ID","Tâches","Points","Récurrence (jours)","Date due","Jours restants"])
    return df

def add_task(conn, lock, name, points, recurrence_days, due_date):
    if not name or str(name).strip() == "":
        return
    with lock:
        conn.execute(
            "INSERT INTO task(name, points, recurrence_days, due_date) VALUES (?,?,?,?)",
            (name.strip(), int(points), int(recurrence_days), str(due_date))
        )
        conn.commit()

def delete_tasks(conn, lock, ids):
    if not ids: return
    with lock:
        conn.executemany("DELETE FROM task WHERE id=?", [(int(i),) for i in ids])
        conn.commit()

def complete_tasks(conn, lock, ids, laveur):
    if not ids: return
    today = pd.Timestamp.today().normalize()
    with lock:
        cur = conn.cursor()
        for tid in ids:
            row = cur.execute(
                "SELECT name, points, recurrence_days, due_date FROM task WHERE id=?",
                (int(tid),)
            ).fetchone()
            if row is None:
                continue
            name, pts, rec, due = row["name"], int(row["points"]), int(row["recurrence_days"]), pd.Timestamp(row["due_date"])

            # 1) Score & historique
            cur.execute("UPDATE scores SET points = points + ? WHERE laveur=?", (pts, laveur))
            cur.execute("INSERT INTO history(task_name, points, laveur) VALUES (?,?,?)",
                        (name, pts, laveur))

            # 2) Récurrence ou suppression
            if rec > 0:
                base = max(due.normalize(), today)  # si en retard, repart d'aujourd'hui
                new_due = (base + pd.Timedelta(days=rec)).date()
                cur.execute("UPDATE task SET due_date=? WHERE id=?", (str(new_due), int(tid)))
            else:
                cur.execute("DELETE FROM task WHERE id=?", (int(tid),))
        conn.commit()

def fetch_scores(conn):
    # garantit l’ordre constant des barres
    df = pd.read_sql_query("SELECT laveur as 'Laveur', points as 'Points' FROM scores", conn)
    order = ["Colita","Xav","Rosalia","Chin"]
    df["sortkey"] = df["Laveur"].apply(lambda x: order.index(x) if x in order else 999)
    df = df.sort_values("sortkey").drop(columns=["sortkey"])
    return df

def fetch_history(conn):
    q = """
    SELECT id as ID, task_name as 'Tâches', laveur as 'Laveur',
           points as 'Points gagnés',
           strftime('%d/%m/%Y', done_at) as 'Date'
    FROM history
    ORDER BY done_at DESC, id DESC
    """
    return pd.read_sql_query(q, conn)

def undo_history_rows(conn, lock, ids):
    if not ids: return
    with lock:
        cur = conn.cursor()
        for hid in ids:
            r = cur.execute("SELECT laveur, points FROM history WHERE id=?", (int(hid),)).fetchone()
            if r:
                laveur, pts = r["laveur"], int(r["points"])
                # rollback points (empêche négatif)
                current = cur.execute("SELECT points FROM scores WHERE laveur=?", (laveur,)).fetchone()[0]
                new_pts = max(0, int(current) - pts)
                cur.execute("UPDATE scores SET points=? WHERE laveur=?", (new_pts, laveur))
                cur.execute("DELETE FROM history WHERE id=?", (int(hid),))
        conn.commit()

# =========================
# UI / APP
# =========================
st.set_page_config(page_title="1100 Gilford clean up crew", page_icon="🧹", layout="wide")

conn, lock = get_db()

st.header("1100 Gilford clean up crew")
tab1, tab2, tab3 = st.tabs(["Tâches", "Historique", "Leaderboard"])

# Qui es-tu ?
choixLaveur = tab1.selectbox("Qui es-tu ?", ["Xav", "Rosalia", "Colita", "Chin"], index=1)

# --- POPUP AJOUTER UNE TÂCHE ---
title = "Ajouter une tâche"
ajouterTacheBouton = tab1.button("Ajouter une tâche", type="primary")

@st.dialog(title)
def popup():
    nomTache = st.text_input("Nom de la tâche")
    echeanceTache = st.number_input("Échéance (en jours)", min_value=0, max_value=365, value=1, step=1)
    nbPointsTache = st.number_input("Nombre de points", min_value=0, max_value=1000, value=10, step=1)

    recurrence = st.checkbox("Récurrence")
    if recurrence:
        nbRecurrence = st.number_input("Récurrence (en jours)", min_value=1, max_value=365, value=7, step=1)
        today_date = pd.Timestamp.today().normalize().date()
        start_date = st.date_input("Date de départ (première occurrence)", value=today_date, format="DD/MM/YYYY")
    else:
        nbRecurrence = 0
        start_date = None

    c1, c2 = st.columns(2)
    with c1:
        valider = st.button("Valider", type="primary")
    with c2:
        annuler = st.button("Annuler", type="secondary")

    if valider:
        today = pd.Timestamp.today().normalize().date()
        if nbRecurrence > 0 and start_date is not None:
            due = start_date
            if due < today:
                delta = (today - due).days
                steps = math.ceil(delta / nbRecurrence)
                due = due + dt.timedelta(days=steps * nbRecurrence)
            due_date = due
        else:
            due_date = today + dt.timedelta(days=int(echeanceTache))

        add_task(conn, lock, nomTache, nbPointsTache, nbRecurrence, due_date)
        st.success("Tâche ajoutée !")
        st.rerun()

if ajouterTacheBouton:
    popup()

# --- TABLE DES TÂCHES (partagée) ---
tasks_df = fetch_tasks(conn)
if not tasks_df.empty:
    tasks_df = tasks_df.sort_values(["Jours restants", "Points"], ascending=[True, False]).reset_index(drop=True)
    tasks_df["Statut"] = False
    tasks_df["Supprimer"] = False
else:
    tasks_df = pd.DataFrame(columns=["ID","Tâches","Jours restants","Récurrence (jours)","Points","Statut","Supprimer"])

visible_cols = ["ID","Tâches","Jours restants","Récurrence (jours)","Points","Statut","Supprimer"]
editor = tab1.data_editor(
    tasks_df[visible_cols],
    width="stretch",
    hide_index=True,
    num_rows="fixed",
    column_config={
        "ID": st.column_config.Column("ID", help="Identifiant", disabled=True, required=False),
        "Statut": st.column_config.CheckboxColumn("Statut", help="Coche si la tâche est faite"),
        "Supprimer": st.column_config.CheckboxColumn("Supprimer", help="Cocher pour supprimer définitivement la tâche"),
    },
    disabled=["ID","Tâches","Jours restants","Récurrence (jours)","Points"],
    key="ed_tasks_shared"
)

# --- Valider les tâches cochées ---
if tab1.button("Valider les tâches effectuées", type="primary"):
    if len(editor) == 0 or "Statut" not in editor:
        st.info("Aucune tâche cochée.")
    else:
        ids_done = [int(editor.loc[i, "ID"]) for i, done in enumerate(editor["Statut"].tolist()) if done]
        if not ids_done:
            st.info("Aucune tâche cochée.")
        else:
            complete_tasks(conn, lock, ids_done, choixLaveur)
            st.success("Tâche(s) validée(s) !")
            st.rerun()

# --- Supprimer les tâches cochées ---
if tab1.button("Supprimer les tâches sélectionnées", type="secondary"):
    if len(editor) == 0 or "Supprimer" not in editor:
        st.info("Aucune tâche à supprimer.")
    else:
        ids_del = [int(editor.loc[i, "ID"]) for i, s in enumerate(editor["Supprimer"].tolist()) if s]
        if not ids_del:
            st.info("Aucune tâche à supprimer.")
        else:
            delete_tasks(conn, lock, ids_del)
            st.success("Tâche(s) supprimée(s).")
            st.rerun()

# --- LEADERBOARD (partagé) ---
scores = fetch_scores(conn)
tab3.bar_chart(data=scores, x="Laveur", y="Points", use_container_width=True)

# --- HISTORIQUE (partagé) ---
hist = fetch_history(conn)
if hist.empty:
    hist = pd.DataFrame(columns=["ID","Tâches","Laveur","Points gagnés","Date"])
hist["Supprimer"] = False

editor_hist = tab2.data_editor(
    hist[["ID","Tâches","Laveur","Points gagnés","Date","Supprimer"]],
    width="stretch",
    hide_index=True,
    num_rows="fixed",
    column_config={
        "ID": st.column_config.Column("ID", disabled=True),
        "Supprimer": st.column_config.CheckboxColumn("Supprimer", help="Retirer la ligne et reprendre les points")
    },
    disabled=["ID","Tâches","Laveur","Points gagnés","Date"],
    key="ed_history_shared"
)

if tab2.button("Supprimer les tâches cochées de l'historique", type="secondary"):
    if len(editor_hist) == 0 or "Supprimer" not in editor_hist:
        st.info("Aucune ligne cochée.")
    else:
        ids_hist = [int(editor_hist.loc[i, "ID"]) for i, s in enumerate(editor_hist["Supprimer"].tolist()) if s]
        if not ids_hist:
            st.info("Aucune ligne cochée.")
        else:
            undo_history_rows(conn, lock, ids_hist)
            st.success("Ligne(s) supprimée(s) et points repris.")
            st.rerun()
