def clean_staging(cursor, connection):
    cursor.execute("""DROP TABLE IF EXISTS staging_competitions""")
    connection.commit()
    print('staging_competitions dropped')

    cursor.execute("""DROP TABLE IF EXISTS staging_matches""")
    connection.commit()
    print('staging_matches dropped')

    cursor.execute("""DROP TABLE IF EXISTS staging_events""")
    connection.commit()
    print('staging_events dropped')


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
        SELECT {_cols_str} FROM staging_{table}
        WHERE true
        ON CONFLICT({_conflict_keys_str}) 
        DO UPDATE SET 
            {set_clause}
    """

    cursor.execute(upsert_query)
    connection.commit()