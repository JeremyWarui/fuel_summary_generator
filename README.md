# fuel_summary_generator
A simple project using StreamLit for the purpose of generating a summary of a fuel report using the suppliers invoice. Uses Excel documents.

## Output workbook

- **Summary**: every transaction, using the columns picked in the app, plus a final `Receipt_Status` column. Each cell in it has a dropdown that only accepts `Missing` or `Okay` (red and green). Cells start blank so you can mark receipts as you check them.
- **Totals**: quantity and amount per vehicle (`Registration_num`) and product (`Product_or_Article`).

## Run

```
pip install -r requirements.txt
streamlit run app.py
```

## Tests

```
pip install -r requirements-dev.txt
python -m pytest
```
