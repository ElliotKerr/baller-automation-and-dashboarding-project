"""
Competitions utils

Overview
File consists of any functions, variables and dictionaries that relate to the competitions table, collected inside a class to allow for simpler uses in the workflows.


Requirements/Prerequistes
- Install requirements.txt


Author
Elliot Kerr - 05/08/2026

"""
from sqlalchemy import String, Integer, DateTime, Boolean, text
import pandas as pd
from datetime import datetime
import logging

from utils.general import col_cleaning

class Competitions():

    composite_keys = ["competition_id", "season_id"]

    column_mapping = {
        "competition_id": Integer,
        "season_id": Integer,
        "country_name": String,
        "competition_name": String,
        "competition_gender": String,
        "competition_youth": Boolean,
        "competition_international": Boolean,
        "season_name": String,
        "match_updated": DateTime,
        "match_updated_360": DateTime,
        "match_available_360": DateTime,
        "match_available": DateTime,
        "data_valid_from_utc": DateTime,
        "data_valid_to_utc": DateTime,
    }

    def bronze_update_current_historical_records(
            self, 
            brz_dict: dict,
            competitions_df: pd.DataFrame, 
            data_valid_to: datetime, 
        ) -> None:
        """
        Function updates any records in the competitions table that will have newer records added in the refresh.
        Updates the data_valid_to_utc field from None to the data_valid_to value.

        Args:
        brz_dict - Dictionary that includes the schema name, engine and connection for the bronze database.
        competitions_df - Dataframe containing the records that need to be updated.
        data_valid_to - Datetime value initialised in the bronze_main function

        Returns:
        No output
        """
        comp_season_tuple = list(zip(*[competitions_df[c] for c in self.composite_keys]))

        update_dvt_col = f"""
            UPDATE competitions
            SET data_valid_to_utc = '{data_valid_to}'
            WHERE {{where_clause}}
        """

        where_clause = ""

        for comp_id, season_id in comp_season_tuple:
            where_clause += f'((competition_id = {comp_id}) AND (season_id = {season_id})) OR '

        update_dvt_col_full = update_dvt_col.format(where_clause = where_clause[:-4])


        brz_dict['conn'].execute(text(update_dvt_col_full))
        brz_dict['conn'].commit()


    def bronze_competitions(
            self, 
            brz_dict: dict, 
            base_competitions: pd.DataFrame,
            data_valid_to: datetime,
            logger: logging
        ) -> pd.DataFrame:
        """
        Function:
            - transforms the competitions data that has been loaded from the package
            - filters for newly updated records
            - updates any old records that are due to be updated
            - appends the new records to the bronze.competitions table.

        Args:
        brz_dict - Dictionary that includes the schema name, engine and connection for the bronze database.
        base_competitions - Dataframe from sb.competitions().
        data_valid_to - Datetime value initialised in the bronze_main function
        logger - Formatted Logging Instance "BRONZE"

        Returns:
        competitions_df - Returns the competitions to use in the matches function, which will ensure all competitions and seasons are loaded.
        """
        base_competitions = col_cleaning(base_competitions, self.column_mapping)

        last_updated = None

        try:
            last_updated_raw = pd.read_sql_query(f'''
                SELECT 
                    COALESCE(MAX(match_updated),NULL) AS last_updated
                FROM    
                    competitions
            ''', brz_dict['conn'])['last_updated'][0]

            last_updated = pd.to_datetime(last_updated_raw) if pd.notnull(last_updated_raw) else None
        except:
            pass

        logger.info(f"Last Updated: {last_updated}")

        if last_updated is None:
            competitions_df = base_competitions
        else:
            competitions_df = base_competitions[base_competitions['match_updated'] > last_updated]


        if not competitions_df.empty:
            logger.info(f"Updating any old records that are being updated.")
            try:
                self.bronze_update_current_historical_records(brz_dict, competitions_df, data_valid_to)
            except:
                pass

            logger.info(f"Appending {len(competitions_df)} new row(s) to bronze.competitions...")

            competitions_clean_df = competitions_df.astype(object).where(pd.notnull(competitions_df), None)

            competitions_clean_df.to_sql(
                'competitions', 
                con=brz_dict['conn'],
                if_exists='append', 
                dtype=self.column_mapping, 
                index=False
            )
            brz_dict['conn'].commit()
        else:
            logger.info("No new records found (incoming match_updated is not newer than DB).")

        return competitions_df