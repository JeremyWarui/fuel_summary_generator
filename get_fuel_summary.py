import os
import pandas as pd

def generate_custom_fuel_summary(input_file, selected_columns, output_name="fuel_summary"):
    """
    Generate a fuel report using user-selected columns.
    """
    data_file = pd.read_excel(input_file)

    # Clean and prepare known columns if they exist
    if "Transaction_date" in data_file.columns:
        data_file["Transaction_date"] = pd.to_datetime(
            data_file["Transaction_date"], format="%d/%m/%Y", errors="coerce"
        ).dt.date

    if "Quantity" in data_file.columns:
        data_file["Quantity"] = (
            data_file["Quantity"]
            .astype(str)
            .str.replace(",", ".")
            .str.replace("\xa0", "")
        )
        data_file["Quantity"] = pd.to_numeric(data_file["Quantity"], errors="coerce")

    if "Location" in data_file.columns:
        data_file["Location"] = data_file["Location"].astype(str).str.title()

    # Select only user-requested columns (if they exist)
    data_selected = data_file[selected_columns]

    # Try to create grouped summary if possible
    group_cols = [col for col in ["Registration_num", "Product_or_Article"] if col in data_file.columns]
    if group_cols:
        grouped_data = data_file.groupby(group_cols).agg({
            col: "sum" for col in data_file.columns if col in ["Quantity", "Amount_incl_Tax"]
        }).reset_index()
    else:
        grouped_data = pd.DataFrame()

    output_file = f"{output_name}.xlsx"

    # Write both sheets
    with pd.ExcelWriter(output_file) as writer:
        data_selected.to_excel(writer, sheet_name="Summary", index=False)
        if not grouped_data.empty:
            grouped_data.to_excel(writer, sheet_name="Totals", index=False)

    return output_file

# # get_summary.py
# import os
# import pandas as pd

# def generate_fuel_summary(input_file):
#     """
#     Generates a summary of the fuel details from the input Excel file.
#     Returns the output file path.
#     """
#     if not input_file.endswith('.xlsx'):
#         raise ValueError("Invalid file format. Please provide an Excel (.xlsx) file")

#     formatted_name = os.path.splitext(os.path.basename(input_file))[0]
#     output_file = f"{formatted_name}_summary.xlsx"

#     data_file = pd.read_excel(input_file)

#     # Ensure 'Transaction_date' is read as a date column
#     data_file['Transaction_date'] = pd.to_datetime(
#         data_file['Transaction_date'], format='%d/%m/%Y', errors='coerce'
#     ).dt.date

#     # Handle comma as decimal separator
#     data_file['Quantity'] = data_file['Quantity'].astype(str).str.replace(',', '.').str.replace('\xa0', '').astype(float)

#     # Capitalize location names
#     data_file['Location'] = data_file['Location'].astype(str).str.title()

#     selected_cols = [
#         'Transaction_date', 'Registration_num', 'Ticket',
#         'Location', 'Product_or_Article', 'Quantity', 'Amount_incl_Tax'
#     ]
#     data_selected = data_file[selected_cols]

#     # Group by vehicle & product
#     grouped_data = data_file.groupby(['Registration_num', 'Product_or_Article']).agg({
#         'Quantity': 'sum',
#         'Amount_incl_Tax': 'sum'
#     }).reset_index()

#     # Write both sheets
#     with pd.ExcelWriter(output_file) as writer:
#         data_selected.to_excel(writer, sheet_name='Summary', index=False)
#         grouped_data.to_excel(writer, sheet_name='Totals', index=False)

#     return output_file
