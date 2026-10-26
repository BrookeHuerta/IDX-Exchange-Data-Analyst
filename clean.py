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
    sold["lising_after_close_flag"] = (
        sold["LisingContractDate"] > sold["CloseDate"]
    )

    #Flag purchase contracts dated after closing
    sold["purchase_after_close_flag"] = (
        sold["PurchaseContractDate"] > sold["closeDate"]
    )

    #Flag purchase contracts dated before the property was listed 
    sold["negative_timeline_flag"] = (
        sold["PurchaseContractDate"] < sold["ListingContractDate"]
    )