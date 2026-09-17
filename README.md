# CCGT valuation & dispatch optimization

A dynamic-programming solver for the optimal dispatch of a combined-cycle gas
turbine (CCGT) power plant, valued as a strip of spark-spread options under
realistic operational constraints. Applied to 2023 Italian day-ahead
electricity prices (PUN) and Dutch TTF gas prices.

## The problem

A CCGT plant earns money by burning gas to produce electricity, but only when
it is profitable to do so. The hourly margin is the **clean spark spread**:

```
spark_spread = power_price − heat_rate × gas_price − emission_factor × CO2_price
```

In each hour the operator chooses whether to run: if the spread is positive the
plant produces and earns the margin, otherwise it stays off. Being free to run
or not makes the plant a **strip of hourly options** on the spark spread, and
its unconstrained value the sum of those options.

A real plant, however, cannot switch freely:

- **start-up cost** — turning the plant on from cold incurs a fixed cost, so a
  short profitable window may not be worth starting up for;
- **minimum up-time / down-time** — once on (or off), the plant must stay in
  that state for a minimum number of hours before it can switch again.

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

The plant is valued under three strategies of increasing realism:

- **Always on** — the plant runs every hour regardless of price (the naive
  must-run baseline, which ignores the option to shut down);
- **Ideal, unconstrained** — the option is exercised freely: run in every hour
  with a positive spread, at no switching cost. This is the theoretical ceiling,
  the pure strip-of-options value;
- **Optimal, constrained** — the dynamic-programming dispatch under start-up
  cost and minimum up/down-time.

Comparing them answers the two questions the project is about: how much the
physical constraints cost (ideal → optimal), and how much the option to switch
off is worth (always-on → optimal).

## Results (2023)

| Strategy | Yearly gross margin |
|----------|--------------------:|
| Always on (must-run baseline) | €71.9M |
| Ideal, unconstrained (option ceiling) | €83.9M |
| Optimal, constrained (DP) | €81.0M |

The €2.9M gap between the ideal and the constrained optimum — the cost of the
operational constraints — breaks down as:

- **start-up costs** — 134 starts × €15k = **€2.01M**;
- **run-at-loss** — hours run at a negative spread, forced by the min-up-time =
  **€0.81M**;
- **profit foregone** — profitable hours left off, because a start-up would not
  be repaid = **€0.09M**.

The constrained optimum still beats the must-run baseline by **€9.1M**, the
value of the option to shut the plant down. `analysis.ipynb` shows this
decomposition as a waterfall chart (`plotting.plot_value_waterfall`).

## Project structure

```
ccgt-valuation/
├── data/
│   └── raw/                # PUN and TTF price data + SOURCES.md
├── output/                 # generated results (git-ignored): dispatch CSV + summary + value waterfall plot
├── data_loader.py          # load and align hourly PUN with daily TTF prices
├── dispatch.py             # spark spread, allowed transitions, DP solver
├── plotting.py             # spark-spread and value-decomposition plots
├── analysis.ipynb          # loads data, runs the solver, shows results
├── requirements.in         # direct dependencies
├── requirements.txt        # pinned lock, compiled from requirements.in
└── README.md
```

### Modules

- **`data_loader.py`** — reads hourly PUN prices and daily TTF gas prices,
  aligns the daily gas price onto the hourly grid (forward-filled over weekends
  and holidays, when the gas market is closed), and returns a single DataFrame
  indexed by hour of the year. An optional integrity check verifies there are no
  missing values and that per-day hour counts are consistent (including the
  23-hour and 25-hour DST days).
- **`dispatch.py`** — the core logic: computing the clean spark spread,
  enumerating the legal switch choices from a state, applying a state
  transition, and the dynamic-programming solver that returns the optimal value
  together with the optimal on/off profile (plus a start-up counter).
- **`plotting.py`** — `plot_series_vs_threshold`, used to visualise the spark
  spread against zero, and `plot_value_waterfall`, the ideal→optimal value
  decomposition.

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
the spark spread, runs the three strategies, shows the waterfall decomposition,
and writes the optimal hourly dispatch and a text summary to `output/`, where
also the value waterfall plot is saved.

## Modelling assumptions

- The plant is either on at full capacity or off (no partial load, no ramp-rate
  limits).
- The daily gas settlement price is applied to all hours of its delivery day;
  the series is forward-filled so each hour uses the last quoted price, avoiding
  lookahead.
- The model captures the operating margin of dispatch (revenues net of fuel,
  CO₂, and start-up costs); fixed plant costs and taxes are out of scope, as they
  do not affect the hour-by-hour dispatch decision.

