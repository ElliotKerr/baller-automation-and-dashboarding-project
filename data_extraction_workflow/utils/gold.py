"""
Gold utils

Overview
File consists of any functions, variables and dictionaries that relate to the gold layer, collected inside a class to allow for simpler uses in the workflows.


Requirements/Prerequistes
- Install requirements.txt


Author
Elliot Kerr - 05/08/2026

"""
from sqlalchemy import text
import logging

class Gold():

    COMBINED_PASSES = f"""
        WITH passes AS (
            SELECT 
                *
                ,CASE
                    WHEN home_score = away_score THEN 'Draw'
                    WHEN home_score > away_score THEN home_team
                    ELSE away_team
                END AS winning_team
                ,CASE
                    WHEN home_score = away_score THEN 'Draw'
                    WHEN home_score > away_score THEN home_team_id
                    ELSE away_team_id
                END AS winning_team_id
                ,CASE WHEN period = 1 THEN '1st Half' ELSE '2nd Half' END AS which_half
                ,CASE WHEN pass_outcome IS NULL THEN 'Success' ELSE pass_outcome END AS pass_outcome_complete
                ,CASE 
                    WHEN COS(pass_angle) > 0 THEN 'Forward'
                    WHEN COS(pass_angle) < 0 THEN 'Backward'
                    ELSE 'Lateral'
                END AS pass_direction
                ,CASE 
                    WHEN location LIKE '[%,%]' THEN 
                        CAST(
                            SUBSTR(
                                location, 
                                2, 
                                INSTR(location, ',') - 2
                            ) AS REAL
                        )
                    ELSE NULL
                END AS pass_start_x
                ,CASE                 
                    WHEN location LIKE '[%,%]' THEN 
                        CAST(
                            SUBSTR(
                                location, 
                                INSTR(location, ',') + 2, 
                                LENGTH(location) - INSTR(location, ',') - 2
                            ) AS REAL
                        )
                    ELSE NULL
                END AS pass_start_y
                ,CASE 
                    WHEN pass_end_location IS NULL OR pass_end_location = '' THEN NULL
                    
                    WHEN pass_end_location LIKE '[%,%]' THEN 
                        CAST(
                            SUBSTR(
                                pass_end_location, 
                                2, 
                                INSTR(pass_end_location, ',') - 2
                            ) AS REAL
                        )
                    ELSE NULL
                END AS pass_end_x
                ,CASE 
                    WHEN pass_end_location IS NULL OR pass_end_location = '' THEN NULL
                    WHEN pass_end_location LIKE '[%,%]' THEN 
                        CAST(
                            SUBSTR(
                                pass_end_location, 
                                INSTR(pass_end_location, ',') + 2, 
                                LENGTH(pass_end_location) - INSTR(pass_end_location, ',') - 2
                            ) AS REAL
                        )
                    ELSE NULL
                END AS pass_end_y
            FROM 
                silver.combined
            WHERE 
                LOWER(type) = 'pass'
        )

        SELECT 
            competition_id
            ,season_id
            ,country_name
            ,competition_name
            ,season_name
            ,match_id
            ,match_date
            ,CONCAT(home_team, ' vs ', away_team) AS match_name
            ,kick_off
            ,home_score
            ,away_score
            ,match_week
            ,home_team
            ,away_team
            ,winning_team_id
            ,winning_team
            ,competition_stage
            ,CAST(CASE 
                WHEN LOWER(competition_stage) LIKE 'group%stage' THEN 1
                WHEN LOWER(competition_stage) LIKE 'round%of%128' THEN 2
                WHEN LOWER(competition_stage) LIKE 'round%of%64' THEN 3
                WHEN LOWER(competition_stage) LIKE 'round%of%32' THEN 4
                WHEN LOWER(competition_stage) LIKE 'round%of%16' THEN 5
                WHEN LOWER(competition_stage) LIKE 'quarter%final%' THEN 6
                WHEN LOWER(competition_stage) LIKE 'semi%final%' THEN 7
                WHEN LOWER(competition_stage) LIKE 'final%' THEN 8
                ELSE 9
            END AS INT) AS competition_stage_ranking
            ,id
            ,period
            ,which_half
            ,timestamp
            ,minute
            ,second
            ,type
            ,possession
            ,possession_team
            ,play_pattern
            ,team
            ,team_id
            ,CAST(CASE 
                WHEN team_id = winning_team_id THEN 1
                ELSE 0
            END AS INT) AS part_of_winning_team
            ,player
            ,player_id
            ,position
            ,location
            ,duration
            ,CAST(CASE WHEN under_pressure = 1 THEN 1 ELSE 0 END AS INT) AS under_pressure
            ,CAST(CASE WHEN off_camera = 1 THEN 1 ELSE 0 END AS INT) AS off_camera
            ,CAST(CASE WHEN out = 1 THEN 1 ELSE 0 END AS INT) AS out
            ,CAST(CASE WHEN counterpress = 1 THEN 1 ELSE 0 END AS INT) AS counterpress
            ,pass_recipient
            ,pass_recipient_id
            ,pass_length
            ,pass_angle
            ,pass_direction
            ,pass_height
            ,pass_end_location
            ,pass_start_x
            ,pass_start_y
            ,pass_end_x
            ,pass_end_y
            ,CASE 
                WHEN pass_end_x >= 80 THEN 'Final 3rd'
                WHEN pass_end_x >= 40 THEN 'Middle 3rd'
                WHEN pass_end_x >= 0 THEN 'Defensive 3rd'
                ELSE pass_end_x
            END AS pass_end_sector
            ,CASE 
                WHEN pass_end_x >= 80 THEN 1
                WHEN pass_end_x >= 40 THEN 2
                WHEN pass_end_x >= 0 THEN 3
                ELSE pass_end_x
            END AS pass_end_sector_rank
            ,pass_body_part
            ,pass_type
            ,pass_outcome_complete AS pass_outcome
            ,pass_technique
            ,CAST(CASE WHEN pass_switch = 1 THEN 1 ELSE 0 END AS INT) AS pass_switch
            ,CAST(CASE WHEN pass_cross = 1 THEN 1 ELSE 0 END AS INT) AS pass_cross
            ,pass_assisted_shot_id
            ,CAST(CASE WHEN pass_shot_assist = 1 THEN 1 ELSE 0 END AS INT) AS pass_shot_assist
            ,CAST(CASE WHEN pass_inswinging = 1 THEN 1 ELSE 0 END AS INT) AS pass_inswinging
            ,CAST(CASE WHEN pass_outswinging = 1 THEN 1 ELSE 0 END AS INT) AS pass_outswinging
            ,CAST(CASE WHEN pass_cut_back = 1 THEN 1 ELSE 0 END AS INT) AS pass_cut_back
            ,CAST(CASE WHEN pass_deflected = 1 THEN 1 ELSE 0 END AS INT) AS pass_deflected
            ,CAST(CASE WHEN pass_through_ball = 1 THEN 1 ELSE 0 END AS INT) AS pass_through_ball
        FROM 
            passes
    """

    def create_gold(
            self, 
            gld_dict: dict, 
            query: str, 
            table_name: str, 
            logger: logging
        ):
        """
        Function creates the silver table for the specified table name by only selecting records with data_valid_to_utc NULL.
        Each time this is ran, the table is dropped and replaced to prevent possible overwriting issues.

        Args:
        slv_dict - Dictionary that includes the schema name, engine and connection for the silver database.
        table_name - Name of the table to create in the silver database
        logger - Formatted Logging Instance "SILVER"

        Returns:
        No Output
        """
        try:
            gld_dict['conn'].execute(text(f"DROP TABLE main.{table_name}"))
        except:
            pass

        logger.info(f'Creating the gold.{table_name} table!')
        gld_dict['conn'].execute(text(f"CREATE TABLE main.{table_name} AS {query}"))

        gld_dict['conn'].commit()