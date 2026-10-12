"""
LandGuard Synthetic Dataset PostgreSQL Loader
Executes database/seed_synthetic_100.sql to load the 100 synthetic test records
and their ownership history into the PostgreSQL 'landguard_db' database.
"""

import os
import sys
import argparse

try:
    import psycopg2
    from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
except ImportError:
    psycopg2 = None


def get_db_params():
    return {
        "host": os.getenv("POSTGRES_HOST", "localhost"),
        "port": int(os.getenv("POSTGRES_PORT", 5432)),
        "user": os.getenv("POSTGRES_USER", "postgres"),
        "password": os.getenv("POSTGRES_PASSWORD", "postgres"),
        "dbname": os.getenv("POSTGRES_DB", "landguard_db"),
    }


def load_synthetic_data(params):
    if not psycopg2:
        print("❌ Error: psycopg2 module is not installed. Run 'pip install psycopg2-binary'")
        sys.exit(1)

    base_dir = os.path.dirname(os.path.abspath(__file__))
    sql_path = os.path.join(base_dir, "seed_synthetic_100.sql")

    if not os.path.exists(sql_path):
        print(f"❌ Seed script not found at {sql_path}")
        sys.exit(1)

    print(f"Connecting to PostgreSQL database '{params['dbname']}' on {params['host']}:{params['port']}...")
    conn = None
    try:
        conn = psycopg2.connect(**params)
        cur = conn.cursor()

        print("Executing seed_synthetic_100.sql inside an atomic transaction...")
        with open(sql_path, "r", encoding="utf-8") as f:
            sql_content = f.read()
            cur.execute(sql_content)
        
        # Commit transaction only after all inserts succeed
        conn.commit()

        # Count records
        cur.execute("SELECT COUNT(*) FROM land_records WHERE record_id LIKE 'SYN-%';")
        syn_land_count = cur.fetchone()[0]

        cur.execute("SELECT COUNT(*) FROM ownership_history WHERE history_id LIKE 'SYN-%';")
        syn_hist_count = cur.fetchone()[0]

        cur.execute("SELECT COUNT(*) FROM land_records;")
        total_land_count = cur.fetchone()[0]

        cur.close()
        conn.close()
        conn = None

        print("✅ Synthetic dataset loaded successfully!")
        print(f"📊 Synthetic Land Records: {syn_land_count} (Total in DB: {total_land_count})")
        print(f"📊 Synthetic Ownership History Records: {syn_hist_count}")

    except Exception as e:
        if conn:
            try:
                conn.rollback()
                conn.close()
                print("🔄 Transaction rolled back: No partial changes were written to the database.")
            except Exception:
                pass
        print(f"❌ Error loading synthetic dataset into PostgreSQL: {e}")
        print("Ensure PostgreSQL is running and credentials are valid.")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="Load LandGuard 100 Synthetic Records into PostgreSQL")
    parser.add_argument("--password", help="PostgreSQL password for user 'postgres'")
    parser.add_argument("-P", "--prompt", action="store_true", help="Prompt securely for password without echoing")
    parser.add_argument("--host", help="PostgreSQL host")
    parser.add_argument("--port", type=int, help="PostgreSQL port")
    parser.add_argument("--dbname", help="PostgreSQL database name")
    args = parser.parse_args()

    params = get_db_params()
    if args.prompt:
        import getpass
        params["password"] = getpass.getpass("Enter PostgreSQL password for user 'postgres': ")
    elif args.password:
        params["password"] = args.password
    if args.host:
        params["host"] = args.host
    if args.port:
        params["port"] = args.port
    if args.dbname:
        params["dbname"] = args.dbname

    load_synthetic_data(params)


if __name__ == "__main__":
    main()
