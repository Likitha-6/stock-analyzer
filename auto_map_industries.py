#!/usr/bin/env python3
"""
AUTOMATIC INDUSTRY & SECTOR MAPPING
Fetches industry/sector from Yahoo Finance and maps to standardized categories
Run: python3 auto_map_industries.py
"""

import sqlite3
import pandas as pd
import yfinance as yf
from typing import Tuple, Optional
import time

# Mapping from Yahoo Finance industries to NSE standardized sectors
YAHOO_TO_SECTOR_MAP = {
    # Consumer Discretionary
    "Automotive": "Consumer Discretionary",
    "Automotive Retail": "Consumer Discretionary",
    "Auto Manufacturers": "Consumer Discretionary",
    "Auto Parts": "Consumer Discretionary",
    "Retailers": "Consumer Discretionary",
    "Department Stores": "Consumer Discretionary",
    "Specialty Retail": "Consumer Discretionary",
    "Apparel Manufacturing": "Consumer Discretionary",
    "Footwear & Accessories": "Consumer Discretionary",
    "Home Furnishings": "Consumer Discretionary",
    "Housewares": "Consumer Discretionary",
    "Leisure": "Consumer Discretionary",
    "Restaurants": "Consumer Discretionary",
    "Hotels": "Consumer Discretionary",
    "Gambling": "Consumer Discretionary",
    "Publishing": "Consumer Discretionary",
    "Media": "Consumer Discretionary",
    "Entertainment": "Consumer Discretionary",
    
    # Consumer Staples
    "Grocery Stores": "Fast Moving consumer goods",
    "Food Distribution": "Fast Moving consumer goods",
    "Packaged Foods": "Fast Moving consumer goods",
    "Beverages": "Fast Moving consumer goods",
    "Beverages - Brewers": "Fast Moving consumer goods",
    "Tobacco": "Fast Moving consumer goods",
    "Household Products": "Fast Moving consumer goods",
    "Personal Services": "Fast Moving consumer goods",
    "Cosmetics": "Fast Moving consumer goods",
    "Agriculture": "Fast Moving consumer goods",
    "Farm Products": "Fast Moving consumer goods",
    
    # Energy
    "Oil & Gas": "Energy",
    "Oil & Gas E&P": "Energy",
    "Oil & Gas Equipment & Services": "Energy",
    "Oil & Gas Pipelines": "Energy",
    "Oil & Gas Refining & Marketing": "Energy",
    "Oil & Gas Storage & Transportation": "Energy",
    "Coal": "Energy",
    "Utilities": "Utilities",
    "Electric Utilities": "Utilities",
    "Power Generation": "Energy",
    
    # Financials
    "Banks": "Services",
    "Banks - Regional": "Services",
    "Banks - Diversified": "Services",
    "Asset Management": "Services",
    "Credit Services": "Services",
    "Financial Conglomerates": "Services",
    "Capital Markets": "Services",
    "Insurance": "Services",
    "Insurance - Diversified": "Services",
    "Insurance - Specialty": "Services",
    "Insurance - Property & Casualty": "Services",
    "Insurance - Life": "Services",
    "Insurance Brokers": "Services",
    "Real Estate": "Consumer Discretionary",
    "Real Estate Investment Trusts": "Consumer Discretionary",
    "Real Estate Services": "Consumer Discretionary",
    
    # Healthcare
    "Healthcare": "Healthcare",
    "Biotech": "Healthcare",
    "Drug Manufacturers": "Healthcare",
    "Drug Manufacturers - Major": "Healthcare",
    "Drug Manufacturers - Specialty & Generic": "Healthcare",
    "Drug Manufacturers - General": "Healthcare",
    "Healthcare Plans": "Healthcare",
    "Medical Care Facilities": "Healthcare",
    "Diagnostic Substances": "Healthcare",
    "Medical Devices": "Healthcare",
    "Medical Instruments & Supplies": "Healthcare",
    "Surgical Instruments & Supplies": "Healthcare",
    "Veterinary Services": "Healthcare",
    
    # Industrials
    "Aerospace & Defense": "Industrials",
    "Aerospace & Defense Products & Services": "Industrials",
    "Building Products & Equipment": "Industrials",
    "Conglomerates": "Industrials",
    "Construction & Engineering": "Industrials",
    "Electrical Equipment & Parts": "Industrials",
    "Industrial Distribution": "Industrials",
    "Machinery": "Industrials",
    "Metals & Mining": "Commodities",
    "Diversified Metals & Mining": "Commodities",
    "Copper": "Commodities",
    "Gold": "Commodities",
    "Precious Metals & Minerals": "Commodities",
    "Steel": "Commodities",
    "Specialty Industrial Machinery": "Industrials",
    "Textiles": "Industrials",
    "Waste Management": "Industrials",
    "Transportation": "Industrials",
    "Railroads": "Industrials",
    "Shipping": "Industrials",
    "Airlines": "Services",
    "Trucking": "Industrials",
    "Delivery Services": "Services",
    
    # Information Technology
    "Software": "Information Technology",
    "Software - Application": "Information Technology",
    "Software - Infrastructure": "Information Technology",
    "Hardware": "Information Technology",
    "Computer Peripherals": "Information Technology",
    "Semiconductors": "Information Technology",
    "Semiconductor Equipment & Materials": "Information Technology",
    "IT Services": "Information Technology",
    "Consulting Services": "Information Technology",
    "Internet": "Information Technology",
    "Internet Retail": "Consumer Discretionary",
    "Computer & Technology": "Information Technology",
    "Data Processing & Outsourced Services": "Information Technology",
    
    # Materials / Commodities
    "Chemicals": "Commodities",
    "Commodity Chemicals": "Commodities",
    "Specialty Chemicals": "Commodities",
    "Fertilizers & Agrochemicals": "Commodities",
    "Forest Products": "Commodities",
    "Paper & Paper Products": "Commodities",
    "Containers & Packaging": "Commodities",
    "Pollution & Treatment Controls": "Commodities",
    
    # Telecommunication
    "Telecom": "Telecommunication",
    "Telecom Services": "Telecommunication",
    "Telecom Equipment": "Telecommunication",
}

# Industry mapping rules based on company name keywords
COMPANY_NAME_INDUSTRY_MAP = {
    "Bank": "Banks - Regional",
    "Insurance": "Insurance",
    "Pharma": "Pharmaceuticals & Biotechnology",
    "Biotech": "Pharmaceuticals & Biotechnology",
    "Hospital": "Healthcare Services",
    "Clinic": "Healthcare Services",
    "Software": "IT - Software",
    "Hardware": "IT - Hardware",
    "Telecom": "Telecom - Equipment & Accessories",
    "Textile": "Textiles, Apparels & Accessories",
    "Apparel": "Textiles, Apparels & Accessories",
    "Auto": "Automobile & Auto Components",
    "Motors": "Automobile & Auto Components",
    "Vehicles": "Automobile & Auto Components",
    "Retail": "Retailing",
    "Store": "Retailing",
    "Hotel": "Leisure Services",
    "Restaurant": "Leisure Services",
    "Construction": "Construction",
    "Steel": "Ferrous Metals",
    "Metal": "Ferrous Metals",
    "Mining": "Minerals & Mining",
    "Chemical": "Chemicals & Petrochemicals",
    "Fertilizer": "Fertilizers & Agrochemicals",
    "Food": "Food Products",
    "Beverage": "Food Products",
    "FMCG": "Fast Moving consumer goods",
    "FMCG Limited": "Fast Moving consumer goods",
    "Energy": "Energy",
    "Power": "Utilities",
    "Utility": "Utilities",
    "Real": "Realty",
    "Real Estate": "Realty",
    "Property": "Realty",
    "Infrastructure": "Construction",
    "Logistics": "Delivery Services",
    "Shipping": "Delivery Services",
    "Transport": "Delivery Services",
    "Finance": "Capital Markets",
    "Investment": "Capital Markets",
    "Consulting": "IT - Services",
    "Services": "IT - Services",
    "Technology": "IT - Services",
}

def get_yahoo_industry(symbol: str) -> Tuple[Optional[str], Optional[str]]:
    """Fetch industry and sector from Yahoo Finance"""
    try:
        ticker = yf.Ticker(f"{symbol}.NS")
        info = ticker.info
        
        yahoo_industry = info.get('industry')
        yahoo_sector = info.get('sector')
        
        return yahoo_industry, yahoo_sector
    except Exception as e:
        print(f"  ⚠️  Error fetching {symbol} from Yahoo: {str(e)[:50]}")
        return None, None

def map_to_standardized_industry(yahoo_industry: str, company_name: str) -> str:
    """Map Yahoo industry to NSE standardized industry"""
    
    if not yahoo_industry:
        # Use company name keywords as fallback
        company_name_upper = company_name.upper()
        for keyword, industry in COMPANY_NAME_INDUSTRY_MAP.items():
            if keyword.upper() in company_name_upper:
                return industry
        return "IT - Services"  # Default fallback
    
    return yahoo_industry

def map_to_standardized_sector(yahoo_industry: str, yahoo_sector: str) -> str:
    """Map Yahoo industry to NSE standardized sector"""
    
    # Try to map from yahoo_industry
    if yahoo_industry and yahoo_industry in YAHOO_TO_SECTOR_MAP:
        return YAHOO_TO_SECTOR_MAP[yahoo_industry]
    
    # Try to map from yahoo_sector
    if yahoo_sector and yahoo_sector in YAHOO_TO_SECTOR_MAP:
        return YAHOO_TO_SECTOR_MAP[yahoo_sector]
    
    # Fallback based on industry keywords
    if yahoo_industry:
        for keyword, sector in YAHOO_TO_SECTOR_MAP.items():
            if keyword.lower() in yahoo_industry.lower():
                return sector
    
    # Default fallback
    return "Services"

def auto_map_industries():
    """Automatically map industries and sectors using Yahoo Finance"""
    
    print("\n" + "="*90)
    print("AUTOMATIC INDUSTRY & SECTOR MAPPING")
    print("="*90)
    
    conn = sqlite3.connect('nse.db')
    cursor = conn.cursor()
    
    # Get all stocks with NULL industry or sector
    query = """
        SELECT Symbol, CompanyName, Industry, `Big Sectors`
        FROM DimCompany 
        WHERE Industry IS NULL OR `Big Sectors` IS NULL
        ORDER BY Symbol
    """
    
    missing = pd.read_sql(query, conn)
    
    print(f"\nFound {len(missing)} stocks with missing mappings")
    print("Starting automatic mapping from Yahoo Finance...\n")
    
    updated_count = 0
    skipped_count = 0
    
    for idx, row in missing.iterrows():
        symbol = row['Symbol']
        company_name = row['CompanyName']
        current_industry = row['Industry']
        current_sector = row['Big Sectors']
        
        print(f"[{idx+1}/{len(missing)}] {symbol}: {company_name[:40]}", end=" ... ")
        
        # Fetch from Yahoo Finance
        yahoo_industry, yahoo_sector = get_yahoo_industry(symbol)
        
        if not yahoo_industry and not yahoo_sector:
            print("⏭️  Skipped (no data from Yahoo)")
            skipped_count += 1
            continue
        
        # Map to standardized values
        mapped_industry = map_to_standardized_industry(yahoo_industry, company_name)
        mapped_sector = map_to_standardized_sector(yahoo_industry, yahoo_sector)
        
        # Update database
        try:
            cursor.execute("""
                UPDATE DimCompany 
                SET Industry = ?, `Big Sectors` = ?
                WHERE Symbol = ?
            """, (mapped_industry, mapped_sector, symbol))
            
            conn.commit()
            print(f"✅ {mapped_industry} / {mapped_sector}")
            updated_count += 1
            
        except Exception as e:
            print(f"❌ Error updating: {str(e)[:30]}")
            skipped_count += 1
        
        # Rate limit to avoid hitting Yahoo limits
        time.sleep(0.5)
    
    conn.close()
    
    print("\n" + "="*90)
    print(f"MAPPING COMPLETE")
    print("="*90)
    print(f"Updated: {updated_count} stocks")
    print(f"Skipped: {skipped_count} stocks")
    print(f"Total:   {updated_count + skipped_count} stocks processed")
    print("="*90 + "\n")

if __name__ == "__main__":
    auto_map_industries()
