import geopandas as gpd
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import os

# Set a modern style
plt.style.use('ggplot')

def perform_comparison_analysis(tza_gpkg, rwa_shp, output_dir):
    print("Loading datasets...")
    # Load Tanzania Wards
    tza = gpd.read_file(tza_gpkg, engine="pyogrio")
    if tza.crs is None: tza.set_crs(epsg=4326, inplace=True)
    
    # Load Rwanda Subnational
    rwa = gpd.read_file(rwa_shp, engine="pyogrio")
    if rwa.crs is None: rwa.set_crs(epsg=4326, inplace=True)
    # Filter out 'Water'
    rwa = rwa[rwa['adm_name'].str.upper() != 'WATER'].copy()

    # Calculate Areas
    print("Calculating areas...")
    # TZA: UTM 37S
    tza_projected = tza.to_crs(epsg=32737)
    tza_areas = tza_projected.area / 10**6
    
    # RWA: UTM 35S (suitable for Rwanda)
    rwa_projected = rwa.to_crs(epsg=32735)
    rwa_areas = rwa_projected.area / 10**6
    
    # 1. Comparison Histogram (Log x, Linear y)
    print("Generating comparison histogram...")
    fig, ax = plt.subplots(figsize=(12, 7))
    
    # Combined range for bins
    all_areas = pd.concat([tza_areas, rwa_areas])
    log_bins = np.logspace(np.log10(all_areas.min()), np.log10(all_areas.max()), 60)
    
    ax.hist(tza_areas, bins=log_bins, color='#3498db', alpha=0.6, label='Tanzania Wards (n=4,344)', edgecolor='white')
    ax.hist(rwa_areas, bins=log_bins, color='#e67e22', alpha=0.6, label='Rwanda Sectors (n=416)', edgecolor='white')
    
    ax.set_xscale('log')
    ax.set_title("Scientific Comparison: Admin Unit Sizes (TZA vs RWA)", fontsize=16, fontweight='bold', pad=20)
    ax.set_xlabel("Area (sq km, Log Scale)", fontsize=12)
    ax.set_ylabel("Frequency (Linear)", fontsize=12)
    
    ax.grid(True, which="both", ls="-", alpha=0.2)
    
    # Statistics annotations
    ax.axvline(tza_areas.median(), color='#2980b9', linestyle='--', alpha=0.8, label=f'TZA Median: {tza_areas.median():.1f} km²')
    ax.axvline(rwa_areas.median(), color='#d35400', linestyle='--', alpha=0.8, label=f'RWA Median: {rwa_areas.median():.1f} km²')
    
    ax.legend()
    
    comp_hist_path = os.path.join(output_dir, "tza_rwa_comparison_histogram.png")
    plt.savefig(comp_hist_path, dpi=300, bbox_inches='tight')
    print(f"Saved comparison histogram to {comp_hist_path}")
    plt.close()

    # 2. Cumulative Distribution Plot (Better for comparing scales)
    print("Generating distribution comparison...")
    fig, ax = plt.subplots(figsize=(10, 6))
    
    tza_sorted = np.sort(tza_areas)
    rwa_sorted = np.sort(rwa_areas)
    
    ax.step(tza_sorted, np.arange(len(tza_sorted))/len(tza_sorted), label='Tanzania (Cumulative %)', color='#3498db', lw=2)
    ax.step(rwa_sorted, np.arange(len(rwa_sorted))/len(rwa_sorted), label='Rwanda (Cumulative %)', color='#e67e22', lw=2)
    
    ax.set_xscale('log')
    ax.set_title("Cumulative Area Distribution", fontsize=14, fontweight='bold')
    ax.set_xlabel("Area (sq km, Log Scale)")
    ax.set_ylabel("Cumulative Fraction")
    ax.grid(True, alpha=0.3)
    ax.legend()
    
    dist_path = os.path.join(output_dir, "tza_rwa_area_cdf.png")
    plt.savefig(dist_path, dpi=300, bbox_inches='tight')
    plt.close()

if __name__ == "__main__":
    GPKG_TZA = r"c:\Users\nando\Downloads\popcornoutputs\tanzania_census_2022\data\processed\TZA_2022_Census_Final_Mapped.gpkg"
    SHP_RWA = r"c:\Users\nando\Downloads\popcornoutputs\RWA\Subnational\Shapefile\rwa_subnational_2000_2020.shp"
    OUT_DIR = r"c:\Users\nando\Downloads\popcornoutputs\tanzania_census_2022\data\processed"
    
    perform_comparison_analysis(GPKG_TZA, SHP_RWA, OUT_DIR)
