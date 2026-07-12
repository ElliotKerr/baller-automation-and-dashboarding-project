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
from utils.events import Events

start_time = time.time()

# Class storing the fields and composite key used in the merge procedure.
comp = Competitions()
match = Matches()
event = Events()

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


engine = create_engine('sqlite:///dbs/competitions.db', echo=False, pool_pre_ping=True)
print(engine.connect())

connection = sqlite3.connect('./dbs/competitions.db')
cursor = connection.cursor()

cursor.execute("""DROP TABLE IF EXISTS staging_competitions""")
connection.commit()
print('staging_competitions dropped')

cursor.execute("""DROP TABLE IF EXISTS staging_matches""")
connection.commit()
print('staging_matches dropped')

cursor.execute("""DROP TABLE IF EXISTS staging_events""")
connection.commit()
print('staging_events dropped')


competitions = sb.competitions()

for col in comp.date_columns:
    if col in competitions.columns:
        competitions[col] = pd.to_datetime(competitions[col], format="ISO8601")

try:
    last_updated = pd.read_sql_query('SELECT COALESCE(MAX(match_updated),NULL) as last_updated FROM competitions', connection)['last_updated'][1]
except:
    last_updated = None

if last_updated is None:
    competitions_df = competitions
else:
    competitions_df = competitions[competitions['match_updated'] > last_updated]

print(f"Writing competitions into the staging table!")

competitions_df.to_sql('staging_competitions', con=engine, if_exists='replace', dtype = comp.column_mapping, index = False)

print(f"Merging staging_competitions into competitions")

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
        ''', connection)['last_updated'][1]
    except:
        match_last_updated = None
    
    if match_last_updated is None:
        matches_df = matches
    else:
        matches_df = matches[matches['last_updated'] > match_last_updated]

    
    print(f"Writing matches for competition-season {competition_id}-{season_id}.")
    matches_df.to_sql('staging_matches', con=engine, if_exists='append', dtype = match.column_mapping, index = False)

    match_ids_df = matches_df[['match_id']]

    match_ids_dict = match_ids_df.to_dict()

    match_ids_list = [match_ids_dict['match_id'][i] for i in list(match_ids_dict['match_id'].keys())]
    
    for match_id in match_ids_list:
        print(f'Starting Events extraction for match {match_id}')
        events = sb.events(match_id=match_id)
        events_df = events.reindex(columns=event.column_mapping.keys())

        print(f"Writing into staging_events")
        events_df.to_sql('staging_events', con=engine, if_exists='append', dtype = event.column_mapping, index = False)
    
    print(f"Merging events for competition-season {competition_id}-{season_id}.")
    _merge(cursor, connection, event, 'events')

print(f"Merging all matches.")

_merge(cursor, connection, match, 'matches')

print("Merge complete!")
# Close the database connection
connection.close()

print(f"Total Runtime {time.time() - start_time} seconds")