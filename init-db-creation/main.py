"""
Orchestrate Initial Database Creation Workflows


Overview
Main ETL workflow to orchestrate the medallion structured pipeline for extracting competition, match and event information from the Statsbombpy package.
Currently using 1 competition (FIFA World Cup 2022), creating a Data Warehouse to store the data in SQLite.


Workflow Description
1. Creates the SQLite databases if they don't already exist.
2. Calls bronze_main from the bronze workflow to create the bronze layer


Requirements/Prerequistes
- Install requirements.txt
- Read through the README.md for more information on the project


Author
Elliot Kerr - 03/08/2026
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


SCHEMAS = {
    'STAGING_SCHEMA' : 'staging',
    'BRONZE_SCHEMA' : 'bronze', 
    # 'SILVER_SCHEMA' : 'silver', 
    # 'GOLD_SCHEMA' : 'gold'
}


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
    
    for schema_names in list(SCHEMAS.values()):

        if f"{schema_names}.db" not in os.listdir("./dbs"):
            main_logger.info(f"Creating database '{schema_names}'")
            create_dbs(schema_names)


    bronze_main(SCHEMAS['STAGING_SCHEMA'], SCHEMAS['BRONZE_SCHEMA'], get_logger("BRONZE"), competition_id = 43, season_id = 106)

    # silver_main(
    #     SILVER_SCHEMA, BRONZE_SCHEMA, get_logger("SILVER")
    # )
    