import sqlite3
import psycopg2
from pathlib import Path

def migrate_to_postgres():
    """Migrate SQLite data to PostgreSQL"""
    sqlite_path = Path(__file__).resolve().parents[1] / "jobs.db"
    
    # Connect to SQLite
    sqlite_conn = sqlite3.connect(str(sqlite_path))
    sqlite_conn.row_factory = sqlite3.Row
    sqlite_cursor = sqlite_conn.cursor()
    
    # Connect to PostgreSQL
    pg_conn = psycopg2.connect(
        host="localhost",
        port=5432,
        database="postgres",
        user="josephwei"
    )
    pg_conn.autocommit = True
    pg_cursor = pg_conn.cursor()
    
    # Create database
    try:
        pg_cursor.execute("CREATE DATABASE devin_jobs")
        print("✅ Created devin_jobs database")
    except psycopg2.errors.DuplicateDatabase:
        print("ℹ️  Database devin_jobs already exists")
    
    pg_conn.close()
    
    # Connect to the new database
    pg_conn = psycopg2.connect(
        host="localhost",
        port=5432,
        database="devin_jobs",
        user="josephwei"
    )
    pg_conn.autocommit = True
    pg_cursor = pg_conn.cursor()
    
    # Create table
    create_table_sql = """
    CREATE TABLE IF NOT EXISTS jobs (
        id SERIAL PRIMARY KEY,
        issue_number INTEGER NOT NULL,
        issue_url TEXT,
        devin_session_id TEXT,
        pr_number INTEGER,
        state TEXT NOT NULL DEFAULT 'queued',
        attempts INTEGER NOT NULL DEFAULT 0,
        created_at TIMESTAMP NOT NULL,
        updated_at TIMESTAMP NOT NULL,
        cost FLOAT NOT NULL DEFAULT 0.0,
        notes TEXT,
        effort_hours FLOAT NOT NULL DEFAULT 0.0,
        validated_at TIMESTAMP,
        labeled_at TIMESTAMP,
        slack_thread_ts TEXT
    );
    """
    pg_cursor.execute(create_table_sql)
    print("✅ Created jobs table")
    
    # Create metrics view
    create_view_sql = """
    CREATE OR REPLACE VIEW vw_job_metrics AS
    SELECT 
        id,
        issue_number,
        issue_url,
        devin_session_id,
        pr_number,
        state,
        attempts,
        created_at,
        updated_at,
        cost,
        effort_hours,
        validated_at,
        labeled_at,
        slack_thread_ts,
        notes,
        CASE 
            WHEN validated_at IS NOT NULL AND labeled_at IS NOT NULL 
            THEN EXTRACT(EPOCH FROM (validated_at - labeled_at)) / 3600
            ELSE NULL 
        END as mttr_hours,
        CASE 
            WHEN notes LIKE '%test%' THEN 'test'
            WHEN notes LIKE '%bug%' THEN 'bug'
            ELSE 'dependency'
        END as stream
    FROM jobs;
    """
    pg_cursor.execute(create_view_sql)
    print("✅ Created vw_job_metrics view")
    
    # Migrate data
    sqlite_cursor.execute("SELECT * FROM jobs")
    rows = sqlite_cursor.fetchall()
    
    for row in rows:
        insert_sql = """
        INSERT INTO jobs (id, issue_number, issue_url, devin_session_id, pr_number, state, 
                         attempts, created_at, updated_at, cost, notes, effort_hours, 
                         validated_at, labeled_at, slack_thread_ts)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (id) DO UPDATE SET
            issue_number = EXCLUDED.issue_number,
            issue_url = EXCLUDED.issue_url,
            devin_session_id = EXCLUDED.devin_session_id,
            pr_number = EXCLUDED.pr_number,
            state = EXCLUDED.state,
            attempts = EXCLUDED.attempts,
            created_at = EXCLUDED.created_at,
            updated_at = EXCLUDED.updated_at,
            cost = EXCLUDED.cost,
            notes = EXCLUDED.notes,
            effort_hours = EXCLUDED.effort_hours,
            validated_at = EXCLUDED.validated_at,
            labeled_at = EXCLUDED.labeled_at,
            slack_thread_ts = EXCLUDED.slack_thread_ts;
        """
        
        pg_cursor.execute(insert_sql, (
            row['id'],
            row['issue_number'],
            row['issue_url'],
            row['devin_session_id'],
            row['pr_number'],
            row['state'],
            row['attempts'],
            row['created_at'],
            row['updated_at'],
            row['cost'],
            row['notes'],
            row['effort_hours'],
            row['validated_at'],
            row['labeled_at'],
            row['slack_thread_ts']
        ))
    
    print(f"✅ Migrated {len(rows)} rows to PostgreSQL")
    
    # Verify migration
    pg_cursor.execute("SELECT COUNT(*) FROM jobs")
    count = pg_cursor.fetchone()[0]
    print(f"📊 Total rows in PostgreSQL: {count}")
    
    sqlite_conn.close()
    pg_conn.close()
    
    print("\n🔗 PostgreSQL connection string for Superset:")
    print("postgresql://josephwei@localhost:5432/devin_jobs")
    print("\n🔗 Connection string for orchestrator config:")
    print("postgresql://josephwei@localhost:5432/devin_jobs")

if __name__ == "__main__":
    migrate_to_postgres()