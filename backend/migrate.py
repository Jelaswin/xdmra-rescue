import sqlite3
import os
from app.database import engine, Base
from app.models import *

def migrate():
    print("Creating new tables...")
    Base.metadata.create_all(bind=engine)
    
    db_path = 'xdmra.db'
    if not os.path.exists(db_path):
        print(f"DB {db_path} does not exist. Created new.")
        return
        
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("Altering allocations...")
    new_cols = [
        "superseded_by_allocation_id INTEGER",
        "supersedes_allocation_id INTEGER",
        "ended_at DATETIME",
        "termination_reason VARCHAR",
        "reallocation_reason VARCHAR",
        "approved_by VARCHAR"
    ]
    for col in new_cols:
        try:
            cursor.execute(f"ALTER TABLE allocations ADD COLUMN {col}")
        except Exception as e:
            print(f"Column {col.split()[0]} might already exist: {e}")
            
    print("Recreating route_conditions...")
    try:
        cursor.execute("DROP TABLE route_conditions")
    except Exception as e:
        print("Failed to drop route_conditions:", e)
        
    conn.commit()
    conn.close()
    
    Base.metadata.create_all(bind=engine)
    print("Migration finished successfully.")

if __name__ == '__main__':
    migrate()
