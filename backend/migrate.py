import os
import shutil
from app.database import engine, Base
from app.models import *

def migrate():
    db_path = 'xdmra.db'
    backup_path = 'xdmra_phase6.db.bak'
    
    if os.path.exists(db_path):
        print(f"Backing up {db_path} to {backup_path}...")
        shutil.copy2(db_path, backup_path)
        
        # In this phase, we are doing a destructive wipe and re-seed 
        # to ensure the complex supply-chain schema is clean.
        print("Dropping existing tables...")
        Base.metadata.drop_all(bind=engine)
        
    print("Creating new tables...")
    Base.metadata.create_all(bind=engine)
    
    print("Migration finished successfully.")
    
    from app.database import SessionLocal
    from app.seed import seed_db
    
    db = SessionLocal()
    try:
        print("Seeding database...")
        seed_db(db)
        print("Seeding complete.")
    finally:
        db.close()

if __name__ == '__main__':
    migrate()
