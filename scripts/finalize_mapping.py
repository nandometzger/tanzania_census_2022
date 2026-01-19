import geopandas as gpd
import pandas as pd
import re
import os

# Manual name overrides to fix known mismatches between Shapefile and Census
# (Shapefile Name: Census Name)
NAME_OVERRIDES = {
    "NGHAHELEZE": "NGAHELEZE",
    "USA RIVER": "USA-RIVER",
    "OLOIRIEN/MAGAIDURU": "OLOIRIEN MAGAIDURU",
    "OLOIRIEN / MAGAIDURU": "OLOIRIEN MAGAIDURU",
    "VIWANJA SITINI": "VIWANJASITINI",
    "MATALE": "MATALE A", 
    "KIHANGIMAHUKA": "KIHANGI MAHUKA"
}

def normalize_text(text):
    if not text: return ""
    text = str(text).upper()
    if text in NAME_OVERRIDES:
        text = NAME_OVERRIDES[text]
    
    text = re.sub(r"\b(DISTRICT|COUNCIL|TOWN|CITY|MUNICIPAL|HALMASHAURI|WILAYA|YA|WA|LA)\b", "", text)
    text = re.sub(r"^\d+[\s\.]+", "", text)
    text = re.sub(r"[^\w\s]", " ", text)
    return " ".join(text.split())

def finalize_mapping(raw_shp_dir, census_csv_path, output_path):
    print("Loading data...")
    df_census = pd.read_csv(census_csv_path)
    
    shp_file = None
    for root, dirs, files in os.walk(raw_shp_dir):
        for file in files:
            if file.endswith(".shp"):
                shp_file = os.path.join(root, file)
                break
    
    if not shp_file:
        print("Error: Could not find shapefile in the raw data directory.")
        return

    gdf = gpd.read_file(shp_file, engine="pyogrio")
    
    print(f"Normalizing datasets for merging...")
    df_census['reg_norm'] = df_census['Region'].apply(normalize_text)
    df_census['dist_norm'] = df_census['Council'].apply(normalize_text)
    df_census['ward_norm'] = df_census['Ward'].apply(normalize_text)
    
    df_census = df_census.drop_duplicates(subset=['reg_norm', 'dist_norm', 'ward_norm'])

    gdf['reg_norm'] = gdf['reg_name'].apply(normalize_text)
    gdf['dist_norm'] = gdf['dist_name'].apply(normalize_text)
    gdf['ward_norm'] = gdf['ward_name'].apply(normalize_text)
    
    # 1. Primary Join
    merged = gdf.merge(
        df_census[['reg_norm', 'dist_norm', 'ward_norm', 'Total_Pop', 'Male_Pop', 'Female_Pop']], 
        on=['reg_norm', 'dist_norm', 'ward_norm'], 
        how='left'
    )
    
    # 2. Secondary Join for unmatched (Region + Ward only)
    unmatched_mask = merged['Total_Pop'].isnull()
    print(f"Unmatched after primary join: {unmatched_mask.sum()}")
    
    census_unique_rw = df_census.drop_duplicates(subset=['reg_norm', 'ward_norm'])
    
    temp_key = merged.loc[unmatched_mask, ['reg_norm', 'ward_norm']]
    sec_matches = temp_key.merge(
        census_unique_rw[['reg_norm', 'ward_norm', 'Total_Pop', 'Male_Pop', 'Female_Pop']],
        on=['reg_norm', 'ward_norm'],
        how='left'
    )
    merged.loc[unmatched_mask, ['Total_Pop', 'Male_Pop', 'Female_Pop']] = sec_matches[['Total_Pop', 'Male_Pop', 'Female_Pop']].values

    final_match_count = merged['Total_Pop'].notnull().sum()
    print(f"Final Matched: {final_match_count} / {len(gdf)} ({final_match_count/len(gdf)*100:.2f}%)")
    
    # 3. Spatial Calculations
    print("Calculating area and population density (UTM 37S)...")
    if merged.crs is None:
        merged.set_crs(epsg=4326, inplace=True)
    
    # Project to UTM Zone 37S (EPSG:32737) for accurate area in meters
    gdf_projected = merged.to_crs(epsg=32737)
    merged['area_sqkm'] = gdf_projected.area / 10**6
    merged['density'] = merged['Total_Pop'] / merged['area_sqkm']
    
    # Save output
    cols_to_keep = [col for col in gdf.columns if not col.endswith('_norm')] + \
                   ['Total_Pop', 'Male_Pop', 'Female_Pop', 'area_sqkm', 'density']
    
    merged[cols_to_keep].to_file(output_path, driver="GPKG")
    print(f"Saved integrated geospatial dataset to: {output_path}")

if __name__ == "__main__":
    # Internal paths relative to the project root
    SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
    ROOT = os.path.dirname(SCRIPT_DIR)
    
    RAW_SHP = os.path.join(ROOT, "data", "raw", "en-1714652282-TANZANIA_2022PHC_WARD_SHAPEFILES")
    RAW_CENSUS = os.path.join(ROOT, "data", "processed", "tza_census_2022_wards_clean.csv")
    OUTPUT = os.path.join(ROOT, "data", "processed", "TZA_2022_Census_Final_Mapped.gpkg")
    
    finalize_mapping(RAW_SHP, RAW_CENSUS, OUTPUT)
