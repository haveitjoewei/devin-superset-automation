import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

"""
Superset Dashboard Setup Script

This script helps set up the Devin Remediation dashboard in Superset.
It creates the database connection and provides instructions for manual dashboard creation.
"""

import sqlite3
import os
from pathlib import Path

def verify_metrics_view():
    """Verify the metrics view exists in the database"""
    db_path = Path(__file__).parent / "jobs.db"
    
    if not db_path.exists():
        print(f"❌ Database not found at {db_path}")
        return False
    
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    try:
        cursor.execute("SELECT name FROM sqlite_master WHERE type='view' AND name='vw_job_metrics'")
        view_exists = cursor.fetchone()
        
        if view_exists:
            print("✅ Metrics view vw_job_metrics exists")
            
            # Show sample data
            cursor.execute("SELECT * FROM vw_job_metrics LIMIT 3")
            columns = [description[0] for description in cursor.description]
            rows = cursor.fetchall()
            
            print("\n📊 Sample data from vw_job_metrics:")
            print("Columns:", ", ".join(columns))
            for row in rows:
                print(f"  {row}")
            
            return True
        else:
            print("❌ Metrics view vw_job_metrics not found")
            return False
    finally:
        conn.close()

def setup_instructions():
    """Print setup instructions for Superset"""
    print("\n" + "="*60)
    print("SUPERSET DASHBOARD SETUP INSTRUCTIONS")
    print("="*60)
    
    db_path = Path(__file__).parent / "jobs.db"
    abs_db_path = db_path.absolute()
    
    print(f"\n1. DATABASE CONNECTION")
    print(f"   Database file: {abs_db_path}")
    print(f"   Connection string: sqlite:///{abs_db_path}")
    
    print("\n2. STEPS IN SUPERSET:")
    print("   a. Go to Settings → Database Connections")
    print("   b. Click '+ Database'")
    print("   c. Select 'SQLite'")
    print(f"   d. Enter: sqlite:///{abs_db_path}")
    print("   e. Name: 'Devin Jobs'")
    print("   f. Test connection and save")
    
    print("\n3. CREATE DATASET:")
    print("   a. Go to Datasets")
    print("   b. Click '+ Dataset'")
    print("   c. Select 'Devin Jobs' database")
    print("   d. Select 'vw_job_metrics' as the table")
    print("   e. Name: 'Job Metrics'")
    print("   f. Save")
    
    print("\n4. CREATE DASHBOARD:")
    print("   Dashboard Name: 'Devin Auto-Fix — Effectiveness'")
    print("   Charts to create:")
    print("   - Big Number: Success Rate")
    print("   - Big Number: Throughput (this week)")
    print("   - Big Number: Dev Hours Saved")
    print("   - Big Number: Net $ Saved")
    print("   - Big Number: MTTR (hours)")
    print("   - Time Series: Validated PRs per day")
    print("   - Bar Chart: Tasks by state")
    print("   - Bar Chart: Dev hours saved by stream")
    print("   - Table: Recent jobs")
    
    print("\n5. EXPORT DASHBOARD:")
    print("   a. Go to Dashboard → ... → Export")
    print("   b. Save as: dashboards/superset_export.zip")
    print("   c. Import on startup: superset import-dashboards -p dashboards/superset_export.zip")
    
    print("\n6. METRIC DEFINITIONS:")
    print("   - success_rate = validated / (validated + failed)")
    print("   - throughput = count(validated) per day/week")
    print("   - dev_hours_saved = Σ effort_hours where state = validated")
    print("   - devin_cost = Σ cost")
    print("   - net_saved = dev_hours_saved × $90 - devin_cost")
    print("   - mttr_hours = avg(validated_at - labeled_at)")
    print("   - state_breakdown = count grouped by state")
    
    print("\n" + "="*60)

if __name__ == "__main__":
    print("🔍 Verifying database setup...")
    if verify_metrics_view():
        setup_instructions()
    else:
        print("\n⚠️  Please start the orchestrator API to create the metrics view first:")
        print("   python3.12 -m uvicorn api:app --host 0.0.0.0 --port 8000")