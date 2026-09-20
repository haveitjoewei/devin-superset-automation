from database import SessionLocal, init_db
from sqlalchemy import text

def migrate_database():
    """Add new columns to jobs table for observability"""
    init_db()
    
    with SessionLocal() as session:
        # Add new columns if they don't exist
        try:
            session.execute(text("ALTER TABLE jobs ADD COLUMN effort_hours FLOAT DEFAULT 0.0"))
            print("Added effort_hours column")
        except Exception as e:
            print(f"effort_hours column might already exist: {e}")
        
        try:
            session.execute(text("ALTER TABLE jobs ADD COLUMN validated_at DATETIME"))
            print("Added validated_at column")
        except Exception as e:
            print(f"validated_at column might already exist: {e}")
        
        try:
            session.execute(text("ALTER TABLE jobs ADD COLUMN labeled_at DATETIME"))
            print("Added labeled_at column")
        except Exception as e:
            print(f"labeled_at column might already exist: {e}")
        
        try:
            session.execute(text("ALTER TABLE jobs ADD COLUMN slack_thread_ts TEXT"))
            print("Added slack_thread_ts column")
        except Exception as e:
            print(f"slack_thread_ts column might already exist: {e}")
        
        session.commit()
        print("Database migration completed")

if __name__ == "__main__":
    migrate_database()