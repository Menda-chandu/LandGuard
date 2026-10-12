"""
LandGuard Automated Database Initializer & Migration Script
This script creates the PostgreSQL 'landguard_db' database (if not existing),
applies table DDL schemas from schema.sql, and loads initial CSV sample records.
"""

import os
import sys
import csv
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


def create_database_if_not_exists(params):
    if not psycopg2:
        print("❌ Error: psycopg2 module is not installed. Run 'pip install psycopg2-binary'")
        sys.exit(1)

    # Connect to default 'postgres' database to check/create target database
    admin_params = params.copy()
    admin_params["dbname"] = "postgres"

    try:
        conn = psycopg2.connect(**admin_params)
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cur = conn.cursor()

        target_db = params["dbname"]
        cur.execute("SELECT 1 FROM pg_catalog.pg_database WHERE datname = %s", (target_db,))
        exists = cur.fetchone()

        if not exists:
            print(f"📦 Creating database '{target_db}'...")
            cur.execute(f'CREATE DATABASE "{target_db}"')
            print(f"✅ Database '{target_db}' created successfully.")
        else:
            print(f"ℹ️ Database '{target_db}' already exists.")

        cur.close()
        conn.close()
    except Exception as e:
        print(f"⚠️ Error creating database: {e}")
        print("Make sure PostgreSQL is running and credentials are correct.")
        sys.exit(1)


def run_schema_migration(params):
    print("📜 Running database schema migrations...")
    base_dir = os.path.dirname(os.path.abspath(__file__))
    schema_path = os.path.join(base_dir, "schema.sql")
    seed_path = os.path.join(base_dir, "seed_data.sql")

    if not os.path.exists(schema_path):
        print(f"❌ schema.sql not found at {schema_path}")
        return

    try:
        conn = psycopg2.connect(**params)
        cur = conn.cursor()

        with open(schema_path, "r", encoding="utf-8") as f:
            schema_sql = f.read()
            cur.execute(schema_sql)
        conn.commit()
        print("✅ Database schema applied successfully.")

        if os.path.exists(seed_path):
            with open(seed_path, "r", encoding="utf-8") as f:
                seed_sql = f.read()
                cur.execute(seed_sql)
            conn.commit()
            print("✅ Initial seed data inserted into PostgreSQL tables.")

        cur.close()
        conn.close()
    except Exception as e:
        print(f"❌ Error applying schema/seed migrations: {e}")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="LandGuard Database Initializer")
    parser.add_argument("--password", help="PostgreSQL password for user 'postgres'")
    args = parser.parse_args()

    params = get_db_params()
    if args.password:
        params["password"] = args.password

    print(f"🚀 Initializing LandGuard Database on {params['host']}:{params['port']}...")
    create_database_if_not_exists(params)
    run_schema_migration(params)
    print("🎉 Database setup complete! LandGuard PostgreSQL is ready.")


if __name__ == "__main__":
    main()
