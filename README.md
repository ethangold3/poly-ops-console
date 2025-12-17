# Polymarket Trading Terminal

CLI tool for trading on Polymarket. Search markets, place orders, and manage your portfolio from the command line.

## Features

- Search and filter markets by keyword, volume, liquidity, etc
- View live order books
- Place market and limit orders
- Track your open positions and P&L
- Manage open orders (view/cancel)
- View leaderboard stats and performance analytics

## Setup

You'll need Python 3.11+ and a Polymarket account with your private key and proxy address.

### Installation

1. Clone repo and cd into it
2. Create a virtual environment: `python -m venv venv`
3. Activate it: `venv\Scripts\activate` (Windows) or `source venv/bin/activate` (Mac/Linux)
4. Install dependencies: `pip install -r requirements.txt`
5. Create a `.env` file with your credentials:
```
PRIVATE_MAGIC_KEY=your_private_key
PROXY_ADDRESS=your_wallet_address
```

## Usage

Just run `python main.py` and follow the menus:

**Main Menu:**
- `[1]` Wallet & Orders - view holdings, manage open orders, see analytics
- `[2]` Discover Markets - search and browse markets, then trade
- `[q]` Quit

**Trading Flow:**
1. Choose discovery method (keyword search or browse by filters)
2. Pick an event from the results
3. Select a market to view the order book
4. Place a trade (market or limit order)

**Wallet Flow:**
1. View current holdings with P&L
2. Manage open limit orders (cancel specific or all)
3. Check performance stats by time period

## Code Structure

```
├── main.py                    # Entry point, main terminal logic
├── displays.py                # UI/display functions
├── data/
│   ├── events_node.py        # EventNode and MarketNode data classes
│   └── trader_node.py        # Trading client wrapper
└── backend_functions/
    ├── discovery.py          # Market search/filtering
    └── wallet_analytics.py   # Portfolio and stats functions
```

## Notes

- The terminal uses py-clob-client for order execution
- All market data comes from Polymarket's public APIs
- Search results are enriched with full event details in parallel for speed
