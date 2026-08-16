"""
General Utils

Overview
Python file containing regularly used functions and variables


Requirements/Prerequistes
- Install requirements.txt

Author
Elliot Kerr - 05/08/2026

"""

from datetime import datetime, date
import pandas as pd
from sqlalchemy import String, Integer, DateTime, Float, JSON, Boolean, Date, create_engine, text

DB_ENGINE_STRING = 'sqlite:///dbs/{db_name}.db'


SQL_PY_DTYPE_MAPPING = {
    String: str,
    Integer: int,
    DateTime: datetime,
    Date: date,
    Float: float,
    JSON: dict,
    Boolean: bool
}


def col_cleaning(
        df: pd.DataFrame, 
        column_mapping: dict
    ) -> pd.DataFrame:
    """
    Function identifies the columns that exist in the df, then for each column, cleans the data based on the SQLAlchemy datatypes.

    Args:
    df - Raw Dataframe that requires cleaning
    column_mapping - SQLAlchemy datatype dictionary

    Returns:
    df - Cleaned Dataframe
    """
    target_cols = [col for col in column_mapping if col in df.columns]
    
    if not target_cols:
        return df

    df[target_cols] = df[target_cols].replace(['NaN', 'None', 'Null', 'nan', 'null', ''], None)

    for col in target_cols:
        sql_dtype = column_mapping[col]
        py_type = SQL_PY_DTYPE_MAPPING.get(sql_dtype)

        if py_type is None:
            continue

        if py_type is datetime or py_type is datetime:
            df[col] = pd.to_datetime(df[col], format="ISO8601", errors='coerce')
            
        elif py_type is date or py_type is date:
            df[col] = pd.to_datetime(df[col], format="ISO8601", errors='coerce').dt.date

        elif py_type is int:
            df[col] = pd.to_numeric(df[col], errors='coerce').astype('Int64')

        elif py_type is float:
            df[col] = pd.to_numeric(df[col], errors='coerce').astype('Float64')

        elif py_type is bool:
            df[col] = df[col].astype('boolean')

        elif py_type is str:
            df[col] = df[col].astype('string')

    return df


def create_db_engine_func(db_name: str, engine_string: str):
    """
    Function creates the engine for the database connection.

    Args:
    db_name - Database name we are connecting to
    engine_string - Engine string that allows for access to the db

    Returns:
    engine - SQLAlchemy engine to connect to the database specified
    """
    return create_engine(
        engine_string.format(db_name = db_name), 
        echo=False, 
        # pool_pre_ping=True
    )

def bronze_update_current_historical_records(
        brz_dict: dict,
        table_name: String,
        where_clause: String, 
        data_valid_to: datetime, 
    ) -> None:
    """
    Function updates any records in the competitions table that will have newer records added in the refresh.
    Updates the data_valid_to_utc field from None to the data_valid_to value.

    Args:
    brz_dict - Dictionary that includes the schema name, engine and connection for the bronze database.
    table_name - Table Name
    where_clause - SQL where clause to only update the required records
    data_valid_to - Datetime value initialised in the bronze_main function

    Returns:
    No output
    """
    update_dvt_col = f"""
        UPDATE {table_name}
        SET data_valid_to_utc = '{data_valid_to}'
        WHERE {where_clause}
    """

    brz_dict['conn'].execute(text(update_dvt_col))
    brz_dict['conn'].commit()