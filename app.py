import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(layout="wide", page_title="Mein Pflanzen-Dashboard")
st.title("🌱 Flora Incognita - Interaktives Dashboard")

# 1. Datei-Uploader in der Sidebar
st.sidebar.header("📁 Datenupload")
uploaded_file = st.sidebar.file_uploader("Lade deine Flora Incognita CSV-Datei hoch", type=["csv"])

# Hilfsfunktion zum Laden der hochgeladenen Datei (akzeptiert beide CSV-Formate)
def load_data(file):
    # Datei ganz normal einlesen (Pandas benennt doppelte 'id's automatisch zu 'id', 'id.1', 'id.2' etc.)
    df = pd.read_csv(file)
    
    # Bereinigung der ID-Spalten, falls der Export das neue Format mit 7 IDs nutzt
    if 'id' in df.columns:
        id_columns = [col for col in df.columns if col == 'id' or col.startswith('id.')]
        if len(id_columns) > 1:
            # Die letzte ID-Spalte (id.6 beim neuen Export) enthält die echte Beobachtungs-ID
            echte_id = id_columns[-1]
            df = df.rename(columns={echte_id: 'id_clean'})
            # Alle anderen ID-Dummys (id.1, id.2...) wegschmeißen
            df = df.drop(columns=[c for c in id_columns if c != echte_id])
            df = df.rename(columns={'id_clean': 'id'})
    
    # Standard-Bereinigungen des Dashboards
    df = df[df['name'].notna()]
    df = df[~df['name'].str.contains("Unbekanntes", na=False, case=False)]
    df['date'] = pd.to_datetime(df['date'], format='%Y-%m-%dT%H_%M_%SZ', errors='coerce')
    df = df.dropna(subset=['latitude', 'longitude'])
    return df

# Funktion zur Erstellung einer GPX-Datei aus den gefilterten Funden
def convert_to_gpx(df):
    gpx_lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<gpx version="1.1" creator="Flora Incognita Dashboard" xmlns="http://www.topografix.com/GPX/1/1">'
    ]
    for _, row in df.iterrows():
        lat = row['latitude']
        lon = row['longitude']
        name = str(row['name']).replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
        sci = str(row['scientific name']).replace('&', '&amp;')
        score = round(row['score'], 1) if pd.notna(row['score']) else 0
        date_str = row['date'].strftime('%Y-%m-%d') if pd.notna(row['date']) else 'Unbekannt'
        altitude_str = f" | Höhe: {int(row['altitude'])}m" if pd.notna(row['altitude']) else ""
        
        desc = f"Wiss. Name: {sci} | Sicherheit: {score}% | Datum: {date_str}{altitude_str}"
        
        gpx_lines.append(f'  <wpt lat="{lat}" lon="{lon}">')
        gpx_lines.append(f'    <name>{name}</name>')
        gpx_lines.append(f'    <desc>{desc}</desc>')
        gpx_lines.append('  </wpt>')
        
    gpx_lines.append('</gpx>')
    return '\n'.join(gpx_lines)

if uploaded_file is not None:
    try:
        df = load_data(uploaded_file)

        # 2. Sidebar-Filter
        st.sidebar.markdown("---")
        st.sidebar.header("🔍 Filteroptionen")
        
        if 'min_score' not in st.session_state:
            st.session_state.min_score = 80
        min_score = st.sidebar.slider("Minimale Bestimmungssicherheit (%)", 0, 100, key='min_score')
        
        df_filtered = df[df['score'] >= min_score]

        # 3. Regionseinschränkung per Schnellwahl oder Zahleneingabe
        st.sidebar.subheader("🗺️ Region einschränken")

        min_lat_data, max_lat_data = float(df['latitude'].min()), float(df['latitude'].max())
        min_lon_data, max_lon_data = float(df['longitude'].min()), float(df['longitude'].max())

        if 'min_lat' not in st.session_state: st.session_state.min_lat = min_lat_data
        if 'max_lat' not in st.session_state: st.session_state.max_lat = max_lat_data
        if 'min_lon' not in st.session_state: st.session_state.min_lon = min_lon_data
        if 'max_lon' not in st.session_state: st.session_state.max_lon = max_lon_data

        # Schnellwahl-Buttons
        st.sidebar.caption("Schnellwahl Region:")
        col_btn1, col_btn2 = st.sidebar.columns(2)
        
        with col_btn1:
            if st.button("📍 Burghausen"):
                st.session_state.min_lat = 48.1200
                st.session_state.max_lat = 48.2000
                st.session_state.min_lon = 12.7800
                st.session_state.max_lon = 12.8700
                st.rerun()
                
        with col_btn2:
            if st.button("🏔️ Berchtesgaden"):
                st.session_state.min_lat = 47.4500
                st.session_state.max_lat = 47.7000
                st.session_state.min_lon = 12.8000
                st.session_state.max_lon = 13.0500
                st.rerun()

        st.sidebar.markdown("---")

        col_lat1, col_lat2 = st.sidebar.columns(2)
        with col_lat1:
            lat_min_input = st.number_input("Breite Min (Süd)", format="%.4f", key='min_lat')
        with col_lat
