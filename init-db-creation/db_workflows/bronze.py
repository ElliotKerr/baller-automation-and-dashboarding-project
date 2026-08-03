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
from sqlalchemy import create_engine, text
import time
from datetime import datetime, timedelta, timezone

from utils.general import _merge, create_db_engine_func, DB_ENGINE_STRING, col_cleaning
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

    brz_engine = create_db_engine_func(brz_schema, DB_ENGINE_STRING, create_engine)
    brz_dict = {'schema': brz_schema, 'engine': brz_engine, 'conn': brz_engine.connect()}

    valid_from = datetime.now(timezone.utc).replace(tzinfo=None)
    valid_to = valid_from - timedelta(milliseconds=1)

    competitions = sb.competitions()

    if not (competition_id is None or season_id is None):
        competitions = competitions[
            (competitions['competition_id'] == competition_id) & 
            (competitions['season_id'] == season_id)
        ].copy()


    competitions['data_valid_from_utc'] = valid_from
    competitions['data_valid_to_utc'] = None


    competitions_df = comp_pyclass.etl_competitions(
        brz_dict, 
        comp_pyclass, 
        competitions,
        col_cleaning,
        valid_to,
        logger
    ) 


    # match_pyclass.etl_matches(
    #     sb,
    #     event_pyclass,
    #     stg_engine, 
    #     stg_schema,
    #     brz_connection, 
    #     brz_cursor, 
    #     _merge, 
    #     match_pyclass, 
    #     competitions_df,
    #     logger
    # )

    brz_dict['conn'].close()
    brz_dict['engine'].dispose()