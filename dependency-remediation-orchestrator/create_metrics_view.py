from database import SessionLocal, init_db
from sqlalchemy import text

def create_metrics_view():
    """Create SQL view for job metrics"""
    init_db()
    
    with SessionLocal() as session:
        # Drop view if exists
        try:
            session.execute(text("DROP VIEW IF EXISTS vw_job_metrics"))
            print("Dropped existing view")
        except Exception as e:
            print(f"No existing view to drop: {e}")
        
        # Create the metrics view
        create_view_sql = """
        CREATE VIEW vw_job_metrics AS
        SELECT 
            id,
            issue_number,
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
            -- Calculate time to remediation in hours
            CASE 
                WHEN validated_at IS NOT NULL AND labeled_at IS NOT NULL 
                THEN (julianday(validated_at) - julianday(labeled_at)) * 24
                ELSE NULL 
            END as mttr_hours,
            -- Stream classification (based on notes or default to dependency)
            CASE 
                WHEN notes LIKE '%test%' THEN 'test'
                WHEN notes LIKE '%bug%' THEN 'bug'
                ELSE 'dependency'
            END as stream
        FROM jobs
        """
        
        session.execute(text(create_view_sql))
        session.commit()
        print("Created vw_job_metrics view")

if __name__ == "__main__":
    create_metrics_view()