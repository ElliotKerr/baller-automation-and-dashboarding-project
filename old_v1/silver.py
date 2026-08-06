"""
Silver Tables Creation ETL

Overview



Workflow Description


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

import sqlite3
from sqlalchemy import create_engine
import time
import pandas as pd

from data_extraction_workflow.utils.general import _merge, create_db_engine_func, create_db_connection_func, DB_ENGINE_STRING

from data_extraction_workflow.utils.competitions import Competitions
from data_extraction_workflow.utils.matches import Matches
from data_extraction_workflow.utils.events import Events

# Class storing the fields and composite key used in the merge procedure.
comp_pyclass = Competitions()
match_pyclass = Matches()
event_pyclass = Events()

def extract_field_names(table_class):
    """
    Doc String
    """
    return list(table_class.column_mapping.keys())

COMP_MATCH_QUERY = """
    SELECT 
        {competition_field_names}
        ,{match_field_names}
    FROM 
        {brz_schema}.competitions c
    LEFT JOIN 
        {brz_schema}.matches m
    ON 
        c.competition_id = m.competition_id
    AND 
        c.season_id = m.season_id
"""

COMPLETE_QUERY = """
    SELECT 
        {competition_field_names}
        ,{match_field_names}
        ,{event_field_names}
    FROM 
        {brz_schema}.competitions c
    LEFT JOIN 
        {brz_schema}.matches m
    ON 
        c.competition_id = m.competition_id
    AND
        c.season_id = m.season_id
    LEFT JOIN 
        {brz_schema}.events e
    ON 
        m.match_id = e.match_id
"""

def create_combined_tables(slv_cursor, logger):
    competition_field_names = extract_field_names(comp_pyclass)
    competition_field_names_v2 = [f'"{field_name}"' for field_name in competition_field_names if '360' not in field_name]

    match_field_names = extract_field_names(match_pyclass)
    match_field_names_v2 = [f'"{field_name}"' for field_name in match_field_names if ('360' not in field_name) and (field_name != 'competition_id') and (field_name != 'season_id') and (field_name not in competition_field_names_v2)]

    event_field_names = extract_field_names(event_pyclass)
    event_field_names_v2 = [f'"{field_name}"' for field_name in event_field_names if ('360' not in field_name) and (field_name != 'match_id') and (field_name not in competition_field_names_v2) and (field_name not in match_field_names_v2)]

    

    logger.info("Dropping silver.comp_matches if it exists already")

    slv_cursor.execute("""DROP TABLE IF EXISTS comp_matches""")

    logger.info("Creating a new version of silver.comp_matches.")

    competition_field_names_string = "c."
    competition_field_names_string += ',c.'.join(competition_field_names_v2)

    match_field_names_string = "m."
    match_field_names_string += ',m.'.join(match_field_names_v2)

    event_field_names_string = "e."
    event_field_names_string += ',e.'.join(event_field_names_v2)


    slv_cursor.execute(f"""
        CREATE TABLE comp_matches AS 
        {COMP_MATCH_QUERY.format(competition_field_names = competition_field_names_string, match_field_names = match_field_names_string, brz_schema = brz_schema)}
    """)

    logger.info("Dropping silver.complete if it exists already")

    slv_cursor.execute("""DROP TABLE IF EXISTS complete""")

    logger.info("Creating a new version of silver.complete.")

    slv_cursor.execute(f"""
        CREATE TABLE complete AS 
        {COMPLETE_QUERY.format(competition_field_names = competition_field_names_string, match_field_names = match_field_names_string, event_field_names = event_field_names_string, brz_schema = brz_schema)}
    """)


# def clean_bronze_tables(slv_cursor, logger):


def silver_main(
        slv_schema : str, 
        brz_schema : str,
        logger
    ):
    """
    Doc String
    """
    slv_engine = create_db_engine_func(slv_schema, DB_ENGINE_STRING, create_engine)
    slv_connection, slv_cursor = create_db_connection_func(slv_schema, sqlite3)

    slv_cursor.execute("ATTACH DATABASE './dbs/bronze.db' AS bronze")

    create_combined_tables(slv_cursor, logger)

    slv_cursor.execute("DETACH DATABASE bronze")
    slv_connection.close()