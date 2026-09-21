"""
Synthetic price scenarios for the Monte Carlo valuation.
"""

import random
import pandas as pd

def generate_year_bootstrap_monthly(df_historical):
    """
    Build a synthetic year by monthly block bootstrap: for each calendar
    month, take that month from a historical year drawn at random (with
    replacement). This preserves the within-month shape of prices while
    resampling across years; month-to-month dependence is not preserved.

    Parameters
    ----------
    df_historical : DataFrame with a 'time' column (datetime) spanning
        several full years, plus the price/spark-spread columns to resample.

    Returns
    -------
    DataFrame, one synthetic year (12 monthly blocks concatenated in
    calendar order), same columns as the input.
    """
    df_synthetic=pd.DataFrame()
    past_years=df_historical["time"].dt.year.unique().tolist()

    for i in range (1,13):
        random_year=random.choice(past_years)
        df_extracted_month=(
            df_historical[
                (df_historical["time"].dt.year==random_year) &
                (df_historical["time"].dt.month==i)
            ]
        )
        df_synthetic=pd.concat([df_synthetic, df_extracted_month], ignore_index=True)
    return df_synthetic

