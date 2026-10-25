import pandas as pd
from pathlib import Path
import matplotlib.pyplot as plt

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
---------------------------------------------------------------------------------
2. Load residential sold dataset and inspect structure
---------------------------------------------------------------------------------
"""
#loads CSV into a DataFrame called "sold"
sold = pd.read_csv(csv_folder / "combined_sold_residential.csv", low_memory=False)

print("\nNumber of rows:", sold.shape[0])
print("Number of columns:", sold.shape[1])

print("\nColumn data types:")
print(sold.dtypes.to_string())

print("\nFirst five rows:")
print(sold.head().to_string())

#keep only Residential properties
sold = sold[sold["PropertyType"] == "Residential"].copy()

print("\nProperty types after filtering:")
print(sold["PropertyType"].unique())


"""
------------------------------------------------------------------------------------
3. Missing values
------------------------------------------------------------------------------------
"""
#check missing values in each column
missing_count = sold.isna().sum()

#calculate the percentage missing in each column
missing_percent = (missing_count / len(sold)) * 100

#combine the results into one table
missing_summary = pd.DataFrame({"Missing Count": missing_count, "Missing Percent": missing_percent})

#put the columns with the most missing values first
missing_summary = missing_summary.sort_values(by="Missing Count", ascending=False)

#flag columns with more than 90% missing values
missing_summary["Above 90% Null"] = (
    missing_summary["Missing Percent"] > 90
)

print("\nMissing values by column:")
print(missing_summary.round(2).to_string())

# Summarize key numerical columns
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

print("\nNumerical summary:")
print(sold[numeric_columns].describe().round(2).to_string())

"""
---------------------------------------------------------------------------------------------
4. Histograms and boxplots
----------------------------------------------------------------------------------------------
"""
#create a folder for the plots
plot_folder = csv_folder.parent / "eda_plots"
plot_folder.mkdir(exist_ok=True)

for column in numeric_columns:
    values = sold[column].dropna()     #exlcude missing values
    fig, axes = plt.subplots(1,2, figsize=(12, 4))
    axes[0].hist(values, bins=50)
    axes[0].set_title(f"{column} histogram")
    axes[0].set_xlabel(column)
    axes[0].set_ylabel("Number of properties")
    axes[1].boxplot(values)
    axes[1].set_title(f"{column} boxplot")
    axes[1].set_ylabel(column)

    fig.tight_layout()
    fig.savefig(plot_folder / f"{column}.png")
    plt.close(fig)


"""
------------------------------------------------------------------------------------------------
5. Field roles and missing-value decisions
-------------------------------------------------------------------------------------------------
"""
#core fields to retain even when partially missing
core_fields = numeric_columns + [
    "PropertyType",
    "CloseDate",
    "ListingContractDate",
    "CountyOrParish"
]

#metadata examples present in this dataset
metadata_fields = [
    "ListingKey",
    "ListingKeyNumeric",
    "ListingId",
    "ListAgentEmail",
    "ListAgentFirstName",
    "ListAgentLastName",
    "BuyerAgentMlsId",
    "OriginatingSystemName"
]

print("\nCore market analysis fields:")
print(core_fields)

print("\nMetadata examples:")
print(metadata_fields)

#propose dropping highly incomplete fields, except core fields
drop_candidates = [
    column
    for column in missing_summary.index
    if missing_summary.loc[column, "Above 90% Null"]
    and column not in core_fields
]

print("\nColumns proposed for dropping during cleaning:")
print(drop_candidates)

print("\nRetain core fields even when partially missing.")


"""
------------------------------------------------------------------------------------
6. Flag extreme outliers for later review
------------------------------------------------------------------------------------
"""
outlier_results = []

for column in numeric_columns:
    values = sold[column].dropna()

    q1 = values.quantile(0.25)
    q3 = values.quantile(0.75)
    iqr = q3 - q1

    # Use outer fences to flag potential extreme outliers
    lower_bound = q1 - 3 * iqr
    upper_bound = q3 + 3 * iqr

    extreme = (values < lower_bound) | (values > upper_bound)

    outlier_results.append({
        "Field": column,
        "Lower Bound": lower_bound,
        "Upper Bound": upper_bound,
        "Extreme Count": extreme.sum()
    })

print("\nPotential extreme outliers using 3 × IQR:")
print(pd.DataFrame(outlier_results).round(2).to_string(index=False))

#save the filtered dataset as a new CSV
output_path = csv_folder / "eda_sold_residential.csv"
sold.to_csv(output_path, index=False)

print(f"\nFiltered dataset saved to: {output_path}")