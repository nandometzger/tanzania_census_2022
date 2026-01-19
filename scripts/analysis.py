import geopandas as gpd
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import os

# Set a modern style
plt.style.use('ggplot')

def perform_analysis(gpkg_path, output_dir):
    print(f"Loading data from {gpkg_path}...")
    gdf = gpd.read_file(gpkg_path, engine="pyogrio")
    
    if gdf.crs is None:
        gdf.set_crs(epsg=4326, inplace=True)
    
    # Calculate Area using a suitable local projection
    print("Calculating areas (UTM 37S)...")
    gdf_projected = gdf.to_crs(epsg=32737)
    gdf['area_sqkm'] = gdf_projected.area / 10**6
    
    print("Calculating population density...")
    gdf_pop = gdf[gdf['Total_Pop'].notnull()].copy()
    gdf_pop['density'] = gdf_pop['Total_Pop'] / gdf_pop['area_sqkm']
    
    # 1. Main Population Density Map (9 classes)
    print("Generating main population density map...")
    fig, ax = plt.subplots(1, 1, figsize=(15, 12))
    gdf_pop.plot(column='density', ax=ax, legend=True, 
                scheme='quantiles', k=9, cmap='YlOrRd',
                legend_kwds={'title': "People per Sq Km", 'loc': 'lower left', 'fmt': "{:.0f}"})
    ax.set_title("Tanzania 2022 Census: Population Density by Ward", fontsize=18, fontweight='bold', pad=20)
    ax.axis('off')
    plt.savefig(os.path.join(output_dir, "tza_pop_density_map.png"), dpi=300, bbox_inches='tight')
    plt.close()

    # 2. Zoom - Dar es Salaam
    print("Generating Dar es Salaam zoom map...")
    dar = gdf_pop[gdf_pop['reg_name'].str.contains('Dar es Salaam', case=False, na=False)].copy()
    if not dar.empty:
        fig, ax = plt.subplots(1, 1, figsize=(12, 12))
        dar.plot(column='density', ax=ax, legend=True, scheme='quantiles', k=9, cmap='YlOrRd',
                legend_kwds={'title': "Density", 'loc': 'lower right', 'fmt': "{:.0f}"})
        ax.set_title("Dar es Salaam: Population Density (2022)", fontsize=16, fontweight='bold')
        ax.axis('off')
        plt.savefig(os.path.join(output_dir, "zoom_dar_density.png"), dpi=300, bbox_inches='tight')
        plt.close()

    # 3. Zoom - Zanzibar (Unguja & Pemba)
    print("Generating Zanzibar zoom map...")
    # Regions containing 'Unguja' or 'Pemba'
    znz = gdf_pop[gdf_pop['reg_name'].str.contains('Unguja|Pemba|Zanzibar', case=False, na=False)].copy()
    if not znz.empty:
        fig, ax = plt.subplots(1, 1, figsize=(12, 12))
        znz.plot(column='density', ax=ax, legend=True, scheme='quantiles', k=9, cmap='YlOrRd',
                legend_kwds={'title': "Density", 'loc': 'lower right', 'fmt': "{:.0f}"})
        ax.set_title("Zanzibar: Population Density (2022)", fontsize=16, fontweight='bold')
        ax.axis('off')
        plt.savefig(os.path.join(output_dir, "zoom_zanzibar_density.png"), dpi=300, bbox_inches='tight')
        plt.close()

    # 4. Modern Histogram (Log x-axis, Linear y-axis)
    print("Generating modern ward size histogram...")
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # Filter out 0 area if any
    areas = gdf[gdf['area_sqkm'] > 0]['area_sqkm']
    
    # Create log bins
    log_bins = np.logspace(np.log10(areas.min()), np.log10(areas.max()), 50)
    
    ax.hist(areas, bins=log_bins, color='#3498db', edgecolor='white', alpha=0.8)
    ax.set_xscale('log')
    
    ax.set_title("Distribution of ward areas in Tanzania (2022)", fontsize=16, fontweight='bold', pad=20)
    ax.set_xlabel("Area (sq km, Log Scale)", fontsize=12)
    ax.set_ylabel("Frequency (Linear)", fontsize=12)
    
    # Add a grid for readability
    ax.grid(True, which="both", ls="-", alpha=0.2)
    
    # Add some descriptive text
    median_val = areas.median()
    ax.axvline(median_val, color='#e74c3c', linestyle='--', label=f'Median: {median_val:.1f} km²')
    ax.legend()

    plt.savefig(os.path.join(output_dir, "tza_ward_size_histogram.png"), dpi=300, bbox_inches='tight')
    plt.close()

    # 5. Save descriptive statistics
    print("Saving statistics...")
    stats_path = os.path.join(output_dir, "tza_spatial_stats.txt")
    with open(stats_path, "w") as f:
        f.write("Tanzania 2022 Ward Spatial Statistics\n")
        f.write("======================================\n\n")
        f.write(f"Total polygons analyzed: {len(gdf)}\n")
        f.write(f"Mean Ward Area: {gdf['area_sqkm'].mean():.2f} sq km\n")
        f.write(f"Median Ward Area: {gdf['area_sqkm'].median():.2f} sq km\n")
        f.write(f"Total Land Area (mapped): {gdf['area_sqkm'].sum():.2f} sq km\n\n")
        
        f.write("Population Density Statistics (for matched wards):\n")
        f.write(gdf_pop['density'].describe().to_string())
        
        max_row = gdf_pop.loc[gdf_pop['density'].idxmax()]
        f.write("\n\nMaximum Density Ward:\n")
        f.write(f"Name: {max_row['ward_name']} ({max_row['reg_name']})\n")
        f.write(f"Population: {max_row['Total_Pop']}\n")
        f.write(f"Density: {max_row['density']:.2f} people/sq km\n")
    
    print(f"Stats updated at {stats_path}")

if __name__ == "__main__":
    # Internal paths relative to project root
    SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
    ROOT_DIR = os.path.dirname(SCRIPT_DIR)
    
    GPKG_PATH = os.path.join(ROOT_DIR, "data", "processed", "TZA_2022_Census_Final_Mapped.gpkg")
    OUTPUT_DIR = os.path.join(ROOT_DIR, "data", "processed")
    
    perform_analysis(GPKG_PATH, OUTPUT_DIR)
