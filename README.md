# Tanzania 2022 Population and Housing Census (PHC) Data Compilation

This project provides a comprehensive, granular (Ward-level) population dataset for the United Republic of Tanzania, integrated with the official 2022 administrative boundaries.

![Tanzania Population Density 2022](data/processed/tza_pop_density_map.png)

## 1. Data Sources

*   **Population Data**: National Bureau of Statistics (NBS) Tanzania.
    *   **Report**: *Administrative Units Population Distribution Report (Volume 1A)*, published January 2024.
    *   **Official Link**: [https://www.nbs.go.tz/uploads/statistics/documents/en-1705484562-Administrative_units_Population_Distribution_Report_Tanzania_volume1a.pdf](https://www.nbs.go.tz/uploads/statistics/documents/en-1705484562-Administrative_units_Population_Distribution_Report_Tanzania_volume1a.pdf)
*   **Geospatial Data**: National Bureau of Statistics (NBS) Tanzania.
    *   **Layer**: 2022 PHC Ward Boundaries.
    *   **Direct Link (Zip)**: [https://www.nbs.go.tz/uploads/statistics/documents/en-1714652282-TANZANIA_2022PHC_WARD_SHAPEFILES.zip](https://www.nbs.go.tz/uploads/statistics/documents/en-1714652282-TANZANIA_2022PHC_WARD_SHAPEFILES.zip)

---

## 2. Detailed Methodology

### Phase 1: Robust Data Retrieval
*   **Solution**: A Python script (`download_census.py`) mimics a browser session to bypass NBS server blocks.
*   **Verification**: PDF data verified against known regional totals.

### Phase 2: PDF Data Extraction
*   **Process**: Programmatic extraction from pages 54--280 using `pdfplumber`. 
*   **Logic**: Context-aware parsing that tracks Region and Council state changes while identifying granular Ward-level (Mainland) and **Shehia-level (Zanzibar)** population counts.

### Phase 3: Data Cleaning & Normalization
*   **Standardization**: Names normalized to uppercase and stripped of administrative suffixes (e.g., "District Council") to enable reliable joining.
*   **Filtering**: Systematic removal of summary/aggregate rows (District/Council totals) to prevent population inflation.

### Phase 4: Geospatial Mapping
*   **Strategy**: Multistage join (Full context -> Fallback) with manual overrides for specific naming variances (e.g., `Nghaheleze` → `Ngaheleze`).
*   **Match Rate**: **98.41%** overall successful mapping across the NBS ward boundary layer.
    *   **Zanzibar Match Rate**: **98.1%** (achieved by correctly parsing *Shehia* unit types).

---

## 3. Data Quality & Corrections

### The "Tunduma Outlier"
During initial runs, a density outlier was identified in **Tunduma Ward** (~568,000 people/sq km).
*   **Root Cause**: The parser originally mapped Council-level summary totals to individual Ward polygons sharing the same name.
*   **Fix**: Implemented strict keyword filtering and page-schema detection in `extract_census_data.py`.

### The "Zanzibar Data Gap"
Initial maps showed white areas (missing data) in Unguja and Pemba.
*   **Root Cause**: Zanzibar administrative units are officially called **Shehia**, not *Wards*. The initial extraction script only looked for "Ward" labels.
*   **Fix**: Updated the parser to recognize both "Ward" and "Shehia" headers/units, increasing Zanzibar coverage from ~59% to over 98%.

---

## 4. Spatial Analysis & Results

Basic spatial analysis was performed using **UTM Zone 37S (EPSG:32737)** for area calculations.

### Key Metrics:
*   **Total Polygons Analyzed**: 4,344
*   **Matched Records**: 4,275
*   **Mean Ward Area**: 204.65 sq km
*   **Max Population Density**: ~37,222 people/sq km (Tandale Ward, Dar es Salaam).
*   **Median Population Density**: 138 people/sq km.

### Visual Analysis

#### Ward Size Distribution
The histogram below showing the distribution of ward areas (log-scaled x-axis) highlights the extreme contrast between compact urban wards and expansive rural ones.

![Ward Size Distribution](data/processed/tza_ward_size_histogram.png)

#### International Comparison: Tanzania vs. Rwanda
To contextualize the scale of Tanzania's administrative units, we compared Ward sizes with **Rwanda's Sectors (Imirenge)**. 
- While Rwanda is significantly smaller, its administrative units (Sectors) show a much narrower distribution, centered around ~60 km².

![TZA vs RWA Comparison](data/processed/tza_rwa_comparison_histogram.png)

#### Regional Density Zooms
Detailed views of high-density areas:

| Dar es Salaam | Zanzibar |
| :---: | :---: |
| ![Dar es Salaam Density](data/processed/zoom_dar_density.png) | ![Zanzibar Density](data/processed/zoom_zanzibar_density.png) |

---

## 5. Final Data Product & Usage

*   **File**: `data/processed/TZA_2022_Census_Final_Mapped.gpkg` (GeoPackage)
*   **Attributes**: Original NBS boundary fields + `Total_Pop`, `Male_Pop`, `Female_Pop`, `area_sqkm`, `density`.

### How to Reproduce

```powershell
# 1. Download Census PDF
python scripts/download_census.py

# 2. Extract Data to CSV
python scripts/extract_census_data.py

# 3. Join with Shapefile
python scripts/finalize_mapping.py

# 4. Generate Analysis & Plots
python scripts/analysis.py
```

---
**Date**: January 19, 2026
