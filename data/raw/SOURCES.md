# SOURCES

This file documents the raw data used in this project. Raw files are kept
untouched; all cleaning happens downstream in data_loader.py.

Two files:
- pun_2023.xlsx
- ttf_2023.csv

## pun_2023.xlsx

Source: https://www.mercatoelettrico.org/it-it/Home/Esiti/Elettricita/MGP/Statistiche/DatiStorici
downloaded "Anno 2023.zip" (downloaded: 12 Sept 2026).
Original name: Anno 2023_12.xlsx

Hourly PUN prices for all of 2023, in sheet "Prezzi-Prices".
Relevant columns:
- "Data/Date (YYYYMMDD)"  — date, format YYYYMMDD
- "Ora/Hour"              — hour, format h or hh, convention 1–24
                            (hour 1 = 00:00–01:00 ... hour 24 = 23:00–24:00);
                            note DST days have 23 (date 20230326) or 25 (date 20231029) hours
- "PUN"                   — price, float, EUR/MWh

## ttf_2023.csv

Source:https://www.investing.com/commodities/dutch-ttf-gas-c1-futures-historical-data
(downloaded: 21 Sept 2026).

Dutch TTF natural gas futures, daily. Covers multiple years; only 2023 is used
(filtered in cleaning). Rows are in reverse chronological order.
Columns: "Date","Price","Open","High","Low","Vol.","Change %"
- "Date"   — format DD/MM/YYYY
- "Price"  — daily settlement price, EUR/MWh  
Example row:
"29/11/2024","47.350","46.450","47.945","46.235","0.54K","1.23%"