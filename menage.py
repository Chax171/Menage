import streamlit as st
import pandas as pd

st.header("1100 Gilford clean up crew")

#TABS
tab1, tab2, tab3= st.tabs(["Tâches", "Historique", "Leaderboard"])

#IDENTIFIATION
choixLaveur = tab1.selectbox("Qui es-tu?",
 ["Xav", "Rosalia", "Colita", "Chin"])


#BOUTON AJOUTER UNE TACHE
tab1.button("Ajouter une tâche",
    type = "secondary")


#DATAFRAME DES TACHES
tachesDf = ['Sortir les poubelles', 'Sortir le recyclage', 'Faire les litières']
echeanceDf = ['1 jours', '2 jours', '0 Aujourd\'hui']
pointsDf = [10, 5, 15]
statutDf = [False, False, True]



taches = pd.DataFrame({
    'Tâches': tachesDf,
    'Échéance': echeanceDf,
    'Points': pointsDf,
    'Statut': statutDf
})

#TABLEAU DES TACHES
tab1.data_editor(taches,
    width="stretch",
    height="auto",
    use_container_width=None,
    hide_index=True,
    column_order=None,
    column_config=None,
    num_rows="fixed",
    disabled=['Tâches', 'Échéance', 'Points'],
    key=None,
    on_change=None,
    args=None,
    kwargs=None,
    row_height=None)

#BOUTON VALIDER
tab1.button("Valider les tâches effectuées", 
    type = "primary")
    
#POINTS GAGNÉS PAR LE LAVEUR
Colita_points = 100
Xav_points = 10
Rosalia_points = 50
Chin_points = 1000

points = pd.DataFrame({
    'Points': [Colita_points, Xav_points, Rosalia_points, Chin_points],
    'Laveur': ['Colita', 'Xav', 'Rosalia', 'Chin']
})

#LEADERBOARD
tab3.bar_chart(data=points,
    x='Laveur',
    y='Points',
    width=0,
    height=0,
    use_container_width=True)

#TABLEAU HISTORIQUE
historiqueDf = ['taches 1', 'taches 2', 'taches 3']
dateDf = ['01/01/2024', '02/01/2024', '03/01/2024']
pointsGagnesDf = [10, 20, 15]
laveurDf = ['Xav', 'Rosalia', 'Chin']

historique = pd.DataFrame({
    'Tâches': historiqueDf,
    'Date': dateDf,
    'Points gagnés': pointsGagnesDf,
    'Laveur': laveurDf,
    'Récupération': [False, False, False]
})

tab2.data_editor(historique,
    width="stretch",
    height="auto",
    use_container_width=None,
    hide_index=True,
    column_order=None,
    column_config=None,
    num_rows="fixed",
    disabled=['Tâches', 'Date', 'Points gagnés', 'Laveur'],
    key=None,
    on_change=None,
    args=None,
    kwargs=None,
    row_height=None)

#BOUTON RECUPERATION
tab2.button('Récupérer la tâche',
    type = "secondary")