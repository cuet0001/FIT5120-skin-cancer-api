import os
from flask import Flask, make_response
import pandas as pd
import folium
import matplotlib.pyplot as plt
import base64
from io import BytesIO

app = Flask(__name__)


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
city_to_state = {
    "sydney": "NSW",
    "newcastle": "NSW",
    "melbourne": "VIC",
    "brisbane": "QLD",
    "gold_coast": "QLD",
    "townsville": "QLD",
    "emerald": "QLD",
    "perth": "WA",
    "adelaide": "SA",
    "kingston": "TAS",
    "canberra": "ACT",
    "darwin": "NT",
    "alice_springs": "NT"
}
uv_records = []
for city, df in uv_data.items():
    avg_uv = pd.to_numeric(df["UV_Index"], errors="coerce").mean()
    uv_records.append({"city": city, "state": city_to_state.get(city, None), "avg_uv_index": avg_uv})
uv_df = pd.DataFrame(uv_records).dropna(subset=["state"])
state_uv = uv_df.groupby("state")["avg_uv_index"].mean().reset_index()
representative_coords = location.groupby("state")[["lat", "long"]].mean().reset_index().rename(columns={"lat": "mean_lat", "long": "mean_long"})
state_map_data = pd.merge(state_uv, representative_coords, on="state", how="inner")

m = folium.Map(location=[-25, 133], zoom_start=4)
for _, row in state_map_data.iterrows():
    state = row["state"]
    try:
        img_base64 = generate_popup_chart(state)
    except Exception as e:
        img_base64 = ""
        print(f"Error generating chart for {state}: {e}")
    popup_html = f\"\"\"
    <b>{state}</b><br>
    Average UV Index (2023): {row['avg_uv_index']:.2f}<br>
    {f'<img src="data:image/png;base64,{img_base64}" width="300">' if img_base64 else '<i>No recent data available</i>'}
    \"\"\"
    folium.CircleMarker(
        location=[row["mean_lat"], row["mean_long"]],
        radius=row["avg_uv_index"] * 10,
        popup=popup_html,
        color="blue",
        fill=True,
        fill_opacity=0.7
    ).add_to(m)
map_html = m._repr_html_()

@app.route('/api/uv_index_by_location', methods=['GET'])
def uv_index_by_location():
    return make_response(map_html, 200)

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=True, host='0.0.0.0', port=port)
