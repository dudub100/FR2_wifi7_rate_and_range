import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import pathLossClasses as pl
import wifi7Class as wifi

# Set up the page
st.set_page_config(page_title="Wi-Fi 7 mmWave Link Calculator", layout="wide")
st.title("Wi-Fi 7 mmWave Range and Capacity Calculator")

# --- SIDEBAR INPUTS ---
st.sidebar.header("System Parameters")

frequency = st.sidebar.number_input("Frequency (GHz)", min_value=1.0, max_value=100.0, value=31.0, step=1.0)

# Extract rain zones from the Link class
temp_link = pl.Link()
rain_zones = list(temp_link.rainRate001.keys())
default_zone_idx = rain_zones.index('K') if 'K' in rain_zones else 0
rain_zone = st.sidebar.selectbox("Rain Zone", rain_zones, index=default_zone_idx)

# Extract Channel BW options from wifi7Class
temp_radio = wifi.wifi7Radio()
bw_options = list(temp_radio.bwToTones.keys())
default_bw_idx = bw_options.index(140) if 140 in bw_options else 0
ch_bw = st.sidebar.selectbox("Channel BW (MHz)", bw_options, index=default_bw_idx)

# --- NEW: Tx Antenna Elements & Max MCS ---
st.sidebar.markdown("---")
st.sidebar.header("Advanced Capabilities")
tx_elements = st.sidebar.number_input("Tx Antenna Elements", min_value=1, max_value=128, value=32, step=1)
max_mcs = st.sidebar.slider("Maximum MCS limit", min_value=0, max_value=13, value=10, step=1)

# --- NEW: Throughput Parameters ---
st.sidebar.markdown("---")
st.sidebar.header("Throughput Parameters")
num_streams = st.sidebar.number_input("Number of Streams", min_value=1, max_value=16, value=2, step=1)
overhead_percent = st.sidebar.slider("MAC Efficiency / Overhead (%)", min_value=10, max_value=100, value=75, step=1)
overhead_factor = overhead_percent / 100.0

st.sidebar.markdown("---")
st.sidebar.header("Distance Table Parameters")
target_availability = st.sidebar.number_input("Target Availability (%)", value=99.9, step=0.01)

# Constants from original script
GantTx = 5 + 10 * np.log10(tx_elements)  # Dynamically calculated based on user input
GantRx = 5 + 10 * np.log10(32)           # Keeping Rx at 32 as per original script
tx_power = 14 + 10 * np.log10(8)
noise_figure = 7

# --- GRAPH: Capacity vs Distance vs Availability ---
st.header("Capacity vs. Distance")

distanceRange = np.linspace(0.1, 2, 100)  # Km
availabilities = [99, 99.5, 99.9, 99.95, 99.99, 99.995]

radio1 = wifi.wifi7Radio(chBW=ch_bw)
radio1.txPower = tx_power
radio1.noiseFigure = noise_figure

link1 = pl.Link(frequency=frequency, rainZone=rain_zone)

results = np.zeros((len(availabilities), len(distanceRange)))

with st.spinner("Calculating graph data..."):
    for indAvl, avl in enumerate(availabilities):
        for indDistance, distance in enumerate(distanceRange):
            for mcs in range(max_mcs + 1):  # Respects the Max MCS limit
                radio1.mcs = mcs
                link1.distance = distance
                link1.availability = avl
                
                pathLoss = link1.freeSpaceLoss() + link1.atmosphericLoss() + link1.rainLoss()
                rsl = radio1.txPower + GantTx - pathLoss + GantRx
                
                if rsl - radio1.thresholdRsl() >= 2:
                    results[indAvl][indDistance] = max(results[indAvl][indDistance], radio1.capacity())

# Plotting the Graph
fig, ax = plt.subplots(figsize=(10, 5))
for indAvl, avl in enumerate(availabilities):
    # User throughput based on user-defined streams and overhead
    user_capacity = results[indAvl] * num_streams * overhead_factor
    ax.plot(distanceRange, user_capacity, label=f"{avl}%")

ax.grid(True)
ax.legend(title="Availability")
ax.set_xlabel("Distance (Km)")
ax.set_ylabel(f"User Capacity [Mbps] ({num_streams} Streams)")
ax.set_title(f"{frequency}GHz, Rain Zone {rain_zone}, {ch_bw}MHz BW, Max MCS {max_mcs}")

st.pyplot(fig)


# --- TABLE 1: Max Distance per MCS for all BWs ---
st.header(f"Maximum Distance (Km) at {target_availability}% Availability")

def find_max_distance(mcs_val, bw_val, freq_val, rz_val, avail_val):
    rad = wifi.wifi7Radio(chBW=bw_val)
    rad.mcs = mcs_val
    rad.txPower = tx_power
    rad.noiseFigure = noise_figure
    
    lnk = pl.Link(frequency=freq_val, rainZone=rz_val)
    lnk.availability = avail_val
    
    # Binary search boundaries
    min_d, max_d = 0.001, 10.0
    best_d = 0
    
    for _ in range(20):
        mid_d = (min_d + max_d) / 2
        lnk.distance = mid_d
        
        pathLoss = lnk.freeSpaceLoss() + lnk.atmosphericLoss() + lnk.rainLoss()
        rsl = rad.txPower + GantTx - pathLoss + GantRx
        
        if rsl - rad.thresholdRsl() >= 2:
            best_d = mid_d
            min_d = mid_d
        else:
            max_d = mid_d
            
    return round(best_d, 2)

with st.spinner("Calculating distances for all Channel Bandwidths..."):
    dist_table_data = []
    for mcs in range(max_mcs + 1): # Respects the Max MCS limit
        row = {"MCS": mcs}
        for bw in bw_options:
            row[f"{bw} MHz"] = find_max_distance(mcs, bw, frequency, rain_zone, target_availability)
        dist_table_data.append(row)

df_dist_table = pd.DataFrame(dist_table_data)
st.dataframe(df_dist_table, use_container_width=True, hide_index=True)


# --- TABLE 2: Capacity per MCS and BW ---
st.header(f"User Capacity per MCS and Bandwidth (Mbps) - {num_streams} Streams, {overhead_percent}% Efficiency")

with st.spinner("Calculating capacity matrix..."):
    cap_table_data = []
    for mcs in range(max_mcs + 1):  # Respects the Max MCS limit
        row = {"MCS": mcs}
        for bw in bw_options:
            temp_rad = wifi.wifi7Radio(chBW=bw)
            temp_rad.mcs = mcs
            
            # Math: physical rate x number of streams x overhead percentage
            raw_phy_rate = temp_rad.capacity()
            user_throughput = raw_phy_rate * num_streams * overhead_factor
            
            # Rounding to 2 decimal places for cleaner display
            row[f"{bw} MHz"] = round(user_throughput, 2) 
            
        cap_table_data.append(row)

df_cap_table = pd.DataFrame(cap_table_data)
st.dataframe(df_cap_table, use_container_width=True, hide_index=True)
