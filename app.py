# app.py
import streamlit as st
import pandas as pd
from get_fuel_summary import generate_custom_fuel_summary
import tempfile
import os

st.set_page_config(page_title="Fuel Report Generator", page_icon="⛽", layout="wide")

st.title("⛽ Fuel Invoice Summary Generator")
st.write("Upload an Excel fuel invoice, choose columns to include, and generate a custom report.")

uploaded_file = st.file_uploader("📤 Upload Excel File (.xlsx)", type=["xlsx"])

if uploaded_file is not None:
    # Read uploaded Excel
    df = pd.read_excel(uploaded_file)
    
    st.subheader("Preview of Uploaded Data")
    st.dataframe(df.head(), width='stretch')

    st.subheader("Select Columns for the Report")
    all_columns = list(df.columns)
    selected_columns = st.multiselect(
        "Choose the columns you want in your Summary sheet:",
        options=all_columns,
        default=[c for c in all_columns if c.lower() in ["transaction_date", "registration_num", "ticket", "location", "product_or_article", "quantity", "amount_incl_tax"]]
    )

    st.subheader("📄 Report Settings")
    output_name = st.text_input("Enter output filename (without extension)", "fuel_summary_report")

    if st.button("🚀 Generate Report"):
        if not selected_columns:
            st.warning("Please select at least one column to include.")
        else:
            with st.spinner("Processing file..."):
                # Reset file pointer to beginning before reading again
                uploaded_file.seek(0)
                with tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx") as tmp_in:
                    tmp_in.write(uploaded_file.read())
                    tmp_in_path = tmp_in.name

                # Pass selected columns and generate report
                from get_fuel_summary import generate_custom_fuel_summary
                output_file_path = generate_custom_fuel_summary(tmp_in_path, selected_columns, output_name)

            st.success("✅ Report generated successfully!")
            with open(output_file_path, "rb") as f:
                st.download_button(
                    label="⬇️ Download Custom Report",
                    data=f,
                    file_name=os.path.basename(output_file_path),
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )


