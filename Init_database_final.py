#!/usr/bin/env python3
import sqlite3
import pandas as pd
import sys

conn = sqlite3.connect('nse.db')
cursor = conn.cursor()

# Drop old table
cursor.execute("DROP TABLE IF EXISTS DimCompany")

# Create new table
cursor.execute("""
    CREATE TABLE DimCompany (
        Symbol TEXT PRIMARY KEY,
        CompanyName TEXT,
        Industry TEXT,
        Big_Sectors TEXT,
        PE_Ratio REAL,
        EPS REAL,
        ROE REAL,
        ProfitMargin REAL,
        DebtToEquity REAL,
        MarketCap REAL,
        Description TEXT
    )
""")

# Load stocks
stocks_df = pd.read_csv('data/nse_stocks_.csv')
print(f"Loading {len(stocks_df)} stocks...")

success = 0
for idx, row in stocks_df.iterrows():
    if (idx + 1) % 500 == 0:
        print(f"  [{idx + 1}/{len(stocks_df)}]")
    
    symbol = row['Symbol']
    company_name = row.get('Company Name', row.get('NAME OF COMPANY', symbol))
    industry = row.get('Industry', 'N/A')
    sector = row.get('Big Sectors', 'N/A')
    
    try:
        cursor.execute("""
            INSERT INTO DimCompany (Symbol, CompanyName, Industry, Big_Sectors)
            VALUES (?, ?, ?, ?)
        """, (symbol, company_name, industry, sector))
        success += 1
    except Exception as e:
        pass

conn.commit()
conn.close()

print(f"\n✅ Created nse.db with {success} stocks!")
print("Upload this nse.db to GitHub")
