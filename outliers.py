from pathlib import Path
import pandas as pd

"""
--------------------------------------------------------------------------------
1. Load engineered dataset
--------------------------------------------------------------------------------
"""
csv_dir = Path(__file__).resolve().parent / "csv"
input_file = csv_dir / "engineered_sold_residential.csv"

df = pd.read_csv(input_file, low_memory=False)

starting_rows = len(df)



"""
--------------------------------------------------------------------------------
2. Summarize numeric fields
--------------------------------------------------------------------------------
"""
numeric_columns = [
    "ClosePrice",
    "LivingArea",
    "DaysOnMarket",
]

for column in numeric_columns:
    df[column] = pd.to_numeric(df[column], errors="coerce")

print("\nNumeric field summary:")
print(
    df[numeric_columns].describe(
        percentiles=[0.01, 0.25, 0.50, 0.75, 0.99]
    ).to_string()
)



"""
--------------------------------------------------------------------------------
3. Add business-rule and missing value flags
--------------------------------------------------------------------------------
"""
#Business-rule flags
df["invalid_close_price_flag"] = df["ClosePrice"] <= 0
df["invalid_living_area_flag"] = df["LivingArea"] <= 0 
df["negative_days_on_market_flag"] = df["DaysOnMarket"] < 0

#Missing-value flags
df["missing_close_price_flag"] = df["ClosePrice"].isna()
df["missing_living_area_flag"] = df["LivingArea"].isna()
df["missing_days_on_market_flag"] = df["DaysOnMarket"].isna()

flag_columns = [
    "invalid_close_price_flag",
    "invalid_living_area_flag",
    "negative_days_on_market_flag",
    "missing_close_price_flag",
    "missing_living_area_flag",
    "missing_days_on_market_flag",
]
print("\nInvaild and missing-value counts:")
print(df[flag_columns].sum())




"""
--------------------------------------------------------------------------------
4. Add IQR outlier flags
--------------------------------------------------------------------------------
"""
outlier_flag_columns = []
for column in numeric_columns:
    
    Q1 = df[column].quantile(0.25)
    Q3 = df[column].quantile(0.75)
    IQR = Q3 - Q1
    lower = Q1 - 1.5 * IQR
    upper = Q3 + 1.5 * IQR

    flag_column = f"{column}_iqr_outlier_flag"

    df[flag_column] = (df[column] < lower) | (df[column] > upper)
    outlier_flag_columns.append(flag_column)

    print(f"\n{column}:")
    print(f"  Lower boundary: {lower:,.2f}")
    print(f"  Upper boundary: {upper:,.2f}")
    print(f"  Outliers flagged: {df[flag_column].sum():,}")



"""
--------------------------------------------------------------------------------
5. Create separate filtered dataset
--------------------------------------------------------------------------------
"""
#Combine the flags from section 3 with the IQR flags
all_flag_columns = flag_columns + outlier_flag_columns

#Identify rows with at least one flag
exclude_row = df[all_flag_columns].any(axis=1)

#Put unflagged rows in a separate dataset
filtered_df = df.loc[~exclude_row].copy()

print("\nRows before filtering:", len(df))
print("Rows after filtering:", len(filtered_df))
print("Rows excluded:", exclude_row.sum())



"""
--------------------------------------------------------------------------------
6. Compare before and after filtering
--------------------------------------------------------------------------------
"""
rows_removed = len(df) - len(filtered_df)
percent_removed = (rows_removed / len(df)) * 100

print("\nDataset size comparison:")
print(f"Before filtering: {len(df):,}")
print(f"After filtering: {len(filtered_df):,}")
print(f"Rows excluded: {rows_removed:,}")
print(f"Percentage excluded: {percent_removed:.2f}%")

median_comparison = pd.DataFrame({
    "MedianBefore": df[numeric_columns].median(),
    "MedianAfter": filtered_df[numeric_columns].median(),
})

median_comparison["Change"] = (
    median_comparison["MedianAfter"]
    - median_comparison["MedianBefore"]
)

print("\nMedian comparison:")
print(median_comparison.round(2).to_string())



"""
--------------------------------------------------------------------------------
7. Save datasets + written comparison
--------------------------------------------------------------------------------
"""
