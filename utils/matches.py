"""
Script Doc String

Overview


Workflow Description



Requirements/Prerequistes




Author

"""

from sqlalchemy import String, Integer, DateTime, Date
import pandas as pd

class Matches():

    composite_keys = ["competition_id", "season_id", 'match_id']

    column_mapping = {
        'match_id': Integer, 
        'match_date': Date, 
        'kick_off': String, 
        'home_score': Integer, 
        'away_score': Integer,
        'match_status': String, 
        'match_status_360': String, 
        'last_updated': DateTime, 
        'last_updated_360': DateTime,
        'match_week': Integer, 
        'competition_id': Integer, 
        'competition_country_name': String,
        'competition_name': String, 
        'competition': String, 
        'season_id': Integer, 
        'season': String,
        'home_team_id': Integer, 
        'home_team': String, 
        'home_team_gender': String, 
        'home_team_group': String,
        'home_team_country_id': Integer, 
        'home_team_country_name': String, 
        'away_team_id': Integer,
        'away_team': String, 
        'away_team_gender': String, 
        'away_team_group': String,
        'away_team_country_id': Integer, 
        'away_team_country_name': String,
        'competition_stage_id': Integer, 
        'competition_stage': String, 
        'stadium_id': Integer, 
        'stadium': String,
        'stadium_country_id': Integer, 
        'stadium_country_name': String, 
        'referee_id': Integer, 
        'referee': String,
        'referee_country_id': Integer, 
        'referee_country_name': String, 
        'home_managers': String,
        'away_managers': String, 
        'home_manager_id': Integer, 
        'home_manager_name': String,
        'home_manager_nickname': String, 
        'home_manager_dob': Date, 
        'home_manager_country_id': String,
        'home_manager_country_name': String, 
        'away_manager_id': Integer, 
        'away_manager_name': String,
        'away_manager_nickname': String, 
        'away_manager_dob': Date, 
        'away_manager_country_id': String,
        'away_manager_country_name': String, 
        'data_version': String, 
        'shot_fidelity_version': String,
        'xy_fidelity_version': String
    }

    date_columns = ['last_updated', 'last_updated_360', 'match_date', 'home_manager_dob', 'away_manager_dob']

    def etl_matches(
            self,
            sb,
            event_class,
            stg_engine, 
            stg_schema,
            brz_connection, 
            brz_cursor, 
            _merge, 
            match_class, 
            competitions_df,
            logger
        ):
        """
        Doc String
        """
        comp_id_season_id_df = competitions_df[['competition_id', 'season_id']]

        comp_id_season_id_dict = comp_id_season_id_df.to_dict()

        comp_id_season_id_list = [
            [
                comp_id_season_id_dict['competition_id'][i], 
                comp_id_season_id_dict['season_id'][i]
            ] for i in list(comp_id_season_id_dict['competition_id'].keys())]

        for _array in comp_id_season_id_list:
            competition_id = _array[0]
            season_id = _array[1]

            matches = sb.matches(competition_id=competition_id, season_id=season_id)

            for col in match_class.date_columns:
                if col in matches.columns:
                    matches[col] = pd.to_datetime(matches[col], format="ISO8601")        

            try:
                match_last_updated = pd.read_sql_query(f'''
                    SELECT 
                        COALESCE(MAX(last_updated),NULL) AS last_updated 
                    FROM 
                        matches 
                    WHERE 
                        competition_id = {competition_id} 
                    AND 
                        season_id = {season_id}
                ''', brz_connection)['last_updated'][0]
            except:
                match_last_updated = None
            
            if match_last_updated is None:
                matches_df = matches
            else:
                matches_df = matches[matches['last_updated'] > match_last_updated]

            logger.info(f"Writing matches for competition-season {competition_id}-{season_id} into {stg_schema}.matches.")

            matches_df.to_sql(
                'matches', 
                con=stg_engine, 
                if_exists='append', 
                dtype = match_class.column_mapping, 
                index = False
            )

            event_class.etl_events(
                sb,
                stg_engine, 
                stg_schema,
                brz_connection, 
                brz_cursor, 
                _merge, 
                event_class, 
                matches_df,
                competition_id,
                season_id,
                logger
            )

        logger.info(f"Merging all matches into bronze.matches.")

        _merge(stg_schema, brz_cursor, brz_connection, match_class, 'matches')