"""
Uruchamia zamrozona strategie na najswiezszych danych i zapisuje wynik do results/.
Odpalane codziennie przez GitHub Actions. Mozna tez odpalic recznie: python run.py
"""
import datetime as dt
import math
import pandas as pd
import yfinance as yf
import strategy as S

FORWARD_START = pd.Timestamp("2026-09-05", tz="America/New_York")  # start forward testu


def metrics(df):
    if df.empty:
        return dict(n=0, wr=0.0, pf=0.0, net=0.0, z=0.0)
    w = int((df["PnL"] > 0).sum())
    n = len(df)
    gross_w = df.loc[df["PnL"] > 0, "PnL"].sum()
    gross_l = abs(df.loc[df["PnL"] < 0, "PnL"].sum())
    p0 = S.BREAKEVEN_WR
    sd = math.sqrt(n * p0 * (1 - p0))
    return dict(n=n, wr=w / n * 100, pf=(gross_w / gross_l if gross_l else float("inf")),
                net=df["PnL"].sum(), z=((w - n * p0) / sd if sd else 0.0))


def main():
    all_trades, open_now = [], []
    for tk, cfg in S.PORTFOLIO.items():
        d = yf.download(tk, period="730d", interval="1h", auto_adjust=True, progress=False)
        if isinstance(d.columns, pd.MultiIndex):
            d.columns = d.columns.get_level_values(0)
        d = S.add_indicators(d)
        if len(d) < S.WARMUP + 50:
            print(f"POMINIETO {tk}: za malo danych ({len(d)})")
            continue
        tr, op = S.backtest(d, cfg["name"], cfg["allow_short"])
        all_trades += tr
        if op:
            open_now.append(op)

    df = pd.DataFrame(all_trades).sort_values("Date").reset_index(drop=True)
    df["Equity"] = 3000 + df["PnL"].cumsum()
    cm = df["Equity"].cummax()
    max_dd_pct = ((cm - df["Equity"]) / cm).max() * 100      # poprawna formula
    fwd = df[df["Date"] >= FORWARD_START]

    hist, fw = metrics(df[df["Date"] < FORWARD_START]), metrics(fwd)
    days = (dt.date.today() - FORWARD_START.date()).days

    lines = [
        f"# Status na {dt.date.today()}",
        "",
        f"Prog oplacalnosci: **{S.BREAKEVEN_WR*100:.1f}%** | wygrana +${S.WIN_PNL:.0f} / przegrana ${S.LOSS_PNL:.0f}",
        "",
        "| Okres | Trejdy | Win rate | PF | Netto | z vs prog |",
        "|---|---|---|---|---|---|",
        f"| Historia (do startu) | {hist['n']} | {hist['wr']:.1f}% | {hist['pf']:.2f} | ${hist['net']:+,.0f} | {hist['z']:.2f} |",
        f"| **FORWARD** ({days} dni) | {fw['n']} | {fw['wr']:.1f}% | {fw['pf']:.2f} | ${fw['net']:+,.0f} | {fw['z']:.2f} |",
        "",
        f"Max obsuniecie (cala historia): {max_dd_pct:.1f}%",
        "",
        "## Otwarte pozycje",
    ]
    lines += ([f"- {o['Asset']}: {o['Kierunek']} od {o['Od']}, wejscie {o['Wejscie']}, "
               f"SL {o['SL']}, TP {o['TP']}" for o in open_now] or ["- brak"])

    need = 100
    lines += ["", "## Werdykt", ""]
    if fw["n"] < need:
        lines.append(f"ZBIERANIE DANYCH: {fw['n']}/{need} trejdow. Za wczesnie na jakikolwiek wniosek.")
    elif fw["z"] > 2.0:
        lines.append(f"Forward potwierdza przewage (z={fw['z']:.2f}) przy {fw['n']} trejdach.")
    else:
        lines.append(f"Forward NIE potwierdza przewagi (z={fw['z']:.2f}) przy {fw['n']} trejdach.")

    open(f"results/status.md", "w").write("\n".join(lines) + "\n")
    df.to_csv("results/trades.csv", index=False)
    print("\n".join(lines))


if __name__ == "__main__":
    main()
