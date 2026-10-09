import pandas as pd
from datetime import date
from pathlib import Path
csv_folder = Path(__file__).resolve().parent / "csv"

#1. Create the date range
year = 2024
month = 1

today = date.today()
if today.month == 1:
    end_month = 12
    end_year = today.year - 1
else:
    end_month = today.month - 1
    end_year = today.year


#2. Load monthly csv files
sold_files = []
listing_files = []

while (year, month) <= (end_year, end_month):
    month_string = f"{year}{month:02d}"  #make format 202401, 202402, etc.

    sold_filename = f"CRMLSSold{month_string}.csv"
    listing_filename = f"CRMLSListing{month_string}.csv"

    sold_path = csv_folder / sold_filename
    if not sold_path.exists():
        sold_path = csv_folder / f"CRMLSSold{month_string}_filled.csv"

    sold_df = pd.read_csv(sold_path, low_memory=False)
    listing_df = pd.read_csv(csv_folder / listing_filename, low_memory=False)

    sold_files.append(sold_df)
    listing_files.append(listing_df)

    month += 1       #At December, move to January of next year
    if month > 12:
        month = 1
        year += 1


#3. Check row counts and concatenate monthly files
sold_rows_before = sum(len(df) for df in sold_files)            
listing_rows_before = sum(len(df) for df in listing_files)      

combined_sold = pd.concat(sold_files, ignore_index=True)
combined_listing = pd.concat(listing_files, ignore_index=True)

sold_rows_after = len(combined_sold)                            
listing_rows_after = len(combined_listing)                      

print("Sold rows before:", sold_rows_before)
print("Sold rows after:", sold_rows_after)

print("Listing rows before:", listing_rows_before)
print("Listing rows after:", listing_rows_after)

    #Sold rows before:     736517
    #Sold rows after:      736517
    #Listing rows before:  1025339
    #Listing rows after:   1025339


#4. Filter to residential properties
combined_sold = combined_sold[
    combined_sold["PropertyType"] == "Residential"
].copy()

combined_listing = combined_listing[
    combined_listing["PropertyType"] == "Residential"
].copy()


#5. Save the combined datasets
combined_sold.to_csv(
    csv_folder / "combined_sold_residential.csv",
    index=False
)

combined_listing.to_csv(
    csv_folder / "combined_listing_residential.csv",
    index=False
)

#6. Print final row counts
print("Final residential sold rows:", len(combined_sold))
print("Final residential listing rows:", len(combined_listing))

    #Final residential sold rows:     495321
    #Final residential listing rows:  652026