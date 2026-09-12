"""Command line entry point.

    python3 -m xauusd.cli backtest --csv data/XAUUSD_M5.csv
    python3 -m xauusd.cli backtest --synthetic 60000
    python3 -m xauusd.cli walkforward --csv data/XAUUSD_M5.csv
    python3 -m xauusd.cli signals --csv data/XAUUSD_M5.csv --last 20
    python3 -m xauusd.cli costcurve --csv data/XAUUSD_M5.csv
"""

from __future__ import annotations

import argparse
import csv
import sys
from dataclasses import asdict, replace

from .backtest import run
from .broker import Costs, breakeven_win_rate
from .data import load_csv, synthetic, write_csv
from .metrics import compute, format_report
from .strategy import StrategyConfig, build_context, signal_at
from .walkforward import parameter_stability, run_walkforward


def _add_common(p: argparse.ArgumentParser) -> None:
    src = p.add_argument_group("data")
    src.add_argument("--csv", help="path to M5 OHLC csv")
    src.add_argument("--synthetic", type=int, metavar="N", help="generate N synthetic bars instead")
    src.add_argument("--tz-shift", type=float, default=0.0,
                     help="hours to add to timestamps to reach UTC (GMT+2 broker => -2)")
    src.add_argument("--from-date", help="ignore bars before YYYY-MM-DD")
    src.add_argument("--to-date", help="ignore bars after YYYY-MM-DD")

    costs = p.add_argument_group("costs")
    costs.add_argument("--spread", type=float, default=0.30, help="USD/oz round-turn spread")
    costs.add_argument("--commission", type=float, default=7.0, help="USD per lot round turn")
    costs.add_argument("--slippage", type=float, default=0.10, help="USD/oz adverse slip on stops")

    risk = p.add_argument_group("strategy")
    risk.add_argument("--rr", type=float, default=3.0)
    risk.add_argument("--risk-pct", type=float, default=0.5, help="percent of equity per trade")
    risk.add_argument("--equity", type=float, default=10_000.0)
    risk.add_argument("--retrace", type=float, default=0.382)
    risk.add_argument("--sl-buffer-atr", type=float, default=0.30)
    risk.add_argument("--breakout-lookback", type=int, default=20)
    risk.add_argument("--expire-bars", type=int, default=12)
    risk.add_argument("--no-htf", action="store_true", help="drop the H1 trend filter")
    risk.add_argument("--all-hours", action="store_true", help="disable session filter")
    risk.add_argument("--be-at-r", type=float, default=0.0, help="move stop to break-even at N R")


def _load(args: argparse.Namespace):
    if args.csv:
        bars = load_csv(args.csv, args.tz_shift)
        label = args.csv
    elif args.synthetic:
        bars = synthetic(args.synthetic)
        label = f"SYNTHETIC({args.synthetic}) - plumbing only, no edge information"
    else:
        raise SystemExit("need --csv or --synthetic")
    if args.from_date:
        bars = [b for b in bars if b.ts.strftime("%Y-%m-%d") >= args.from_date]
    if args.to_date:
        bars = [b for b in bars if b.ts.strftime("%Y-%m-%d") <= args.to_date]
    if len(bars) < 1000:
        raise SystemExit(f"only {len(bars)} bars - not enough to conclude anything")
    return bars, label


def _cfg(args: argparse.Namespace) -> StrategyConfig:
    cfg = StrategyConfig(
        rr=args.rr,
        retrace=args.retrace,
        sl_buffer_atr=args.sl_buffer_atr,
        breakout_lookback=args.breakout_lookback,
        expire_bars=args.expire_bars,
        risk_pct=args.risk_pct / 100.0,
        require_htf_bias=not args.no_htf,
        move_sl_to_be_at_r=args.be_at_r,
    )
    if args.all_hours:
        cfg = replace(cfg, sessions=((0, 24 * 60),), force_flat_minute=24 * 60)
    return cfg


def _costs(args: argparse.Namespace) -> Costs:
    return Costs(spread=args.spread, commission_per_lot=args.commission, stop_slippage=args.slippage)


def cmd_backtest(args: argparse.Namespace) -> int:
    bars, label = _load(args)
    cfg, costs = _cfg(args), _costs(args)
    res = run(bars, cfg, costs, args.equity)
    st = compute(res.trades, res.start_equity, cfg.rr)
    extra = {
        "data": label,
        "period": f"{bars[0].ts.date()} -> {bars[-1].ts.date()}  ({res.bars:,} bars)",
        "costs": f"spread {costs.spread:.2f} | comm {costs.commission_per_lot:.2f}/lot | slip {costs.stop_slippage:.2f}",
        "risk per trade": f"{cfg.risk_pct * 100:.2f}%  (3:1 fixed, limit entries)",
        "setups / filled": f"{res.setups} / {res.filled}  ({res.fill_rate * 100:.1f}% fill rate)",
        "orders expired / killed": f"{res.expired} / {res.invalidated}",
    }
    print(format_report(st, extra))
    if args.trades_csv:
        _dump_trades(res.trades, args.trades_csv)
        print(f"  trades written to {args.trades_csv}")
    if st.trades < 100:
        print("  NOTE: under 100 trades. That is an anecdote, not a result.")
    return 0


def cmd_walkforward(args: argparse.Namespace) -> int:
    bars, label = _load(args)
    cfg, costs = _cfg(args), _costs(args)
    print(f"walk-forward on {label}  ({len(bars):,} bars)")
    print(f"  train {args.train:,} bars -> test {args.test:,} bars, rolling\n")
    res = run_walkforward(
        bars, cfg, costs, train_bars=args.train, test_bars=args.test, start_equity=args.equity
    )
    if not res.folds:
        raise SystemExit("not enough bars for one train+test fold - shrink --train/--test")
    print()
    print(format_report(
        res.oos_stats,
        {
            "data": label,
            "result type": "OUT OF SAMPLE, stitched across folds",
            "folds": f"{len(res.folds)}  ({res.positive_folds} profitable)",
            "combos tested per fold": res.combos_tested,
        },
    ))
    print("\n  parameter stability (how often each value was picked)")
    for key, counts in parameter_stability(res).items():
        ranked = sorted(counts.items(), key=lambda kv: -kv[1])
        print(f"   {key:<20} " + "  ".join(f"{v}x{n}" for v, n in ranked))
    print("\n  A parameter that changes every fold is noise. Pin it or delete it.")
    return 0


def cmd_signals(args: argparse.Namespace) -> int:
    """Print the most recent setups: what the live system would have ordered."""
    bars, label = _load(args)
    cfg = _cfg(args)
    ctx = build_context(bars, cfg)
    rows = []
    for i in range(len(bars)):
        s = signal_at(ctx, i, cfg)
        if s:
            rows.append(s)
    print(f"{label}: {len(rows)} setups\n")
    header = f"{'signal bar close':<20} {'side':<6} {'limit':>10} {'stop':>10} {'target':>10} {'R($)':>7} {'expires':<20}"
    print(header)
    print("-" * len(header))
    for s in rows[-args.last :]:
        print(
            f"{bars[s.signal_bar].ts.strftime('%Y-%m-%d %H:%M'):<20} "
            f"{'BUY' if s.side.sign > 0 else 'SELL':<6} {s.entry:>10.2f} {s.sl:>10.2f} "
            f"{s.tp:>10.2f} {s.r_price:>7.2f} "
            f"{bars[min(s.expire_bar, len(bars) - 1)].ts.strftime('%Y-%m-%d %H:%M'):<20}"
        )
    return 0


def cmd_costcurve(args: argparse.Namespace) -> int:
    """Sensitivity to execution quality. If the edge dies at a 0.5 spread, it
    was never an edge, it was a rebate on someone else's bad fill."""
    bars, label = _load(args)
    cfg = _cfg(args)
    print(f"cost sensitivity on {label}\n")
    print(f"{'spread':>8} {'comm/lot':>9} {'trades':>7} {'win%':>7} {'exp R':>8} {'total R':>9}")
    print("-" * 52)
    for spread in (0.10, 0.20, 0.30, 0.45, 0.60, 0.90):
        costs = Costs(spread=spread, commission_per_lot=args.commission, stop_slippage=args.slippage)
        res = run(bars, cfg, costs, args.equity)
        st = compute(res.trades, res.start_equity, cfg.rr)
        print(f"{spread:>8.2f} {args.commission:>9.2f} {st.trades:>7} "
              f"{st.win_rate * 100:>6.1f}% {st.expectancy_r:>+8.3f} {st.total_r:>+9.1f}")
    print("\n  break-even win rate at 3:1 =", f"{breakeven_win_rate(3.0, 0.1) * 100:.1f}% with 0.1R of costs")
    return 0


def cmd_makedata(args: argparse.Namespace) -> int:
    bars = synthetic(args.bars)
    write_csv(bars, args.out)
    print(f"wrote {len(bars):,} SYNTHETIC bars to {args.out}")
    print("This data contains no real market structure. Use it to test the")
    print("machinery, never to decide whether the strategy makes money.")
    return 0


def _dump_trades(trades, path: str) -> None:
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["entry_ts", "exit_ts", "side", "lots", "entry", "sl", "tp", "exit",
                    "reason", "pnl", "r_multiple", "mae_r", "mfe_r", "bars", "equity_after"])
        for t in trades:
            w.writerow([
                t.entry_ts, t.exit_ts, "LONG" if t.side.sign > 0 else "SHORT", f"{t.lots:.2f}",
                f"{t.entry:.2f}", f"{t.sl:.2f}", f"{t.tp:.2f}", f"{t.exit:.2f}", t.exit_reason,
                f"{t.pnl:.2f}", f"{t.r_multiple:.3f}", f"{t.mae_r:.2f}", f"{t.mfe_r:.2f}",
                t.bars_held, f"{t.equity_after:.2f}",
            ])


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="xauusd", description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("backtest", help="single-pass backtest")
    _add_common(p)
    p.add_argument("--trades-csv", help="write the trade blotter here")
    p.set_defaults(func=cmd_backtest)

    p = sub.add_parser("walkforward", help="rolling out-of-sample validation")
    _add_common(p)
    p.add_argument("--train", type=int, default=16_000)
    p.add_argument("--test", type=int, default=4_000)
    p.set_defaults(func=cmd_walkforward)

    p = sub.add_parser("signals", help="list setups the live system would place")
    _add_common(p)
    p.add_argument("--last", type=int, default=25)
    p.set_defaults(func=cmd_signals)

    p = sub.add_parser("costcurve", help="edge vs execution cost")
    _add_common(p)
    p.set_defaults(func=cmd_costcurve)

    p = sub.add_parser("makedata", help="write a synthetic csv for testing")
    p.add_argument("--bars", type=int, default=60_000)
    p.add_argument("--out", default="data/SYNTHETIC_M5.csv")
    p.set_defaults(func=cmd_makedata)

    args = ap.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
