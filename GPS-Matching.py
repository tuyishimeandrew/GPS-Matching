#!/usr/bin/env python
# coding: utf-8

# In[ ]:


import streamlit as st
import pandas as pd
from geopy.distance import geodesic
import io

st.title("GPS Matcher by Farmercode + File")

uploaded_file = st.file_uploader("Upload your inspection Excel file", type=["xlsx"])
github_url = "https://raw.githubusercontent.com/tuyishimeandrew/GPS-Matching/main/Matching.xlsx"


if uploaded_file and github_url:
    try:
        # Load both Excel files
        df = pd.read_excel(uploaded_file)
        ref_df = pd.read_excel(github_url)

        # Required columns
        required_cols_user = {'Farmercode', 'GPS-Latitude', 'GPS-Longitude'}
        required_cols_ref = {'Farmercode', 'Latitude', 'Longitude', 'File'}

        # Validate columns
        if not required_cols_user.issubset(df.columns):
            st.error(f"Missing in uploaded file: {required_cols_user - set(df.columns)}")
        elif not required_cols_ref.issubset(ref_df.columns):
            st.error(f"Missing in reference file: {required_cols_ref - set(ref_df.columns)}")
        else:
            results = []

            # Process each row in the uploaded file
            for _, row in df.iterrows():
                farmer = row['Farmercode']
                point1 = (row['GPS-Latitude'], row['GPS-Longitude'])

                # Get all matches for Farmercode
                matches = ref_df[ref_df['Farmercode'] == farmer]

                if not matches.empty:
                    # Compute distances
                    distances = matches.apply(
                        lambda r: geodesic(point1, (r['Latitude'], r['Longitude'])).meters,
                        axis=1
                    )
                    min_idx = distances.idxmin()
                    best_match = matches.loc[min_idx]
                    results.append({
                        **row.to_dict(),
                        'Best Match File': best_match['File'],
                        'Distance_m': round(distances[min_idx], 2)
                    })
                else:
                    # No match found
                    results.append({
                        **row.to_dict(),
                        'Best Match File': 'No Match',
                        'Distance_m': None
                    })

            result_df = pd.DataFrame(results)

            # Show preview
            st.success(f"Processed {len(result_df)} records.")
            st.dataframe(result_df.head())

            # Download link
            output = io.BytesIO()
            result_df.to_excel(output, index=False, engine='openpyxl')

            st.download_button(
                label="📥 Download Final Excel with Best File + Distance",
                data=output.getvalue(),
                file_name="gps_distance_matched.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

    except Exception as e:
        st.error(f"❌ Error: {e}")

