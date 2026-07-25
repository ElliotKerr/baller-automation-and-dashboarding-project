from sqlalchemy import String, Integer, DateTime, Float, JSON, Boolean

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
    }


    def etl_events(
            self,
            sb,
            stg_engine, 
            brz_connection, 
            brz_cursor, 
            _merge, 
            event_class, 
            matches,
            competition_id,
            season_id,
            logger
        ):
        """
        Doc String
        """

        match_ids_df = matches[['match_id']]

        match_ids_dict = match_ids_df.to_dict()

        match_ids_list = [match_ids_dict['match_id'][i] for i in list(match_ids_dict['match_id'].keys())]


        for match_id in match_ids_list:
            logger.info(f"Starting Events extraction for match {match_id}")
            events = sb.events(match_id=match_id)
            events_df = events.reindex(columns=event_class.column_mapping.keys())

            logger.info(f"Writing into staging.events")

            events_df.to_sql(
                'events', 
                con=stg_engine, 
                if_exists='append', 
                dtype = event_class.column_mapping, 
                index = False
            )
        
        logger.info(f"Merging events for competition-season {competition_id}-{season_id}.")
        _merge(brz_cursor, brz_connection, event_class, 'events')