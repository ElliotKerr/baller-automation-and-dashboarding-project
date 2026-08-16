"""
Silver utils

Overview
File consists of any functions, variables and dictionaries that relate to the silver layer, collected inside a class to allow for simpler uses in the workflows.


Requirements/Prerequistes
- Install requirements.txt


Author
Elliot Kerr - 05/08/2026

"""
from sqlalchemy import String, Integer, DateTime, Date, text, Boolean, JSON, Float
import numpy as np
from statsbombpy import sb
import pandas as pd
import logging

class Silver():

    combined_column_mapping = {
        "competitions": {
            "competition_id": Integer,
            "season_id": Integer,
            "country_name": String,
            "competition_name": String,
            "competition_gender": String,
            "competition_youth": Boolean,
            "competition_international": Boolean,
            "season_name": String
        },

        "matches": {
            'match_id': Integer, 
            'match_date': Date, 
            'kick_off': String, 
            'home_score': Integer, 
            'away_score': Integer,
            'match_status': String, 
            'match_week': Integer, 
            'match_name': String,
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
            'winning_team': String,
            'winning_team_id': Integer,
            'competition_stage_id': Integer, 
            'competition_stage': String, 
            'fixed_competition_stage': String,
            'competition_stage_ranking': Integer,
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
            'penalty_shootout': Integer,
            'home_pen_score': Integer,
            'away_pen_score': Integer
        },

        "events" : {
            ## Core
            "id": String,
            "period": Integer,
            "timestamp": String,
            "minute": Integer,
            "second": Integer,
            "type": String,

            ## Possession
            "possession": Integer,
            "possession_team": String,
            "play_pattern": String,

            ## Teams / Players
            "team": String,
            "team_id": Integer,
            "player": String,
            "player_id": Integer,
            "position": String,
            "tactics": JSON,

            ## Event descriptors
            "location": JSON,
            "duration": Float,
            "under_pressure": Boolean,
            "off_camera": Boolean,
            "out": Boolean,
            "counterpress": Boolean,

            ## Pass
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

            ## Carry
            "carry_end_location": JSON,

            ## Shot
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

            ## Goalkeeper
            "goalkeeper_position": String,
            "goalkeeper_type": String,
            "goalkeeper_outcome": String,
            "goalkeeper_body_part": String,
            "goalkeeper_end_location": JSON,
            "goalkeeper_technique": String,

            ## Dribble
            "dribble_outcome": String,
            "dribble_overrun": Boolean,
            "dribble_nutmeg": Boolean,

            ## Duel
            "duel_type": String,
            "duel_outcome": String,

            ## 50/50
            "50_50": JSON,

            ## Block
            "block_deflection": Boolean,
            "block_offensive": Boolean,

            ## Clearance
            "clearance_head": Boolean,
            "clearance_left_foot": Boolean,
            "clearance_right_foot": Boolean,
            "clearance_body_part": String,
            "clearance_aerial_won": Boolean,

            ## Ball Receipt
            "ball_receipt_outcome": String,

            ## Ball Recovery
            "ball_recovery_recovery_failure": Boolean,
            "ball_recovery_offensive": Boolean,

            ## Fouls
            "foul_committed_type": String,
            "foul_committed_advantage": Boolean,
            "foul_committed_card": String,
            "foul_committed_penalty": Boolean,

            "foul_won_advantage": Boolean,
            "foul_won_defensive": Boolean,

            ## Interception
            "interception_outcome": String,

            ## Miscontrol
            "miscontrol_aerial_won": Boolean,

            ## Injury
            "injury_stoppage_in_chain": Boolean,

            ## Substitution
            "substitution_outcome": String,
            "substitution_outcome_id": Integer,
            "substitution_replacement": String,
            "substitution_replacement_id": Integer,

            ## Related events
            "related_events": JSON
        }
    }

    def update_penalty_shootout_result(self, slv_dict: dict, logger: logging):
        """
        Function updates any records in the matches table that have gone to a penalty shootout, as matches doesn't show the penalty shootout winner.

        Args:
        df - The matches dataframe.

        Returns:
        df - The updated version of the matches df with penalty shootouts decided.
        """

        draws = pd.read_sql_query('SELECT match_id, home_team, away_team FROM matches WHERE competition_stage_ranking > 1 AND winning_team = "Draw"', slv_dict['conn'])

        match_ids = draws['match_id'].to_list()

        for m_id in match_ids:
            events = sb.events(match_id=m_id)

            # Filter for Period 5 (Penalty Shootouts) and successful goals
            shootout_goals = events[
                (events["period"] == 5)
                & (events["type"] == "Shot")
                & (events["shot_outcome"] == "Goal")
            ]

            # If period 5 exists and has goals, we have a shootout winner!
            if not shootout_goals.empty:
                # Get home and away team names for this match
                match_row = draws[draws["match_id"] == m_id].iloc[0]
                home_team = match_row["home_team"]
                away_team = match_row["away_team"]

                # Count shootout goals per team
                goal_counts = shootout_goals["team"].value_counts()
                home_pen_score = goal_counts.get(home_team, 0)
                away_pen_score = goal_counts.get(away_team, 0)

                # Determine winner
                if home_pen_score > away_pen_score:
                    winner_name = home_team
                else:
                    winner_name = away_team

                # Extract winning team_id
                winner_id = shootout_goals[shootout_goals["team"] == winner_name][
                    "team_id"
                ].iloc[0]

                update_query = f"""
                    UPDATE matches
                    SET penalty_shootout = 1,
                        winning_team = '{winner_name}',
                        winning_team_id = {winner_id},
                        home_pen_score = {home_pen_score},
                        away_pen_score = {away_pen_score}
                    WHERE 
                        match_id = {m_id}
                """

                slv_dict['conn'].execute(text(update_query))
                slv_dict['conn'].commit()


    def clean_bronze_tables(
            self, 
            slv_dict:dict, 
            table_name:str, 
            logger:logging,
            added_fields:str = ""
        ) -> None:
        """
        Function creates the silver table for the specified table name by only selecting records with data_valid_to_utc NULL.
        Each time this is ran, the table is dropped and replaced to prevent possible overwriting issues.

        Args:
        slv_dict - Dictionary that includes the schema name, engine and connection for the silver database.
        table_name - Name of the table to create in the silver database
        logger - Formatted Logging Instance "SILVER"
        added_fields | "" - When a table needs fields to be created, this can be done through the added fields parameter.

        Returns:
        No Output
        """
        query = f"""
            SELECT 
                *
                {added_fields}
            FROM 
                bronze.{table_name}
            WHERE 
                data_valid_to_utc IS NULL    
        """
        try:
            slv_dict['conn'].execute(text(f"DROP TABLE main.{table_name}"))
        except:
            pass
        
        slv_dict['conn'].execute(text(f"CREATE TABLE main.{table_name} AS {query}"))

        slv_dict['conn'].commit()

        logger.info(f"Created silver.{table_name} using the cleaned version of bronze.{table_name}")


    def create_combined_table(self, slv_dict, logger):
        """
        Doc String
        """
        alias_mapping = {
            'competitions': 'c', 
            'matches': 'm', 
            'events': 'e'
        }

        select_columns = ""

        for table, column_mapping in self.combined_column_mapping.items():
            alias = alias_mapping[table]

            select_columns += ', '.join(f'{alias}."{c}"' for c in list(column_mapping.keys())) + ", "


        select_columns_final = select_columns[:-2]

        combined_query = f"""
            SELECT 
                {select_columns_final}
            FROM 
                competitions c
            
            LEFT JOIN matches m
            ON c.competition_id = m.competition_id
            AND c.season_id = m.season_id
            
            LEFT JOIN events e
            ON e.match_id = m.match_id
        """

        try:
            slv_dict['conn'].execute(text(f"DROP TABLE combined"))
        except:
            pass
        
        slv_dict['conn'].execute(text(f"CREATE TABLE combined AS {combined_query}"))

        slv_dict['conn'].commit()

        logger.info(f"Created silver.combined using the cleaned silver tables!")



    