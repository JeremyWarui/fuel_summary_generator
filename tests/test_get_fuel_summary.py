import pandas as pd
import pytest
from openpyxl import load_workbook

from get_fuel_summary import (
    RECEIPT_STATUS_COLUMN,
    generate_custom_fuel_summary,
)

SELECTED = [
    "Transaction_date",
    "Registration_num",
    "Ticket",
    "Location",
    "Product_or_Article",
    "Quantity",
    "Amount_incl_Tax",
]


def write_invoice(path, rows):
    pd.DataFrame(
        rows,
        columns=SELECTED + ["Driver"],
    ).to_excel(path, index=False)


@pytest.fixture
def invoice(tmp_path):
    path = tmp_path / "invoice.xlsx"
    write_invoice(
        path,
        [
            ["01/10/2026", "KAA 123A", "T1", "nairobi west", "Diesel", "40,5", 7000, "A"],
            ["02/10/2026", "KAA 123A", "T2", "nakuru", "Diesel", "20", 3500, "A"],
            ["03/10/2026", "KBB 456B", "T3", "mombasa road", "Super", "15,25", 2900, "B"],
        ],
    )
    return path


def build(tmp_path, invoice_path, columns=SELECTED):
    out = generate_custom_fuel_summary(str(invoice_path), columns, str(tmp_path / "report"))
    return load_workbook(out)


def test_receipt_status_is_last_column_of_summary(tmp_path, invoice):
    ws = build(tmp_path, invoice)["Summary"]
    headers = [c.value for c in ws[1]]
    assert headers == SELECTED + [RECEIPT_STATUS_COLUMN]


def test_receipt_status_cells_start_blank(tmp_path, invoice):
    ws = build(tmp_path, invoice)["Summary"]
    assert [ws.cell(row=r, column=8).value for r in range(2, 5)] == [None, None, None]


def test_receipt_status_dropdown_offers_only_missing_and_okay(tmp_path, invoice):
    ws = build(tmp_path, invoice)["Summary"]
    validations = ws.data_validations.dataValidation
    assert len(validations) == 1
    dv = validations[0]
    assert dv.type == "list"
    assert dv.formula1 == '"Missing,Okay"'
    assert dv.showErrorMessage is True
    assert dv.allow_blank is True
    assert str(dv.sqref) == "H2:H4"


def test_dropdown_follows_column_count(tmp_path, invoice):
    ws = build(tmp_path, invoice, ["Registration_num", "Quantity"])["Summary"]
    assert ws["C1"].value == RECEIPT_STATUS_COLUMN
    assert str(ws.data_validations.dataValidation[0].sqref) == "C2:C4"


def test_dropdown_covers_header_only_sheet_when_no_rows(tmp_path):
    path = tmp_path / "empty.xlsx"
    write_invoice(path, [])
    ws = build(tmp_path, path)["Summary"]
    assert ws["H1"].value == RECEIPT_STATUS_COLUMN
    assert str(ws.data_validations.dataValidation[0].sqref) == "H2"


def test_missing_and_okay_are_colour_coded(tmp_path, invoice):
    ws = build(tmp_path, invoice)["Summary"]
    rules = [rule for cf in ws.conditional_formatting for rule in cf.rules]
    formulas = sorted(rule.formula[0] for rule in rules)
    assert formulas == ['$H2="Missing"', '$H2="Okay"']


def test_totals_sheet_has_no_receipt_status(tmp_path, invoice):
    wb = build(tmp_path, invoice)
    ws = wb["Totals"]
    headers = [c.value for c in ws[1]]
    assert RECEIPT_STATUS_COLUMN not in headers
    assert not ws.data_validations.dataValidation
    totals = {
        (row[0], row[1]): row[2]
        for row in ws.iter_rows(min_row=2, values_only=True)
    }
    assert totals[("KAA 123A", "Diesel")] == pytest.approx(60.5)
    assert totals[("KBB 456B", "Super")] == pytest.approx(15.25)
