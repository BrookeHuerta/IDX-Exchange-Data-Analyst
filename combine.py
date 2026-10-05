import pandas as pd
from datetime import date


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

    sold_filename = f"csv/CRMLSSold{month_string}.csv"
    listing_filename = f"csv/CRMLSListing{month_string}.csv"

    sold_df = pd.read_csv(sold_filename)
    listing_df = pd.read_csv(listing_filename)

    sold_files.append(sold_df)
    listing_files.append(listing_df)

    month += 1       #At December, move to January of next year
    if month > 12:
        month = 1
        year += 1


#3. Check row counts and concatenate monthly files
sold_rows_before = sum(len(df) for df in sold_files)
listing_rows_before = sum(len(df) for df in listing_files)

sold = pd.concat(sold_files, ignore_index=True)
listing = pd.concat(listing_files, ignore_index=True)

sold_rows_after = len(sold)
listing_rows_after = len(listing)


#4. Filter to residential properties

#5. Save the combined datasets

#6. Print final row counts