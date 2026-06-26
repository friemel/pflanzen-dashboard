import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(layout="wide", page_title="Mein Pflanzen-Dashboard")
st.title("🌱 Flora Incognita - Interaktives Dashboard")

# 1. Datei-Uploader in der Sidebar
st.sidebar.header("📁 Datenupload")
uploaded_file = st.sidebar.file_uploader("Lade deine Flora Incognita CSV-Datei hoch", type=["csv"])

# Hilfsfunktion zum Laden der hochgeladenen Datei
def load_data(file):
    column_names = ['id', 'id2', 'id3', 'id4', 'id5', 'id6', 'id7', 'date', 
                    'scientific name', 'name', 'score', 'latitude', 'longitude', 
                    'altitude', 'accuracy', 'notes', 'tags', 'predictions', 'questionnaire']
    
    df = pd.read_csv(file, skiprows=1, names=column_names)
    df = df[df['name'].notna()]
    df = df[~df['name'].str.contains("Unbekanntes", na=False, case=False)]
    df['date'] = pd.to_datetime(df['date'], format='%Y-%m-%dT%H_%M_%SZ', errors='coerce')
    df = df.dropna(subset=['latitude', 'longitude'])
    return df

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

        # ABSOLUT SICHERES INITIALISIEREN: Verhindert den KeyError im Cloud-Server
        if 'min_lat' not in st.session_state: st.session_state['min_lat'] = min_lat_data
        if 'max_lat' not in st.session_state: st.session_state['max_lat'] = max_lat_data
        if 'min_lon' not in st.session_state: st.session_state['min_lon'] = min_lon_data
        if 'max_lon' not in st.session_state: st.session_state['max_lon'] = max_lon_data

        # Schnellwahl-Buttons für Burghausen und Berchtesgaden
        st.sidebar.caption("Schnellwahl Region:")
        col_btn1, col_btn2 = st.sidebar.columns(2)
        
        with col_btn1:
            if st.button("📍 Burghausen"):
                st.session_state['min_lat'] = 48.1200
                st.session_state['max_lat'] = 48.2000
                st.session_state['min_lon'] = 12.7800
                st.session_state['max_lon'] = 12.8700
                st.rerun()
                
        with col_btn2:
            if st.button("🏔️ Berchtesgaden"):
                st.session_state['min_lat'] = 47.4500
                st.session_state['max_lat'] = 47.7000
                st.session_state['min_lon'] = 12.8000
                st.session_state['max_lon'] = 13.0500
                st.rerun()

        st.sidebar.markdown("---")

        # Eingabefelder im Raster mit Fallback-Werten
        col_lat1, col_lat2 = st.sidebar.columns(2)
        with col_lat1:
            lat_min_input = st.number_input("Breite Min (Süd)", format="%.4f", value=st.session_state['min_lat'], key='mlat_input')
        with col_lat2:
            lat_max_input = st.number_input("Breite Max (Nord)", format="%.4f", value=st.session_state['max_lat'], key='maxlat_input')

        col_lon1, col_lon2 = st.sidebar.columns(2)
        with col_lon1:
            lon_min_input = st.number_input("Länge Min (West)", format="%.4f", value=st.session_state['min_lon'], key='mlon_input')
        with col_lon2:
            lon_max_input = st.number_input("Länge Max (Ost)", format="%.4f", value=st.session_state['max_lon'], key='maxlon_input')

        # Synchronisiere die Eingaben zurück in den Session State
        st.session_state['min_lat'] = lat_min_input
        st.session_state['max_lat'] = max_lat_input
        st.session_state['min_lon'] = lon_min_input
        st.session_state['max_lon'] = lon_max_input

        # Daten nach Region filtern
        df_filtered = df_filtered[
            (df_filtered['latitude'] >= lat_min_input) & 
            (df_filtered['latitude'] <= lat_max_input) &
            (df_filtered['longitude'] >= lon_min_input) & 
            (df_filtered['longitude'] <= lon_max_input)
        ]

        # Buttons ganz unten in der Sidebar
        st.sidebar.markdown("---")
        if st.sidebar.button("🔄 Filter zurücksetzen (Alle)", use_container_width=True):
            st.session_state['min_lat'] = min_lat_data
            st.session_state['max_lat'] = max_lat_data
            st.session_state['min_lon'] = min_lon_data
            st.session_state['max_lon'] = max_lon_data
            st.rerun()

        if st.sidebar.button("❌ App beenden", use_container_width=True):
            st.toast("Anwendung wurde gestoppt. Du kannst das Browserfenster jetzt schließen.")
            st.stop()

        # 4. Metriken anzeigen
        col1, col2, col3 = st.columns(3)
        col1.metric("Funde in dieser Region", len(df_filtered))
        col2.metric("Artenvielfalt hier", df_filtered['name'].nunique())
        col3.metric("Höchster Punkt", f"{int(df_filtered['altitude'].max())} m" if not df_filtered['altitude'].isna().all() and not df_filtered.empty else "N/A")

        st.markdown("---")

        # 5. Layout: Karte und Statistik
        left_col, right_col = st.columns([2, 1])

        with left_col:
            st.subheader("📍 Fundorte in der ausgewählten Region")
            if not df_filtered.empty:
                fig_map = px.scatter_map(
                    df_filtered, 
                    lat="latitude", 
                    lon="longitude", 
                    hover_name="name", 
                    hover_data=["scientific name", "altitude", "score"],
                    zoom=9, 
                    height=600
                )
                fig_map.update_layout(map_style="open-street-map")
                fig_map.update_layout(margin={"r":0,"t":0,"l":0,"b":0})
                st.plotly_chart(fig_map, width="stretch")
            else:
                st.warning("Keine Funde im ausgewählten Kartenbereich vorhanden.")

        with right_col:
            st.subheader("📊 Häufigste Arten in der Region")
            if not df_filtered.empty:
                top_plants = df_filtered['name'].value_counts().head(15).reset_index()
                top_plants.columns = ['Pflanze', 'Anzahl']
                
                fig_chart = px.bar(
                    top_plants, 
                    x='Anzahl', 
                    y='Pflanze', 
                    orientation='h',
                    color='Anzahl',
                    color_continuous_scale='Greens'
                )
                fig_chart.update_layout(yaxis={'categoryorder':'total ascending'}, showlegend=False)
                st.plotly_chart(fig_chart, width="stretch")
            else:
                st.info("Wähle einen größeren Bereich, um Statistiken zu sehen.")

        # 6. Tabellarische Übersicht & GPX-Export
        st.markdown("---")
        col_header, col_download = st.columns([3, 1])
        with col_header:
            st.subheader("📋 Fundliste der Region (Detailansicht)")
        
        with col_download:
            if not df_filtered.empty:
                # GPX-Daten generieren
                gpx_lines = [
                    '<?xml version="1.0" encoding="UTF-8"?>',
                    '<gpx version="1.1" creator="Flora Incognita Dashboard" xmlns="http://www.topografix.com/GPX/1/1">'
                ]
                for _, row in df_filtered.iterrows():
                    lat = row['latitude']
                    lon = row['longitude']
                    p_name = str(row['name']).replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
                    sci = str(row['scientific name']).replace('&', '&amp;')
                    scr = round(row['score'], 1) if pd.notna(row['score']) else 0
                    dt_str = row['date'].strftime('%Y-%m-%d') if pd.notna(row['date']) else 'Unbekannt'
                    alt_str = f" | Höhe: {int(row['altitude'])}m" if pd.notna(row['altitude']) else ""
                    desc = f"Wiss. Name: {sci} | Sicherheit: {scr}% | Datum: {dt_str}{alt_str}"
                    gpx_lines.append(f'  <wpt lat="{lat}" lon="{lon}"><name>{p_name}</name><desc>{desc}</desc></wpt>')
                gpx_lines.append('</gpx>')
                gpx_data = '\n'.join(gpx_lines)
                
                st.download_button(
                    label="💾 Region als GPX herunterladen",
                    data=gpx_data,
                    file_name="flora_incognita_export.gpx",
                    mime="application/gpx+xml",
                    use_container_width=True
                )

        if not df_filtered.empty:
            table_df = df_filtered[['date', 'name', 'scientific name', 'score', 'altitude', 'notes']].copy()
            table_df['date'] = table_df['date'].dt.strftime('%Y-%m-%d %H:%M')
            table_df['score'] = table_df['score'].round(1)
            
            table_df.columns = ['Datum', 'Deutscher Name', 'Wissenschaftlicher Name', 'Sicherheit (%)', 'Höhe (m)', 'Notizen']
            table_df = table_df.sort_values(by='Datum', ascending=False)
            
            st.dataframe(table_df, width="stretch", hide_index=True)
        else:
            st.info("Keine Daten für die Tabelle im aktuellen Filterbereich.")

    except Exception as e:
        st.error(f"Fehler bei der Verarbeitung der Datei: {e}")
else:
    st.info("👋 Bitte lade deine Flora Incognita CSV-Datei in der linken Seitenleiste hoch, um das Dashboard zu starten.")
