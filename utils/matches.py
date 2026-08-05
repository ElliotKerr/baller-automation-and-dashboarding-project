"""
Script Doc String

Overview


Workflow Description



Requirements/Prerequistes




Author

"""

from sqlalchemy import String, Integer, DateTime, Date, text
import pandas as pd

class Matches():

    composite_keys = ['match_id']

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
        'xy_fidelity_version': String,
        "data_valid_from_utc": DateTime,
        "data_valid_to_utc": DateTime
    }

    def bronze_update_current_historical_records(self, match_id_list, data_valid_to, brz_dict):
        """
        Doc String
        """

        update_dvt_col_full = f"""
            UPDATE matches
            SET data_valid_to_utc = '{data_valid_to}'
            WHERE match_id IN ({", ".join(f"'{i}'" for i in match_id_list)})
        """


        brz_dict['conn'].execute(text(update_dvt_col_full))
        brz_dict['conn'].commit()


    def bronze_matches(
            self,
            sb,
            event_pyclass,
            brz_dict,
            col_cleaning,
            competitions_df,
            valid_from,
            valid_to,
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

        for competition_id, season_id in comp_id_season_id_list:

            matches = sb.matches(competition_id=competition_id, season_id=season_id)

            matches['data_valid_from_utc'] = valid_from
            matches['data_valid_to_utc'] = None

            base_matches = col_cleaning(matches, self.column_mapping)    

            try:
                match_last_updated_raw = pd.read_sql_query(f'''
                    SELECT 
                        COALESCE(MAX(last_updated),NULL) AS last_updated 
                    FROM 
                        matches 
                    WHERE 
                        competition_id = {competition_id} 
                    AND 
                        season_id = {season_id}
                ''', brz_dict['conn'])['last_updated'][0]

                match_last_updated = pd.to_datetime(match_last_updated_raw) if pd.notnull(match_last_updated_raw) else None
            except:
                match_last_updated = None
            
            if match_last_updated is None:
                matches_df = base_matches
            else:
                matches_df = base_matches[base_matches['last_updated'] > match_last_updated]

            comp_season_match_tuple = []
            
            if not matches_df.empty:
                logger.info(f"Updating any old records that are being updated.")

                match_id_list = matches_df['match_id'].tolist()

                try:
                    self.bronze_update_current_historical_records(match_id_list, valid_to, brz_dict)
                except:
                    pass


                logger.info(f"Appending {len(matches_df)} new row(s) to bronze.matches...")

                matches_clean_df = matches_df.astype(object).where(pd.notnull(matches_df), None)

                matches_clean_df.to_sql(
                    'matches', 
                    con=brz_dict['conn'],
                    if_exists='append', 
                    dtype=self.column_mapping, 
                    index=False
                )
                brz_dict['conn'].commit()
            else:
                logger.info("No new records found (incoming match_updated is not newer than DB).")


            if match_id_list != []:
                event_pyclass.bronze_events(
                    sb,
                    brz_dict,
                    match_id_list,
                    col_cleaning,
                    valid_from,
                    valid_to,
                    logger
                )