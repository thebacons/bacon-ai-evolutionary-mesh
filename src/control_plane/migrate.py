import sqlite3
import os

# Database Path
DB_PATH = "bacon.db"

def migrate():
    if not os.path.exists(DB_PATH):
        print(f"❌ Database {DB_PATH} not found.")
        return

    print(f"🛠️ Migrating database {DB_PATH}...")
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Add parent_id to agent table if it doesn't exist
        cursor.execute("PRAGMA table_info(agent)")
        columns = [row[1] for row in cursor.fetchall()]
        
        if "parent_id" not in columns:
            print("➕ Adding 'parent_id' column to 'agent' table...")
            cursor.execute("ALTER TABLE agent ADD COLUMN parent_id TEXT")
            conn.commit()
            print("✅ Migration successful!")
        else:
            print("ℹ️ 'parent_id' column already exists.")
            
        conn.close()
    except Exception as e:
        print(f"❌ Migration failed: {e}")

if __name__ == "__main__":
    migrate()
