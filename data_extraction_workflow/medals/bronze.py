"""
Bronze Tables Creation ETL

Overview
ETL orchestrates the bronze layer workflows, extracting and loading the competitions, matches and events data from the StatsBombPY package.

Workflow Description
1. Sets up the engine and connections to the bronze database file.
2. Extracts the competitions data from sb.competitions(), filtering for the competition and season ids if they are passed into the function.
3. Adds 2 new fields, data_valid_from_utc and data_valid_to_utc, which are used for SCD tracking.
4. Uses the bronze_competitions function in the Competitions class to transform and append the competitions data into the bronze.competitions table.

5. Using the competitions data, uses the bronze_matches function in the Matches class to complete the same process as for Competitions.
6. bronze_matches also calls bronze_events from the Events class, and the process follows a similar pattern to the others.

7. Closes the db connections to prevent connection issues in the future.


Requirements/Prerequistes
- utils.general, .competitions, .matches and .events
- Install requirements.txt
- Read through the README.md for more information on the project


Author
Elliot Kerr - 05/08/2026

"""
import warnings
from statsbombpy.api_client import NoAuthWarning

# Suppress the NoAuthWarning specifically
warnings.filterwarnings("ignore", category=NoAuthWarning)

from statsbombpy import sb
from datetime import datetime, timedelta, timezone
import logging

from utils.general import create_db_engine_func, DB_ENGINE_STRING
from utils.competitions import Competitions
from utils.matches import Matches
from utils.events import Events

# Class storing the fields and composite key used in the merge procedure.
comp_pyclass = Competitions()
match_pyclass = Matches()
event_pyclass = Events()


def bronze_main(
        brz_schema : str, 
        logger: logging, 
        min_season: str = None,
        competition_id : int = None, 
        season_id : int = None
    ) -> None :
    """
    Function orchestrates the bronze layer, as outlined in the Workflow Description in the file heading.

    Args:
    brz_schema - This is the name of the bronze database, incase another name is preferred for the bronze layer.
    logger - Formatted Logging Instance "BRONZE"

    min_season | None - String that will be used to filter out older seasons with less data included.
    competition_id | None - Exists when specific competitions are required.
    season_id | None - Exists when specific seasons are required.

    Returns:
    No output
    """
    brz_engine = create_db_engine_func(brz_schema, DB_ENGINE_STRING)
    brz_dict = {'schema': brz_schema, 'engine': brz_engine, 'conn': brz_engine.connect()}

    valid_from = datetime.now(timezone.utc).replace(tzinfo=None)
    valid_to = valid_from - timedelta(milliseconds=1)

    competitions = sb.competitions()

    last_edited_where_clause = ""

    if not (competition_id is None or season_id is None):
        competitions = competitions[
            (competitions['competition_id'] == competition_id) & 
            (competitions['season_id'] == season_id)
        ].copy()

        last_edited_where_clause = f'WHERE competition_id = {competition_id} AND season_id = {season_id}'

    elif not competition_id is None:
        competitions = competitions[
            (competitions['competition_id'] == competition_id) &
            (competitions['season_name'] >= min_season)
        ].copy()

        last_edited_where_clause = f'WHERE competition_id = {competition_id}'


    competitions['data_valid_from_utc'] = valid_from
    competitions['data_valid_to_utc'] = None


    competitions_df = comp_pyclass.bronze_competitions(
        brz_dict,
        competitions,
        valid_to,
        last_edited_where_clause,
        logger
    )


    match_pyclass.bronze_matches(
        event_pyclass,
        brz_dict,
        competitions_df,
        valid_from,
        valid_to,
        logger
    )

    brz_dict['conn'].close()
    brz_dict['engine'].dispose()