"""
Silver Tables Creation ETL

Overview
ETL orchestrates the silver layer workflows, removing any historical records and creating the combined view

Workflow Description
1. Sets up the engine and connections to the silver database file.
2. Runs the clean_bronze_tables function from the Silver class to create silver.competitions, .matches and .events
3. Runs the create_combined_table function from the Silver class to create silver.combined


Requirements/Prerequistes
- utils.general, .silver
- Install requirements.txt


Author
Elliot Kerr - 05/08/2026

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

from sqlalchemy import text
import logging
from data_extraction_workflow.utils.general import create_db_engine_func, DB_ENGINE_STRING

from data_extraction_workflow.utils.competitions import Competitions
from data_extraction_workflow.utils.matches import Matches
from data_extraction_workflow.utils.events import Events
from data_extraction_workflow.utils.silver import Silver

# Class storing the fields and composite key used in the merge procedure.
comp_pyclass = Competitions()
match_pyclass = Matches()
event_pyclass = Events()
silver_pyclass = Silver()


def silver_main(
        slv_schema : str, 
        brz_schema : str,
        logger: logging
    ):
    """
    Function is the orchestrator of the silver layer, following the Workflow Description in the file doc string.

    Args:
    slv_schema - Schema name for the silver database, incase any other names are used (i.e. "intermediate")
    brz_schema - Schema name for the bronze database
    logger - Formatted Logging Instance "SILVER"

    Returns:
    No output
    """
    slv_engine = create_db_engine_func(slv_schema, DB_ENGINE_STRING)
    slv_dict = {'schema': slv_schema, 'engine': slv_engine, 'conn': slv_engine.connect()}

    slv_dict['conn'].execute(text(f"ATTACH DATABASE './dbs/{brz_schema}.db' AS bronze"))
    slv_dict['conn'].commit()

    logger.info(f"Cleaning the Bronze tables into Silver.")

    silver_pyclass.clean_bronze_tables(slv_dict, 'competitions', logger)
    silver_pyclass.clean_bronze_tables(slv_dict, 'matches', logger)
    silver_pyclass.clean_bronze_tables(slv_dict, 'events', logger)


    slv_dict['conn'].execute(text("DETACH DATABASE bronze"))
    slv_dict['conn'].commit()


    silver_pyclass.create_combined_table(slv_dict, logger)


    slv_dict['conn'].close()
    slv_dict['engine'].dispose()