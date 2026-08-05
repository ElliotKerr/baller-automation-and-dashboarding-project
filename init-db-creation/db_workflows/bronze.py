"""
Bronze Tables Creation ETL

Overview


Workflow Description
1. Extracts the competitions data from sb.competitions(), filtering specifically for competition_id = 43 and season_id = 106
2. Creates a new dataframe for records that have a match_updated greater than the max value in bronze.competitions


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
from sqlalchemy import create_engine
from datetime import datetime, timedelta, timezone

from utils.general import create_db_engine_func, DB_ENGINE_STRING, col_cleaning
from utils.competitions import Competitions
from utils.matches import Matches
from utils.events import Events

# Class storing the fields and composite key used in the merge procedure.
comp_pyclass = Competitions()
match_pyclass = Matches()
event_pyclass = Events()


def bronze_main(
        brz_schema : str, 
        logger, 
        competition_id : int = None, 
        season_id : int = None
    ):
    """
    Doc String
    """
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


    competitions_df = comp_pyclass.bronze_competitions(
        brz_dict,
        competitions,
        col_cleaning,
        valid_to,
        logger
    )


    match_pyclass.bronze_matches(
        sb,
        event_pyclass,
        brz_dict,
        col_cleaning,
        competitions_df,
        valid_from,
        valid_to,
        logger
    )

    brz_dict['conn'].close()
    brz_dict['engine'].dispose()