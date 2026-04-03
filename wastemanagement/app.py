import streamlit as st
import pandas as pd
import numpy as np
import random
from datetime import datetime, timedelta
from geopy.distance import geodesic

# -----------------
# Configuration
# -----------------
st.set_page_config(page_title="Municipal Waste Dashboard", layout="wide", initial_sidebar_state="expanded")

# UI Aesthetics: Dark Theme / Corporate - primarily handled by Streamlit's settings,
# We can also add some custom CSS for styling components.
st.markdown("""
<style>
    .kpi-card {
        background-color: #ffffff;
        border-radius: 5px;
        padding: 20px;
        margin-bottom: 20px;
        text-align: center;
        border-left: 5px solid #4CAF50;
        box-shadow: 2px 2px 5px rgba(0,0,0,0.1);
    }
    .kpi-card-danger {
        border-left: 5px solid #F44336;
    }
    .kpi-value {
        font-size: 2em;
        font-weight: bold;
        color: #000000;
    }
    .kpi-title {
        color: #555555;
        font-size: 1.1em;
        text-transform: uppercase;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# -----------------
# Data Generation
# -----------------
CITIES = {
    "Mangaluru": {
        "lat": 12.9141, "lon": 74.8560,
        "places": [
            ("Surathkal", 12.9958, 74.7943),
            ("Panambur", 12.9461, 74.8016),
            ("Kavoor", 12.9333, 74.8333),
            ("Urwa", 12.8900, 74.8317),
            ("Bejai", 12.8844, 74.8465),
            ("Kadri", 12.8795, 74.8617),
            ("Hampankatta", 12.8688, 74.8436),
            ("Kankanady", 12.8710, 74.8624),
            ("Pumpwell", 12.8624, 74.8631),
            ("Ullal", 12.8021, 74.8550)
        ]
    }
}

WARN_LEVEL = 50
CRIT_LEVEL = 85
MIN_FILL_GROWTH_RATE_PER_HOUR = -0.2
MAX_FILL_GROWTH_RATE_PER_HOUR = 3.8
PRIORITY_WEIGHT_CURRENT_FILL = 0.45
PRIORITY_WEIGHT_PREDICTED_FILL = 0.45
PRIORITY_WEIGHT_STALENESS = 0.10
STALENESS_NORMALIZATION_FACTOR = 20.0

MUNICIPAL_DEPTS = pd.DataFrame([
    {"Dept_ID": "DEPT-MLR", "City": "Mangaluru", "Latitude": 12.8850, "Longitude": 74.8500}
])

DUMP_GROUNDS = pd.DataFrame([
    {"Name": "Pachanady Dump Yard", "City": "Mangaluru", "Latitude": 12.9200, "Longitude": 74.8800}
])

@st.cache_data
def generate_synthetic_data(num_bins=150, seed=42):
    data = []
    rng = np.random.default_rng(seed)
    cities_list = list(CITIES.keys())
    for i in range(1, num_bins + 1):
        city = cities_list[int(rng.integers(0, len(cities_list)))]
        
        # Pick a major place to scatter bins around
        place_name, p_lat, p_lon = CITIES[city]["places"][int(rng.integers(0, len(CITIES[city]["places"])))]
        
        # Add random offset (approx 0.5-1 km) around the major place
        lat = p_lat + rng.uniform(-0.01, 0.01)
        lon = p_lon + rng.uniform(-0.01, 0.01)
        
        # Simulated Sensor Logic
        fill_level = int(rng.integers(0, 101))
        weight = max(0.0, (fill_level * 0.25) + rng.uniform(-1, 1)) # Weight correlates to fill
        
        ward_name = place_name
            
        mins_since_update = int(rng.integers(1, 61))
        last_updated = datetime.now() - timedelta(minutes=mins_since_update)
        
        # Junk Values / raw sensor data map
        distance_cm = max(0, 100 - fill_level) 
        raw_load_cell = int(weight * 1000) + int(rng.integers(-50, 51))
        
        # Short-term prediction and priority
        fill_growth_hr = max(0.0, rng.uniform(MIN_FILL_GROWTH_RATE_PER_HOUR, MAX_FILL_GROWTH_RATE_PER_HOUR))
        predicted_fill_24h = min(100.0, max(0.0, fill_level + (fill_growth_hr * 24)))
        predicted_status = 'RED' if predicted_fill_24h > CRIT_LEVEL else ('YELLOW' if predicted_fill_24h >= WARN_LEVEL else 'GREEN')
        staleness_hours = mins_since_update / 60.0
        priority_score = min(
            100.0,
            (PRIORITY_WEIGHT_CURRENT_FILL * fill_level)
            + (PRIORITY_WEIGHT_PREDICTED_FILL * predicted_fill_24h)
            + (PRIORITY_WEIGHT_STALENESS * min(100.0, staleness_hours * STALENESS_NORMALIZATION_FACTOR))
        )
        
        # Color coding logic
        if fill_level > CRIT_LEVEL:
            status = 'RED'
        elif fill_level >= WARN_LEVEL:
            status = 'YELLOW'
        else:
            status = 'GREEN'
            
        data.append({
            "Bin_ID": f"BIN-{i:03d}",
            "City": city,
            "Ward_Name": ward_name,
            "Latitude": lat,
            "Longitude": lon,
            "Fill_Level (%)": fill_level,
            "Weight (kg)": round(weight, 2),
            "Status": status,
            "Last_Updated": last_updated.strftime("%Y-%m-%d %H:%M:%S"),
            "Sensor_Distance_cm": distance_cm,
            "Sensor_LoadCell_Raw": raw_load_cell,
            "Fill_Growth_per_hr": round(fill_growth_hr, 2),
            "Predicted_Fill_24h (%)": round(predicted_fill_24h, 2),
            "Predicted_Status_24h": predicted_status,
            "Priority_Score": round(priority_score, 2)
        })
        
    return pd.DataFrame(data)

# Initialize Session State for Data Persistence
if 'df_bins' not in st.session_state:
    st.session_state.num_bins = 150
    st.session_state.seed = 42
    st.session_state.df_bins = generate_synthetic_data(st.session_state.num_bins, st.session_state.seed)

# --- Sidebar Simulation Controls ---
st.sidebar.header("⚙️ Simulation Controls")
num_bins_control = st.sidebar.slider("Number of bins", min_value=50, max_value=500, value=int(st.session_state.num_bins), step=10)
seed_control = int(st.sidebar.number_input("Random seed", min_value=0, max_value=999999, value=int(st.session_state.seed), step=1))
regenerate = st.sidebar.button("🔄 Regenerate Dataset")

if regenerate or num_bins_control != st.session_state.num_bins or seed_control != st.session_state.seed:
    st.session_state.num_bins = int(num_bins_control)
    st.session_state.seed = int(seed_control)
    st.session_state.df_bins = generate_synthetic_data(st.session_state.num_bins, st.session_state.seed)

df = st.session_state.df_bins

# --- Sidebar Search Functionality ---
st.sidebar.header("🔍 Municipal Search")
search_query = st.sidebar.text_input("Search by 'Ward Name' or 'City'", "")

# Filter data
if search_query:
    filtered_df = df[
        df['City'].str.contains(search_query, case=False, na=False) |
        df['Ward_Name'].str.contains(search_query, case=False, na=False)
    ]
else:
    filtered_df = df

st.sidebar.markdown("---")
st.sidebar.markdown("### 🚦 Status Legend")
st.sidebar.markdown("🔴 **Critical (>85%)**: Needs immediate collection")
st.sidebar.markdown("🟡 **Warning (50-85%)**: Scheduled for next 24 hours")
st.sidebar.markdown("🟢 **Clear (<50%)**: Sufficient capacity")
st.sidebar.markdown("📈 **Predicted 24h**: Expected status based on growth trend")

# --- UI Aesthetics: Top Header & KPI Cards ---
st.title("🚯 Mangaluru Municipal Corporation: Smart Waste Management")

# Calculate metrics from filtered_df
total_bins = len(filtered_df)
red_bins = len(filtered_df[filtered_df['Status'] == 'RED'])
predicted_red_bins = len(filtered_df[filtered_df['Predicted_Status_24h'] == 'RED'])
total_weight = filtered_df['Weight (kg)'].sum()
avg_priority = filtered_df['Priority_Score'].mean() if not filtered_df.empty else 0.0

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.markdown(f'<div class="kpi-card"><div class="kpi-title">Total Bins</div><div class="kpi-value">{total_bins}</div></div>', unsafe_allow_html=True)
with col2:
    st.markdown(f'<div class="kpi-card kpi-card-danger"><div class="kpi-title">Bins Needing Attention (RED)</div><div class="kpi-value" style="color:#F44336;">{red_bins}</div></div>', unsafe_allow_html=True)
with col3:
    st.markdown(f'<div class="kpi-card kpi-card-danger"><div class="kpi-title">Likely Critical in 24h</div><div class="kpi-value" style="color:#F44336;">{predicted_red_bins}</div></div>', unsafe_allow_html=True)
with col4:
    st.markdown(f'<div class="kpi-card"><div class="kpi-title">Total Waste Weight</div><div class="kpi-value">{total_weight:.2f} kg</div></div>', unsafe_allow_html=True)
st.caption(f"Average Priority Score: **{avg_priority:.1f}/100**")

# --- Tabs ---
tab1, tab2, tab3 = st.tabs(["🗺️ Map View", "📊 Simulation Dashboard", "🔌 Hardware Circuit"])

with tab1:
    # --- Map Implementation ---
    import folium
    from folium import plugins
    from streamlit_folium import st_folium
    from scipy.spatial import distance
    
    # Determine center of map (auto-zoom logic)
    if not filtered_df.empty:
        center_lat = filtered_df['Latitude'].mean()
        center_lon = filtered_df['Longitude'].mean()
        zoom_start = 14 if search_query else 13
    else:
        center_lat = 12.9141
        center_lon = 74.8560
        zoom_start = 12

    m = folium.Map(location=[center_lat, center_lon], zoom_start=zoom_start, tiles='CartoDB positron', width="100%", height=600)
    
    # Custom trash can icons logic.
    icon_colors = {'RED': 'red', 'YELLOW': 'orange', 'GREEN': 'green'}
    
    for idx, row in filtered_df.iterrows():
        folium.Marker(
            location=[row['Latitude'], row['Longitude']],
            popup=folium.Popup(f"<b>{row['Bin_ID']}</b><br>Ward: {row['Ward_Name']}<br>Fill Level: {row['Fill_Level (%)']}%<br>Weight: {row['Weight (kg)']} kg<br>Updated: {row['Last_Updated']}", max_width=250),
            tooltip=f"{row['Bin_ID']} - {row['Status']}",
            icon=folium.Icon(color=icon_colors[row['Status']], icon="trash", prefix='fa')
        ).add_to(m)
        
    # Plot Municipal Departments
    for idx, dept in MUNICIPAL_DEPTS.iterrows():
        folium.Marker(
            location=[dept['Latitude'], dept['Longitude']],
            popup=f"<b>{dept['City']} Municipal Department</b>",
            icon=folium.Icon(color='blue', icon='building', prefix='fa')
        ).add_to(m)
        
    # Plot Municipal Dump Grounds
    for idx, dump in DUMP_GROUNDS.iterrows():
        folium.Marker(
            location=[dump['Latitude'], dump['Longitude']],
            popup=f"<b>{dump['Name']}</b><br>Municipal Dump Ground - {dump['City']}",
            icon=folium.Icon(color='black', icon='recycle', prefix='fa')
        ).add_to(m)

    # --- Professional Routing (Nearest Neighbor for RED bins) ---
    red_bins_df = filtered_df[filtered_df['Status'] == 'RED']
    route_distance_km = 0.0
    if not red_bins_df.empty:
        red_coords = red_bins_df[['Latitude', 'Longitude']].values
        depot_coords = MUNICIPAL_DEPTS[['Latitude', 'Longitude']].values
        
        # 1. Find the dept closest to the centroid of RED bins
        centroid = red_coords.mean(axis=0)
        depot_dists = distance.cdist([centroid], depot_coords)
        nearest_depot_idx = np.argmin(depot_dists)
        start_depot = MUNICIPAL_DEPTS.iloc[nearest_depot_idx]
        
        # 2. Mathematical Shortest Distance: Nearest Neighbor initialization
        route_points = [[start_depot['Latitude'], start_depot['Longitude']]]
        unvisited = list(range(len(red_bins_df)))
        current_pt = route_points[0]
        
        while unvisited:
            unvis_coords = red_coords[unvisited]
            dists = distance.cdist([current_pt], unvis_coords)[0]
            nearest_idx = np.argmin(dists)
            
            next_pt = unvis_coords[nearest_idx]
            route_points.append(list(next_pt))
            current_pt = next_pt
            unvisited.pop(nearest_idx)
            
        # 3. 2-Opt TSP Algorithm to find strictly mathematical shortest path
        def calculate_total_distance(route):
            dist = 0.0
            for i in range(len(route)-1):
                dist += distance.euclidean(route[i], route[i+1])
            return dist
            
        improved = True
        best_route = route_points[:]
        best_distance = calculate_total_distance(best_route)
        
        while improved:
            improved = False
            for i in range(1, len(best_route) - 2):
                for j in range(i + 1, len(best_route) - 1):
                    new_route = best_route[:]
                    new_route[i:j+1] = best_route[i:j+1][::-1] 
                    new_distance = calculate_total_distance(new_route)
                    if new_distance < best_distance:
                        best_route = new_route
                        best_distance = new_distance
                        improved = True
        
        route_points = best_route
            
        # 3. Add Nearest Dump Ground at the end
        dump_coords = DUMP_GROUNDS[['Latitude', 'Longitude']].values
        dists_to_dumps = distance.cdist([route_points[-1]], dump_coords)[0]
        nearest_dump_idx = np.argmin(dists_to_dumps)
        final_dump = DUMP_GROUNDS.iloc[nearest_dump_idx]
        route_points.append([final_dump['Latitude'], final_dump['Longitude']])
        
        # 4. Compute route distance estimate (km)
        for i in range(len(route_points) - 1):
            route_distance_km += geodesic(route_points[i], route_points[i + 1]).km
            
        # Draw moving truck path (AntPath)
        plugins.AntPath(
            locations=route_points, 
            color="#00BFFF", 
            weight=5, 
            opacity=0.8,
            dash_array=[10, 20],
            pulse_color="white"
        ).add_to(m)

    st_folium(m, use_container_width=True, height=600)
    if not red_bins_df.empty:
        st.info(f"Estimated optimized collection route distance: **{route_distance_km:.2f} km**")
    else:
        st.info("No RED bins currently available for optimized route generation.")

with tab2:
    st.markdown("### 📊 Simulation Dashboard (Raw Data)")
    st.markdown("Displays the raw synthetic data acting as 'Junk Values' for debugging the system.")
    st.markdown("#### 🚚 Priority Queue (Top 10 bins for dispatch)")
    top_priority = filtered_df.sort_values("Priority_Score", ascending=False).head(10)[
        ["Bin_ID", "Ward_Name", "Fill_Level (%)", "Predicted_Fill_24h (%)", "Priority_Score", "Status", "Predicted_Status_24h"]
    ]
    st.dataframe(top_priority, use_container_width=True)
    
    st.markdown("#### 🧭 Area-Level Risk (Average Priority by Ward)")
    ward_priority = filtered_df.groupby("Ward_Name", as_index=False)["Priority_Score"].mean().sort_values("Priority_Score", ascending=False)
    st.bar_chart(ward_priority.set_index("Ward_Name"))
    
    st.dataframe(filtered_df, use_container_width=True)
    
    csv = filtered_df.to_csv(index=False).encode('utf-8')
    st.download_button("Export Data (CSV)", data=csv, file_name="municipal_bins_export.csv", mime='text/csv')

with tab3:
    st.markdown("### 🔌 Interactive Hardware Sandbox")
    st.markdown("Interactive simulation of the **ESP32**, **HC-SR04** (Fill Level), and **HX711** (Weight) components mapping hardware 'Junk Values' to JSON.")
    
    import streamlit.components.v1 as components
    import os
    
    sim_path = os.path.join(os.path.dirname(__file__), 'simulation.html')
    if os.path.exists(sim_path):
        with open(sim_path, 'r', encoding='utf-8') as f:
            html_data = f.read()
        components.html(html_data, height=520)
    else:
        st.error("simulation.html not found.")
    
    st.info("The **HC-SR04** measures the distance to the trash surface. $Distance = 100cm - Fill Level$. The **HX711** amplifies analog signals from the load cell beneath the bin, generating a raw 24-bit ADC value which corresponds to weight. These 'Junk Values' are parsed by the ESP32 and formatted into JSON via MQTT/HTTP.")
