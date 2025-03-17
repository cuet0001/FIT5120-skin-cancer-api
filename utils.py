import pandas as pd
import os

# Paths for datasets
incidence_mortality = "dataset/CDiA-2024-Book-7-Cancer-incidence-and-mortality-by-state-and-territory.xlsx"
loc = "dataset/australian_postcodes.csv"
age_std_incidence = "dataset/CDiA-2024-Book-1a-Cancer-incidence-age-standardised-rates-5-year-age-groups.xlsx"
age_std_mortality = "dataset/CDiA-2024-Book-2a-Cancer-mortality-and-age-standardised-rates-by-age-5-year-groups.xlsx"

# Read datasets
def load_datasets():
    incidence = pd.read_excel(incidence_mortality, sheet_name="Table S7.1", skiprows=5)
    mortality = pd.read_excel(incidence_mortality, sheet_name="Table S7.2", skiprows=5)
    location = pd.read_csv(loc)
    age_incidence = pd.read_excel(age_std_incidence, sheet_name="Table S1a.1", skiprows=5)
    age_mortality = pd.read_excel(age_std_mortality, sheet_name="Table S2a.1", skiprows=5)
    return incidence, mortality, location, age_incidence, age_mortality

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

# Read UV datasets
def load_uv_data():
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
    if age_group in ["00–04", "05–09"]:
        return "0-9"
    elif age_group in ["10–14", "15–19"]:
        return "10-19"
    elif age_group in ["20–24", "25–29"]:
        return "20-29"
    elif age_group in ["30–34", "35–39"]:
        return "30-39"
    elif age_group in ["40–44", "45–49"]:
        return "40-49"
    elif age_group in ["50–54", "55–59"]:
        return "50-59"
    elif age_group in ["60–64", "65–69"]:
        return "60-69"
    elif age_group in ["70–74", "75–79"]:
        return "70-79"
    elif age_group in ["80–84", "85–89", "90+"]:
        return "80+"
    else:
        return age_group

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
