from pathlib import Path
import pandas as pd
import geopandas as gpd

"""
---------------------------------------------------------------------------------------
1. Load cleaned dataset
---------------------------------------------------------------------------------------
"""
csv_dir = Path(__file__).resolve().parent / "csv"

#Replace filename with output filename from clean.py
input_file = csv_dir / "cleaned_sold_residential.csv"

df = pd.read_csv(input_file, low_memory=False)

print("Starting rows:", df.shape[0])
print("Starting columns:", df.shape[1])



"""
---------------------------------------------------------------------------------------
2. Check required columns and data types
---------------------------------------------------------------------------------------
"""
date_columns = [
    "CloseDate",
    "ListingContractDate",
    "PurchaseContractDate",
]

for column in date_columns:
    df[column] = pd.to_datetime(df[column], errors="coerce")

numeric_columns = [
    "ClosePrice",
    "ListPrice",
    "OriginalListPrice",
    "LivingArea",
    "DaysOnMarket",
    "Latitude",
    "Longitude",
]

for column in numeric_columns:
    df[column] = pd.to_numeric(df[column], errors="coerce")



"""
---------------------------------------------------------------------------------------
3. Create engineered metrics 
---------------------------------------------------------------------------------------
"""
df["PriceRatio"] = df["ClosePrice"] / df["OriginalListPrice"]

df["PricePerSqFt"] = df["ClosePrice"] / df["LivingArea"]

#Days on market already exists

#Extract year, month, yrmo from close date
df["Year"] = df["CloseDate"].dt.year
df["Month"] = df["CloseDate"].dt.month
df["YrMo"] = df["CloseDate"].dt.strftime("%Y-%m")

df["CloseToOriginalListRatio"] = (df["ClosePrice"] / df["OriginalListPrice"])

df["ListingToContractDays"] = (df["PurchaseContractDate"] - df["ListingContractDate"]).dt.days

df["ContractToCloseDays"] = (df["CloseDate"] - df["PurchaseContractDate"]).dt.days



"""
---------------------------------------------------------------------------------------
4. Add school districts using coordinates
---------------------------------------------------------------------------------------
"""
#Get school district boundary file
district_file = (
    Path(__file__).resolve().parent / "DistrictAreas2425" / "DistrictAreas2425.shp"
)
districts = gpd.read_file(district_file)

print("\nSchool district columns:")
print(districts.columns.tolist())

print("\nSchool district sample:")
print(districts.head())

print("\nSchool districts coordinate reference system:")
print(districts.crs)

#Select properties with usable coordinates.
valid_coordinates = (
    df["Latitude"].between(-90, 90)
    & df["Longitude"].between(-180, 180)
    & ~((df["Latitude"] == 0) & (df["Longitude"] == 0))
)

#Create geographic points: longitude is x, latitude is y
properties = gpd.GeoDataFrame(
    df.loc[valid_coordinates, ["Latitude", "Longitude"]].copy(),
    geometry=gpd.points_from_xy(
        df.loc[valid_coordinates, "Longitude"],
        df.loc[valid_coordinates, "Latitude"],
    ),
    crs="EPSG:4326",
)

#Match the coordinate system used by the school district boundaries
properties = properties.to_crs(districts.crs)

print("\nProperties with usable coordinates:", len(properties))

print("\nSchool district types:")
print(districts["DistrictTy"].value_counts())

print("\nDistrict name and type sample:")
print(districts[["DistrictNa", "DistrictTy"]].head(10))

#Match property points to the district boundaries containing them.
matches = gpd.sjoin(
    properties,
    districts[["DistrictNa", "DistrictTy", "geometry"]],
    how="left",
    predicate="within",
)

#Add one district column for each district type
for district_type in ["Elementary", "High", "Unified"]:

    #Select matches for this district type
    type_matches = matches.loc[
        matches["DistrictTy"] == district_type
    ]

    #Combine multiple matches without duplicating property rows
    district_names = type_matches.groupby(level=0)["DistrictNa"].agg(
        lambda names: "; ".join(sorted(set(names.dropna())))
    )

    #Match district names back to the original property row indexes
    df[f"{district_type}SchoolDistrict"] = df.index.map(district_names)

print("\nSchool district matches:")
print(
    df[
        [
            "ElementarySchoolDistrict",
            "HighSchoolDistrict",
            "UnifiedSchoolDistrict",
        ]
    ].notna().sum()
)

print("\nRows after adding districts:", len(df))



"""
---------------------------------------------------------------------------------------
5. Sample output table
---------------------------------------------------------------------------------------
"""
sample_columns = [
    "ClosePrice",
    "OriginalListPrice",
    "LivingArea",
    "PriceRatio",
    "PricePerSqFt",
    "DaysOnMarket",
    "Year",
    "Month",
    "YrMo",
    "CloseToOriginalListRatio",
    "ListingToContractDays",
    "ContractToCloseDays",
]
print("\nSample engineered metrics:")
print(df[sample_columns].head(10).to_string(index=False))



"""
---------------------------------------------------------------------------------------
6. Create segmented summary tables
---------------------------------------------------------------------------------------
"""
summary_metrics = {
    "TransactionCount": ("ClosePrice", "size"),
    "MedianClosePrice": ("ClosePrice", "median"),
    "MedianPriceRatio": ("PriceRatio", "median"),
    "MedianPricePerSqFt": ("PricePerSqFt", "median"),
    "MedianDaysOnMarket": ("DaysOnMarket", "median"),
    "MedianCloseToOriginalListRatio": ("CloseToOriginalListRatio", "median"),
    "MedianListingToContractDays": ("ListingToContractDays", "median"),
    "MedianContractToCloseDays": ("ContractToCloseDays", "median"),
}

segment_columns = [
    "PropertyType",
    "PropertySubType",
    "CountyOrParish",
    "MLSAreaMajor",
    "ListOfficeName",
    "BuyerOfficeName",
]

summaries = {}

for column in segment_columns:
    summary = (
        df.groupby(column, dropna=False)
        .agg(**summary_metrics)
        .reset_index()
    )
    summaries[column] = summary

    print(f"\nSummary by {column}:")
    print(summary.head(10).round(2).to_string(index=False))




"""
---------------------------------------------------------------------------------------
7. Save and display the outputs
---------------------------------------------------------------------------------------
"""
df.to_csv(
    csv_dir / "engineered_sold_residential.csv",
    index=False,
)

df[sample_columns].head(10).to_csv(
    csv_dir / "sample_engineered_metrics.csv",
    index=False,
)

for column, summary in summaries.items():
    summary.to_csv(
        csv_dir / f"summary_by_{column}.csv",
        index=False,
    )

print("\nEngineered dataset, sample table, and summaries saved.")



