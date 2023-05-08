import streamlit as st
import pandas as pd
import numpy as np
import datetime
from streamlit_timeline import st_timeline
import matplotlib.pyplot as plt
import matplotlib
import json
import holoviews as hv
import hvplot.pandas
import extra_streamlit_components as stx
from streamlit_option_menu import option_menu

st.set_page_config(layout="wide")
hv.extension('bokeh')

# st.title("Planning Cerisiers 2023")

# Add a text input for the google sheet url

# Define the cookie key
# Define the URL query parameter key
URL_PARAM = "url"

# Load the URL from the cookie, if it exists
cookie_manager = stx.CookieManager()
url = cookie_manager.get(URL_PARAM)

with st.sidebar:    
    selected=option_menu("Menu",["Calendrier","Plan","Données"],icons=["calendar","map","table"], menu_icon="cast", default_index=0)


#Get categorical cmap from matplotlib
cmap = plt.get_cmap("hsv")

#Create a function to get a color from text
def get_color(string):
    color = cmap(hash(string) % 256)  # Get a color from cmap
    #Make it less flashy
    color = np.array(color) * 0.8
    #Convert to hex
    color = matplotlib.colors.rgb2hex(color)
    return color

def load_clients():
    if url:
        try:
            sheet_id = url.split("/")[-2]
            sheet_name = "sejour"
            # Encode sheet_name to url format
            full_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&sheet={sheet_name}"
            df = pd.read_csv(full_url)
            df['Date d\'arrivée'] = df['Date d\'arrivée'].apply(lambda x: datetime.datetime.strptime(x, "%d/%m/%Y").date())
            df['Date de départ'] = df['Date de départ'].apply(lambda x: datetime.datetime.strptime(x, "%d/%m/%Y").date()) 
            # "Liste des clients",df
            return df
        except:
            st.error("Le lien ne fonctionne pas !")
            return pd.DataFrame()
    else:
        return pd.DataFrame()

if selected=="Données":
    url_input = st.text_input("Entrer le lien", value=url)
    if st.button("Charger"):
        url = url_input.strip()
        cookie_manager.set(URL_PARAM, url, datetime.datetime(year=2024, month=2, day=2))
    if url!='None':    
        sejours=load_clients()
        if sejours.shape[0] > 0:
            sejours
        else:
            url_img= "https://1.bp.blogspot.com/-bcTOkJU4joo/X5RMnyGIAjI/AAAAAAACu6s/XEWr4uUt8R4z09a9do-dj1kDH0QD1IYlwCLcBGAsYHQ/w1200-h630-p-k-no-nu/Partager.png"
            st.markdown("Pour charger les données, il faut que la feuille s'appelle **sejour** et qu'elle contienne au moins les colonnes suivantes : **Nom du client**, **Emplacement**, **Date d'arrivée**, **Date de départ**")
            st.markdown('Il faut également que la feuille soit partagée en cliquant sur le bouton "Partager" en haut à droite de la feuille et en rendant le lien accessible à tous.')
            st.image(url_img,width=200)
            st.markdown("Après avoir cliqué sur Partager, sous 'Accès général' il faut cliquer sur 'Limité' et choisir 'Tout les utilisateurs qui ont le lien'.")
            st.markdown("Une fois la feuille partagée, il faut copier le lien et le coller dans le champ ci-dessus.")
def get_timeline():
    """
    Build timeline from clients with st_timeline
    """
    sejours = load_clients()
    # If sejours is not empty
    if sejours.shape[0] > 0:
        emplacement_groups = [
            {"id": x, "content": f"Empl. {x}"} for x in range(1, 26)
        ]
        data = pd.DataFrame()
        data["id"] = sejours.index
        data["group"] = sejours["Emplacement"]
        data["start"] = sejours["Date d'arrivée"]
        # Convert to datetime
        data["start"] = data["start"].apply(
            lambda x: str(x))
        data["end"] = sejours["Date de départ"]
        data["end"] = data["end"].apply(
            lambda x: str(x))
        data["content"] = sejours["Nom du client"]
  
        items = data.to_dict("records")
        for i, item in enumerate(items):
            id = item["id"]
            # Get sejour line that matches id
            sejour = sejours[sejours.index == id].T
            items[i]["title"] = sejour.to_html()
        # Set color by content
        options = dict(
            editable=False,
            minHeight=800,
            width="100%",
            showCurrentTime=True,
            verticalScroll=True,
            preferZoom=True,
            showWeekScale=True,
        )
        st_timeline(items, emplacement_groups, options)
 
def get_day():
    """
    Load client and return info for selected day.
    It should return a dict with keys = Emplacement, and values = client or None
    """
    sejours = load_clients()
    # If sejours is not empty
    if sejours.shape[0] > 0:
        # Convert date to string
        day=date_slider
        # Filter sejours if day is between "Date d'arrivée" and "Date de départ"
        sejours = sejours[sejours["Date d'arrivée"] <= day][sejours["Date de départ"] >= day]

        # Create dict with emplacement as key and client as value
        return sejours
    else:
        return pd.DataFrame()

def read_dot_file():
    with open('dots.json') as f:
        data = json.load(f)
    return pd.DataFrame(data)

dots = read_dot_file()
#Add column Dispo to dots
dots['Dispo']=True
map = hv.RGB.load_image('map.png').opts(width=1000,height=600)

def get_map(day):
    """
    Build a map from map.png
    """
    #Get unique values of emplacement
    emplacements = day['Emplacement'].unique()

    #Set Dispo to False for emplacements in day
    dots.loc[dots['Emplacement'].isin(emplacements),'Dispo']=False
    #Duplicate row in dots if there are more than one client in the same emplacement in day
    nb_clients=day.groupby('Emplacement').size().reset_index(name='counts')
    #If count > 1, duplicate row in dots
    dots.merge(nb_clients[nb_clients['counts']>1],on='Emplacement',how='left')
    dots['Nom du client']=dots['Emplacement'].apply(lambda x: day[day['Emplacement']==x]['Nom du client'].values[0] if x in emplacements else None)
    day.set_index(keys='Emplacement',inplace=True)
    day=day.drop(columns=['Horodateur'])
    day=day[['Nom du client', "Date d'arrivée", 'Date de départ', "Nombre d'adultes", 'Enfants de - 2 ans',
       'Enfants de 2-7 ans', 'Enfants de 8-17 ans', 'Véhicule', 'Electricité',
       'Frigo', 'Animaux']]
    col1, col2 = st.columns(2)
    with col2:
        st.markdown("#### Clients de la journée")
        day
    with col1:        
        #Use cmap that goes from green to red
        scatter=dots[dots['Dispo']].hvplot.scatter(x='x', y='y', size=800,alpha=0.5, legend=False,hover_cols=['Emplacement','Nom du client'],color='green')
        scatter=scatter*dots[~dots['Dispo']].hvplot.scatter(x='x', y='y', size=800,alpha=0.5, legend=False,hover_cols=['Emplacement','Nom du client'],color='red')
        #Only keep Emplacement column for hover
        map_with_dots=map*scatter
        map_with_dots.opts(width=1000, height=600, xaxis=None, yaxis=None)
        #Get bokeh figure
        p = hv.render(map_with_dots, backend='bokeh')

        st.bokeh_chart(p, use_container_width=True)

if selected!='Données':
    sejours=load_clients()
    if sejours.shape[0] > 0:

        if selected=="Calendrier":
            df = get_timeline()

        elif selected=="Plan":
            ds_value = datetime.date.today() if datetime.date(2023,6,1) <= datetime.date.today() <= datetime.date(2023,9,30) else datetime.date(2023,6,1)
            date_slider=st.slider('Date',datetime.date(2023,6,1),datetime.date(2023,9,30),ds_value,format="DD/MM/YYYY")
            day=get_day()
            get_map(day)
            
    else:   
        st.warning("Mauvais url du Google Sheet ou pas de données")


