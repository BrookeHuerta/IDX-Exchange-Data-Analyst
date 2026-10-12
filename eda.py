import pandas as pd
from pathlib import Path

"""
--------------------------------------------------------------------------------
1. Inspect original categories
--------------------------------------------------------------------------------
"""
#locate csv folder
csv_folder = Path(__file__).resolve().parent / "csv"

#find original mothly sold files including filled versions
sold_files_by_month = {}

#remove prefix and filled suffix
for sold_path in sorted(csv_folder.glob("CRMLSSold*.csv")):
    month_string = sold_path.stem.removeprefix("CRMLSSold")
    month_string = month_string.removesuffix("_filled")

    #only accept filenames with six-digit year and month
    if len(month_string) == 6 and month_string.isdigit():
        #prefer regular file when both versions exist
        if month_string not in sold_files_by_month or (sold_path.stem == f"CRMLSSold{month_string}"):
            sold_files_by_month[month_string] = sold_path

sold_files = [sold_files_by_month[month] for month in sorted(sold_files_by_month)]


#read each file's property types
property_types = []

for sold_path in sold_files:
    sold_df = pd.read_csv(
        sold_path,
        usecols=["PropertyType"]
    )
    property_types.append(sold_df["PropertyType"])

#join columns
all_property_types = pd.concat(property_types, ignore_index=True)

#count each property type
property_counts = all_property_types.value_counts(dropna = False)
print("Sold property types before filtering:")
print(property_counts)

"""
calculate residential percentage
check each row (.eq) and return True for residential and False otherwise
.mean() makes True=1 and False=0
Their average*100 is the percentage of records that are residential
"""
residential_share = (all_property_types.eq("Residential").mean() * 100)


print(f"\nResidential share: {residential_share:.2f}%")
print(f"Other or missing share: {100 - residential_share:.2f}%")


"""
---------------------------------------------------------------------------------
2. Load residential sold dataset and inspect structure
---------------------------------------------------------------------------------
"""
#loads CSV into a DataFrame called "sold"
sold = pd.read_csv(csv_folder / "combined_sold_residential.csv", low_memory=False)

print("\nNumber of rows:", sold.shape[0])
print("Number of columns:", sold.shape[1])

print("\nColumn names:")
print(sold.dtypes.to_string())

print("\n First five rows:")
print(sold.head())

print("\nProperty types after filtering:")
print(sold["PropertyType"].unique())


"""
------------------------------------------------------------------------------------
3. Missing values
------------------------------------------------------------------------------------
"""