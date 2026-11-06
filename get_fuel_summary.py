import os
import pandas as pd
from openpyxl.formatting.rule import FormulaRule
from openpyxl.styles import Font, PatternFill
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.datavalidation import DataValidation
from openpyxl.worksheet.table import Table, TableStyleInfo

RECEIPT_STATUS_COLUMN = "Receipt_Status"
RECEIPT_STATUS_OPTIONS = ("Missing", "Okay")
TABLE_STYLE = "TableStyleMedium2"
NUMBER_COLUMNS = ("Quantity", "Amount_incl_Tax")
NUMBER_FORMAT = "#,##0.00"


def style_as_table(worksheet, dataframe, table_name):
    """Format a sheet written from dataframe as a blue banded Excel table with fitted columns."""
    last_col = get_column_letter(len(dataframe.columns))
    # An Excel table needs at least one body row, even an empty one.
    last_row = max(len(dataframe) + 1, 2)
    table = Table(displayName=table_name, ref=f"A1:{last_col}{last_row}")
    table.tableStyleInfo = TableStyleInfo(
        name=TABLE_STYLE, showRowStripes=True, showColumnStripes=False
    )
    worksheet.add_table(table)

    # pandas styles headers itself; clearing that lets the table style colour them.
    for cell in worksheet[1]:
        cell.style = "Normal"

    for index, column in enumerate(dataframe.columns, start=1):
        letter = get_column_letter(index)
        if column in NUMBER_COLUMNS:
            for (cell,) in worksheet.iter_rows(
                min_row=2, max_row=last_row, min_col=index, max_col=index
            ):
                cell.number_format = NUMBER_FORMAT
        longest = max(
            [len(str(column))]
            + [len(f"{v:,.2f}" if column in NUMBER_COLUMNS and isinstance(v, (int, float)) else str(v))
               for v in dataframe[column].dropna()]
        )
        # Extra room for the header's filter arrow.
        worksheet.column_dimensions[letter].width = longest + 4


def add_receipt_status_dropdown(worksheet, column_index, row_count):
    """Restrict a column's data cells to a Missing/Okay dropdown and colour the choices.

    column_index is 1-based. Blank cells stay allowed so unchecked receipts can stay empty.
    """
    letter = get_column_letter(column_index)
    last_row = max(row_count + 1, 2)
    cell_range = f"{letter}2:{letter}{last_row}"

    validation = DataValidation(
        type="list",
        formula1='"' + ",".join(RECEIPT_STATUS_OPTIONS) + '"',
        allow_blank=True,
        showDropDown=False,
        showErrorMessage=True,
        errorTitle="Invalid receipt status",
        error="Choose Missing or Okay from the list.",
        showInputMessage=True,
        promptTitle="Receipt status",
        prompt="Is the receipt present? Choose Missing or Okay.",
    )
    validation.add(cell_range)
    worksheet.add_data_validation(validation)

    styles = {
        "Missing": ("FFC7CE", "9C0006"),
        "Okay": ("C6EFCE", "006100"),
    }
    for value, (fill, font) in styles.items():
        worksheet.conditional_formatting.add(
            cell_range,
            FormulaRule(
                formula=[f'${letter}2="{value}"'],
                fill=PatternFill(start_color=fill, end_color=fill, fill_type="solid"),
                font=Font(color=font),
            ),
        )

    worksheet.column_dimensions[letter].width = max(len(RECEIPT_STATUS_COLUMN) + 2, 16)


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
    data_selected = data_file[selected_columns].copy()
    data_selected[RECEIPT_STATUS_COLUMN] = ""

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
    with pd.ExcelWriter(output_file, engine="openpyxl") as writer:
        data_selected.to_excel(writer, sheet_name="Summary", index=False)
        style_as_table(writer.sheets["Summary"], data_selected, "Transactions")
        add_receipt_status_dropdown(
            writer.sheets["Summary"],
            column_index=data_selected.columns.get_loc(RECEIPT_STATUS_COLUMN) + 1,
            row_count=len(data_selected),
        )
        if not grouped_data.empty:
            grouped_data.to_excel(writer, sheet_name="Totals", index=False)
            style_as_table(writer.sheets["Totals"], grouped_data, "VehicleTotals")

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
