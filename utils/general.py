"""
Script Doc String

Overview


Workflow Description



Requirements/Prerequistes




Author

"""

import logging

DB_ENGINE_STRING = 'sqlite:///dbs/{db_name}.db'

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


def _merge(cursor, connection, _class, table):
    _fields = list(_class.column_mapping.keys())

    _merge_fields = [f for f in _fields]

    _cols_str = ", ".join(f'"{c}"' for c in _merge_fields)
    _conflict_keys_str = ", ".join(_class.composite_keys)

    # When conflicts occur in the merge, they are stored in the temporary EXCLUDED table.
    set_clause = ",".join(
        [f'"{col}" = EXCLUDED."{col}"' for col in _merge_fields]
    )

    cursor.execute(f"""
        CREATE UNIQUE INDEX IF NOT EXISTS idx_{table}_keys 
        ON {table} ({_conflict_keys_str})
    """)
    connection.commit()

    upsert_query = f"""
        INSERT INTO {table} ({_cols_str})
        SELECT {_cols_str} FROM staging.{table}
        WHERE true
        ON CONFLICT({_conflict_keys_str}) 
        DO UPDATE SET 
            {set_clause}
    """

    cursor.execute(upsert_query)
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