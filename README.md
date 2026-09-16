# CCGT dispatch optimization

A dynamic-programming solver for the optimal dispatch of a combined-cycle gas
turbine (CCGT) power plant, valued as a strip of spark-spread options under
realistic operational constraints. Applied to 2023 Italian day-ahead
electricity prices and Dutch TTF gas prices.

## The problem

A CCGT plant earns money by burning gas to produce electricity, but only when
it is profitable to do so. The hourly margin is the **clean spark spread**:

```
spark_spread = power_price − heat_rate × gas_price − emission_factor × CO2_price
```

In each hour the operator chooses whether to run: if the spread is positive the
plant produces and earns the margin, otherwise it stays off. This makes the
plant a **strip of hourly options** on the spark spread, and its value the sum
of those options.

The naive value (run in every hour with a positive spread) ignores physical
constraints. A real plant cannot switch freely:

- **start-up cost**: every time the plant is turned on from a cold state it
  incurs a fixed cost, so short profitable windows may not be worth starting up
  for;
- **minimum up-time / down-time**: once on (or off), the plant must stay in that
  state for a minimum number of hours before it can switch again.

These constraints couple each hour's decision to its neighbours, turning the
valuation into a **multi-period optimization**: finding the on/off sequence over
the whole year that maximizes total profit subject to the constraints.

## Approach

The optimal dispatch is found with **dynamic programming**. The plant state is
`(status, hours_in_status)`, where the hour counter is capped at the minimum
up/down time (beyond the minimum, only "constraint satisfied" matters, so the
last state of each branch is absorbing). The solver works backwards in time: for
each hour and each state it stores the best achievable profit from that point
onward, then reconstructs the optimal on/off sequence forwards from the initial
state.

The value obtained is compared against the naive "always profitable hour"
strategy; the difference measures how much value the operational constraints
destroy, and the drop in the number of start-ups shows the mechanism at work.

## Project structure

```
ccgt-valuation/
├── data/
│   └── raw/                # PUN and TTF price data + SOURCES.md
├── data_loader.py          # load and align hourly PUN with daily TTF prices
├── dispatch.py             # spark spread, allowed transitions, DP solver
├── plotting.py             # time-series plotting helpers
├── analysis.ipynb          # loads data, runs the solver, shows results
├── requirements.txt
└── README.md
```

### Modules

- **`data_loader.py`** — reads hourly PUN prices and daily TTF gas prices,
  aligns the daily gas price onto the hourly grid (forward-filled over weekends
  and holidays, when the gas market is closed), and returns a single DataFrame
  indexed by hour of the year. An optional integrity check verifies there are no
  missing values and that per-day hour counts are consistent (including the
  23-hour and 25-hour DST days).
- **`dispatch.py`** — the core logic: computing the spark spread, enumerating
  the legal switch choices from a state, applying a state transition, and the
  dynamic-programming solver that returns the optimal value together with the
  optimal on/off profile.
- **`plotting.py`** — a generic helper to plot a time series highlighting the
  regions above and below a threshold, used to visualise the spark spread.

## Data

- **PUN** — hourly Italian day-ahead electricity price, from the GME
  (Gestore dei Mercati Energetici), €/MWh.
- **TTF** — daily Dutch TTF natural gas futures settlement price, €/MWh.

Full provenance for each file is documented in `data/raw/SOURCES.md`. Raw files
are kept untouched; all cleaning happens downstream in `data_loader.py`.

## Running it

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Then open `analysis.ipynb` and run the cells: it loads the price data, computes
the spark spread, runs the dispatch solver, and reports the optimal value, the
hourly on/off profile, and the number of start-ups over the year.

## Modelling assumptions

- The plant is either on at full capacity or off (no partial load, no ramp-rate
  limits).
- The daily gas settlement price is applied to all hours of its delivery day;
  the series is forward-filled so each hour uses the last quoted price, avoiding
  lookahead. 
- The model captures the operating margin of dispatch (revenues net of fuel,
  CO₂, and start-up costs); fixed plant costs and taxes are out of scope, as they
  do not affect the hour-by-hour dispatch decision.