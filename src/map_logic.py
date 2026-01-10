import pandas as pd
import pydeck as pdk
import random

# --- HACKATHON GEOCODER ---
LOCATION_MAP = {
    "United States": [-95.7129, 37.0902], "USA": [-95.7129, 37.0902], "U.S.": [-95.7129, 37.0902],
    "Washington": [-77.0369, 38.9072], "New York": [-74.0060, 40.7128], "California": [-119.4179, 36.7783],
    "China": [104.1954, 35.8617], "Beijing": [116.4074, 39.9042],
    "Russia": [105.3188, 61.5240], "Moscow": [37.6173, 55.7558],
    "Ukraine": [31.1656, 48.3794], "Kyiv": [30.5234, 50.4501],
    "United Kingdom": [-3.4359, 55.3781], "UK": [-3.4359, 55.3781], "London": [-0.1276, 51.5074],
    "France": [2.2137, 46.2276], "Paris": [2.3522, 48.8566],
    "Germany": [10.4515, 51.1657], "Berlin": [13.4050, 52.5200],
    "India": [78.9629, 20.5937], "Delhi": [77.1025, 28.7041],
    "Israel": [34.8516, 31.0461], "Gaza": [34.3088, 31.3547],
    "Japan": [138.2529, 36.2048], "Tokyo": [139.6917, 35.6895],
    "Canada": [-106.3468, 56.1304], "Ottawa": [-75.6972, 45.4215],
    "Brazil": [-51.9253, -14.2350],
    "Iran": [53.6880, 32.4279],
    "Taiwan": [120.9605, 23.6978],
    "Australia": [133.7751, -25.2744],
    "Europe": [15.2551, 54.5260], "EU": [15.2551, 54.5260],
    "Silicon Valley": [-122.05, 37.38],
}

def get_map_data(articles):
    """
    Scans article text for location keywords and assigns coordinates.
    Returns a dataframe ready for PyDeck.
    """
    map_data = []

    for art in articles:
        # SCANNING MORE TEXT NOW (1000 chars) to catch locations mentioned later
        text_content = (art['title'] + " " + art['text'][:1000]).lower()
        
        lat, lon = None, None
        found_loc = "Unknown"

        for loc_name, coords in LOCATION_MAP.items():
            if loc_name.lower() in text_content:
                lon, lat = coords
                found_loc = loc_name
                break 
        
        if lat and lon:
            # Jitter to prevent stacking
            lat += random.uniform(-0.5, 0.5)
            lon += random.uniform(-0.5, 0.5)
            
            map_data.append({
                "title": art['title'],
                "url": art['url'],
                "lat": lat,
                "lon": lon,
                "location": found_loc
            })
            
    return pd.DataFrame(map_data)

def generate_3d_map(df):
    """
    Creates a PyDeck 3D Map (The Global Newsroom).
    """
    if df.empty:
        return None

    # Layer 1: Glowing Columns (Pillars of Light)
    column_layer = pdk.Layer(
        "ColumnLayer",
        data=df,
        get_position=["lon", "lat"],
        get_elevation=100000, 
        elevation_scale=100,  # MUCH TALLER PILLARS
        radius=200000,        # MUCH FATTER PILLARS (200km wide) for visibility
        get_fill_color=[255, 0, 100, 200], # Neon Pink/Red Glow
        pickable=True,
        auto_highlight=True,
    )

    view_state = pdk.ViewState(
        latitude=20.0,
        longitude=0.0,
        zoom=1.0, # Zoomed out to see the whole world
        pitch=45, 
    )

    tooltip = {
        "html": "<b>{location}</b><br/>{title}",
        "style": {"backgroundColor": "black", "color": "white"}
    }

    r = pdk.Deck(
        layers=[column_layer],
        initial_view_state=view_state,
        tooltip=tooltip,
        # REMOVED map_style="mapbox://..." to fix the black screen bug
        # Streamlit will now provide the default dark map automatically
    )
    
    return r