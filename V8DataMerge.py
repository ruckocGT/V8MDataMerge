import pandas as pd
import streamlit as st
from datetime import date
import numpy as np

def fill_missing_values(df):
    # Fill missing values for suffixed columns
    for col in ['Form template', 'Form template version', 'Request Type', 'Risk Level', 'Audit Opinion']:
        if f'{col}_x' in df.columns and f'{col}_y' in df.columns:
            df[f'{col}_x'].fillna(df[f'{col}_y'], inplace=True)
            df[f'{col}_y'].fillna(df[f'{col}_x'], inplace=True)
    
    # Forward fill for specific columns
    for col in ['Form template', 'Form template version', 'Request Type', 'Risk Level', 'Audit Opinion']:
        df[f'{col}_x'].ffill(inplace=True)
        df[f'{col}_y'].ffill(inplace=True)
    
    # Handle 'Not Entered' condition
    bad_cols = ['Request Type', 'Risk Level', 'Audit Opinion']
    for col in bad_cols:
        df.loc[(df['Page name_x'] == 'Title') & (df[f'{col}_x'].isin(["", "-", np.nan])), f'{col}_x'] = 'Not Entered'
        df[f'{col}_x'].ffill(inplace=True)
    
    # Select the final columns to use
    for col in ['Form template', 'Form template version', 'Request Type', 'Risk Level', 'Audit Opinion']:
        df[col] = df[f'{col}_x']
    
    return df

def add_data_from_masterfile(all_df, master_df):
    master_cols = ['Audit Opinion', 'Risk Level']
    for col in master_cols:
        temp_df = master_df[['Form_instance_ID', col]].drop_duplicates()
        all_df = pd.merge(all_df, temp_df, on='Form_instance_ID', how='left', suffixes=('', '_master'))
        all_df.loc[(all_df[col] == "Not Entered") & (all_df[col+'_master'].notna()), col] = all_df[col+'_master']
        all_df.drop(columns=[col+'_master'], inplace=True)
    
    all_df['Assignee'] = all_df['Assignee'].str.replace('--', '-')
    all_df['Role'] = all_df['Assignee'].str.split('-', expand=True)[1]
    all_df['Assignee'] = all_df['Assignee'].str.split('-', expand=True)[0]
    all_df['Page name'] = all_df['Page name'].str.strip()
    all_df['Status'] = all_df['Status'].str.strip()
    
    all_df['SLA_Date'] = all_df['Completed'].fillna(date.today())
    
    time_cols = ['Created', 'Started', 'Last Updated', 'Completed', 'SLA_Date']
    for col in time_cols:
        all_df[col] = pd.to_datetime(all_df[col], errors='coerce', infer_datetime_format=True)
    all_df['month_year'] = all_df['Created'].dt.to_period('M')
    for col in time_cols:
        all_df[col] = all_df[col].dt.date
    
    return all_df

def main():
    st.title("Valid8ME Data Merge")

    st.write("Upload Master Data (file1):")
    file1 = st.file_uploader("Upload Master Data", type=['xlsx'])

    st.write("Upload Valid8Me Output (file2):")
    file2 = st.file_uploader("Upload Valid8Me Output", type=['xlsx'])

    if st.button("Clean Data Process"):
        if file1 is not None and file2 is not None:
            try:
                df1 = pd.read_excel(file1, engine='openpyxl')
                df2 = pd.read_excel(file2, engine='openpyxl')

                # Normalize column names
                df1.columns = df1.columns.str.strip()
                df2.columns = df2.columns.str.strip()

                # Debug: Display columns in the dataframes
                st.write("Columns in the master dataframe (df1):")
                st.write(df1.columns.tolist())
                st.write("Columns in the Valid8Me dataframe (df2):")
                st.write(df2.columns.tolist())

                # Ensure Form_instance_ID columns are of the same type
                df1['Form_instance_ID'] = df1['Form_instance_ID'].astype(str)
                df2['Form_instance_ID'] = df2['Form_instance_ID'].astype(str)

                # Check if required columns exist
                required_columns = ['Form_instance_ID', 'Page name']
                for col in required_columns:
                    if col not in df1.columns:
                        st.warning(f"Column '{col}' is missing in the master dataframe.")
                        return
                    if col not in df2.columns:
                        st.warning(f"Column '{col}' is missing in the Valid8Me dataframe.")
                        return

                # Merge data
                merged_df = pd.merge(df1, df2, on=['Form_instance_ID', 'Page name'], how='outer')

                # Debug: Display columns after merge
                st.write("Columns after merge:")
                st.write(merged_df.columns.tolist())

                # Fill missing values
                merged_df = fill_missing_values(merged_df)

                # Debug: Display columns after filling missing values
                st.write("Columns after fill_missing_values:")
                st.write(merged_df.columns.tolist())

                # Add data from master file
                merged_df = add_data_from_masterfile(merged_df, df1)

                # Debug: Display columns after adding data from master file
                st.write("Columns after add_data_from_masterfile:")
                st.write(merged_df.columns.tolist())

                # Save merged file
                merged_file_path = "merged_file.xlsx"
                merged_df.to_excel(merged_file_path, index=False)

                # Provide download link for CSV
                csv_data = merged_df.to_csv(index=False).encode('utf-8')
                st.download_button(label="Download CSV", data=csv_data, file_name="Valid8MeAggregate.csv", mime="text/csv")

                st.success("Merged Excel file saved successfully.")
            except Exception as e:
                st.warning(f"Merge failed: {e}")
        else:
            st.warning("Please upload both Master Data and Valid8Me Output files.")

if __name__ == "__main__":
    main()


