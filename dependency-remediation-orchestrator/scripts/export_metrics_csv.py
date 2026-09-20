import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import sqlite3
import csv
from pathlib import Path

def export_to_csv():
    """Export job metrics to CSV for Superset import"""
    db_path = Path(__file__).parent / "jobs.db"
    csv_path = Path(__file__).parent / "job_metrics.csv"
    
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    # Get column names
    cursor.execute("SELECT * FROM vw_job_metrics LIMIT 1")
    columns = [description[0] for description in cursor.description]
    
    # Export to CSV
    cursor.execute("SELECT * FROM vw_job_metrics")
    rows = cursor.fetchall()
    
    with open(csv_path, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(columns)
        writer.writerows(rows)
    
    conn.close()
    
    print(f"✅ Exported {len(rows)} rows to {csv_path}")
    print(f"📊 Columns: {', '.join(columns)}")
    print(f"\n📥 Import into Superset:")
    print(f"   1. Go to Datasets → + Dataset")
    print(f"   2. Select 'Upload a CSV'")
    print(f"   3. Upload: {csv_path}")
    print(f"   4. Name: 'Job Metrics'")

if __name__ == "__main__":
    export_to_csv()