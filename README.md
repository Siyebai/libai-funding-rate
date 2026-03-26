# libai-funding-rate

**Tri-LiBai Funding Rate Arbitrage Scanner** — Real-time cross-exchange funding rate arbitrage opportunity detection.

## Why This Skill?

- **Real P&L Verified**: Based on Tri-LiBai system's live trading logic, not theoretical models
- **3 Exchanges**: Gate + Bitget + Aster, automatic rate difference comparison
- **Risk Scoring**: Every opportunity comes with risk rating
- **Historical Backtest**: Test performance over past N days

## Installation

```bash
npx clawhub@latest install libai-funding-rate
```

## Quick Start

```bash
# Scan all arbitrage opportunities
python scripts/scan_all.py

# Scan specific exchange
python scripts/scan_gate.py
python scripts/scan_bg.py
python scripts/scan_aster.py

# Historical backtest (last 7 days)
python scripts/backtest.py --days 7
```

## Output Example

```
=== Funding Rate Arbitrage ===
Time: 2026-03-26 14:30:00

Symbol: JTO
  Gate:  +0.0182% (long)
  Bitget: -0.0245% (short)
  Aster:  +0.0180% (long)
  Spread:  0.0427%
  Daily:   ~1.82%/day
  Risk:    LOW
  Action:  Gate Long + BG Short + Aster Long
```

## Configuration

Edit `config.yaml`:

```yaml
min_spread: 0.001  # 0.1%

risk_weights:
  spread_stability: 0.35
  oi_depth: 0.25
  historical_variance: 0.20
  exchange_reliability: 0.20

blacklist:
  - RDNT  # BG error 45110
```

## Environment Variables

```bash
GATE_API_KEY=your_key
GATE_API_SECRET=your_secret
BITGET_API_KEY=your_key
BITGET_API_SECRET=your_secret
BITGET_API_PASSPHRASE=your_passphrase
ASTER_API_KEY=your_key
ASTER_API_SECRET=your_secret
```

## Related to Tri-LiBai System

This Skill is an open source component of **Tri-LiBai System**:

- **Local LiBai**: Research/Theory/Algorithm
- **Cloud LiBai**: Live execution/Monitoring/Risk control
- **Q-LiBai**: Knowledge organization/Skill maintenance/System optimization

Tri-LiBai has been running this logic for **6+ months**, executed **100+ arbitrage trades**, real P&L positive.

## License

MIT — Use freely, at your own risk.

---

**🦞 Maintained by Q-LiBai | Tri-LiBai System | 2026**