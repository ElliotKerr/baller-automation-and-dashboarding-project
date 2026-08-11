"""
Orchestrate Initial Database Creation Workflows


Overview
Main ETL workflow to orchestrate the medallion structured pipeline for extracting competition, match and event information from the Statsbombpy package.
Currently using 2 competitions (FIFA World Cup 2018 & 2022), creating a Data Warehouse to store the data in SQLite.


Workflow Description
1. Creates the SQLite databases if they don't already exist.
2. Calls bronze_main from the bronze workflow to create the bronze layer


Requirements/Prerequistes
- Install requirements.txt
- Read through the README.md for more information on the project


Author
Elliot Kerr - 03/08/2026

"""
import sqlite3
import logging
import os
from medals.bronze import bronze_main
from medals.silver import silver_main
from medals.gold import gold_main


SCHEMAS = {
    'BRONZE_SCHEMA' : 'bronze', 
    'SILVER_SCHEMA' : 'silver', 
    'GOLD_SCHEMA' : 'gold'
}


def create_dbs(db_name:str) -> None:
    """
    Function opens a connection to a db, which then creates the db if it doesn't already exist, then closes the connection.

    *Postgres: creating the db is not required, although there would need to be a CREATE SCHEMA query executed instead.*

    Args:
    db_name - Name of the database that needs to be created

    Returns:
    No output
    """
    connection = sqlite3.connect(f'./dbs/{db_name}.db')

    connection.close()


def get_logger(logging_type: str) -> logging:
    """
    Function used to create a logger. This is done through the function to allow for improved separation between layers.

    Args:
    logging_type - Name of the logger required i.e. BRONZE, SILVER, ...

    Returns:
    logger - Formatted Logging Instance
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


comp_seasons = [
    [43,106], 
    [43,3]
]


if __name__ == '__main__':
    main_logger = get_logger(" MAIN ")
    
    for schema_names in list(SCHEMAS.values()):

        if f"{schema_names}.db" not in os.listdir("./dbs"):
            main_logger.info(f"Creating database '{schema_names}'")
            create_dbs(schema_names)

    if comp_seasons == []:
        bronze_main(SCHEMAS['BRONZE_SCHEMA'], get_logger("BRONZE"))
    else:
        for competition_id, season_id in comp_seasons:
            bronze_main(SCHEMAS['BRONZE_SCHEMA'], get_logger("BRONZE"), competition_id = competition_id, season_id = season_id)

    silver_main(
        SCHEMAS['SILVER_SCHEMA'], SCHEMAS['BRONZE_SCHEMA'], get_logger("SILVER")
    )

    gold_main(SCHEMAS['SILVER_SCHEMA'], SCHEMAS['GOLD_SCHEMA'], get_logger(" GOLD "))
    