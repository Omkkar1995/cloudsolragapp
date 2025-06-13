import pandas as pd
import pyodbc

# Load Excel file
df = pd.read_excel("users.xlsx")

# SQL Server connection details
server = 'ragapp-server.database.windows.net'
database = 'ragapp-users'
username = 'ragapp-cloudsol2'
password = 'Pasona!224026'

# Connection string
conn_str = (
    f'DRIVER={{ODBC Driver 18 for SQL Server}};'
    f'SERVER={server};DATABASE={database};UID={username};PWD={password}'
)

# Connect to SQL DB
conn = pyodbc.connect(conn_str)
cursor = conn.cursor()

# Create table if not exists (optional)
cursor.execute("""
IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='Users' AND xtype='U')
CREATE TABLE Users (
    Id INT PRIMARY KEY IDENTITY(1,1),
    Username NVARCHAR(100) NOT NULL,
    Password NVARCHAR(100) NOT NULL
)
""")
conn.commit()

# Insert rows
for index, row in df.iterrows():
    cursor.execute(
        "INSERT INTO Users (Username, Password) VALUES (?, ?)",
        row['username'], row['password']
    )

conn.commit()
cursor.close()
conn.close()

print("✅ Excel data migrated to Azure SQL DB.")
