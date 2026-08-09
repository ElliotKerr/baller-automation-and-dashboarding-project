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
                comb.*
                ,CASE WHEN comb.period = 1 THEN '1st Half' ELSE '2nd Half' END AS which_half
                ,CASE WHEN comb.pass_outcome IS NULL THEN 'Success' ELSE comb.pass_outcome END AS pass_outcome_complete
                ,CASE 
                    WHEN COS(comb.pass_angle) > 0 THEN 'Forward'
                    WHEN COS(comb.pass_angle) < 0 THEN 'Backward'
                    ELSE 'Lateral'
                END AS pass_direction
                ,CASE 
                    WHEN comb.location LIKE '[%,%]' THEN 
                        CAST(
                            SUBSTR(
                                comb.location, 
                                2, 
                                INSTR(comb.location, ',') - 2
                            ) AS REAL
                        )
                    ELSE NULL
                END AS pass_start_x
                ,CASE                 
                    WHEN comb.location LIKE '[%,%]' THEN 
                        CAST(
                            SUBSTR(
                                comb.location, 
                                INSTR(comb.location, ',') + 2, 
                                LENGTH(comb.location) - INSTR(comb.location, ',') - 2
                            ) AS REAL
                        )
                    ELSE NULL
                END AS pass_start_y
                ,CASE 
                    WHEN comb.pass_end_location IS NULL OR comb.pass_end_location = '' THEN NULL
                    
                    WHEN comb.pass_end_location LIKE '[%,%]' THEN 
                        CAST(
                            SUBSTR(
                                comb.pass_end_location, 
                                2, 
                                INSTR(comb.pass_end_location, ',') - 2
                            ) AS REAL
                        )
                    ELSE NULL
                END AS pass_end_x
                ,CASE 
                    WHEN comb.pass_end_location IS NULL OR comb.pass_end_location = '' THEN NULL
                    WHEN comb.pass_end_location LIKE '[%,%]' THEN 
                        CAST(
                            SUBSTR(
                                comb.pass_end_location, 
                                INSTR(comb.pass_end_location, ',') + 2, 
                                LENGTH(comb.pass_end_location) - INSTR(comb.pass_end_location, ',') - 2
                            ) AS REAL
                        )
                    ELSE NULL
                END AS pass_end_y
                ,cr.matches_played
                ,cr.wins
                ,cr.draw
                ,cr.losses
                ,cr.stage_reached
            FROM 
                silver.combined comb

            LEFT JOIN main.combined_results cr
            ON comb.competition_id = cr.competition_id
            AND comb.season_id = cr.season_id
            AND comb.team_id = cr.team_id

            WHERE 
                LOWER(type) = 'pass'
        )

        SELECT 
            CONCAT(competition_id, '-', season_id, '-', team_id) AS cst_composite_id
            ,CONCAT(competition_id, '-', season_id, '-', match_id) AS csm_composite_id
            ,competition_id
            ,season_id
            ,country_name
            ,competition_name
            ,season_name
            ,CONCAT(competition_name, ' ', season_name) AS competition
            ,match_id
            ,match_date
            ,match_name
            ,kick_off
            ,home_score
            ,away_score
            ,penalty_shootout
            ,home_pen_score
            ,away_pen_score
            ,match_week
            ,home_team
            ,away_team
            ,winning_team_id
            ,winning_team
            ,competition_stage
            ,competition_stage_ranking
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
            ,matches_played
            ,wins
            ,draw
            ,losses
            ,stage_reached
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

    COMBINED_MATCHES = f"""
        SELECT 
            CONCAT(competition_id, '-', season_id, '-', match_id) AS csm_composite_id
            ,competition_id
            ,season_id
            ,country_name
            ,competition_name
            ,season_name
            ,CONCAT(competition_name, ' ', season_name) AS competition
            ,match_id
            ,match_date
            ,match_name
            ,kick_off
            ,home_score
            ,away_score
            ,match_week
            ,home_team
            ,home_team_id
            ,away_team
            ,away_team_id
            ,winning_team
            ,winning_team_id
            ,competition_stage
            ,competition_stage_ranking
            ,penalty_shootout
            ,home_pen_score
            ,away_pen_score
        FROM 
            silver.combined
        GROUP BY 
            competition_id
            ,season_id
            ,country_name
            ,competition_name
            ,season_name
            ,match_id
            ,match_date
            ,match_name
            ,kick_off
            ,home_score
            ,away_score
            ,match_week
            ,home_team
            ,away_team
            ,winning_team
            ,winning_team_id
            ,competition_stage
            ,competition_stage_ranking
            ,penalty_shootout
            ,home_pen_score
            ,away_pen_score
    """

    COMBINED_RESULTS = f"""
        WITH matches_cte AS (
            SELECT 
                competition_id
                ,season_id
                ,country_name
                ,competition_name
                ,season_name
                ,home_team_id AS team_id
                ,home_team AS team_name
                ,COUNT(DISTINCT match_id) AS matches_played
                ,COUNT(DISTINCT CASE 
                    WHEN home_team_id = winning_team_id AND penalty_shootout != 1 THEN match_id
                END) AS win_non_pens
                ,COUNT(DISTINCT CASE 
                    WHEN home_team_id = winning_team_id AND penalty_shootout = 1 THEN match_id
                END) AS win_in_pens
                ,COUNT(DISTINCT CASE 
                    WHEN winning_team_id = -1 THEN match_id
                END) AS draw
                ,COUNT(DISTINCT CASE 
                    WHEN home_team_id != winning_team_id AND winning_team_id != -1 AND penalty_shootout != 1 THEN match_id
                END) AS lost_non_pens
                ,COUNT(DISTINCT CASE 
                    WHEN home_team_id != winning_team_id AND winning_team_id != -1 AND penalty_shootout = 1 THEN match_id
                END) AS lost_in_pens
                ,MAX(competition_stage_ranking) AS max_competition_stage_ranking
            FROM 
                combined
            GROUP BY 
                competition_id
                ,season_id
                ,country_name
                ,competition_name
                ,season_name
                ,home_team_id
                ,home_team

            UNION ALL

            SELECT 
                competition_id
                ,season_id
                ,country_name
                ,competition_name
                ,season_name
                ,away_team_id AS team_id
                ,away_team AS team_name
                ,COUNT(DISTINCT match_id) AS matches_played
                ,COUNT(DISTINCT CASE 
                    WHEN away_team_id = winning_team_id AND winning_team_id != -1 AND penalty_shootout != 1 THEN match_id
                END) AS win_non_pens
                ,COUNT(DISTINCT CASE 
                    WHEN away_team_id = winning_team_id AND winning_team_id != -1 AND penalty_shootout = 1 THEN match_id
                END) AS win_in_pens
                ,COUNT(DISTINCT CASE 
                    WHEN winning_team_id = -1 THEN match_id
                END) AS draw
                ,COUNT(DISTINCT CASE 
                    WHEN away_team_id != winning_team_id AND winning_team_id != -1 AND penalty_shootout != 1 THEN match_id
                END) AS lost_non_pens
                ,COUNT(DISTINCT CASE 
                    WHEN away_team_id != winning_team_id AND winning_team_id != -1 AND penalty_shootout = 1 THEN match_id
                END) AS lost_in_pens
                ,MAX(competition_stage_ranking) AS max_competition_stage_ranking
            FROM 
                combined
            GROUP BY 
                competition_id
                ,season_id
                ,country_name
                ,competition_name
                ,season_name
                ,away_team_id
                ,away_team
        )

        ,competition_stage_cte AS (
            SELECT 
                competition_stage
                ,competition_stage_ranking
            FROM 
                combined
            GROUP BY 
                competition_stage
                ,competition_stage_ranking
        )
        ,who_won_finals AS (
            SELECT 
                competition_id
                ,season_id
                ,country_name
                ,competition_name
                ,season_name
                ,competition_stage_ranking
                ,CASE WHEN competition_stage_ranking = 9 THEN winning_team END AS third_place_winner
                ,CASE WHEN competition_stage_ranking = 10 THEN winning_team END AS first_place_winner
            FROM 
                combined
            WHERE 
                competition_stage_ranking IN (9,10)
            GROUP BY 
                competition_id
                ,season_id
                ,country_name
                ,competition_name
                ,season_name
                ,competition_stage_ranking
                ,winning_team
                
        )
        ,final_cte AS (
            SELECT 
                CONCAT(competition_id, '-', season_id, '-', team_id) AS cst_composite_id
                ,competition_id
                ,season_id
                ,country_name
                ,competition_name
                ,season_name
                ,CONCAT(competition_name, ' ', season_name) AS competition
                ,team_id
                ,team_name
                ,SUM(matches_played) AS matches_played
                ,SUM(win_non_pens) AS win_non_pens
                ,SUM(win_in_pens) AS win_in_pens
                ,SUM(draw) AS draw
                ,SUM(lost_non_pens) AS lost_non_pens
                ,SUM(lost_in_pens) AS lost_in_pens 
                ,MAX(max_competition_stage_ranking) AS max_competition_stage_ranking
            FROM 
                matches_cte
            GROUP BY 
                competition_id
                ,season_id
                ,country_name
                ,competition_name
                ,season_name
                ,team_id
                ,team_name
        )
        SELECT 
            f.cst_composite_id
            ,f.competition_id
            ,f.season_id
            ,f.country_name
            ,f.competition_name
            ,f.season_name
            ,f.competition
            ,f.team_id
            ,f.team_name
            ,f.matches_played
            ,f.win_non_pens
            ,f.win_in_pens
            ,f.draw
            ,f.lost_non_pens
            ,f.lost_in_pens 

            ,CASE 
                WHEN f.max_competition_stage_ranking = 10 AND wwf.first_place_winner = f.team_name THEN '1st Place'
                WHEN f.max_competition_stage_ranking = 10 AND wwf.first_place_winner != f.team_name THEN '2nd Place'
                WHEN f.max_competition_stage_ranking = 9  AND wwf.third_place_winner = f.team_name THEN '3rd Place'
                WHEN f.max_competition_stage_ranking = 9  AND wwf.third_place_winner != f.team_name THEN '4th Place'
                ELSE cs.competition_stage
            END AS stage_reached
            ,CASE 
                WHEN f.max_competition_stage_ranking = 10 AND wwf.first_place_winner = f.team_name THEN 14
                WHEN f.max_competition_stage_ranking = 10 AND wwf.first_place_winner != f.team_name THEN 13
                WHEN f.max_competition_stage_ranking = 9  AND wwf.third_place_winner = f.team_name THEN 12
                WHEN f.max_competition_stage_ranking = 9  AND wwf.third_place_winner != f.team_name THEN 10
                ELSE f.max_competition_stage_ranking
            END AS max_competition_stage_ranking

            ,COALESCE(f.win_non_pens, 0) + COALESCE(f.win_in_pens, 0) AS wins
            ,COALESCE(f.lost_non_pens, 0) + COALESCE(f.lost_in_pens, 0) AS losses
        FROM 
            final_cte f
        LEFT JOIN 
            competition_stage_cte cs
        ON 
            f.max_competition_stage_ranking = cs.competition_stage_ranking
        LEFT JOIN 
            who_won_finals wwf
        ON 
            f.competition_id = wwf.competition_id 
        AND 
            f.season_id = wwf.season_id 
        AND 
            f.max_competition_stage_ranking = wwf.competition_stage_ranking
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