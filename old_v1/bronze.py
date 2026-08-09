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
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
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

from utils.general import clean_staging, _merge, create_db_engine_func, create_db_connection_func, DB_ENGINE_STRING
from utils.competitions import Competitions
from utils.matches import Matches
from utils.events import Events

# Class storing the fields and composite key used in the merge procedure.
comp_pyclass = Competitions()
match_pyclass = Matches()
event_pyclass = Events()


def bronze_main(
        stg_schema : str, 
        brz_schema : str, 
        logger, 
        competition_id : int = None, 
        season_id : int = None
    ):
    """
    Doc String
    """
    start_time = time.time()

    stg_engine = create_db_engine_func(stg_schema, DB_ENGINE_STRING, create_engine)
    stg_connection, stg_cursor = create_db_connection_func(stg_schema, sqlite3)


    brz_engine = create_db_engine_func(brz_schema, DB_ENGINE_STRING, create_engine)
    brz_connection, brz_cursor = create_db_connection_func(brz_schema, sqlite3)

    brz_cursor.execute(f"ATTACH DATABASE './dbs/{stg_schema}.db' AS {stg_schema}")

    clean_staging(stg_cursor, stg_connection)

    competitions = sb.competitions()

    if not (competition_id is None or season_id is None):
        competitions = competitions[
            (competitions['competition_id'] == competition_id) & 
            (competitions['season_id'] == season_id)
        ].copy()


    competitions_df = comp_pyclass.bronze_competitions(
        stg_engine, 
        stg_schema,
        brz_connection, 
        brz_cursor, 
        _merge, 
        comp_pyclass, 
        competitions,
        logger
    ) 


    match_pyclass.bronze_matches(
        sb,
        event_pyclass,
        stg_engine, 
        stg_schema,
        brz_connection, 
        brz_cursor, 
        _merge, 
        match_pyclass, 
        competitions_df,
        logger
    )


    brz_cursor.execute(f"DETACH DATABASE {stg_schema}")


    stg_connection.close()
    brz_connection.close()