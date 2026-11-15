import sys,os,csv
import geopandas as gpd
import pandas as pd
from geodatasets import get_path
import tempfile
import folium
import rasterio
import jupyter_loopback

import localtileserver
#print(localtileserver.Report())

from localtileserver import get_folium_tile_layer
from localtileserver import TileClient
from folium import Map
import matplotlib.pyplot as plt
from shapely.geometry import Point
from PySide6.QtCore import QDate, Qt,QUrl
from PySide6.QtGui import QIcon

from shapely.geometry import Point

from PySide6.QtWebEngineCore import QWebEngineSettings
from PySide6.QtWebEngineWidgets import QWebEngineView

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget,QGroupBox,QTabWidget,
    QVBoxLayout, QHBoxLayout, QLabel, QFrame,QCheckBox,QPushButton,
    QLineEdit,QListWidget,QListWidgetItem,
)

jupyter_loopback.enable_comm_bridge()
localtileserver.enable_jupyter_loopback(8000)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("MARPS")
        self.resize(1200, 800)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
    
       
        main_layout = QHBoxLayout(central_widget)

        
        right_container = QWidget()
        right_layout = QVBoxLayout(right_container)
        right_layout.setContentsMargins(0, 0, 0, 0)

      
        header = QFrame()
        header.setStyleSheet("background-color: #802716;")
        header.setFixedHeight(50)
        header_layout = QVBoxLayout(header)
        

        
        date_actuelle = QDate.currentDate()

       
        texte_date = date_actuelle.toString(Qt.ISODate)  
       
       
        self.label = QLabel(f"DATE: {texte_date}")

        header_layout.addWidget(self.label)

       
        content = QFrame()
        content.setStyleSheet("background-color: #ffffff;")
        content_layout = QVBoxLayout(content)

       
        self.lbl_info = QLabel("Informations géographiques")       
        content_layout.addWidget(self.lbl_info)

        map_box = QGroupBox("Carte Interactive (Folium / Explore)")
        map_layout = QVBoxLayout(map_box)
        
      
        self.web_view = QWebEngineView()
       
        self.web_view.settings().setAttribute(QWebEngineSettings.WebAttribute.LocalContentCanAccessRemoteUrls,True)
        
      
        right_layout.addWidget(header)
        right_layout.addWidget(self.web_view)
        
        
        sidebar = QFrame()
        sidebar.setStyleSheet("background-color: #802716; color: white;")
        sidebar.setFixedWidth(200)
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        
        options_group = QGroupBox("FILTRAGE DES PLANS")
        options_layout = QVBoxLayout(options_group)
        
        self.chk_satellite = QCheckBox("TOPOLOGY")
        self.chk_routes = QCheckBox("WATER")
        self.chk_relief = QCheckBox("GEOLOGICALS ZONES")
        self.chk_relief.setChecked(False)  

      
        options_layout.addWidget(self.chk_satellite)
        options_layout.addWidget(self.chk_routes)
        options_layout.addWidget(self.chk_relief)

        
        group_recherche=QFrame()
        recherche_layout = QVBoxLayout(group_recherche)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Find a marquer")
        self.search_input.textChanged.connect(self.filter_list)

       
        self.list_widget = QListWidget()

        self.list_widget.setSortingEnabled(True)
        self.list_widget.itemClicked.connect(self.centrer_sur_point)

       
        self.search_input.textChanged.connect(self.filter_list)
        
       
        self.entree0 = QLineEdit()
        self.entree0.setPlaceholderText("Nom")

        self.entree1 = QLineEdit()
        self.entree1.setPlaceholderText("Latitude")

        self.entree2 = QLineEdit()
        self.entree2.setPlaceholderText("Longitude")

        self.entree3 = QLineEdit()
        self.entree3.setPlaceholderText("Details")

       
        self.bouton = QPushButton("Valider")


        self.resultat = QLabel("")

  
        coord_group = QGroupBox("COORDONATES SITE")
        layout_champs = QVBoxLayout(coord_group)
        layout_champs.addWidget(self.entree0)
        layout_champs.addWidget(self.entree3)
        layout_champs.addWidget(self.entree1)
        layout_champs.addWidget(self.entree2)
        layout_champs.addWidget(self.bouton)
        layout_champs.addWidget(self.resultat)


     
        sidebar_layout.addWidget(options_group)       
        sidebar_layout.addWidget(self.search_input)     
        sidebar_layout.addWidget(self.list_widget)
        sidebar_layout.addWidget(coord_group)
      


        main_layout.addWidget(right_container)
        main_layout.addWidget(sidebar)
        self.showMaximized()

      
        self.load_nybb_map()

        self.bouton.clicked.connect(self.valider)

    def valider(self):
    
        try:
            nom = self.entree0.text().strip()
            description = self.entree3.text().strip()

            latitude = float(self.entree1.text())
            longitude = float(self.entree2.text())

            if not nom:
                raise ValueError

            if not (-90 <= latitude <= 90):
                raise ValueError

            if not (-180 <= longitude <= 180):
                raise ValueError


            ajouter_point(
                nom,
                latitude,
                longitude,
                description
            )

          
            self.gdf_points = charger_points_csv()
            self.actualiser_liste_points()

     
            self.actualiser_carte(
                centre=[latitude, longitude],
                zoom=8
            )

    
            self.resultat.setText("Point enregistré !")

         
            self.entree0.clear()
            self.entree1.clear()
            self.entree2.clear()
            self.entree3.clear()

        except ValueError:
            self.resultat.setText("Coordonnées invalides !")
        
    def actualiser_carte(self,centre=None, zoom=8):

        
        map_kwds = {"zoom_start": zoom}

        if centre is not None:
            map_kwds["location"] = centre

   
        
        m = self.gdf_base.explore(
        column="area",
        cmap="viridis",
        tiles="OpenStreetMap",
        legend=True,
        zoom_start=zoom,
        location=centre,
        fit_bounds=(centre is None)
        )
        
   
        points_affichage = self.gdf_points.to_crs("EPSG:4326")

        for _, ligne in points_affichage.iterrows():

            latitude = ligne.geometry.y
            longitude = ligne.geometry.x

            folium.CircleMarker(
                location=[latitude, longitude],
                radius=10,
                color="white",
                weight=3,
                fill=True,
                fill_color="red",
                fill_opacity=1,

              
                tooltip=ligne["nom"],

              
                popup=folium.Popup(
                    f"""
                    <h3>{ligne['nom']}</h3>
                    <p>{ligne['description']}</p>
                    <p>Latitude : {ligne.geometry.y:.5f}</p>
                    <p>Longitude : {ligne.geometry.x:.5f}</p>
                    """,
                    max_width=300
                )

            ).add_to(m)

  
        html_path = os.path.abspath("map_test.html")

        m.save(html_path)
  
        self.web_view.setUrl(
            QUrl.fromLocalFile(html_path)
        )
        return(m)
    
    def actualiser_liste_points(self):

        self.list_widget.clear()

        for nom in self.gdf_points["nom"].dropna().unique():
            self.list_widget.addItem(str(nom))
    def centrer_sur_point(self, item):

       
        nom = item.text()

       
        point = self.gdf_points[
            self.gdf_points["nom"] == nom
        ]

        if point.empty:
            return

       
        latitude = point.iloc[0].geometry.y
        longitude = point.iloc[0].geometry.x

        
        self.actualiser_carte(
            centre=[latitude, longitude],
            zoom=10
        )
    def load_nybb_map(self):

        print("Loading...")

        path = get_path("nybb")
        gdf = gpd.read_file(path)

        gdf = gdf.set_index("BoroName")
        gdf["area"] = gdf.area

        self.gdf_base = gdf       

        
        self.gdf_points = charger_points_csv()
        self.actualiser_liste_points()

        
        self.actualiser_carte()
        
    def filter_list(self, text):
        
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
           
            match = text.lower() in item.text().lower()
            item.setHidden(not match)
    

    def on_satellite_toggled(self, checked):
        print("Satellite :", "activé" if checked else "désactivé")


def initialiser_csv():
    if not os.path.exists(FICHIER_CSV):
        with open(FICHIER_CSV, mode='w', newline='', encoding='utf-8') as fichier:
            writer = csv.writer(fichier)
            writer.writerow(["Nom", "Latitude", "Longitude", "Description"])
    return()

def ajouter_point(nom, latitude, longitude, description):
    initialiser_csv()
    with open(FICHIER_CSV, mode='a', newline='', encoding='utf-8') as fichier:
        writer = csv.writer(fichier)
        writer.writerow([nom, latitude, longitude, description])
    return()

def lister_points():
    initialiser_csv()
    with open(FICHIER_CSV, mode='r', encoding='utf-8') as fichier:
        reader = csv.reader(fichier)
        liste_of_listes = list(reader)
    return liste_of_listes

def charger_points_csv():

    initialiser_csv()

    df = pd.read_csv(FICHIER_CSV)

   
    if df.empty:
        return gpd.GeoDataFrame(
            columns=["nom", "description", "geometry"],
            geometry="geometry",
            crs="EPSG:4326"
        )

    
    geometries = [
        Point(lon, lat)
        for lat, lon in zip(df["Latitude"], df["Longitude"])
    ]

    gdf = gpd.GeoDataFrame(
        {
            "nom": df["Nom"],
            "description": df["Description"]
        },
        geometry=geometries,
        crs="EPSG:4326"
    )

    return gdf

FICHIER_CSV = "points.csv"
app = QApplication(sys.argv)
app.setWindowIcon(QIcon("logo2.png"))
window = MainWindow()
window.show()
sys.exit(app.exec())