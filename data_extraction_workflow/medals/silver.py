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
import warnings
from statsbombpy.api_client import NoAuthWarning

# Suppress the NoAuthWarning specifically
warnings.filterwarnings("ignore", category=NoAuthWarning)

from sqlalchemy import text
import logging
from utils.general import create_db_engine_func, DB_ENGINE_STRING

from utils.competitions import Competitions
from utils.matches import Matches
from utils.events import Events
from utils.silver import Silver

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

    matches_additional_query = f"""
        ,CONCAT(home_team, ' vs ', away_team) AS match_name
        ,CASE
            WHEN home_score = away_score THEN 'Draw'
            WHEN home_score > away_score THEN home_team
            ELSE away_team
        END AS winning_team
        ,CASE
            WHEN home_score = away_score THEN -1
            WHEN home_score > away_score THEN home_team_id
            ELSE away_team_id
        END AS winning_team_id
        ,CAST(CASE 
            WHEN LOWER(competition_stage) LIKE '%regular%season%' 
            OR LOWER(competition_stage) LIKE '%league%' THEN 0

            WHEN LOWER(competition_stage) LIKE '%group%' THEN 1

            WHEN LOWER(competition_stage) LIKE '%play-in%' 
            OR LOWER(competition_stage) LIKE '%qualif%' THEN 2

            WHEN LOWER(competition_stage) LIKE '%128%' 
            OR LOWER(competition_stage) LIKE '%1st%round%' 
            OR LOWER(competition_stage) LIKE '%2nd%round%' THEN 3

            WHEN LOWER(competition_stage) LIKE '%64%' 
            OR LOWER(competition_stage) LIKE '%32nd%final%' 
            OR LOWER(competition_stage) LIKE '%3rd%round%' 
            OR LOWER(competition_stage) LIKE '%4th%round%' THEN 4

            WHEN LOWER(competition_stage) LIKE '%32%' 
            OR LOWER(competition_stage) LIKE '%16th%final%' THEN 5

            WHEN LOWER(competition_stage) LIKE '%16%' 
            OR LOWER(competition_stage) LIKE '%8th%final%' THEN 6

            WHEN LOWER(competition_stage) LIKE '%quarter%' 
            OR LOWER(competition_stage) LIKE '%qtr%' THEN 7

            WHEN LOWER(competition_stage) LIKE '%semi%' THEN 8

            WHEN LOWER(competition_stage) LIKE '%3rd%' 
            OR LOWER(competition_stage) LIKE '%third%' THEN 9

            WHEN LOWER(competition_stage) LIKE '%final%' THEN 10

            ELSE 99
        END AS INT) AS competition_stage_ranking
        ,0 AS penalty_shootout
        ,0 AS home_pen_score
        ,0 AS away_pen_score
    """

    silver_pyclass.clean_bronze_tables(slv_dict, 'matches', logger, matches_additional_query)
    silver_pyclass.update_penalty_shootout_result(slv_dict)


    silver_pyclass.clean_bronze_tables(slv_dict, 'events', logger)


    slv_dict['conn'].execute(text("DETACH DATABASE bronze"))
    slv_dict['conn'].commit()


    silver_pyclass.create_combined_table(slv_dict, logger)


    slv_dict['conn'].close()
    slv_dict['engine'].dispose()