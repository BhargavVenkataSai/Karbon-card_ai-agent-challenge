import pdfplumber
import pandas as pd

pdf_path = "data/icici/icic_sample.pdf"
csv_path = "data/icici/icic_sample.csv"

rows = []
with pdfplumber.open(pdf_path) as pdf:
    for page in pdf.pages:
        tables = page.extract_tables()
        for table in tables:
            for row in table:
                # skip completely empty or header rows
                if not row or row[0] == "Date" or "Karbon Bannk" in str(row):
                    continue
                # keep only first 5 columns
                rows.append(row[:5])

df = pd.DataFrame(rows, columns=["Date","Description","Debit Amt","Credit Amt","Balance"])
df.to_csv(csv_path, index=False)
print(f"✅ Wrote {len(df)} rows to {csv_path}")
