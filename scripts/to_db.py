import pandas as pd
import psycopg2
from sqlalchemy import create_engine, text

# Database connection parameters
DB_USER = 'postgres'
DB_PASSWORD = 'postgres'
DB_HOST = 'localhost'
DB_PORT = '5432'
DB_NAME = 'card_database'

# Read the CSV file
df = pd.read_csv('all_opc.csv')

# Clean data
df = df.apply(lambda x: x.str.strip() if x.dtype == "object" else x)

# Convert price columns to float
price_columns = ['TCG Market Price', 'TCG Direct Low', 'TCG Low Price With Shipping', 'TCG Low Price']
for col in price_columns:
    df[col] = pd.to_numeric(df[col], errors='coerce')

# Convert quantity columns to integer
quantity_columns = ['Total Quantity', 'Add to Quantity']
for col in quantity_columns:
    df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0).astype(int)

# Create SQLAlchemy engine
engine = create_engine(f'postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}')

# Create table and insert data
table_name = 'one_piece_cards'
df.to_sql(table_name, engine, if_exists='replace', index=False)

# Verify data insertion using the correct SQLAlchemy 2.0 pattern
with engine.connect() as conn:
    result = conn.execute(text(f"SELECT COUNT(*) FROM {table_name}"))
    count = result.scalar()
    print(f"Successfully imported {count} records to PostgreSQL table '{table_name}'")
    
    # Execute the UPDATE statement
    conn.execute(text('UPDATE one_piece_cards SET "TCG Marketplace Price" = 1'))
    conn.commit()
    print("\nUpdated TCG Marketplace Price to 1 for all records")

     # Show first few rows
    result = conn.execute(text(f"SELECT * FROM {table_name} LIMIT 5"))
    rows = result.fetchall()
    print("\nFirst 5 rows in database:")
    for row in rows:
        print(row)