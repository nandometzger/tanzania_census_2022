import pdfplumber
import pandas as pd
import re
import os

def parse_number(s):
    if not s: return 0
    s = str(s).replace(',', '').strip()
    try:
        return int(s)
    except:
        return 0

TZA_REGIONS = [
    "DODOMA", "ARUSHA", "KILIMANJARO", "TANGA", "MOROGORO", "PWANI", 
    "DAR ES SALAAM", "LINDI", "MTWARA", "RUVUMA", "IRINGA", "MBEYA", 
    "SINGIDA", "TABORA", "RUKWA", "KIGOMA", "SHINYANGA", "KAGERA", 
    "MWANZA", "MARA", "MANYARA", "NJOMBE", "KATAVI", "SIMIYU", 
    "GEITA", "SONGWE", "KASKAZINI UNGUJA", "KUSINI UNGUJA", 
    "MJINI MAGHARIBI", "KASKAZINI PEMBA", "KUSINI PEMBA"
]

# Keywords that indicate a row is a summary level (District, Council, Town, etc.)
# If these appear in the "Ward" name column, we should usually skip them.
SUMMARY_KEYWORDS = ["COUNCIL", "DISTRICT", "TOWN", "CITY", "MUNICIPAL", "REGION", "TOTAL"]

def extract_census(pdf_path, start_page=50):
    data = []
    
    if not os.path.exists(pdf_path):
        print(f"Error: PDF file not found at {pdf_path}. Please run download_census.py first.")
        return None

    with pdfplumber.open(pdf_path) as pdf:
        total_pages = len(pdf.pages)
        print(f"Total Pages: {total_pages}. Starting extraction...")
        
        current_region = "Unknown"
        current_council = "Unknown"
        
        for i in range(start_page, total_pages):
            page = pdf.pages[i]
            text = page.extract_text()
            
            if not text:
                continue

            # Check if this page is a summary page (like "Population Distribution by Council")
            # Usually these have titles like "Table X.0" or "by Council ... Region" 
            # while ward tables are "Table X.1", "Table X.2", etc.
            is_summary_page = False
            if "Table " in text:
                table_num_match = re.search(r"Table\s+(\d+)\.0", text)
                if table_num_match:
                    is_summary_page = True

            # Robust Region Detection
            region_match = re.search(r"Region\s*\d*:\s*([\w\s]+)", text)
            if region_match:
                r_name = region_match.group(1).split('\n')[0].strip().upper()
                for reg in TZA_REGIONS:
                    if reg in r_name:
                        current_region = reg
                        current_council = "Unknown"
                        break
            
            table_region_match = re.search(r"by Council\s*([\w\s]+)\s*Region", text, re.IGNORECASE)
            if table_region_match:
                r_name = table_region_match.group(1).split('\n')[0].strip().upper()
                for reg in TZA_REGIONS:
                    if reg in r_name:
                        if reg != current_region:
                            current_region = reg
                            current_council = "Unknown"
                        break

            council_match = re.search(r"\d+\.\d+\s+([\w\s]+COUNCIL|[\w\s]+DISTRICT|[\w\s]+TOWN|[\w\s]+CITY)", text.upper())
            if council_match:
                c_name = council_match.group(1).strip()
                if len(c_name) < 50:
                    current_council = c_name

            tables = page.extract_tables()
            if not tables:
                continue
                
            for table in tables:
                header_row = [str(c) for c in table[0] if c]
                # A ward table usually has "Ward" in its header, summary tables have "Council"
                is_ward_table = any("Ward" in h for h in header_row)
                
                # If we are on a summary page or it's clearly not a ward table, be extremely careful
                if is_summary_page and not is_ward_table:
                    continue

                for row in table:
                    clean_row = [str(c).replace('\n', ' ').strip() if c else '' for c in row]
                    if not any(clean_row): continue
                    
                    name = clean_row[0]
                    if not name or "Sex Ratio" in str(clean_row) or "Population" in name: continue
                    
                    # Update Region if found in name
                    if name.upper() in TZA_REGIONS or "REGION" in name.upper():
                         row_text = " ".join(clean_row).upper()
                         for reg in TZA_REGIONS:
                             if reg in row_text and len(row_text.split()) < 10:
                                 current_region = reg
                         continue

                    # Update council if row indicates a new council context
                    if any(kw in name.upper() for kw in ["COUNCIL", "DISTRICT", "TOWN", "CITY"]):
                        current_council = name
                        # We don't skip the row here if it's a ward table, 
                        # but we must skip it if it's acting as a header
                        if not is_ward_table: continue

                    # Extract numbers
                    numeric_cells = []
                    text_cells = []
                    for idx, cell in enumerate(clean_row):
                        val_clean = cell.replace(',', '').strip()
                        if re.match(r"^\d+[\.,]?\d*$", val_clean):
                            numeric_cells.append(parse_number(cell))
                        else:
                            if cell.strip(): text_cells.append(cell.strip())
                    
                    if len(numeric_cells) < 3: continue

                    # Skip index number at start
                    if len(numeric_cells) >= 4 and numeric_cells[0] < 500 and numeric_cells[1] > numeric_cells[0]:
                        numeric_cells = numeric_cells[1:]

                    ward_name = " ".join(text_cells)
                    if not ward_name: ward_name = name
                    
                    # FINAL FILTER: Skip if ward name is essentially a council or summary label
                    w_upper = ward_name.upper()
                    if any(kw in w_upper for kw in SUMMARY_KEYWORDS):
                        continue
                    if w_upper == current_council.upper() or w_upper == current_region.upper():
                        continue

                    total = numeric_cells[0]
                    male = numeric_cells[1]
                    female = numeric_cells[2]
                    
                    if total < 10: continue

                    data.append({
                        "Region": current_region,
                        "Council": current_council,
                        "Ward": ward_name,
                        "Total_Pop": total,
                        "Male_Pop": male,
                        "Female_Pop": female
                    })
                    
            if i % 20 == 0:
                print(f"Processed page {i}/{total_pages} ({current_region} / {current_council})...")

    df = pd.DataFrame(data)
    df = df.drop_duplicates()
    print(f"\nExtraction complete. Found {len(df)} records.")
    return df

if __name__ == "__main__":
    ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    input_pdf = os.path.join(ROOT, "data", "raw", "TZA_2022_Census_Vol1A.pdf")
    output_csv = os.path.join(ROOT, "data", "processed", "tza_census_2022_wards_clean.csv")
    
    df = extract_census(input_pdf)
    if df is not None:
        df.to_csv(output_csv, index=False)
        print(f"Saved cleaned census data to: {output_csv}")
