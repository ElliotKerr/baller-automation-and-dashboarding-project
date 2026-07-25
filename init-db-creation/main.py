"""
Run Initial Database Creation Workflows

Overview



Workflow Description


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


import sqlite3
from sqlalchemy import create_engine
import pandas as pd
import logging
import os
from db_workflows.bronze import bronze_main
from db_workflows.silver import silver_main

STAGING_SCHEMA = 'staging'
BRONZE_SCHEMA = 'bronze'
SILVER_SCHEMA = 'intermediate'
GOLD_SCHEMA = 'prod'

SCHEMAS = [STAGING_SCHEMA, BRONZE_SCHEMA, SILVER_SCHEMA, GOLD_SCHEMA]
DB_NAMES = ['staging', 'bronze', 'intermediate', 'prod']


def create_dbs(db_name):
    """
    Doc String
    """
    connection = sqlite3.connect(f'./dbs/{db_name}.db')

    connection.close()


def get_logger(logging_type):
    """
    Doc String
    """
    logger = logging.getLogger(logging_type)

    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            f"[%(asctime)s] %(levelname)s - {logging_type} - %(message)s"
        )
        handler.setFormatter(formatter)

        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
        
        logger.propagate = False

    return logger


if __name__ == '__main__':
    main_logger = get_logger(" MAIN ")
    
    for i in range(len(SCHEMAS)):
        db_name = DB_NAMES[i]
        schema = SCHEMAS[i]

        if f"{db_name}.db" not in os.listdir("./dbs"):
            main_logger.info(f"Creating database '{schema}'")
            create_dbs(schema)


    # bronze_main(STAGING_SCHEMA, BRONZE_SCHEMA, get_logger("BRONZE"), competition_id = 43, season_id = 106)

    silver_main(
        SILVER_SCHEMA, get_logger("SILVER")
    )
    