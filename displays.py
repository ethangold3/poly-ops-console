from data.events_node import EventNode
from typing import List, Dict, Any

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

    # 2. Print Header
    print(f"\n{'='*55}")
    print(f"{market_title:^55}")
    print(f"{'='*55}")
    print(f"{'BID SIZE':>12} | {'BID PRICE':>10}   {'ASK PRICE':<10} | {'ASK SIZE':<12}")
    print(f"{'-'*12}-+-{'-'*10}---{'-'*10}-+-{'-'*12}")

    # 3. Print Rows
    for i in range(7):
        # Extract data if available, else use empty strings
        b_price = float(best_bids[i].price) if i < len(best_bids) else None
        b_size  = float(best_bids[i].size)  if i < len(best_bids) else None
        a_price = float(best_asks[i].price) if i < len(best_asks) else None
        a_size  = float(best_asks[i].size)  if i < len(best_asks) else None

        # Format strings (showing '-' if no order exists at that depth)
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