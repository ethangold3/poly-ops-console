from data.events_node import EventNode
from typing import List, Dict, Any
import time

def print_orderbook_summary(orderbook, market_title):
    """
    Prints a readable dashboard of the top 7 bids and asks closest to the spread.
    Sorts logic: Best Bids = Highest Prices | Best Asks = Lowest Prices.
    """
    # 1. Sort and Slice: Get the top 7 closest to the spread
    # Bids: Descending (Highest price is best)
    # Asks: Ascending (Lowest price is best)
    best_bids = sorted(orderbook.bids, key=lambda x: float(x.price), reverse=True)[:7]
    best_asks = sorted(orderbook.asks, key=lambda x: float(x.price), reverse=False)[:7]

    print(f"\n{'='*55}")
    print(f"{market_title:^55}")
    print(f"{'='*55}")
    print(f"{'BID SIZE':>12} | {'BID PRICE':>10}   {'ASK PRICE':<10} | {'ASK SIZE':<12}")
    print(f"{'-'*12}-+-{'-'*10}---{'-'*10}-+-{'-'*12}")

    for i in range(7):
        b_price = float(best_bids[i].price) if i < len(best_bids) else None
        b_size  = float(best_bids[i].size)  if i < len(best_bids) else None
        a_price = float(best_asks[i].price) if i < len(best_asks) else None
        a_size  = float(best_asks[i].size)  if i < len(best_asks) else None

        b_str_price = f"{b_price:10.3f}" if b_price is not None else "          "
        b_str_size  = f"{b_size:12.2f}"  if b_size  is not None else "            "
        a_str_price = f"{a_price:<10.3f}" if a_price is not None else "          "
        a_str_size  = f"{a_size:<12.2f}"  if a_size  is not None else "            "

        print(f"{b_str_size} | {b_str_price}   {a_str_price} | {a_str_size}")

    print(f"{'='*55}\n")

def display_events_menu(events: list[EventNode]):
    """Prints a numbered menu of events for the user to select."""
    print("\nTOP ACTIVE EVENTS")
    print("=" * 80)
    print(f"{'#':<4} | {'Event Name':<50} | {'Volume':<15}")
    print("-" * 80)
    
    for i, e in enumerate(events):
        # Truncate title if it's too long
        title = (e.title[:47] + "...") if len(e.title) > 47 else e.title
        print(f"{i+1:<4} | {title:<50} | ${e.volume:,.0f}")
    
    print("=" * 80)


def display_event_table(event):
    """
    Display markets in an event with numbers for selection.
    Returns the sorted list of markets for interaction.
    """
    print(f"\nDRILL DOWN: {event.title}")
    print("=" * 105)
    print(f"{'#':<4} | {'ID':<10} | {'Question':<60} | {'Yes Price':<10} | {'Liq':<10}")
    print("-" * 105)
    
    # Sort markets by probability (primary_price) in descending order
    sorted_markets = sorted(event.markets, key=lambda m: m.primary_price, reverse=True)
    
    for i, m in enumerate(sorted_markets, 1):
        q_text = (m.question[:57] + '...') if len(m.question) > 57 else m.question
        print(f"{i:<4} | {m.id:<10} | {q_text:<60} | {m.primary_price:<10.2f} | ${m.liquidity:,.0f}")
    
    print("=" * 105)
    
    return sorted_markets


def display_holdings(holdings: List[Dict[str, Any]]):
    """
    Display user's current holdings/positions in a formatted table.
    
    Args:
        holdings: List of position dictionaries from get_holdings()
    """
    if not holdings:
        print("\nNo holdings found.")
        return
    
    print("\n" + "=" * 150)
    print(f"{'PORTFOLIO HOLDINGS':^150}")
    print("=" * 150)
    
    total_value = sum(pos.get('currentValue', 0) for pos in holdings)
    total_pnl = sum(pos.get('cashPnl', 0) for pos in holdings)
    total_initial = sum(pos.get('initialValue', 0) for pos in holdings)
    total_pct_pnl = ((total_pnl / total_initial) * 100) if total_initial > 0 else 0
    
    print(f"\nTotal Portfolio Value: ${total_value:,.2f}")
    print(f"Total P&L: ${total_pnl:,.2f} ({total_pct_pnl:+.2f}%)")
    print(f"Positions: {len(holdings)}\n")
    
    print(f"{'#':<4} | {'Market':<50} | {'Side':<4} | {'Size':<8} | {'Avg':<7} | {'Curr':<7} | {'Value':<10} | {'P&L $':<10} | {'P&L %':<10}")
    print("-" * 150)
    
    sorted_holdings = sorted(holdings, key=lambda x: abs(x.get('cashPnl', 0)), reverse=True)
    
    for i, pos in enumerate(sorted_holdings, 1):
        title = pos.get('title', 'Unknown Market')
        title_short = (title[:47] + '...') if len(title) > 47 else title
        
        outcome = pos.get('outcome', '?')
        size = pos.get('size', 0)
        avg_price = pos.get('avgPrice', 0)
        cur_price = pos.get('curPrice', 0)
        current_value = pos.get('currentValue', 0)
        cash_pnl = pos.get('cashPnl', 0)
        pct_pnl = pos.get('percentPnl', 0)
        
        pnl_indicator = "+" if cash_pnl >= 0 else "-"
        
        print(f"{i:<4} | {title_short:<50} | {outcome:<4} | {size:<8.1f} | ${avg_price:<6.3f} | ${cur_price:<6.3f} | ${current_value:<9.2f} | {pnl_indicator}${abs(cash_pnl):<8.2f} | {pct_pnl:+9.2f}%")
    
    print("=" * 150)
    print(f"{'TOTAL':<69} | ${total_value:<9.2f} | ${total_pnl:<9.2f} | {total_pct_pnl:+9.2f}%")
    print("=" * 150 + "\n")


def display_wallet_analytics(analytics: Dict[str, Any]):
    """
    Display wallet performance analytics from leaderboard.
    
    Args:
        analytics: Dictionary with keys time_period, pnl, volume, rank, username
    """
    if not analytics:
        print("\nNo analytics data available.")
        return
    
    time_period = analytics.get('time_period', 'N/A')
    pnl = analytics.get('pnl', 0)
    volume = analytics.get('volume', 0)
    rank = analytics.get('rank')
    username = analytics.get('username', 'Anonymous')
    
    period_display = {
        'DAY': 'Today',
        'WEEK': 'This Week',
        'MONTH': 'This Month',
        'ALL': 'All Time'
    }.get(time_period, time_period)
    
    pnl_indicator = "+" if pnl >= 0 else "-"
    rank_display = f"#{rank}" if rank else "Unranked"
    
    print("\n" + "=" * 70)
    print(f"{'WALLET ANALYTICS':^70}")
    print("=" * 70)
    print(f"\nUser: {username}")
    print(f"Period: {period_display}")
    print(f"{pnl_indicator} P&L: ${pnl:,.2f}")
    print(f"Volume: ${volume:,.2f}")
    print(f"Rank: {rank_display}")
    print("=" * 70 + "\n")


def display_open_orders(orders: List[Dict[str, Any]]):
    """
    Display user's open orders in a formatted table.
    
    Args:
        orders: List of order dictionaries from get_limit_orders()
    
    Returns:
        List of live orders for further interaction
    """
    if not orders:
        print("\nNo open orders found.")
        return []
    
    live_orders = [order for order in orders if order.get('status') == 'LIVE']
    
    if not live_orders:
        print("\nNo open orders found.")
        return []
    
    print("\n" + "=" * 130)
    print(f"{'OPEN ORDERS':^130}")
    print("=" * 130)
    print(f"\nTotal Open Orders: {len(live_orders)}\n")
    
    print(f"{'#':<4} | {'Order ID':<12} | {'Market':<35} | {'Side':<4} | {'Outcome':<7} | {'Price':<8} | {'Size':<8} | {'Filled':<8} | {'Type':<5} | {'Age':<12}")
    print("-" * 130)
    
    sorted_orders = sorted(live_orders, key=lambda x: x.get('created_at', 0), reverse=True)
    
    current_time = int(time.time())
    
    for i, order in enumerate(sorted_orders, 1):
        order_id = order.get('id', 'N/A')[:10]
        market = order.get('market', 'Unknown')[:33]
        side = order.get('side', '?')
        outcome = order.get('outcome', '?')
        price = order.get('price', 0)
        original_size = float(order.get('original_size', 0))
        size_matched = float(order.get('size_matched', 0))
        size_remaining = original_size - size_matched
        order_type = order.get('order_type', 'N/A')
        created_at = order.get('created_at', 0)
        
        age_seconds = current_time - created_at
        if age_seconds < 60:
            age_str = f"{age_seconds}s"
        elif age_seconds < 3600:
            age_str = f"{age_seconds // 60}m"
        elif age_seconds < 86400:
            age_str = f"{age_seconds // 3600}h"
        else:
            age_str = f"{age_seconds // 86400}d"
        
        filled_pct = (size_matched / original_size * 100) if original_size > 0 else 0
        filled_str = f"{filled_pct:.0f}%"
        
        side_indicator = "+" if side == "BUY" else "-"
        
        print(f"{i:<4} | {order_id:<12} | {market:<35} | {side_indicator}{side:<3} | {outcome:<7} | ${float(price):<7.3f} | {size_remaining:<8.1f} | {filled_str:<8} | {order_type:<5} | {age_str:<12}")
    
    print("=" * 130 + "\n")
    
    return live_orders