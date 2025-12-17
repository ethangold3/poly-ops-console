import sys
import os
from typing import Any, List, Optional
from dotenv import load_dotenv

from data.trader_node import TraderNode
from data.events_node import EventNode
from backend_functions.discovery import search_events, get_current_events, filter_events
from backend_functions.wallet_analytics import get_wallet_analytics, get_holdings
from displays import (
    display_events_menu, display_event_table, print_orderbook_summary,
    display_holdings, display_wallet_analytics, display_open_orders
)

load_dotenv()

class PolyTerminal:
    def __init__(self):
        self.proxy_address = os.getenv("PROXY_ADDRESS")
        self.private_key = os.getenv("PRIVATE_MAGIC_KEY")

        if not self.proxy_address or not self.private_key:
            print("Error: PROXY_ADDRESS and PRIVATE_MAGIC_KEY must be set in your .env file.")
            sys.exit(1)
        
        # Initialize the trader node immediately
        self.trader = TraderNode(
            private_key=self.private_key,
            sig_type=1,
            funder=self.proxy_address,
            label="Trading Node"
        )

    # --- INPUT HELPERS ---
    def _get_input(self, prompt: str, default: Any = None, cast_type: type = str) -> Any:
        user_val = input(f"{prompt} [default: {default}]: ").strip()
        if not user_val:
            return default
        try:
            if cast_type == bool:
                return user_val.lower() in ('true', 't', 'yes', 'y', '1')
            return cast_type(user_val)
        except ValueError:
            print(f"Invalid input type. Using default: {default}")
            return default

    def _get_float(self, prompt: str, min_val: float = None, max_val: float = None) -> Optional[float]:
        while True:
            try:
                user_input = input(f"{prompt}: ").strip()
                if not user_input:
                    return None
                
                val = float(user_input)
                if min_val is not None and val < min_val:
                    print(f"Value must be > {min_val}")
                    continue
                if max_val is not None and val > max_val:
                    print(f"Value must be < {max_val}")
                    continue
                return val
            except ValueError:
                print("Invalid number.")
            except KeyboardInterrupt:
                return None

    # --- WALLET & ANALYTICS ---
    def run_wallet_menu(self):
        while True:
            print(f"\n{'='*80}\nWALLET MENU\n{'='*80}")
            print(" [1] Current Holdings")
            print(" [2] Manage Open Orders")
            print(" [3] PnL & Volume")
            print(" [b] Back")
            
            choice = input("\nAction: ").strip().lower()
            if choice == 'b': return
            
            if choice == '1':
                self._show_holdings()
            elif choice == '2':
                self._manage_orders()
            elif choice == '3':
                self._show_analytics()

    def _show_holdings(self):
        print("\nFetching your current holdings from Polymarket...")
        try:
            holdings = get_holdings(self.proxy_address)
            if holdings:
                display_holdings(holdings)
            else:
                print("You have no open positions. Start trading to build your portfolio!")
        except Exception as e:
            print(f"Error fetching holdings: {e}")
        input("\nPress Enter to continue...")

    def _manage_orders(self):
        # Refresh loop for order management
        while True:
            print("\nFetching open orders...")
            try:
                orders = self.trader.get_open_orders()
                if not orders:
                    print("You have no open orders. All your orders have been filled or cancelled!")
                    input("\nPress Enter to continue...")
                    return

                live_orders = display_open_orders(orders)
                if not live_orders: return

                print("\nORDER MANAGEMENT:")
                print("   [1,2,3...] Enter order number to cancel that specific order")
                print("   [a] Cancel ALL open orders")
                print("   [r] Refresh order list")
                print("   [b] Back to wallet menu")
                action = input("\nEnter your choice: ").strip().lower()

                if action == 'b': return
                if action == 'r': continue
                if action == 'a':
                    print(f"\nWARNING: You are about to cancel ALL {len(live_orders)} open orders!")
                    print("   This action cannot be undone.")
                    if input("\nType 'yes' to confirm: ").lower() == 'yes':
                        try:
                            self.trader.kill_limit_orders()
                            print("All orders cancelled successfully!")
                        except Exception as e:
                            print(f"Error: {e}")
                    else:
                        print("Cancellation aborted.")
                    continue
                
                try:
                    idx = int(action) - 1
                    if 0 <= idx < len(live_orders):
                        self._cancel_single_order(live_orders[idx])
                except ValueError:
                    pass

            except Exception as e:
                print(f"Error: {e}")
                return

    def _cancel_single_order(self, order_data):
        order_id = order_data.get('id')
        print(f"\nCANCEL ORDER:")
        print(f"   Order ID: {order_id[:20]}...")
        print(f"   Side: {order_data.get('side')}")
        print(f"   Outcome: {order_data.get('outcome')}")
        print(f"   Price: ${float(order_data.get('price', 0)):.3f}")
        print(f"   Size: {float(order_data.get('original_size', 0)):.1f} shares")
        
        if input("\nConfirm cancellation? (y/n): ").lower() == 'y':
            try:
                self.trader.cancel_specific_order(order_id)
                print("Order cancelled successfully!")
            except Exception as e:
                print(f"Error cancelling order: {e}")
        else:
            print("Cancellation aborted.")

    def _show_analytics(self):
        period_map = {'1': 'DAY', '2': 'WEEK', '3': 'MONTH', '4': 'ALL'}
        print("\nSELECT TIME PERIOD FOR ANALYTICS:")
        print("   [1] Today (last 24 hours)")
        print("   [2] This Week (last 7 days)")
        print("   [3] This Month (last 30 days)")
        print("   [4] All Time (complete history)")
        p = input("\nEnter period (1-4): ").strip()
        
        if p in period_map:
            try:
                data = get_wallet_analytics(self.proxy_address, period_map[p])
                if data:
                    display_wallet_analytics(data)
                else:
                    print("No analytics data found for this time period.")
                    print("   This may mean you haven't traded during this period or aren't ranked yet.")
            except Exception as e:
                print(f"Error: {e}")
        input("\nPress Enter...")

    # --- MARKET DISCOVERY ---
    def run_discovery_flow(self):
        # Step 1: Get Data
        events = self._fetch_events()
        if not events: return

        # Step 2: Browse Loop
        current_view = events[:]
        while True:
            display_events_menu(current_view)
            print("\nAVAILABLE ACTIONS:")
            print("   [1,2,3...] Enter event number to inspect markets")
            print("   [f] Filter results by title, volume, or liquidity")
            print("   [r] Reset filters (show all events)")
            print("   [w] Open wallet menu")
            print("   [n] Start new search")
            print("   [q] Quit application")
            
            choice = input("Action: ").strip().lower()
            
            if choice == 'q': sys.exit()
            if choice == 'w': self.run_wallet_menu()
            if choice == 'r': current_view = events[:]
            if choice == 'n': return
            
            if choice == 'f':
                params = {
                    "search_query": self._get_input("Search Title", default=None),
                    "min_vol": self._get_input("Min Vol", default=None, cast_type=float),
                    "min_liquidity": self._get_input("Min Liq", default=None, cast_type=float),
                    "expiring_soon": self._get_input("Expiring <48h?", default=False, cast_type=bool)
                }
                current_view = filter_events(events, **params)
            
            elif choice.isdigit():
                idx = int(choice) - 1
                if 0 <= idx < len(current_view):
                    self._handle_event_selection(current_view[idx])

    def _fetch_events(self) -> List[EventNode]:
        print("\n[1] Keyword Search  [2] Attribute Filter")
        method = self._get_input("Method", default="2")

        try:
            if method == "1":
                q = input("Search term: ").strip()
                if not q: return []
                raw = search_events(q=q)
            else:
                use_filter = self._get_input("Use filters?", default=False, cast_type=bool)
                
                tag_slug = None
                sort_by = "volume"
                liquidity_min = 0
                limit = 20
                featured = False
                show_closed = False
                ascending = False

                if use_filter:
                    tag_slug = self._get_input("Tag slug (e.g. 'politics')", default=None)
                    sort_by = self._get_input("Sort By", default="volume")
                    liquidity_min = self._get_input("Min Liquidity", default=5000, cast_type=int)
                    limit = self._get_input("Limit", default=20, cast_type=int)
                    featured = self._get_input("Featured Only?", default=False, cast_type=bool)
                    show_closed = self._get_input("Show Closed?", default=False, cast_type=bool)
                    ascending = self._get_input("Ascending Order?", default=False, cast_type=bool)
                
                params = {
                    "tag_slug": tag_slug,
                    "sort_by": sort_by,
                    "liquidity_min": liquidity_min,
                    "limit": limit,
                    "featured": featured,
                    "show_closed": show_closed,
                    "ascending": ascending
                }
                
                print(f"\nFetching with: {params}")
                raw = get_current_events(**params)

            if not raw:
                print("No events found.")
                return []
            
            return [EventNode.from_json(i) for i in raw]
            
        except Exception as e:
            print(f"API Error: {e}")
            return []

    def _handle_event_selection(self, event: EventNode):
        while True:
            sorted_markets = display_event_table(event)
            print("\nMARKET ACTIONS:")
            print("   [1,2,3...] Enter market number to view order book & trade")
            print("   [w] Open wallet menu")
            print("   [b] Back to events list")
            choice = input("\nEnter your choice: ").strip().lower()

            if choice == 'b': break
            if choice == 'w': 
                self.run_wallet_menu()
                continue
            
            if choice.isdigit():
                idx = int(choice) - 1
                if 0 <= idx < len(sorted_markets):
                    self._handle_market_interaction(sorted_markets[idx])

    def _handle_market_interaction(self, market):
        if not market.clob_token_ids:
            print("This market doesn't have valid trading tokens available.")
            return

        token_id = market.clob_token_ids[0]
        print(f"\nFetching live order book...")
        print(f"   Market: {market.question[:70]}")
        
        try:
            book = self.trader.get_order_book(token_id)
            if book:
                print_orderbook_summary(book, market.question)
                if input("\nWould you like to place a trade on this market? (y/n): ").lower() == 'y':
                    self._execute_trade_flow(market)
            else:
                print("Order book is empty - no liquidity available for trading.")
        except Exception as e:
            print(f"Error fetching order book: {e}")
        
        input("\nPress Enter to continue...")

    # --- TRADING LOGIC ---
    def _execute_trade_flow(self, market):
        # 1. Outcome Selection
        print("\nWHICH OUTCOME DO YOU WANT TO BUY?")
        print("   [1] YES - Buy shares that pay $1 if outcome is YES")
        print("   [2] NO  - Buy shares that pay $1 if outcome is NO")
        outcome = input("\nChoose outcome (1 or 2): ").strip()
        if outcome not in ['1', '2']: 
            print("Invalid choice. Trade cancelled.")
            return
        
        outcome_idx = int(outcome) - 1
        outcome_str = market.outcomes[outcome_idx] if outcome_idx < len(market.outcomes) else ("YES" if outcome == '1' else "NO")

        # 2. Type Selection
        print(f"\nORDER TYPE FOR {outcome_str}:")
        print("   [1] Market Order - Execute immediately at best available price")
        print("   [2] Limit Order  - Set your own price (may not fill immediately)")
        type_choice = input("\nChoose order type (1 or 2): ").strip()
        if type_choice not in ['1', '2']: 
            print("Invalid choice. Trade cancelled.")
            return

        # 3. Parameters
        price = None
        if type_choice == '2':
            price = self._get_float("Price (0.01 - 0.99)", 0.001, 0.999)
            if not price: return

        print(f"\nHOW MANY SHARES DO YOU WANT TO BUY?")
        print(f"   Minimum: 1 share")
        size = self._get_float("Number of shares", min_val=1.0)
        if not size: 
            print("Invalid size. Trade cancelled.")
            return

        # 4. Confirmation
        print("\n" + "="*70)
        print("TRADE CONFIRMATION")
        print("="*70)
        try:
            balance = self.trader.get_cash_on_hand()
            print(f"Your USDC Balance: ${balance:,.2f}")
        except:
            pass
        
        print(f"\n   Market: {market.question[:60]}")
        print(f"   Outcome: {outcome_str}")
        print(f"   Side: BUY")
        print(f"   Order Type: {'Market Order' if type_choice == '1' else 'Limit Order'}")
        if price:
            print(f"   Price: ${price:.3f} per share")
            print(f"   Size: {size:.2f} shares")
            print(f"   Estimated Cost: ${price * size:.2f}")
        else:
            print(f"   Size: {size:.2f} shares")
            print(f"   Cost: Market price (best available)")
        print("="*70)
        
        if input("\nExecute this trade? (y/n): ").lower() != 'y': 
            print("Trade cancelled.")
            return

        # 5. Execution
        print("\nSending order...")
        try:
            if type_choice == '1':
                res = self.trader.place_market_order(market, outcome_idx, "BUY", size)
            else:
                res = self.trader.create_limit_order(market, outcome_idx, "BUY", price, size)
            
            status = res.get('status')
            if status == 'success': print("FILLED")
            elif status == 'live': print("ORDER LIVE (Unfilled)")
            else: print(f"Failed: {res}")
            
        except Exception as e:
            print(f"Execution Error: {e}")

    # --- MAIN ENTRY ---
    def run(self):
        while True:
            print(f"\n{'='*80}\nPOLYMARKET TERMINAL\n{'='*80}")
            print(" [1] Wallet & Orders")
            print(" [2] Discover Markets")
            print(" [q] Quit")
            
            choice = input("\nAction: ").strip().lower()
            
            if choice == 'q': 
                print("\nGoodbye!")
                sys.exit()
            elif choice == '1': 
                self.run_wallet_menu()
            elif choice == '2': 
                self.run_discovery_flow()
            else: 
                print("Invalid choice. Please enter 1, 2, or q.")

if __name__ == "__main__":
    print("\n" + "="*80)
    print("WELCOME TO POLYMARKET TRADING TERMINAL")
    print("="*80)
    print("Initializing trader node and connecting to exchange...")
    
    try:
        app = PolyTerminal()
        print("Connected successfully!")
        app.run()
    except Exception as e:
        print(f"Failed to initialize: {e}")
        print("   Please check your .env file has PRIVATE_MAGIC_KEY and PROXY_ADDRESS")
        sys.exit(1)