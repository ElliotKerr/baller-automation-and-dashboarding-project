"""
Events utils

Overview
File consists of any functions, variables and dictionaries that relate to the events table, collected inside a class to allow for simpler uses in the workflows.


Requirements/Prerequistes
- Install requirements.txt


Author
Elliot Kerr - 05/08/2026

"""
from sqlalchemy import String, Integer, DateTime, Date, text, Boolean, JSON, Float
import pandas as pd
from datetime import datetime
import logging
from typing import List
from statsbombpy import sb

from utils.general import col_cleaning

class Events():

    composite_keys = ["id"]

    column_mapping = {
        # Core
        "id": String,
        "period": Integer,
        "timestamp": String,
        "minute": Integer,
        "second": Integer,
        "type": String,

        # Possession
        "possession": Integer,
        "possession_team": String,
        "play_pattern": String,

        # Teams / Players
        "team": String,
        "team_id": Integer,
        "player": String,
        "player_id": Integer,
        "position": String,
        "tactics": JSON,

        # Event descriptors
        "location": JSON,
        "duration": Float,
        "under_pressure": Boolean,
        "off_camera": Boolean,
        "out": Boolean,
        "counterpress": Boolean,

        # Pass
        "pass_recipient": String,
        "pass_recipient_id": Integer,
        "pass_length": Float,
        "pass_angle": Float,
        "pass_height": String,
        "pass_end_location": JSON,
        "pass_body_part": String,
        "pass_type": String,
        "pass_outcome": String,
        "pass_technique": String,
        "pass_switch": Boolean,
        "pass_cross": Boolean,
        "pass_assisted_shot_id": String,
        "pass_shot_assist": Boolean,
        "pass_inswinging": Boolean,
        "pass_outswinging": Boolean,
        "pass_cut_back": Boolean,
        "pass_deflected": Boolean,
        "pass_through_ball": Boolean,

        # Carry
        "carry_end_location": JSON,

        # Shot
        "shot_end_location": JSON,
        "shot_statsbomb_xg": Float,
        "shot_outcome": String,
        "shot_type": String,
        "shot_body_part": String,
        "shot_technique": String,
        "shot_first_time": Boolean,
        "shot_key_pass_id": String,
        "shot_aerial_won": Boolean,
        "shot_freeze_frame": JSON,

        # Goalkeeper
        "goalkeeper_position": String,
        "goalkeeper_type": String,
        "goalkeeper_outcome": String,
        "goalkeeper_body_part": String,
        "goalkeeper_end_location": JSON,
        "goalkeeper_technique": String,

        # Dribble
        "dribble_outcome": String,
        "dribble_overrun": Boolean,
        "dribble_nutmeg": Boolean,

        # Duel
        "duel_type": String,
        "duel_outcome": String,

        # 50/50
        "50_50": JSON,

        # Block
        "block_deflection": Boolean,
        "block_offensive": Boolean,

        # Clearance
        "clearance_head": Boolean,
        "clearance_left_foot": Boolean,
        "clearance_right_foot": Boolean,
        "clearance_body_part": String,
        "clearance_aerial_won": Boolean,

        # Ball Receipt
        "ball_receipt_outcome": String,

        # Ball Recovery
        "ball_recovery_recovery_failure": Boolean,
        "ball_recovery_offensive": Boolean,

        # Fouls
        "foul_committed_type": String,
        "foul_committed_advantage": Boolean,
        "foul_committed_card": String,
        "foul_committed_penalty": Boolean,

        "foul_won_advantage": Boolean,
        "foul_won_defensive": Boolean,

        # Interception
        "interception_outcome": String,

        # Miscontrol
        "miscontrol_aerial_won": Boolean,

        # Injury
        "injury_stoppage_in_chain": Boolean,

        # Substitution
        "substitution_outcome": String,
        "substitution_outcome_id": Integer,
        "substitution_replacement": String,
        "substitution_replacement_id": Integer,

        # Related events
        "related_events": JSON,

        # Metadata
        "match_id": Integer,
        "data_valid_from_utc": DateTime,
        "data_valid_to_utc": DateTime
    }

    def bronze_update_current_historical_records(
            self, 
            brz_dict: dict, 
            id_list: List[str], 
            data_valid_to: datetime
        ):
        """
        Function updates any records in the events table that will have newer records added in the refresh.
        Updates the data_valid_to_utc field from None to the data_valid_to value.

        Args:
        brz_dict - Dictionary that includes the schema name, engine and connection for the bronze database.
        id_list - List
        data_valid_to - Datetime value initialised in the bronze_main function

        Returns:
        No output
        """
        update_dvt_col = f"""
            UPDATE events
            SET data_valid_to_utc = '{data_valid_to}'
            WHERE id IN ({", ".join(f"'{i}'" for i in id_list)})
        """

        brz_dict['conn'].execute(text(update_dvt_col))
        brz_dict['conn'].commit()

    def bronze_events(
            self,
            brz_dict: dict,
            match_id_list: List[str],
            valid_from: datetime,
            valid_to: datetime,
            logger: logging
        ) -> None:
        """
        Function:
            - load the events data and clean
            - updates any records currently in the db for each match
            - appends the new records to the bronze.matches table.

        Args:
        brz_dict - Dictionary that includes the schema name, engine and connection for the bronze database.
        match_id_list - List of match ids that we want to extract events for
        valid_from - Datetime value initialised in the bronze_main function
        valid_to - Datetime value initialised in the bronze_main function
        logger - Formatted Logging Instance "BRONZE"

        Returns:
        No output
        """
        for match_id in match_id_list:
            logger.info(f"Starting Events extraction for match {match_id}")
            events = sb.events(match_id=match_id)

            events['data_valid_from_utc'] = valid_from
            events['data_valid_to_utc'] = None

            base_events = col_cleaning(events, self.column_mapping)  

            base_events['player'] = base_events['player'].apply(lambda x: x.replace("N''", "N'") if isinstance(x, str) else x)

            base_events['pass_recipient'] = base_events['pass_recipient'].apply(lambda x: x.replace("N''", "N'") if isinstance(x, str) else x)

            events_df = base_events.reindex(columns=self.column_mapping.keys())

            if not events_df.empty:
                logger.info(f"Updating any old records that are being updated.")

                id_list = events_df['id'].tolist()
                try:
                    self.bronze_update_current_historical_records(id_list, valid_to, brz_dict)
                except:
                    pass

                logger.info(f"Writing into {brz_dict['schema']}.events")

                events_clean_df = events_df.astype(object).where(pd.notnull(events_df), None)

                events_clean_df.to_sql(
                    'events', 
                    con=brz_dict['conn'], 
                    if_exists='append', 
                    dtype = self.column_mapping, 
                    index = False
                )

                brz_dict['conn'].commit()
    