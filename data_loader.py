import pandas as pd

def load_pun_ttf_prices(
    diagnostic: bool = False,
    year: int = 2023,
):
    """
    Load hourly PUN and daily TTF prices into a single DataFrame.

    PUN data are loaded from the year-specific file:
        data/raw/pun_{year}.xlsx

    TTF data are loaded from the historical multi-year file:
        data/raw/ttf_historical.csv

    The requested year is selected dynamically from the TTF historical
    data. A few days before January 1st are included in the TTF calendar
    so that weekends/holidays at the beginning of the year can inherit
    the last available TTF price from the previous year.

    Returns a DataFrame with columns 'time', 'pun_price' (EUR/MWh) and
    'ttf_price' (EUR/MWh).
    """

    # ---------------------------------------------------------
    # PUN: hourly electricity prices
    # ---------------------------------------------------------
    file_path = f"data/raw/pun_{year}.xlsx"

    df = pd.read_excel(
        file_path,
        sheet_name="Prezzi-Prices",
        skiprows=1,
        header=None,
        usecols=[0, 1, 2],
        names=["date", "hour", "pun_price"],
    )

    df["date"] = pd.to_datetime(
        df["date"],
        format="%Y%m%d",
    )

    # Keep only the requested year
    df = df[
        df["date"].dt.year == year
    ].copy()

    # Sort so the progressive index reflects true chronological order
    df = (
        df.sort_values(["date", "hour"])
        .reset_index(drop=True)
    )

    # GME hours run 1..24:
    # hour 1 -> offset 0h -> 00:00
    df["time"] = (
        df["date"]
        + pd.to_timedelta(
            df["hour"] - 1,
            unit="h",
        )
    )

    df = df.drop(columns=["hour"])

    # ---------------------------------------------------------
    # TTF: daily gas prices
    # ---------------------------------------------------------
    df_ttf = pd.read_csv(
        "data/raw/ttf_historical.csv",
        usecols=[0, 1],
        skiprows=1,
        header=None,
        names=["date", "ttf_price"],
    )

    df_ttf["date"] = pd.to_datetime(
        df_ttf["date"],
        format="%d/%m/%Y",
    )

    # ---------------------------------------------------------
    # Build a continuous daily calendar
    # ---------------------------------------------------------
    start_date = pd.Timestamp(f"{year}-01-01")
    end_date = pd.Timestamp(f"{year}-12-31")

    # Start a few days before January 1st so that, if the first
    # days of the year are weekends/holidays, ffill() can inherit
    # the last quoted price from the previous year.
    all_days = pd.DataFrame(
        {
            "date": pd.date_range(
                start_date - pd.Timedelta(days=5),
                end_date,
                freq="D",
            )
        }
    )

    ttf_daily = all_days.merge(
        df_ttf,
        on="date",
        how="left",
    )

    # TTF has no weekend/holiday observations:
    # inherit the last available quoted price.
    ttf_daily["ttf_price"] = (
        ttf_daily["ttf_price"]
        .ffill()
    )

    # After forward-filling, keep only the requested year.
    ttf_daily = ttf_daily[
        (ttf_daily["date"] >= start_date)
        & (ttf_daily["date"] <= end_date)
    ].copy()

    # ---------------------------------------------------------
    # Align TTF to each PUN hour by calendar date
    # ---------------------------------------------------------
    prices = df.merge(
        ttf_daily,
        on="date",
        how="left",
    )

    prices = prices[
        ["time", "pun_price", "ttf_price"]
    ]

    # ---------------------------------------------------------
    # Diagnostics
    # ---------------------------------------------------------
    if diagnostic:
        _check_prices(prices)

    return prices


def _check_prices(prices):
    """Integrity checks on the loaded price DataFrame."""

    # no missing values
    n_missing = (
        prices[["pun_price", "ttf_price"]]
        .isna()
        .sum()
        .sum()
    )

    assert n_missing == 0, (
        f"found {n_missing} missing price values"
    )

    # hours per calendar day
    hours_per_day = (
        prices["time"]
        .dt.date
        .value_counts()
    )

    n_23 = (hours_per_day == 23).sum()
    n_25 = (hours_per_day == 25).sum()
    n_24 = (hours_per_day == 24).sum()

    assert n_23 == 1, (
        f"expected exactly one 23-hour day, found {n_23}"
    )

    assert n_25 == 1, (
        f"expected exactly one 25-hour day, found {n_25}"
    )

    assert n_24 == len(hours_per_day) - 2, (
        "all other days should have 24 hours; "
        f"got {n_24} of {len(hours_per_day)} days"
    )

    print(
        f"diagnostic OK: {len(prices)} hours, "
        f"{len(hours_per_day)} days "
        f"({n_24} x 24h, one 23h, one 25h), "
        f"no missing values"
    )