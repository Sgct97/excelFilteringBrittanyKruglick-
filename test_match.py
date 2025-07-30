import pandas as pd
from fuzzy_matcher import preprocess_data, run_specific_match

# Load sample CSVs
df1_raw = pd.read_csv('coloniel hyundai sales_mayjunejuly.csv')
df2_raw = pd.read_csv('coloniel hyundai sales match_mayjunejuly.csv')

# Preprocess
df1 = preprocess_data(df1_raw)
df2 = preprocess_data(df2_raw)

# Run example match for FullAddress
results = run_specific_match(df1, df2, 'FullAddress', threshold=0.0)  # Lower threshold to include all

# Save all results to CSV for full review
results.to_csv('test_results.csv', index=False)
print("All results saved to test_results.csv")

# Print summary: number of matches below 100%
num_below_100 = len(results[results['Match Score'] < 100])
print(f"Number of matches with score below 100%: {num_below_100}")

# Print lowest 5 for quick view
print("Lowest 5 FullAddress Matches:")
print(results.sort_values(by='Match Score', ascending=True).head(5))