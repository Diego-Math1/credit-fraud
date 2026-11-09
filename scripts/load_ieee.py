# scripts/load_ieee.py
import csv
import os
import sys
from pathlib import Path

import psycopg2
from dotenv import load_dotenv
from psycopg2 import sql

load_dotenv()

DB_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "dbname": "credit_fraud",
    "user": "postgres",
    "password": "postgres",
}


def create_raw_schema(conn):
    with conn.cursor() as cur:
        cur.execute("CREATE SCHEMA IF NOT EXISTS raw;")
    conn.commit()


def infer_column_types(header_row):
    """Infere tipos: TransactionID -> BIGINT, isFraud -> INTEGER, resto TEXT."""
    types = []
    for col in header_row:
        if col == "TransactionID":
            types.append("BIGINT")
        elif col == "isFraud":
            types.append("INTEGER")
        else:
            types.append("TEXT")
    return types


def create_table(conn, table_name, header_row):
    columns = infer_column_types(header_row)
    cols_ddl = ", ".join(f'"{col}" {typ}' for col, typ in zip(header_row, columns, strict=False))
    with conn.cursor() as cur:
        cur.execute(f'DROP TABLE IF EXISTS raw."{table_name}";')
        cur.execute(f'CREATE TABLE raw."{table_name}" ({cols_ddl});')
    conn.commit()
    print(f"✅ Tabela raw.{table_name} criada com {len(header_row)} colunas.")


def load_csv(conn, csv_path, table_name):
    csv_path = Path(csv_path)
    if not csv_path.exists():
        raise FileNotFoundError(f"CSV não encontrado: {csv_path}")

    with open(csv_path, encoding="utf-8", newline="") as f:
        reader = csv.reader(f)
        header = next(reader)

    create_table(conn, table_name, header)

    copy_sql = sql.SQL(
        "COPY raw.{} FROM STDIN WITH (FORMAT csv, HEADER true, DELIMITER ',')"
    ).format(sql.Identifier(table_name))

    with open(csv_path, encoding="utf-8", newline="") as f, conn.cursor() as cur:
        cur.copy_expert(copy_sql, f)
    conn.commit()

    with conn.cursor() as cur:
        cur.execute(f'SELECT count(*) FROM raw."{table_name}";')
        count = cur.fetchone()[0]
    print(f"✅ {table_name}: {count:,} linhas carregadas.")


def main():
    if len(sys.argv) != 3:
        print("Uso: python scripts/load_ieee.py <pasta_dos_csvs> <transaction|identity>")
        print("Exemplo: python scripts/load_ieee.py C:/caminho/ieee train")
        sys.exit(1)

    csv_dir = sys.argv[1]
    split = sys.argv[2]  # "train" ou "test"

    files = {
        f"{split}_transaction.csv": f"{split}_transactions",
        f"{split}_identity.csv": f"{split}_identity",
    }

    conn = psycopg2.connect(**DB_CONFIG)
    try:
        create_raw_schema(conn)
        for filename, table_name in files.items():
            path = os.path.join(csv_dir, filename)
            if os.path.exists(path):
                load_csv(conn, path, table_name)
            else:
                print(f"⚠️  Pulando {filename} (não encontrado).")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
