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
from statsbombpy import sb
from typing import List
import math

from utils.general import col_cleaning

class Lineups():

    composite_keys = ['match_id', 'player_id']

    column_mapping = {
        'match_id': Integer,
        'player_id': Integer,
        'player_name': String,
        'player_nickname': String,
        'jersey_number': Integer,
        'country': String,
        'first_yellow_time': String,
        'first_yellow_reason': String,
        'first_yellow_period': Integer,
        'second_yellow_time': String,
        'second_yellow_reason': String,
        'second_yellow_period': Integer,
        'red_card_time': String,
        'red_card_reason': String,
        'red_card_period': Integer,
        'starting_xi': Integer,
        'sub_off': String,
        'sub_on': String,
        'removed_due_to_red_card': String,
        'ended_game': Integer,
        "data_valid_from_utc": DateTime,
        "data_valid_to_utc": DateTime,
    }

    def extract_cards(self, row, card_type):
        """
        Doc String
        """
        cards_values = row['cards']
        try:
            card_dict = dict(cards_values)
            if card_type == card_dict['card_type']:
                return (card_dict['time'], card_dict['reason'], card_dict['period'])
        except:
            pass

        return (None, None, None)

    def extract_positions(self, row):
        """
        Doc String
        """
        positions_values = row['positions']
        try:
            position_dict = dict(positions_values)
            return (
                position_dict['position_id'], 
                position_dict['position'], 
                position_dict['from'],
                position_dict['to'], 
                position_dict['from_period'], 
                position_dict['to_period'],
                position_dict['start_reason'], 
                position_dict['end_reason']
            )
        except:
            pass

        return (
                None,
                None,
                None,
                None,
                None,
                None,
                None,
                None
            )

    def start_and_end_game(self, row):
        """
        Doc String
        """
        start_reason = str(row['start_reason']) if row['start_reason'] is not None else ''
        end_reason = str(row['end_reason']) if row['end_reason'] is not None else ''

        starting_xi = 1 if start_reason == 'Starting XI' else None
        sub_on = row['from'] if "Substitution - On" in start_reason else None
        sub_off = row['to'] if "Substitution - Off" in end_reason else None
        removed_due_to_red_card = row['to'] if end_reason == 'Foul Committed (Red Card)' else None
        ended_game = 1 if end_reason == 'Final Whistle' else None

        return (starting_xi, sub_off, sub_on, removed_due_to_red_card, ended_game)

    def bronze_update_current_historical_records(
            self, 
            brz_dict: dict,
            df: pd.DataFrame, 
            data_valid_to: datetime, 
        ) -> None:
        """
        Function updates any records in the competitions table that will have newer records added in the refresh.
        Updates the data_valid_to_utc field from None to the data_valid_to value.

        Args:
        brz_dict - Dictionary that includes the schema name, engine and connection for the bronze database.
        df - Dataframe containing the records that need to be updated.
        data_valid_to - Datetime value initialised in the bronze_main function

        Returns:
        No output
        """
        comp_season_tuple = list(zip(*[df[c] for c in self.composite_keys]))

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

    def bronze_lineups(self,
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
            all_lineups = sb.lineups(match_id = match_id)

            teams = list(all_lineups.keys())

            teams_lineups = []

            for team in teams:
                teams_lineups.append(all_lineups[team])

            lineups = pd.concat(teams_lineups)

            lineups.insert(0, 'match_id', match_id)

            lineups['player_nickname'] = lineups['player_nickname'].fillna(lineups['player_name'])

            cards = lineups.explode('cards')
            cards = cards[['player_id', 'player_nickname', 'cards']]
            cards['cards'] = cards['cards'].fillna(None)

            cards[['first_yellow_time', 'first_yellow_reason', 'first_yellow_period']] = cards.apply(lambda x: self.extract_cards(x, 'Yellow Card'), axis=1, result_type='expand')
            cards[['second_yellow_time', 'second_yellow_reason', 'second_yellow_period']] = cards.apply(lambda x: self.extract_cards(x, 'Second Yellow'), axis=1, result_type='expand')
            cards[['red_card_time', 'red_card_reason', 'red_card_period']] = cards.apply(lambda x: self.extract_cards(x, 'Red Card'), axis=1, result_type='expand')

            cards = cards.drop('cards', axis = 1)

            final_cards = cards.groupby('player_id', as_index = False).agg({
                'first_yellow_time': 'max', 
                'first_yellow_reason': 'max',	
                'first_yellow_period': 'max', 
                'second_yellow_time': 'max', 
                'second_yellow_reason': 'max', 
                'second_yellow_period': 'max',
                'red_card_time': 'max', 
                'red_card_reason': 'max', 
                'red_card_period': 'max'
                }
            )


            new_lineups = lineups.drop('cards', axis = 1).merge(final_cards, on = 'player_id', how = 'left')


            positions = new_lineups.explode('positions')
            positions = positions[['player_id', 'player_nickname', 'positions']]
            positions['positions'] = positions['positions'].fillna(None)


            positions[['position_id', 'position', 'from', 'to', 'from_period', 'to_period', 'start_reason', 'end_reason']] = positions.apply(lambda x: self.extract_positions(x), axis=1, result_type='expand')

            positions = positions.drop('positions', axis = 1)

            starting_11 = positions["start_reason"] == "Starting XI"
            sub_on = positions["start_reason"].str.contains("Substitution - On", na=False)
            sub_off = positions['end_reason'].str.contains("Substitution - Off", na=False)
            red_card = positions['end_reason'] == 'Foul Committed (Red Card)'
            final = positions['end_reason'] == 'Final Whistle'

            combined = starting_11 | sub_on | sub_off | red_card | final

            positions_final = positions[combined]

            positions_final[['starting_xi','sub_off','sub_on','removed_due_to_red_card','ended_game']] = positions_final.apply(lambda x: self.start_and_end_game(x), axis = 1,  result_type='expand').fillna(None)

            grouped_positions = positions_final.groupby(['player_id'], as_index = False).agg({
                'starting_xi': 'max',
                'sub_off': 'max',
                'sub_on': 'max',
                'removed_due_to_red_card': 'max',
                'ended_game': 'max'
            })

            grouped_positions.loc[grouped_positions['removed_due_to_red_card'].notna(), 'ended_game'] = 0

            grouped_positions['starting_xi'] = grouped_positions['starting_xi'].fillna(0)
            grouped_positions['ended_game'] = grouped_positions['ended_game'].fillna(0)

            final_lineups = new_lineups.drop('positions', axis = 1).merge(grouped_positions, on = 'player_id', how = 'left')

            final_lineups['data_valid_from_utc'] = valid_from
            final_lineups['data_valid_to_utc'] = None

            final_lineups = col_cleaning(final_lineups, self.column_mapping)   

            if not final_lineups.empty:
                logger.info(f"Updating any old records that are being updated.")
            try:
                self.bronze_update_current_historical_records(brz_dict, final_lineups, data_valid_to)
            except:
                pass

                logger.info(f"Writing {match_id} into {brz_dict['schema']}.lineups")

                final_lineups_clean_df = final_lineups.astype(object).where(pd.notnull(final_lineups), None)

                final_lineups_clean_df.to_sql(
                    'lineups', 
                    con=brz_dict['conn'], 
                    if_exists='append', 
                    dtype = self.column_mapping, 
                    index = False
                )

                brz_dict['conn'].commit()

            other_values = set(list(positions[~combined].start_reason.values) + list(positions[~combined].end_reason.values))
            other_values = {x for x in other_values if not (isinstance(x, float) and math.isnan(x)) and x != 'Tactical Shift'}

            if other_values:
                logger.warning(f"Values that haven't been accounted for : {other_values}")