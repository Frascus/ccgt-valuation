import pandas as pd


def load_pun_ttf_prices(diagnostic: bool = False):
    """
    Load hourly PUN and daily TTF prices into a single DataFrame.

    Returns a DataFrame with columns 'time', 'pun_price' (EUR/MWh) and
    'ttf_price' (EUR/MWh), with an integer index 0..N-1 representing
    the hours of 2023 in sequence. The daily TTF price is aligned to 
    each hour by calendar date and forward-filled over weekends and 
    holidays (days when the gas market is closed inherit the last quoted
    price).

    Note on the 'time' column: because of DST, exactly one day has 23
    hours (an hour is skipped) and one day has 25 hours (an hour
    repeats, appearing as 00:00 twice on the day after the clock moves
    back). On those days the 'time' value does not map to the true
    physical hour. The reliable key is therefore the integer index,
    which counts hours of the year in order, not the 'time' column.

    Parameters
    ----------
    diagnostic : bool, default False
        If True, run integrity checks on the loaded data and print a
        short summary. Raises AssertionError if a check fails.
    """
    # --- PUN: hourly electricity prices ---
    df = pd.read_excel(
        "data/raw/pun_2023.xlsx",
        sheet_name="Prezzi-Prices",
        skiprows=1,
        header=None,
        usecols=[0, 1, 2],
        names=["date", "hour", "pun_price"],
    )
    df["date"] = pd.to_datetime(df["date"], format="%Y%m%d")
    # sort so the progressive index reflects true chronological order
    df = df.sort_values(["date", "hour"]).reset_index(drop=True)
    # GME hours run 1..24; hour 1 -> offset 0h -> 00:00
    df["time"] = df["date"] + pd.to_timedelta(df["hour"] - 1, unit="h")
    df = df.drop(columns=["hour"])

    # --- TTF: daily gas prices ---
    df_ttf = pd.read_csv(
        "data/raw/ttf_2023.csv",
        usecols=[0, 1],
        skiprows=1,
        header=None,
        names=["date", "ttf_price"],
    )
    df_ttf["date"] = pd.to_datetime(df_ttf["date"], format="%d/%m/%Y")

    # the raw TTF has no weekend/holiday rows: build a continuous daily
    # calendar and forward-fill. Start a few days before 2023 so that
    # early-January days have a past value to inherit if the market was
    # closed.
    all_days = pd.DataFrame(
        {"date": pd.date_range("2022-12-27", "2023-12-31", freq="D")}
    )
    ttf_daily = all_days.merge(df_ttf, on="date", how="left")
    ttf_daily["ttf_price"] = ttf_daily["ttf_price"].ffill()

    # --- align gas to each hour by calendar date ---
    prices = df.merge(ttf_daily, on="date", how="left")
    prices = prices[["time", "pun_price", "ttf_price"]]

    if diagnostic:
        _check_prices(prices)

    return prices


def _check_prices(prices):
    """Integrity checks on the loaded price DataFrame.

    Verifies there are no missing values and that the hour counts per
    day are consistent with a non-leap year containing exactly one DST
    short day (23h) and one DST long day (25h). Raises AssertionError
    on failure; prints a summary on success.
    """
    # no missing values
    n_missing = prices[["pun_price", "ttf_price"]].isna().sum().sum()
    assert n_missing == 0, f"found {n_missing} missing price values"

    # hours per calendar day
    hours_per_day = prices["time"].dt.date.value_counts()
    n_23 = (hours_per_day == 23).sum()
    n_25 = (hours_per_day == 25).sum()
    n_24 = (hours_per_day == 24).sum()

    assert n_23 == 1, f"expected exactly one 23-hour day, found {n_23}"
    assert n_25 == 1, f"expected exactly one 25-hour day, found {n_25}"
    assert n_24 == len(hours_per_day) - 2, (
        "all other days should have 24 hours; "
        f"got {n_24} of {len(hours_per_day)} days"
    )

    print(
        f"diagnostic OK: {len(prices)} hours, {len(hours_per_day)} days "
        f"({n_24} x 24h, one 23h, one 25h), no missing values"
    )