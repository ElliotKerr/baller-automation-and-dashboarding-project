"""
Bronze Tables Creation ETL

Overview
ETL workflow created to extract Competitions, Matches and Events from the Statsbombpy package.
Currently using 1 competition (FIFA World Cup 2022), creating a Data Warehouse to store the data in SQLite.


Workflow Description
1. Extracts the competitions data from sb.competitions(), filtering specifically for competition_id = 43 and season_id = 106
2. Creates a new dataframe for records that have a match_updated greater than the max value in bronze.competitions
3. Loads the new records into bronze.staging_competitions, then merges the staging table into bronze.competitions.

4. Using the competition and season ids, extracts the matches in the competition.
5. Creates a new dataframe used to load the matches incrementally, filtering for last_updated greater than the max last_updated value in bronze.matches
6. Loads the new records into bronze.staging_matches.

7. Using the match id for each match in each competition, extract the events.
8. Since there is no last_updated, we load each event to bronze.staging_events and merge each if the match has been updated into bronze.events.

9. Merges staging to bronze.matches; this merge happens once all competitions, matches and events have been loaded into the required tables.


Requirements/Prerequistes




Author

"""


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
import logging

from utils.general import clean_staging, _merge
from utils.competitions import Competitions
from utils.matches import Matches
from utils.events import Events

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s - %(message)s"
)

start_time = time.time()


# Class storing the fields and composite key used in the merge procedure.
comp = Competitions()
match = Matches()
event = Events()

engine = create_engine(f'sqlite:///dbs/{BRONZE_SCHEMA}.db', echo=False, pool_pre_ping=True)
logging.info(engine.connect())

connection = sqlite3.connect(f'./dbs/{BRONZE_SCHEMA}.db')
cursor = connection.cursor()

clean_staging(cursor, connection)

competitions = sb.competitions()

# Just looking at the 2022 World Cup, which has competition_id = 43 and season_id = 106

competitions = competitions[(competitions['competition_id'] == 43) & (competitions['season_id'] == 106)].copy()

competitions_df = comp.bronze_competitions(connection, cursor, engine, _merge, comp, competitions)


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
        ''', connection)['last_updated'][0]
    except:
        match_last_updated = None
    
    if match_last_updated is None:
        matches_df = matches
    else:
        matches_df = matches[matches['last_updated'] > match_last_updated]

    
    logging.info(f"Writing matches for competition-season {competition_id}-{season_id}.")
    matches_df.to_sql('staging_matches', con=engine, if_exists='append', dtype = match.column_mapping, index = False)

#     match_ids_df = matches_df[['match_id']]

#     match_ids_dict = match_ids_df.to_dict()

#     match_ids_list = [match_ids_dict['match_id'][i] for i in list(match_ids_dict['match_id'].keys())]
    
#     for match_id in match_ids_list:
#         logging.info(f'Starting Events extraction for match {match_id}')
#         events = sb.events(match_id=match_id)
#         events_df = events.reindex(columns=event.column_mapping.keys())

#         logging.info(f"Writing into staging_events")
#         events_df.to_sql('staging_events', con=engine, if_exists='append', dtype = event.column_mapping, index = False)
    
#     logging.info(f"Merging events for competition-season {competition_id}-{season_id}.")
#     _merge(cursor, connection, event, 'events')

# logging.info(f"Merging all matches.")

# _merge(cursor, connection, match, 'matches')

# logging.info("Merge complete!")
# Close the database connection
connection.close()

logging.info(f"Total Runtime {time.time() - start_time} seconds")