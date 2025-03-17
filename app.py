import os
from flask import Flask, make_response
import pandas as pd
import folium
import matplotlib.pyplot as plt
import base64
from io import BytesIO
from utils import load_datasets, load_uv_data, load_temperature_data, process_uv_data  # Import utils.py

app = Flask(__name__)

# Load the data
incidence, mortality, location, age_incidence, age_mortality = load_datasets()
uv_data = load_uv_data()
state_map_data = process_uv_data(uv_data, location)
national_temp = load_temperature_data()

# Aggregate age-specific incidence data
incidence_age = age_incidence.groupby(["Year", "Age Category"]).agg(
    avg_rate=("avg_age_specific_rate", "mean")
).reset_index()

# ============================================
# Function to Generate Popup Chart (2015-2020, by Sex, using Count)
# ============================================
def generate_popup_chart(state):
    inc_state = incidence_filtered[incidence_filtered["State or Territory"] == state].copy()
    mort_state = mortality_filtered[mortality_filtered["State or Territory"] == state].copy()
    inc_state["Year"] = pd.to_numeric(inc_state["Year"], errors="coerce")
    mort_state["Year"] = pd.to_numeric(mort_state["Year"], errors="coerce")
    inc_state = inc_state[inc_state["Year"].between(2015, 2020)]
    mort_state = mort_state[mort_state["Year"].between(2015, 2020)]
    inc_pivot = inc_state.pivot_table(index="Year", columns="Sex", values="Count", aggfunc="sum")
    mort_pivot = mort_state.pivot_table(index="Year", columns="Sex", values="Count", aggfunc="sum")

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(4,4), sharex=True)
    for sex in inc_pivot.columns:
        ax1.plot(inc_pivot.index, inc_pivot[sex], marker="o", label=sex)
    ax1.set_title("Cancer Incidence Count (2015-2020)")
    ax1.set_ylabel("Count")
    ax1.legend(fontsize=8)
    for sex in mort_pivot.columns:
        ax2.plot(mort_pivot.index, mort_pivot[sex], marker="o", label=sex)
    ax2.set_title("Cancer Mortality Count (2015-2020)")
    ax2.set_xlabel("Year")
    ax2.set_ylabel("Count")
    ax2.legend(fontsize=8)

    plt.tight_layout()
    buf = BytesIO()
    plt.savefig(buf, format="png", dpi=100)
    plt.close(fig)
    buf.seek(0)
    img_base64 = base64.b64encode(buf.getvalue()).decode("utf-8")
    return img_base64

# ============================================
# Prepare UV Data and Location Coordinates for Map
# ============================================

m = folium.Map(location=[-25, 133], zoom_start=4)
for _, row in state_map_data.iterrows():
    state = row["state"]
    try:
        img_base64 = generate_popup_chart(state)
    except Exception as e:
        img_base64 = ""
        print(f"Error generating chart for {state}: {e}")

    popup_html = f"""
    <b>{state}</b><br>
    Average UV Index (2023): {row['avg_uv_index']:.2f}<br>
    {f'<img src="data:image/png;base64,{img_base64}" width="300">' if img_base64 else '<i>No recent data available</i>'}
    """
    folium.CircleMarker(
        location=[row["mean_lat"], row["mean_long"]],
        radius=row["avg_uv_index"] * 10,
        popup=popup_html,
        color="blue",
        fill=True,
        fill_opacity=0.7
    ).add_to(m)

map_html = m._repr_html_()

# ============================================
# Function to Generate Temperature & Incidence Chart
# ============================================
def generate_skin_cancer_trends_chart(age_bucket):
    # Filter incidence data for the selected age bucket
    df_inc = incidence_age[incidence_age["Age Category"] == age_bucket]

    # Create a figure with two subplots
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(8, 6))

    # --- Top Subplot: Temperature Trend ---
    ax1.plot(national_temp["year"], national_temp["avg_annual_temp_celsius"],
             marker="o", color="orange", linewidth=2)
    ax1.set_title("National Average Annual Temperature")
    ax1.set_xlabel("Year")
    ax1.set_ylabel("Temperature (°C)")

    # --- Bottom Subplot: Incidence Trend ---
    ax2.plot(df_inc["Year"], df_inc["avg_rate"],
             marker="o", color="green", linewidth=2)
    ax2.set_title(f"Skin Cancer Incidence Trend ({age_bucket})")
    ax2.set_xlabel("Year")
    ax2.set_ylabel("Incidence Rate (per 100,000)")

    plt.tight_layout()

    # Convert plot to Base64 for Flask response
    buf = BytesIO()
    plt.savefig(buf, format="png", dpi=100)
    plt.close()
    buf.seek(0)
    img_base64 = base64.b64encode(buf.getvalue()).decode("utf-8")
    return img_base64


# ============================================
# API Endpoints
# ============================================

@app.route('/api/uv_index_by_location', methods=['GET'])
def uv_index_by_location():
    return make_response(map_html, 200)

@app.route('/api/skin_cancer_trends', methods=['GET'])
def skin_cancer_trends():
    age_bucket = request.args.get("age_bucket", "30-39")
    if age_bucket not in incidence_age["Age Category"].unique():
        return jsonify({"error": "Invalid age group"}), 400

    img_base64 = generate_skin_cancer_trends_chart(age_bucket)
    return jsonify({
        "age_bucket": age_bucket,
        "chart": f"data:image/png;base64, {img_base64}"
    })
