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

from statsbombpy import sb
import sqlite3
from sqlalchemy import create_engine, text
import time
from datetime import datetime, timedelta, timezone
import pandas as pd

from utils.general import create_db_engine_func, DB_ENGINE_STRING, col_cleaning

from utils.competitions import Competitions
from utils.matches import Matches
from utils.events import Events
from utils.silver import Silver

# Class storing the fields and composite key used in the merge procedure.
comp_pyclass = Competitions()
match_pyclass = Matches()
event_pyclass = Events()
silver_pyclass = Silver()

def extract_field_names(table_class):
    """
    Doc String
    """
    return list(table_class.column_mapping.keys())



def silver_main(
        slv_schema : str, 
        brz_schema : str,
        logger
    ):
    """
    Doc String
    """
    slv_engine = create_db_engine_func(slv_schema, DB_ENGINE_STRING, create_engine)
    slv_dict = {'schema': slv_schema, 'engine': slv_engine, 'conn': slv_engine.connect()}

    slv_dict['conn'].execute(text(f"ATTACH DATABASE './dbs/{brz_schema}.db' AS bronze"))
    slv_dict['conn'].commit()

    logger.info(f"Cleaning the Bronze tables into Silver.")

    silver_pyclass.clean_bronze_tables(slv_dict, logger, 'competitions')
    silver_pyclass.clean_bronze_tables(slv_dict, logger, 'matches')
    silver_pyclass.clean_bronze_tables(slv_dict, logger, 'events')


    slv_dict['conn'].execute(text("DETACH DATABASE bronze"))
    slv_dict['conn'].commit()


    silver_pyclass.create_combined_table(slv_dict, logger)


    slv_dict['conn'].close()
    slv_dict['engine'].dispose()