# trading-lab

Forward test strategii Fib + engulfing + EMA200 na portfelu QQQ / EWG / GLD.

**Start forward testu: 2026-09-05.** Aktualny stan: [`results/status.md`](results/status.md)

## Zasady tego testu

1. `strategy.py` jest **zamrozony**. Zadnej zmiany parametru do konca testu.
2. Historia (2023-2026) jest juz zuzyta - byla ogladana wielokrotnie. Nie liczy sie jako dowod.
3. Liczy sie wylacznie wiersz FORWARD w `results/status.md`.
4. Prog decyzyjny: **100 trejdow forward**. Wczesniej zaden wynik nie jest wnioskiem.
5. Jesli chcesz przetestowac wariant - nowa galaz, nowy `FORWARD_START`, licznik od zera.

## Czego ten test NIE sprawdza

- Instrumenty to ETF-y (QQQ/EWG/GLD), a nie CFD z brokera. Inne godziny sesji, inny spread.
- Strata jest zabetonowana na -$33. Brak luk cenowych i poslizgu na SL.
- Brak kontroli ekspozycji: kazde aktywo ryzykuje osobno, a QQQ i EWG sa skorelowane.

## Uruchomienie recznie

```bash
pip install yfinance pandas numpy
python run.py
```
