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

    def etl_competitions(self, connection, cursor, engine, _merge, comp_class, competitions):
        """
        
        """
        for col in comp_class.date_columns:
            if col in competitions.columns:
                competitions[col] = pd.to_datetime(competitions[col], format="ISO8601")

        try:
            last_updated = pd.read_sql_query('SELECT COALESCE(MAX(match_updated),NULL) as last_updated FROM competitions', connection)['last_updated'][0]
        except:
            last_updated = None

        if last_updated is None:
            competitions_df = competitions
        else:
            competitions_df = competitions[competitions['match_updated'] > last_updated]

        print(f"Writing competitions into the staging table!")

        competitions_df.to_sql('staging_competitions', con=engine, if_exists='replace', dtype = comp_class.column_mapping, index = False)

        print(f"Merging staging_competitions into competitions")

        _merge(cursor, connection, comp_class, 'competitions')
    
        return competitions_df