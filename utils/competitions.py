"""
Script Doc String

Overview


Workflow Description



Requirements/Prerequistes




Author

"""


from sqlalchemy import String, Integer, DateTime, Boolean, text
import pandas as pd

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


    def etl_competitions(
            self, 
            brz_dict, 
            comp_class, 
            base_competitions,
            col_cleaner_function,
            data_valid_to,
            logger
        ):
        """
        Doc String
        """

        base_competitions = col_cleaner_function(base_competitions, comp_class.column_mapping)

        last_updated = None
        table_exists = True

        try:
            last_updated_raw = pd.read_sql_query(f'''
                SELECT 
                    COALESCE(MAX(match_updated),NULL) AS last_updated 
                FROM    
                    competitions
            ''', brz_dict['conn'])['last_updated'][0]

            last_updated = pd.to_datetime(last_updated_raw) if pd.notnull(last_updated_raw) else None
        except:
            table_exists = False

        logger.info(f"Last Updated: {last_updated}")

        if last_updated is None:
            competitions_df = base_competitions
        else:
            competitions_df = base_competitions[base_competitions['match_updated'] > last_updated]


        if not competitions_df.empty:
            logger.info(f"Updating any old records that are being updated.")
            ## Create the update process here:
            comp_season_tuple = list(zip(*[competitions_df[c] for c in ['competition_id', 'season_id']]))

            update_dvt_col = f"""
                UPDATE competitions
                SET data_valid_to_utc = '{data_valid_to}'
                WHERE {{where_clause}}
            """

            where_clause = ""

            for comp_id, season_id in comp_season_tuple:
                where_clause += f'((competition_id = {comp_id}) AND (season_id = {season_id})) OR '

            update_dvt_col_full = update_dvt_col.format(where_clause = where_clause[:-4])

            logger.info(update_dvt_col_full)

            brz_dict['conn'].execute(text(update_dvt_col_full))
            brz_dict['conn'].commit()

            logger.info(f"Appending {len(competitions_df)} new row(s) to Bronze...")
            competitions_df.to_sql(
                'competitions', 
                con=brz_dict['conn'],
                if_exists='append', 
                dtype=comp_class.column_mapping, 
                index=False
            )
            brz_dict['conn'].commit()
        else:
            logger.info("No new records found (incoming match_updated is not newer than DB).")

        return competitions_df