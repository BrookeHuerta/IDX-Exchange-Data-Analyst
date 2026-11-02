import pandas as pd
from pathlib import Path


"""
-----------------------------------------------------------------------------------------------------
1. Load data and record starting dimensions
-----------------------------------------------------------------------------------------------------
"""
csv_folder = Path(__file__).resolve().parent / "csv"
sold = pd.read_csv(
    csv_folder / "eda_sold_residential.csv",
    low_memory=False
)
starting_rows = len(sold)
starting_columns = sold.shape[1]
print("Starting rows:", starting_rows)
print("Starting columns:", starting_columns)


"""
-------------------------------------------------------------------------------------------------------
2. Convert date fields to datetime format
-------------------------------------------------------------------------------------------------------
"""
date_columns = [
    "CloseDate",
    "PurchaseContractDate",
    "ListingContractDate",
    "ContractStatusChangeDate"
]
for column in date_columns:
    originally_present = sold[column].notna()  #recall what values were present before conversion
    #Unreadable dates become NaT (pandas' missing datetime value)
    sold[column] = pd.to_datetime(
        sold[column],
        errors = "coerce"
    )

    #Distinguish unreadable dates from missing dates
    conversion_failed = originally_present & sold[column].isna()

    print(f"\n{column}:")
    print("  Date type:", sold[column].dtype)
    print("  Failed conversions:", conversion_failed.sum())
    print("  Total missing dates:", sold[column].isna().sum())


"""
-------------------------------------------------------------------------------------------------------
3. Date consistency checks
-------------------------------------------------------------------------------------------------------
"""
#Listing date <= Purchase contract date <= Closing date

#Flag properties listed after they close
sold["listing_after_close_flag"] = (
    sold["ListingContractDate"] > sold["CloseDate"]
)

#Flag purchase contracts dated after closing
sold["purchase_after_close_flag"] = (
    sold["PurchaseContractDate"] > sold["CloseDate"]
)

#Flag purchase contracts dated before the property was listed 
sold["negative_timeline_flag"] = (
    sold["PurchaseContractDate"] < sold["ListingContractDate"]
)

date_flags = [
    "listing_after_close_flag",
    "purchase_after_close_flag",
    "negative_timeline_flag"
]

print("\nDate consistency flag counts:")
for column in date_flags:
    print(f"  {column}: {sold[column].sum()}")


"""
-------------------------------------------------------------------------------------------------------
4. Geographic data checks
-------------------------------------------------------------------------------------------------------
"""
#Convert coordinates to numbers before checking them
for column in ["Latitude", "Longitude"]:
    originally_present = sold[column].notna()

    sold[column] = pd.to_numeric(
        sold[column],
        errors="coerce"
    )

    conversion_failed = originally_present & sold[column].isna()
    print(f"\n{column}:")
    print("  Data type:", sold[column].dtype)
    print("  Failed conversions:", conversion_failed.sum())

#Flag records missing either coordinate
sold["missing_coordinates_flag"] = (
    sold["Latitude"].isna() | sold["Longitude"].isna()
)

#Flag zero coordinates, which may represent missing data
sold["zero_coordinates_flag"] = (
    (sold["Latitude"] == 0) | (sold["Longitude"] == 0)
)

#Flag longitude>0 errors (California coords should be negative)
sold["positive_longitude_flag"] = sold["Longitude"] > 0

#Flag coordinates outside the possible worldwide ranges
sold["implausible_coordinates_flag"] = (
    (sold["Latitude"].notna() & ~sold["Latitude"].between(-90, 90))
    | (sold["Longitude"].notna() & ~sold["Longitude"].between(-180, 180))
)

#Check: California bounding box; flags records for review
coordinates_present = (
    sold["Latitude"].notna() & sold["Longitude"].notna()
)

sold["outside_california_bounds_flag"] = (
    coordinates_present
    & ~(
        sold["Latitude"].between(32.5, 42.1)
        & sold["Longitude"].between(-124.5, -114.0)
    )
)

#Normalize state labels for comparison
state = sold["StateOrProvince"].astype("string").str.strip().str.upper()

#Flag known non-California state labels; missing states remain separate
sold["out_of_state_flag"] = (
    state.notna() & state.ne("CA")
).fillna(False)

geographic_flags = [
    "missing_coordinates_flag",
    "zero_coordinates_flag",
    "positive_longitude_flag",
    "implausible_coordinates_flag",
    "outside_california_bounds_flag"  #check, not necessary flag
]
    
print("\nGeographic data quality flag counts:")
for column in geographic_flags:
    print(f"  {column}: {sold[column].sum()}")

print(
    "Records with at least one geographic flag:",
    sold[geographic_flags].any(axis=1).sum()
)

print(sold["StateOrProvince"].value_counts(dropna=False))


"""
-------------------------------------------------------------------------------------------------------
5. Convert numeric fields
-------------------------------------------------------------------------------------------------------
"""
numeric_columns = [
    "ClosePrice",
    "ListPrice",
    "OriginalListPrice",
    "LivingArea",
    "LotSizeAcres",
    "BedroomsTotal",
    "BathroomsTotalInteger",
    "DaysOnMarket",
    "YearBuilt"
]

for column in numeric_columns:
    originally_present = sold[column].notna()

    sold[column] = pd.to_numeric(
        sold[column],
        errors = "coerce"
    )
    conversion_failed = originally_present & sold[column].isna()

    print(f"\n{column}:")
    print("  Data type:", sold[column].dtype)
    print("  Failed conversions:", conversion_failed.sum())
    print("  Total missing values:", sold[column].isna().sum())


"""
-------------------------------------------------------------------------------------------------------
6. Flag invalid numeric values
-------------------------------------------------------------------------------------------------------
"""
sold["invalid_close_price_flag"] = sold["ClosePrice"] <= 0

sold["invalid_living_area_flag"] = sold["LivingArea"] <= 0

sold["negative_days_on_market_flag"] = sold["DaysOnMarket"] < 0

sold["negative_bedrooms_flag"] = sold["BedroomsTotal"] < 0

sold["negative_bathrooms_flag"] = sold["BathroomsTotalInteger"] < 0

numeric_flags = [
    "invalid_close_price_flag",
    "invalid_living_area_flag",
    "negative_days_on_market_flag",
    "negative_bedrooms_flag",
    "negative_bathrooms_flag"
]

print("\nInvalid numeric value flag counts:")
for column in numeric_flags:
    print(f"  {column}: {sold[column].sum()}")

print(
    "Records with at least one invalid numeric value:",
    sold[numeric_flags].any(axis=1).sum()
)

"""
-------------------------------------------------------------------------------------------------------
7. Remove unnecessary or redundant columns
-------------------------------------------------------------------------------------------------------
"""
#Identify empty columns
empty_columns = sold.columns[sold.isna().all()].tolist()

print("\nCompletely empty columns:")
print(empty_columns)
print("Number of completely empty columns:", len(empty_columns))

#Remove empty columns
sold = sold.drop(columns=empty_columns)

print("Columns removed:", len(empty_columns))
print("Remaining columns:", sold.shape[1])
print("Rows after removing empty columns:", len(sold))
print("\nRemaining column names:")
print(sold.columns.tolist())


"""
-------------------------------------------------------------------------------------------------------
8. Handle missing values
-------------------------------------------------------------------------------------------------------
"""
missing_counts = sold.isna().sum()

missing_summary = pd.DataFrame({
    "Missing count": missing_counts,
    "Missing percent": (missing_counts / len(sold) * 100).round(2)
})

missing_summary = missing_summary[
    missing_summary["Missing count"] > 0
].sort_values("Missing count", ascending=False)

print("\nMissing-value summary:")
print(missing_summary.to_string())

#Retain missing values as unknown rather than filling them in with guesses
#Flag missing values needed for price and price-per-square-foot analysis
sold["missing_close_price_flag"] = sold["ClosePrice"].isna()
sold["missing_living_area_flag"] = sold["LivingArea"].isna()

print("\nKey missing-value flag counts:")
print("  Missing ClosePrice:", sold["missing_close_price_flag"].sum())
print("  Missing LivingArea:", sold["missing_living_area_flag"].sum())


"""
-------------------------------------------------------------------------------------------------------
9. Save cleaned CSV and print final summary
-------------------------------------------------------------------------------------------------------
"""
output_path = csv_folder / "cleaned_sold_residential.csv"

#Save missing values as blank CSV fields and omit dataframe index
sold.to_csv(output_path, index=False)

print("\nFinal dimensions:")
print("  Starting rows:", starting_rows)
print("  Final rows:", len(sold))
print("  Rows removed:", starting_rows - len(sold))
print("  Starting columns:", starting_columns)
print("  Final columns:", sold.shape[1])

print("\nFinal date types:")
print(sold[date_columns].dtypes.to_string())

print("\nFinal numeric types:")
print(
    sold[numeric_columns + ["Latitude", "Longitude"]]
    .dtypes.to_string()
)

print("\nFinal date consistency flag counts:")
print(sold[date_flags].sum().to_string())

print("\nFinal geographic flag counts:")
print(sold[geographic_flags].sum().to_string())
print(
    "Records with at least one geographic flag:",
    sold[geographic_flags].any(axis=1).sum()
)

print("\nFinal invalid numeric flag counts:")
print(sold[numeric_flags].sum().to_string())
print(
    "Records with at least one invalid numeric value:",
    sold[numeric_flags].any(axis=1).sum()
)

print("\nKey missing-value flag counts:")
print(sold[
    ["missing_close_price_flag", "missing_living_area_flag"]
].sum().to_string())

print("\nRemoved empty columns:", empty_columns)
print("Missing-value policy: retained as unknown; no imputation.")
print("\nCleaned CSV saved to:", output_path)