import random
import pandas as pd

def generate_year_bootstrap_monthly(df_historical):
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

