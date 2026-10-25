import pandas as pd
from pathlib import Path

"""
-----------------------------------------------------------------------------------------
1. Fetch weekly mortgage rates from FRED
-----------------------------------------------------------------------------------------
"""
url = "https://fred.stlouisfed.org/graph/fredgraph.csv?id=MORTGAGE30US"
mortgage = pd.read_csv(url, parse_dates=['observation_date'])
mortgage.columns = ['date', 'rate_30yr_fixed']

print("\nFirst five weekly mortgage rates:")
print(mortgage.head())

print("\nMost recent weekly mortgage rates:")
print(mortgage.tail())


"""
-----------------------------------------------------------------------------------------
2. Calculate monthly average mortgage rates
-----------------------------------------------------------------------------------------
"""
#assign each weekly observation to its calendar month
mortgage['year_month'] = mortgage['date'].dt.to_period('M')
mortgage_monthly = (
    mortgage.groupby('year_month')['rate_30yr_fixed']
    .mean()
    .reset_index()
)
print("\nMost recent monthly mortgages rates:")
print(mortgage_monthly.tail())


"""
-----------------------------------------------------------------------------------------
3. Create a matching year_month key on the MLS datasets
-----------------------------------------------------------------------------------------
"""
#load MLS datasets and create monthly keys
csv_folder = Path(__file__).resolve().parent / "csv"
sold = pd.read_csv(
    csv_folder / "combined_sold_residential.csv",
    low_memory=False
)
listings = pd.read_csv(
    csv_folder / "combined_listing_residential.csv",
    low_memory=False
)
# Match sold properties using their closing month
sold["year_month"] = (
    pd.to_datetime(sold["CloseDate"]).dt.to_period("M")
)
# Match listings using their listing contract month
listings["year_month"] = (
    pd.to_datetime(listings["ListingContractDate"]).dt.to_period("M")
)
print("\nSold monthly keys:")
print(sold[["CloseDate", "year_month"]].head())
print("\nListings monthly keys:")
print(listings[["ListingContractDate", "year_month"]].head())


#sold dataset -- key off CloseDate
sold['year_month'] = pd.to_datetime(sold['CloseDate']).dt.to_period('M')

#Listings dataset -- key off ListingContractDate
listings['year_month'] = pd.to_datetime(listings['ListingContractDate']).dt.to_period('M')


"""
------------------------------------------------------------------------------------------------------
4. Merge monthly mortgage rates onto MLS datasets
------------------------------------------------------------------------------------------------------
"""
sold_with_rates = sold.merge(mortgage_monthly, on='year_month', how='left')
listings_with_rates = listings.merge(mortgage_monthly, on='year_month', how='left')


"""
-------------------------------------------------------------------------------------------------------
5. Validate the merge
--------------------------------------------------------------------------------------------------------
"""
#Check for any unmatched rows (rate should not be null)
print("\nSold rows with missing mortgage rates:")
print(sold_with_rates['rate_30yr_fixed'].isnull().sum())

print("nListings rows with missing mortgage rates:")
print(listings_with_rates['rate_30yr_fixed'].isnull().sum())

#Preview
print("\nSold preview:")
print(
    sold_with_rates[
    ['CloseDate','year_month','ClosePrice','rate_30yr_fixed']
    ].head()
)


"""
---------------------------------------------------------------------------------------------------------
6. Save as new csv
---------------------------------------------------------------------------------------------------------
"""
sold_with_rates.to_csv(
    csv_folder / "sold_with_mortgage_rates.csv",
    index=False
)
listings_with_rates.to_csv(
    csv_folder / "listings_with_mortgage_rates.csv",
    index=False
)
print("\nBoth enriched datasets saved.")