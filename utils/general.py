"""
Script Doc String

Overview


Workflow Description



Requirements/Prerequistes




Author

"""

import logging
from datetime import datetime, date
import pandas as pd
from sqlalchemy import String, Integer, DateTime, Float, JSON, Boolean, Date, create_engine, text

DB_ENGINE_STRING = 'sqlite:///dbs/{db_name}.db'

SQL_PY_DTYPE_MAPPING = {
    String: str,
    Integer: int,
    DateTime: datetime,
    Date: date,
    Float: float,
    JSON: dict,
    Boolean: bool
}

def col_cleaning(df, column_mapping):
    """
    Doc String
    """
    target_cols = [col for col in column_mapping if col in df.columns]
    
    if not target_cols:
        return df

    df[target_cols] = df[target_cols].replace(['NaN', 'None', 'Null', 'nan', 'null', ''], None)

    for col in target_cols:
        sql_dtype = column_mapping[col]
        py_type = SQL_PY_DTYPE_MAPPING.get(sql_dtype)

        if py_type is None:
            continue

        if py_type is datetime or py_type is datetime:
            df[col] = pd.to_datetime(df[col], format="ISO8601", errors='coerce')
            
        elif py_type is date or py_type is date:
            df[col] = pd.to_datetime(df[col], format="ISO8601", errors='coerce').dt.date

        elif py_type is int:
            df[col] = pd.to_numeric(df[col], errors='coerce').astype('Int64')

        elif py_type is float:
            df[col] = pd.to_numeric(df[col], errors='coerce').astype('Float64')

        elif py_type is bool:
            df[col] = df[col].astype('boolean')

        elif py_type is str:
            df[col] = df[col].astype('string')

    return df


def check_table_exists(logger, conn, table):
    """
    Lightweight check if a table exists in the target schema.
    """
    try:
        # Querying sqlite_master (or main.sqlite_master) strictly targets the target DB, 
        # ignoring any ATTACHED schemas!
        result = conn.execute(text(
            f"SELECT 1 FROM sqlite_master WHERE type='table' AND name='{table}'"
        ))
        exists = result.fetchone() is not None
        logger.info(f"Table '{table}' exists in target DB: {exists}")
        return exists
    except Exception as e:
        logger.error(f"Error checking table existence: {e}")
        return False


def create_required_table(logger, source_dict, target_dict, table):
    """
    Copies table DDL from source_dict schema into target_dict database.
    """
    # 1. Execute query and capture the Result object
    result = target_dict['conn'].execute(text(f"""
        SELECT sql
        FROM {source_dict['schema']}.sqlite_master
        WHERE type = 'table'
        AND name = '{table}'
    """))

    # 2. Fetch row from result (NOT target_dict['conn'])
    row = result.fetchone()

    if row is None or row[0] is None:
        logger.info(f"{target_dict['schema']}: '{table}' not found in {source_dict['schema']}.db")
    else:
        create_sql = row[0]

        # 3. Drop existing and create table using text()
        target_dict['conn'].execute(text(f'DROP TABLE IF EXISTS main.{table}'))
        target_dict['conn'].execute(text(create_sql))
        
        # 4. Commit immediately so index creation in _merge sees the table!
        target_dict['conn'].commit()
        logger.info(f"Successfully created table {table}' in {target_dict['schema']}")


def create_db_engine_func(db_name, engine_string, create_engine):
    """
    Doc String
    """
    return create_engine(
        engine_string.format(db_name = db_name), 
        echo=False, 
        # pool_pre_ping=True
    )