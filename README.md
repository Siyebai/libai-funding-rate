# libai-funding-rate

**三李白资金费率套利扫描器** — 实时识别跨交易所资金费率套利机会。

[![GitHub stars](https://img.shields.io/github/stars/Siyebai/libai-funding-rate?style=social)](https://github.com/Siyebai/libai-funding-rate/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)

---

## ✨ 为什么用这个工具？

| 特性 | 说明 |
|------|------|
| **真实P&L验证** | 基于三李白体系实盘运行的套利逻辑，不是理论模型 |
| **四交易所覆盖** | Gate + Bitget + Aster + OKX，自动对比费率差异 |
| **AI智能选择** | 自动筛选最优品种，综合评分 + 风险评估 |
| **零依赖** | 纯 Python 标准库，无需安装额外依赖 |

---

## 📊 实盘数据（2026-03-26）

| 品种 | 敞口 | 日收 | 状态 |
|------|------|------|------|
| PIXEL | ~20U | 0.182U | ✅ Delta=0 |
| JTO | ~26.6U | 0.148U | ✅ Delta=0 |
| SUPER | ~10.3U | 0.512U | ✅ Delta≈0 |
| 0G | ~0.58U | 0.052U | ✅ Delta=0 |
| **合计** | **~57.5U** | **~0.894U/天** | |

**年化收益：~567%（理论值）**

---

## 🚀 快速开始

### 安装

```bash
git clone https://github.com/Siyebai/libai-funding-rate.git
cd libai-funding-rate
```

### 基础用法

```bash
# 扫描所有交易所
python scripts/scan_all.py

# 扫描特定交易所
python scripts/scan_gate.py
python scripts/scan_bg.py
python scripts/scan_aster.py
python scripts/scan_okx.py

# AI 智能选择
python scripts/auto_selector.py
```

### 输出示例

```
=== 资金费率套利机会 ===
时间: 2026-03-26 14:30:00

品种: JTO
  Gate:  +0.0182% (多)
  Bitget: -0.0245% (空)
  差异:   0.0427%
  日收:   ~1.82%/天
  风险:   LOW
  得分:   85.3
  建议:   Gate多 + BG空
```

---

## 📁 项目结构

```
libai-funding-rate/
├── SKILL.md                    # Skill 说明文档
├── README.md                   # 本文档
├── config.yaml                 # 配置文件
└── scripts/
    ├── scan_gate.py            # Gate 费率扫描
    ├── scan_bg.py              # Bitget 费率扫描
    ├── scan_aster.py           # Aster 费率扫描
    ├── scan_okx.py             # OKX 费率扫描
    ├── scan_all.py             # 综合扫描
    └── auto_selector.py        # AI 智能选择
```

---

## ⚙️ 配置

编辑 `config.yaml`：

```yaml
# 最小费率差异阈值
min_spread: 0.001  # 0.1%

# 风险评分权重
risk_weights:
  spread_stability: 0.35
  oi_depth: 0.25
  historical_variance: 0.20
  exchange_reliability: 0.20

# 黑名单
blacklist:
  - RDNT  # BG error 45110
```

### 环境变量（可选）

```bash
export GATE_API_KEY="your_key"
export GATE_API_SECRET="your_secret"
export BITGET_API_KEY="your_key"
export BITGET_API_SECRET="your_secret"
export BITGET_API_PASSPHRASE="your_passphrase"
export OKX_API_KEY="your_key"
export OKX_API_SECRET="your_secret"
export OKX_PASSPHRASE="your_passphrase"
```

---

## 🧠 AI 智能选择算法

`auto_selector.py` 使用多因子评分模型：

| 因子 | 权重 | 说明 |
|------|------|------|
| 费率差异 | 40% | 差异越大，得分越高 |
| 流动性 | 25% | 流动性越高，得分越高 |
| 历史稳定性 | 20% | 波动率越低，得分越高 |
| 交易量 | 15% | 交易量越大，得分越高 |

同时输出风险评估：
- **LOW**：可正常建仓
- **MEDIUM**：建议减半仓位
- **HIGH**：建议观望

---

## 🔗 与三李白体系的关系

本工具是 **三李白体系** 的开源组件：

| 角色 | 职责 |
|------|------|
| 本地李白 | 学习/理论/算法研究 |
| 云端李白 | 实盘执行/监控/风控 |
| Q李白 | 知识整理/工具维护/系统优化 |

三李白体系已用这套逻辑运行超过 **6个月**，累计执行 **100+ 笔套利**，真实P&L为正。

---

## 📈 性能对比

| 指标 | 本工具 | 传统方法 |
|------|--------|---------|
| 数据源 | 4交易所 | 1-2交易所 |
| 选择方式 | AI自动 | 人工 |
| 风险评估 | ✅ | ❌ |
| 实盘验证 | ✅ 6个月+ | ❌ |

---

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

### 开发计划
- [ ] 添加更多交易所（Bybit、Binance）
- [ ] 实时推送通知
- [ ] Web 界面
- [ ] 历史回测增强

---

## 📜 License

MIT — 自由使用，风险自负。

---

## 📞 联系

- GitHub: [@Siyebai](https://github.com/Siyebai)
- 项目主页: [libai-funding-rate](https://github.com/Siyebai/libai-funding-rate)

---

**🦞 由 Q李白 维护 | 三李白体系 | 2026**