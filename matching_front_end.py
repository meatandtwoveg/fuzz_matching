import streamlit as st
import pandas as pd
from fuzzywuzzy import fuzz
from fuzzywuzzy import process

# Function to combine selected columns into one string
def combine_columns(row, columns):
    return " ".join([str(row[col]).strip().upper() for col in columns])

# Function to find the best match using the combined string from montage and the nces dataframe
def find_best_match(montage_string, nces_df, nces_columns, threshold=80):
    nces_combined = nces_df.apply(lambda row: combine_columns(row, nces_columns), axis=1)
    best_match = process.extractOne(montage_string, nces_combined, scorer=fuzz.token_sort_ratio)
    if best_match and best_match[1] >= threshold:
        idx = nces_combined[nces_combined == best_match[0]].index[0]
        return nces_df.iloc[idx], best_match[1]
    return None, None

# Function to update matches using fuzzy matching across multiple columns
def update_school_id_fuzzy(montage_df, nces_df, montage_cols, nces_cols,  output_file1_df_cols, output_file2_df_cols, threshold):
    results = []
    for index, row in montage_df.iterrows():
        montage_string = combine_columns(row, montage_cols)
        match, score = find_best_match(montage_string, nces_df, nces_cols, threshold)
        if match is not None:
            # Store both the original montage values and the matched NCES values
            result = {f"File1: {col}": row[col] for col in output_file1_df_cols}
            result.update({f"File2: {col}": match[col] for col in output_file2_df_cols})
            result["Match Score"] = score
            results.append(result)
    return pd.DataFrame(results)

# Streamlit UI
st.title("Fuzzy Matching Tool")

# Upload CSV files
montage_file = st.file_uploader("Upload File1 Data CSV", type=["csv"])
nces_file = st.file_uploader("Upload File2 Data CSV", type=["csv"])

if montage_file and nces_file:
    montage_data = pd.read_csv(montage_file)
    nces_data = pd.read_csv(nces_file)

    # Allow users to select up to 3 columns from each dataset
    montage_cols = st.multiselect("Select up to 3 columns for matching from Montage Data", montage_data.columns)
    if len(montage_cols) > 3:
        st.error("Please select a maximum of 3 columns for Montage Data.")
        st.stop()

    nces_cols = st.multiselect("Select up to 3 columns for matching from NCES Data", nces_data.columns)
    if len(nces_cols) > 3:
        st.error("Please select a maximum of 3 columns for NCES Data.")
        st.stop()


    output_file1_df_cols = st.multiselect("Select columns from file1 to include in final output", montage_data.columns)
    output_file2_df_cols = st.multiselect("Select columns from file1 to include in final output", nces_data.columns)
    # Set probability score threshold
    threshold = st.slider("Select Match Score Threshold", min_value=0, max_value=100, value=80)

    if st.button("Run Matching"):
        results_df = update_school_id_fuzzy(montage_data, nces_data, montage_cols, nces_cols, output_file1_df_cols, output_file2_df_cols, threshold)
        st.write("Matching Results:")
        st.dataframe(results_df)
        ## Allows user to select which columns to include in the downloadable file
        # download_cols = st.multiselect("Select columns to include in the downloaded file" ,results_df.columns.tolist(), default=results_df.columns.tolist())
        csv_data = results_df.to_csv(index=False)
        # Option to download results
        st.download_button("Download Results", csv_data, "matched_results.csv", "text/csv")