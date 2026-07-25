"""
Script Doc String

Overview


Workflow Description



Requirements/Prerequistes




Author

"""


from sqlalchemy import String, Integer, DateTime
import pandas as pd

class Competitions():

    composite_keys = ["competition_id", "season_id"]

    column_mapping = {
        "competition_id": Integer,
        "season_id": Integer,
        "country_name": String,
        "competition_name": String,
        "competition_gender": String,
        "competition_youth": String,
        "competition_international": String,
        "season_name": String,
        "match_updated": DateTime,
        "match_updated_360": DateTime,
        "match_available_360": DateTime,
        "match_available": DateTime,
    }

    date_columns = ['match_updated', 'match_updated_360', 'match_available_360', 'match_available']

    def etl_competitions(
            self, 
            staging_engine, 
            stg_schema,
            brz_connection, 
            brz_cursor, 
            _merge, 
            comp_class, 
            base_competitions,
            logger
        ):
        """
        Doc String
        """
        for col in comp_class.date_columns:
            if col in base_competitions.columns:
                base_competitions[col] = pd.to_datetime(base_competitions[col], format="ISO8601")

        try:
            last_updated = pd.read_sql_query(f'''
                SELECT 
                    COALESCE(MAX(match_updated),NULL) AS last_updated 
                FROM    
                    competitions
            ''', brz_connection)['last_updated'][0]
        except:
            last_updated = None

        if last_updated is None:
            competitions_df = base_competitions
        else:
            competitions_df = base_competitions[base_competitions['match_updated'] > last_updated]

        logger.info(f"Writing competitions into the staging table!")

        competitions_df.to_sql(
            'competitions', 
            con=staging_engine, 
            if_exists='replace', 
            dtype = comp_class.column_mapping, 
            index = False
        )

        logger.info(f"Merging {stg_schema}.competitions into competitions")

        _merge(stg_schema, brz_cursor, brz_connection, comp_class, 'competitions')
    
        return competitions_df