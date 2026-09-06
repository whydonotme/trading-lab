"""
ZAMROZONA STRATEGIA - Fib retracement + engulfing + filtr EMA200.

!!! NIE ZMIENIAJ TEGO PLIKU PODCZAS TRWANIA FORWARD TESTU !!!
Kazda zmiana parametru unieważnia caly zebrany dotad wynik forward.
Jesli musisz cos zmienic - zaloz nowa galaz i zacznij liczyc od zera.
"""
import numpy as np
import pandas as pd

# --- parametry (ZAMROZONE 2026-09-05) ---
RISK_USD    = 30.0
RR_RATIO    = 2.5
SPREAD_COST = 0.25
LOOKBACK    = 20
FIB_MIN     = 0.382
FIB_MAX     = 0.650
ATR_MULT    = 1.0
EMA_SPAN    = 200
WARMUP      = 600      # EMA200 potrzebuje rozbiegu, wczesniej filtr trendu jest smieciowy

PORTFOLIO = {
    "QQQ": {"name": "Nasdaq 100",  "allow_short": False},
    "EWG": {"name": "GER40 (DAX)", "allow_short": False},
    "GLD": {"name": "Zloto (XAU)", "allow_short": True},
}

WIN_PNL      = RISK_USD * RR_RATIO - SPREAD_COST      # +72
LOSS_PNL     = -RISK_USD - SPREAD_COST                # -33
BREAKEVEN_WR = -LOSS_PNL / (WIN_PNL - LOSS_PNL)       # 0.3143


def add_indicators(d: pd.DataFrame) -> pd.DataFrame:
    d = d.dropna().copy()
    d["EMA"] = d["Close"].ewm(span=EMA_SPAN, adjust=False).mean()
    hl = d["High"] - d["Low"]
    hc = (d["High"] - d["Close"].shift()).abs()
    lc = (d["Low"] - d["Close"].shift()).abs()
    d["ATR"] = np.maximum(hl, np.maximum(hc, lc)).rolling(14).mean()
    return d


def signals(d: pd.DataFrame, allow_short: bool):
    sh = d["High"].rolling(LOOKBACK).max()
    sl = d["Low"].rolling(LOOKBACK).min()
    rng = sh - sl
    f382l, f650l = sh - rng * FIB_MIN, sh - rng * FIB_MAX
    f382s, f650s = sl + rng * FIB_MIN, sl + rng * FIB_MAX
    o, c, cp, op = d["Open"], d["Close"], d["Close"].shift(1), d["Open"].shift(1)
    bull = (c > o) & (cp < op) & (c >= op)
    bear = (c < o) & (cp > op) & (c <= op)
    lo = (c > d["EMA"]) & (d["Low"] <= f382l) & (d["Low"] >= f650l) & bull
    if allow_short:
        so = (c < d["EMA"]) & (d["High"] >= f382s) & (d["High"] <= f650s) & bear
    else:
        so = pd.Series(False, index=d.index)
    return lo, so


def backtest(d: pd.DataFrame, name: str, allow_short: bool):
    """Zwraca (lista zamknietych trejdow, otwarta pozycja albo None)."""
    lo, so = signals(d, allow_short)
    H, L, C, A = d["High"].values, d["Low"].values, d["Close"].values, d["ATR"].values
    LO, SO = lo.values, so.values
    idx = d.index
    pos, slp, tpp, entry_i = 0, 0.0, 0.0, None
    trades = []
    for i in range(max(LOOKBACK, WARMUP), len(d)):
        if pos != 0:
            hit_sl = (L[i] <= slp) if pos == 1 else (H[i] >= slp)
            hit_tp = (H[i] >= tpp) if pos == 1 else (L[i] <= tpp)
            if hit_sl:                      # SL sprawdzany przed TP = pesymistycznie
                trades.append({"Date": idx[i], "Asset": name, "PnL": LOSS_PNL, "Type": "SL"})
                pos = 0
            elif hit_tp:
                trades.append({"Date": idx[i], "Asset": name, "PnL": WIN_PNL, "Type": "TP"})
                pos = 0
        elif not np.isnan(A[i]):
            if LO[i]:
                slp = L[i] - A[i] * ATR_MULT
                if C[i] - slp > 0:
                    tpp, pos, entry_i = C[i] + (C[i] - slp) * RR_RATIO, 1, i
            elif SO[i]:
                slp = H[i] + A[i] * ATR_MULT
                if slp - C[i] > 0:
                    tpp, pos, entry_i = C[i] - (slp - C[i]) * RR_RATIO, -1, i
    open_pos = None
    if pos != 0:
        open_pos = {"Asset": name, "Kierunek": "LONG" if pos == 1 else "SHORT",
                    "Wejscie": round(float(C[entry_i]), 2), "SL": round(slp, 2),
                    "TP": round(tpp, 2), "Od": str(idx[entry_i])}
    return trades, open_pos
