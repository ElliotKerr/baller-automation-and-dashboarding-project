# Only needed in windows:
import sys
from pathlib import Path

# Automatically find project root (1 folder up from this file) and add to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


import warnings
from statsbombpy.api_client import NoAuthWarning

# Suppress the NoAuthWarning specifically
warnings.filterwarnings("ignore", category=NoAuthWarning)

from statsbombpy import sb
import sqlite3
from sqlalchemy import create_engine
import time
import pandas as pd

from utils.competitions import Competitions
from utils.matches import Matches

# Class storing the fields and composite key used in the merge procedure.
comp = Competitions()

match = Matches()

def _merge(cursor, connection, _class, table):
    _fields = list(_class.column_mapping.keys())

    _merge_fields = [f for f in _fields]

    _cols_str = ", ".join(_merge_fields)
    _conflict_keys_str = ", ".join(_class.composite_keys)

    # When conflicts occur in the merge, they are stored in the temporary EXCLUDED table.
    set_clause = ",".join([f"{col} = EXCLUDED.{col}" for col in _merge_fields])

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


engine = create_engine('sqlite:///dbs/competitions.db', echo=False)
connection = sqlite3.connect('./dbs/competitions.db')
cursor = connection.cursor()

cursor.execute("""DELETE FROM staging_competitions""")
connection.commit()

cursor.execute("""DELETE FROM staging_matches""")
connection.commit()


competitions = sb.competitions()

for col in comp.date_columns:
    if col in competitions.columns:
        competitions[col] = pd.to_datetime(competitions[col], format="ISO8601")


last_updated = pd.read_sql_query('SELECT COALESCE(MAX(match_updated),NULL) as last_updated FROM competitions', connection)['last_updated'][0]

if last_updated is None:
    competitions_df = competitions
else:
    competitions_df = competitions[competitions['match_updated'] >= last_updated]

competitions_df.to_sql('staging_competitions', con=engine, if_exists='replace', dtype = comp.column_mapping, index = False)

_merge(cursor, connection, comp, 'competitions')


comp_id_season_id_df = competitions_df[['competition_id', 'season_id']]

comp_id_season_id_dict = comp_id_season_id_df.to_dict()

comp_id_season_id_list = [
    [
        comp_id_season_id_dict['competition_id'][i], 
        comp_id_season_id_dict['season_id'][i]
    ] for i in list(comp_id_season_id_dict['competition_id'].keys())]


for _array in comp_id_season_id_list:
    competition_id = _array[0]
    season_id = _array[1]

    start_time = time.time()
    matches = sb.matches(competition_id=competition_id, season_id=season_id)

    for col in match.date_columns:
        if col in matches.columns:
            matches[col] = pd.to_datetime(matches[col], format="ISO8601")
    try:
        match_last_updated = pd.read_sql_query(f'''
            SELECT 
                COALESCE(MAX(last_updated),NULL) AS last_updated 
            FROM 
                matches 
            WHERE 
                competition_id = {competition_id} 
            AND 
                season_id = {season_id}
        ''', connection)['last_updated'][0]
    except:
        match_last_updated = None
    
    if match_last_updated is None:
        matches_df = matches
    else:
        matches_df = matches[matches['last_updated'] > match_last_updated]

    matches_df.to_sql('staging_matches', con=engine, if_exists='append', dtype = match.column_mapping, index = False)

    duration = time.time() - start_time

    print(f"Loaded {competition_id}-{season_id}. Pausing the process for {duration} seconds for Elastic Banding!")

    time.sleep(duration)

_merge(cursor, connection, match, 'matches')

print("Merge complete!")
# Close the database connection
connection.close()