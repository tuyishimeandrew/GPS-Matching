#!/usr/bin/env python
# coding: utf-8

import streamlit as st
import pandas as pd
from geopy.distance import geodesic
import io

st.title("📍 Follow-ups/Engagements against old GPS data")

uploaded_file = st.file_uploader("📤 Upload your Engagement/Follow-ups Excel or CSV file", type=["xlsx", "csv"])
github_url = "https://raw.githubusercontent.com/tuyishimeandrew/GPS-Matching/main/Matching.xlsx"

# Define distance category function
def categorize_distance(meters):
    if pd.isna(meters):
        return "No Match"
    elif meters < 100:
        return "<100m"
    elif meters < 200:
        return "100m–200m"
    elif meters < 500:
        return "200m–500m"
    elif meters < 1000:
        return "500m–1km"
    else:
        return ">1km"

if uploaded_file and github_url:
    try:
        # Load files
        if uploaded_file.name.endswith(".csv"):
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file)

        ref_df = pd.read_excel(github_url)

        # Required columns
        required_cols_user = {'Farmercode', 'GPS-Latitude', 'GPS-Longitude'}
        required_cols_ref = {'Farmercode', 'Latitude', 'Longitude', 'File'}

        if not required_cols_user.issubset(df.columns):
            st.error(f"Missing in uploaded file: {required_cols_user - set(df.columns)}")
        elif not required_cols_ref.issubset(ref_df.columns):
            st.error(f"Missing in reference file: {required_cols_ref - set(ref_df.columns)}")
        else:
            results = []

            # Process each row
            for _, row in df.iterrows():
                farmer = row['Farmercode']
                point1 = (row['GPS-Latitude'], row['GPS-Longitude'])

                matches = ref_df[ref_df['Farmercode'] == farmer]

                if not matches.empty:
                    distances = matches.apply(
                        lambda r: geodesic(point1, (r['Latitude'], r['Longitude'])).meters,
                        axis=1
                    )
                    min_idx = distances.idxmin()
                    best_match = matches.loc[min_idx]
                    min_distance = round(distances[min_idx], 2)
                    category = categorize_distance(min_distance)

                    results.append({
                        **row.to_dict(),
                        'Best Match File': best_match['File'],
                        'Distance_m': min_distance,
                        'Distance Category': category,
                        'Location Validated?': best_match['Validated?']
                        
                    })
                else:
                    results.append({
                        **row.to_dict(),
                        'Best Match File': 'No Match',
                        'Distance_m': None,
                        'Distance Category': "",
                        'Location Validated?':""
                        
                    })

            result_df = pd.DataFrame(results)

            st.success(f"✅ Matched and categorized {len(result_df)} records.")
            st.dataframe(result_df.head())

            # Prepare Excel download
            output = io.BytesIO()
            result_df.to_excel(output, index=False, engine='openpyxl')

            st.download_button(
                label="📥 Download Final Excel with Distance Category",
                data=output.getvalue(),
                file_name="gps_distance_with_category.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

    except Exception as e:
        st.error(f"❌ Error: {e}")
