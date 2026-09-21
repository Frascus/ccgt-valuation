# Sources

Provenance of the raw data. Raw files are kept untouched; all cleaning
happens downstream in `data_loader.py`.

Files:
- `pun_2022.xlsx`, `pun_2023.xlsx`, `pun_2024.xlsx`, `pun_2025.xlsx`
- `ttf_historical.csv`

## pun_{year}.xlsx

Source: https://www.mercatoelettrico.org/it-it/Home/Esiti/Elettricita/MGP/Statistiche/DatiStorici
One file per year, from the yearly "Anno {year}.zip" download (downloaded
September 2026).

Hourly PUN prices for the whole year, in sheet `Prezzi-Prices`. Columns used
(`data_loader.py` reads the first three by position, skipping the header row):
- `Data/Date (YYYYMMDD)` — date, format `YYYYMMDD`
- `Ora/Hour`             — hour, convention 1–24 (hour 1 = 00:00–01:00 …
                           hour 24 = 23:00–24:00); DST days have 23 or 25 hours
- `PUN`                  — day-ahead price, float, EUR/MWh

## ttf_historical.csv

Source: https://www.investing.com/commodities/dutch-ttf-gas-c1-futures-historical-data
(downloaded September 2026).

Dutch TTF natural gas front-month futures, daily. Covers 2021-12 to 2026-09;
`data_loader.py` selects the requested year (plus a few days before Jan 1 so
weekend/holiday gaps at the start of the year can inherit the last quote).
Rows are in reverse chronological order. Columns: `Date`, `Price`, `Open`,
`High`, `Low`, `Vol.`, `Change %`. Only the first two are used:
- `Date`  — format `MM/DD/YYYY`
- `Price` — daily settlement price, EUR/MWh

Example row:
`"09/21/2026","74.415","75.800","76.150","73.390","0.41K","-6.42%"`
