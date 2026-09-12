import pandas as pd
import numpy as np

def compute_spark_spread(*, pun_price, ttf_price, heat_rate, emission_factor, co2_price):
    """
    function that computes hourly spark spread
    """
    return pun_price - heat_rate * ttf_price - emission_factor * co2_price