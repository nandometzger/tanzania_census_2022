import geopandas as gpd
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import os
from matplotlib.colors import LogNorm

# Set a modern style
plt.style.use('ggplot')

def perform_analysis(gpkg_path, output_dir):
    print(f"Loading data from {gpkg_path}...")
    gdf = gpd.read_file(gpkg_path, engine="pyogrio")
    
    if gdf.crs is None:
        gdf.set_crs(epsg=4326, inplace=True)
    
    # Fill missing population with NaN for explicit handling
    # (These represent wards with no census match, effectively 0 density for this study)
    
    # 1. Main Population Density Map
    print("Generating main population density map with white '0' regions...")
    fig, ax = plt.subplots(1, 1, figsize=(15, 12))
    ax.set_facecolor('#ffffff') # Absolute white background
    
    # Define breaks - explicitly handling the low end
    main_breaks = [1, 5, 15, 30, 60, 125, 250, 500, 1000, 2500, 7500, 15000]
    
    # Plotting:
    # We use missing_kwds to handle '0' (NaN) values as White and add them to the legend
    gdf.plot(column='density', ax=ax, legend=True, 
            scheme='UserDefined', classification_kwds={'bins': main_breaks},
            cmap='YlOrRd',
            edgecolor='black', linewidth=0.04,
            missing_kwds={
                "color": "white",
                "edgecolor": "black",
                "linewidth": 0.04,
                "label": "0 / No Data",
            },
            legend_kwds={'title': "People per Sq Km", 'loc': 'lower left', 'fmt': "{:.0f}"})
    
    ax.set_title("Tanzania 2022 Census: Population Density by Ward", fontsize=18, fontweight='bold', pad=20)
    ax.axis('off')
    plt.savefig(os.path.join(output_dir, "tza_pop_density_map.png"), dpi=300, bbox_inches='tight')
    plt.close()

    # 2. Zoom - Dar es Salaam
    print("Generating Dar es Salaam zoom map...")
    dar_gdf = gdf[gdf['reg_name'].str.contains('Dar es Salaam', case=False, na=False)].copy()
    if not dar_gdf.empty:
        fig, ax = plt.subplots(1, 1, figsize=(12, 12))
        dar_breaks = [500, 1500, 3000, 6000, 10000, 15000, 20000, 25000, 30000, 35000]
        dar_gdf.plot(column='density', ax=ax, legend=True, 
                scheme='UserDefined', classification_kwds={'bins': dar_breaks},
                cmap='YlOrRd',
                edgecolor='black', linewidth=0.15,
                missing_kwds={"color": "white", "edgecolor": "black", "label": "0 / No Data"},
                legend_kwds={'title': "Density", 'loc': 'lower right', 'fmt': "{:.0f}"})
        ax.set_title("Dar es Salaam: Population Density (2022)", fontsize=16, fontweight='bold')
        ax.axis('off')
        plt.savefig(os.path.join(output_dir, "zoom_dar_density.png"), dpi=300, bbox_inches='tight')
        plt.close()

    # 3. Zoom - Zanzibar
    print("Generating Zanzibar zoom map...")
    znz_gdf = gdf[gdf['reg_name'].str.contains('Unguja|Pemba|Zanzibar', case=False, na=False)].copy()
    if not znz_gdf.empty:
        fig, ax = plt.subplots(1, 1, figsize=(12, 12))
        znz_breaks = [50, 150, 300, 500, 750, 1000, 1500, 2000, 3000, 4000]
        znz_gdf.plot(column='density', ax=ax, legend=True, 
                scheme='UserDefined', classification_kwds={'bins': znz_breaks},
                cmap='YlOrRd',
                edgecolor='black', linewidth=0.15,
                missing_kwds={"color": "white", "edgecolor": "black", "label": "0 / No Data"},
                legend_kwds={'title': "Density", 'loc': 'lower right', 'fmt': "{:.0f}"})
        ax.set_title("Zanzibar: Population Density (2022)", fontsize=16, fontweight='bold')
        ax.axis('off')
        plt.savefig(os.path.join(output_dir, "zoom_zanzibar_density.png"), dpi=300, bbox_inches='tight')
        plt.close()

    # 4. Modern Histogram
    print("Generating modern ward size histogram...")
    fig, ax = plt.subplots(figsize=(10, 6))
    areas = gdf[gdf['area_sqkm'] >= 1.0]['area_sqkm']
    log_bins = np.logspace(np.log10(1.0), np.log10(areas.max()), 50)
    ax.hist(areas, bins=log_bins, color='#3498db', edgecolor='white', alpha=0.8)
    ax.set_xscale('log')
    ax.set_xlim(left=1.0)
    ax.set_title("Distribution of ward areas in Tanzania (≥ 1 km²)", fontsize=16, fontweight='bold', pad=20)
    ax.set_xlabel("Area (sq km, Log Scale)", fontsize=12)
    ax.set_ylabel("Frequency", fontsize=12)
    ax.grid(True, which="both", ls="-", alpha=0.2)
    plt.savefig(os.path.join(output_dir, "tza_ward_size_histogram.png"), dpi=300, bbox_inches='tight')
    plt.close()

    # 5. Save descriptive statistics
    print("Saving statistics...")
    stats_path = os.path.join(output_dir, "tza_spatial_stats.txt")
    with open(stats_path, "w") as f:
        f.write("Tanzania 2022 Ward Spatial Statistics\n")
        f.write("======================================\n\n")
        f.write(f"Total polygons analyzed: {len(gdf)}\n")
        f.write(f"Total Land Area (mapped): {gdf['area_sqkm'].sum():.2f} sq km\n\n")
        f.write("Population Density Statistics (for matched wards):\n")
        gdf_matched = gdf[gdf['density'].notnull()]
        f.write(gdf_matched['density'].describe().to_string())
    print(f"Stats updated at {stats_path}")

if __name__ == "__main__":
    SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
    ROOT_DIR = os.path.dirname(SCRIPT_DIR)
    
    GPKG_PATH = os.path.join(ROOT_DIR, "data", "processed", "TZA_2022_Census_Final_Mapped.gpkg")
    OUTPUT_DIR = os.path.join(ROOT_DIR, "data", "processed")
    
    perform_analysis(GPKG_PATH, OUTPUT_DIR)
