import pandas as pd
from fuzzy_matcher import preprocess_data, run_specific_match

# Load sample CSVs
df1_raw = pd.read_csv('coloniel hyundai sales_mayjunejuly.csv')
df2_raw = pd.read_csv('coloniel hyundai sales match_mayjunejuly.csv')

# Preprocess
df1 = preprocess_data(df1_raw)
df2 = preprocess_data(df2_raw)

# Run example match for FullAddress
results = run_specific_match(df1, df2, 'FullAddress', threshold=80.0)

# Print top 5 results for verification
print("Top 5 FullAddress Matches:")
print(results.head(5))