import sqlite3
import csv
from pathlib import Path

def import_quotes():
    # Paths
    db_path = Path(__file__).parent / "quote_bot.db"
    csv_path = Path(__file__).parent / "quotes.csv"
    
    print(f"Database path: {db_path}")
    print(f"CSV path: {csv_path}")
    
    # Check if files exist
    if not csv_path.exists():
        print(f"Error: {csv_path} not found!")
        return
        
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Drop existing table if it exists
        cursor.execute("DROP TABLE IF EXISTS quotes")
        
        # Create the quotes table with the new schema
        cursor.execute('''
        CREATE TABLE quotes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            quote TEXT NOT NULL,
            author TEXT,
            topic TEXT,
            tone TEXT,
            takeaway TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        # Read and insert quotes from CSV
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                cursor.execute('''
                INSERT INTO quotes (quote, author, topic, tone, takeaway)
                VALUES (?, ?, ?, ?, ?)
                ''', (
                    row['quote'],
                    row['author'],
                    row['topic'],
                    row['tone'],
                    row['takeaway']
                ))
        
        conn.commit()
        count = cursor.execute("SELECT COUNT(*) FROM quotes").fetchone()[0]
        print(f"✅ Successfully imported {count} quotes!")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    print("Starting quote import...")
    import_quotes()