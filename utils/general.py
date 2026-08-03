"""
Script Doc String

Overview


Workflow Description



Requirements/Prerequistes




Author

"""

import logging
from datetime import datetime
import pandas as pd
from sqlalchemy import String, Integer, DateTime, Float, JSON, Boolean, Date

DB_ENGINE_STRING = 'sqlite:///dbs/{db_name}.db'

SQL_PY_DTYPE_MAPPING = {
    String: str,
    Integer: int,
    DateTime: datetime,
    Float: float,
    JSON: dict,
    Boolean: bool
}

def col_cleaning(df, column_mapping):
    """
    Doc String
    """
    for col, sql_dtype in column_mapping.items():
        py_type = SQL_PY_DTYPE_MAPPING[sql_dtype]

        df[col] = df[col].apply(lambda x: None if x in ('NaN', 'None', 'Null') else x)

        if py_type is datetime:
            df[col] = pd.to_datetime(df[col], format="ISO8601", utc=True)
        if py_type is int:
            df[col] = pd.to_numeric(df[col]).apply(lambda x: int(x))
        if py_type is float:
            df[col] = pd.to_numeric(df[col]).apply(lambda x: float(x))

    return df


def clean_staging(cursor, connection):
    cursor.execute("""DROP TABLE IF EXISTS competitions""")
    connection.commit()
    logging.info('staging.competitions dropped')

    cursor.execute("""DROP TABLE IF EXISTS matches""")
    connection.commit()
    logging.info('staging.matches dropped')

    cursor.execute("""DROP TABLE IF EXISTS events""")
    connection.commit()
    logging.info('staging.events dropped')


def _merge(source_schema, cursor, connection, _class, table, valid_to_timestamp):
    _fields = list(_class.column_mapping.keys())
    _cols_str = ", ".join(f'"{c}"' for c in _fields)
    _conflict_keys_str = ", ".join(f'"{k}"' for k in _class.composite_keys)

    # Step 1: Ensure unique constraint ONLY applies to currently active records
    cursor.execute(f"""
        CREATE UNIQUE INDEX IF NOT EXISTS idx_{table}_active_keys 
        ON {table} ({_conflict_keys_str})
        WHERE "data_valid_to_utc" IS NULL
    """)

    # Step 2: Expire existing active records matching keys in the source
    join_conditions = " AND ".join(
        [f'{table}."{k}" = {source_schema}.{table}."{k}"' for k in _class.composite_keys]
    )

    update_query = f"""
        UPDATE {table}
        SET data_valid_to_utc = '{valid_to_timestamp}'
        WHERE data_valid_to_utc IS NULL
          AND EXISTS (
              SELECT 1 FROM {source_schema}.{table}
              WHERE {join_conditions}
          )
    """
    cursor.execute(update_query)

    # Step 3: Insert all new rows from the source schema
    insert_query = f"""
        INSERT INTO {table} ({_cols_str})
        SELECT {_cols_str} FROM {source_schema}.{table}
    """
    cursor.execute(insert_query)

    connection.commit()


def create_db_engine_func(db_name, engine_string, create_engine):
    """
    Doc String
    """
    return create_engine(
        engine_string.format(db_name = db_name), 
        echo=False, 
        pool_pre_ping=True
    )

def create_db_connection_func(db_name, sqlite3):
    """
    Doc String
    """
    connection = sqlite3.connect(f'./dbs/{db_name}.db')
    cursor = connection.cursor()

    return connection, cursor