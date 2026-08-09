"""
Gold Tables Creation ETL

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
import warnings
from statsbombpy.api_client import NoAuthWarning

# Suppress the NoAuthWarning specifically
warnings.filterwarnings("ignore", category=NoAuthWarning)

from sqlalchemy import text
import logging
from utils.general import create_db_engine_func, DB_ENGINE_STRING

from utils.gold import Gold

gold_pyclass = Gold()

def gold_main(slv_schema: str, gld_schema: str, logger: logging):
    """
    Function is the orchestrator of the gold layer, following the Workflow Description in the file doc string.

    Args:
    slv_schema - Schema name for the silver database, incase any other names are used (i.e. "intermediate")
    gld_schema - Schema name for the gold database, incase any other names are used (i.e. "prod")
    logger - Formatted Logging Instance " GOLD "

    Returns:
    No output
    """
    gld_engine = create_db_engine_func(gld_schema, DB_ENGINE_STRING)
    gld_dict = {'schema': gld_schema, 'engine': gld_engine, 'conn': gld_engine.connect()}

    gld_dict['conn'].execute(text(f"ATTACH DATABASE './dbs/{slv_schema}.db' AS silver"))
    gld_dict['conn'].commit()

    gold_pyclass.create_gold(gld_dict, gold_pyclass.COMBINED_RESULTS, 'combined_results', logger)

    gold_pyclass.create_gold(gld_dict, gold_pyclass.COMBINED_MATCHES, 'combined_matches', logger)

    gold_pyclass.create_gold(gld_dict, gold_pyclass.COMBINED_PASSES, 'combined_passes', logger)

    gld_dict['conn'].execute(text("DETACH DATABASE silver"))
    gld_dict['conn'].commit()
    gld_dict['conn'].close()
    gld_dict['engine'].dispose()