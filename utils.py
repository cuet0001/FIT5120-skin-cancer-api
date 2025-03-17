import pandas as pd
import os

# Base directory for datasets
DATA_DIR = "dataset"

# Paths for datasets
incidence_mortality = os.path.join(DATA_DIR, "CDiA-2024-Book-7-Cancer-incidence-and-mortality-by-state-and-territory.xlsx")
loc = os.path.join(DATA_DIR, "australian_postcodes.csv")
age_std_incidence = os.path.join(DATA_DIR, "CDiA-2024-Book-1a-Cancer-incidence-age-standardised-rates-5-year-age-groups.xlsx")
age_std_mortality = os.path.join(DATA_DIR, "CDiA-2024-Book-2a-Cancer-mortality-and-age-standardised-rates-by-age-5-year-groups.xlsx")
temperature_data = os.path.join(DATA_DIR, "avg_annual_temperature.csv")

# Load datasets
def load_datasets():
    incidence = pd.read_excel(incidence_mortality, sheet_name="Table S7.1", skiprows=5)
    mortality = pd.read_excel(incidence_mortality, sheet_name="Table S7.2", skiprows=5)
    location = pd.read_csv(loc)
    age_incidence = pd.read_excel(age_std_incidence, sheet_name="Table S1a.1", skiprows=5)
    age_mortality = pd.read_excel(age_std_mortality, sheet_name="Table S2a.1", skiprows=5)
    return incidence, mortality, location, age_incidence, age_mortality

# Load temperature dataset
def load_temperature_data():
    temp_df = pd.read_csv(temperature_data)
    national_temp = temp_df.groupby("year")["avg_annual_temp_celsius"].mean().reset_index()
    return national_temp

# Load UV datasets
def load_uv_data():
    # Define UV dataset paths
    city_paths = {
        "sydney": os.path.join(DATA_DIR, "uv_index_data/uv-sydney-2023.csv"),
        "newcastle": os.path.join(DATA_DIR, "uv_index_data/uv-newcastle-2023.csv"),
        "melbourne": os.path.join(DATA_DIR, "uv_index_data/uv-melbourne-2023.csv"),
        "brisbane": os.path.join(DATA_DIR, "uv_index_data/uv-brisbane-2023.csv"),
        "gold_coast": os.path.join(DATA_DIR, "uv_index_data/uv-gold-coast-2023.csv"),
        "townsville": os.path.join(DATA_DIR, "uv_index_data/uv-townsville-2023.csv"),
        "emerald": os.path.join(DATA_DIR, "uv_index_data/uv-emerald-2023.csv"),
        "perth": os.path.join(DATA_DIR, "uv_index_data/uv-perth-2023.csv"),
        "adelaide": os.path.join(DATA_DIR, "uv_index_data/uv-adelaide-2023.csv"),
        "kingston": os.path.join(DATA_DIR, "uv_index_data/uv-kingston-2023.csv"),
        "canberra": os.path.join(DATA_DIR, "uv_index_data/uv-canberra-2023.csv"),
        "darwin": os.path.join(DATA_DIR, "uv_index_data/uv-darwin-2023.csv"),
        "alice_springs": os.path.join(DATA_DIR, "uv_index_data/uv-alice-springs-2023.csv")
    }
    return {city: pd.read_csv(path) for city, path in city_paths.items()}

# State name mapping
def standardize_state_names(df, column):
    state_name_mapping = {
        "New South Wales": "NSW",
        "Victoria": "VIC",
        "Queensland": "QLD",
        "Western Australia": "WA",
        "South Australia": "SA",
        "Tasmania": "TAS",
        "Australian Capital Territory": "ACT",
        "Northern Territory": "NT",
        "Australia": None  # Drop this row as it's not state-specific
    }
    df[column] = df[column].map(state_name_mapping)
    return df.dropna(subset=[column])

# Recategorize age groups
def recategorise_age(age_group):
    categories = {
        "00–04": "0-9", "05–09": "0-9",
        "10–14": "10-19", "15–19": "10-19",
        "20–24": "20-29", "25–29": "20-29",
        "30–34": "30-39", "35–39": "30-39",
        "40–44": "40-49", "45–49": "40-49",
        "50–54": "50-59", "55–59": "50-59",
        "60–64": "60-69", "65–69": "60-69",
        "70–74": "70-79", "75–79": "70-79",
        "80–84": "80+", "85–89": "80+", "90+": "80+"
    }
    return categories.get(age_group, age_group)

# Aggregate age-based incidence/mortality
def aggregate_age_data(df, count_col, rate_col):
    df["Age Category"] = df["Age group (years)"].apply(recategorise_age)
    return df.groupby(["Year", "Age Category"]).agg(
        total_count=(count_col, "sum"),
        avg_age_specific_rate=(rate_col, "mean")
    ).reset_index()

# Process UV data
def process_uv_data(uv_data, location):
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
        uv_records.append({
            "city": city,
            "state": city_to_state.get(city, None),
            "avg_uv_index": avg_uv
        })
    uv_df = pd.DataFrame(uv_records).dropna(subset=["state"])
    state_uv = uv_df.groupby("state")["avg_uv_index"].mean().reset_index()
    
    # Merge with location data
    representative_coords = location.groupby("state")[["lat", "long"]].mean().reset_index()
    representative_coords.rename(columns={"lat": "mean_lat", "long": "mean_long"}, inplace=True)
    
    return pd.merge(state_uv, representative_coords, on="state", how="inner")

# Export functions for app.py
__all__ = [
    "load_datasets",
    "load_uv_data",
    "standardize_state_names",
    "aggregate_age_data",
    "process_uv_data"
]
