from py_clob_client.client import ClobClient
from py_clob_client.clob_types import BalanceAllowanceParams, TradeParams, BookParams, OrderArgs, OrderType, ApiCreds
import requests
from typing import List
from displays import print_orderbook_summary
from data.events_node import MarketNode

class TraderNode:
    def __init__(self, private_key, sig_type, funder, label):
        self.private_key = private_key
        self.sig_type = sig_type
        self.label = label
        self.funder = funder
        self.client = self._connect()

    
    def _connect(self):
        try:
            temp_client = ClobClient(
                "https://clob.polymarket.com",
                chain_id=137,
                key=self.private_key,
                signature_type=self.sig_type,
                funder=self.funder
            )
            creds = temp_client.create_or_derive_api_creds()
            temp_client.set_api_creds(creds)
            return temp_client
        except Exception as e:
            print("Error connecting in TraderNode._connect:", e)
            return

    def get_holdings(self):

        url = 'https://data-api.polymarket.com/positions'
        all_positions = []
        offset = 0
        limit = 500
        has_more = True

        params_base = {
            "user": self.funder,
            "sizeThreshold": 1,
            "sortBy": "TOKENS",
            "sortDirection": "DESC"
        }

        try:
            while has_more:
                params = params_base.copy()
                params["offset"] = offset
                params["limit"] = limit

                response = requests.get(url, params=params)
                response.raise_for_status()
                current_batch = response.json()  # API returns a direct list
                
                all_positions.extend(current_batch)

                if len(current_batch) < limit:
                    has_more = False
                else:
                    offset += limit
            return all_positions
        except Exception as e:
            print(f"[{self.label}] ❌ Failed to fetch holdings: {e}")
            return None


    def get_trades(self):
        trade_params = TradeParams(
        maker_address=self.client.get_address()
            # before=before,
            # after=after
        )
        print(trade_params)
        resp = self.client.get_trades(trade_params)
        print(resp)
        return resp


    def get_cash_on_hand(self):
        try: 
            params = BalanceAllowanceParams(
                    asset_type="COLLATERAL", 
                    signature_type=self.sig_type
                )
            resp = self.client.get_balance_allowance(params)
            raw_balance = int(resp.get("balance", 0))
                
            # Convert from atomic units (1000000 = $1.00)
            human_balance = raw_balance / 1_000_000
            return human_balance
        except Exception as e:
            print(f"[{self.label}] ❌ Failed to fetch balance: {e}")
            return 0.0

    def get_pnl(self):
        return

    def get_limit_orders(self):
        return self.client.get_orders()

    def kill_limit_orders(self):
        return self.client.cancel_all()

    def sharpe_ratio(self):
        return

    # def create_market_order(self, token: str, side: str, size: float, price: float):
    #     order_params = OrderArgs(
    #     return self.client.create_and_post_order(token, side, size, price)
    
    def create_limit_order(self, market_node: MarketNode, outcome_index: int, side: str, price: float, size: float):
        try:
            token_id = market_node.clob_token_ids[outcome_index]
            
            order_args = OrderArgs(
                price=price,
                size=size,
                side=side,  # BUY or SELL
                token_id=token_id
            )
            
            # GTC = Good Til Cancelled (Standard Limit Order)
            ord = self.client.create_order(order_args)
            resp = self.client.post_order(ord, OrderType.GTC)
            print(f"✅ Limit Order Placed! ID: {resp.get('orderID')}")
            return resp
        except Exception as e:
            print(f"❌ Limit Order Failed: {e}")
            return None   

    def place_market_order(self, market_node: MarketNode, outcome_index: int, side: str, size: float):

        try:
            token_id = market_node.clob_token_ids[outcome_index]
            
            # 1. Determine "Aggressive" Price to ensure fill
            # If Buying, we are willing to pay up to 100 cents (worst case) to ensure we get it.
            # If Selling, we are willing to sell down to 0 cents.
            # (The matching engine gives you the Best Execution price regardless)
            aggressive_price = 0.99 if side == "BUY" else 0.01
            

            order_args = OrderArgs(
                price=aggressive_price,
                size=size,
                side=side,
                token_id=token_id
            )
            
            # FOK = Fill Or Kill. Either fill the WHOLE size immediately, or cancel.
            # This protects you from getting partially filled on a tiny order.
            ord = self.client.create_order(order_args)
            resp = self.client.post_order(ord, OrderType.FOK)
            print(f"⚡ Market Order Executed! ID: {resp.get('orderID')}")
            print('printing full order response: ', resp)
            return resp
        except Exception as e:
            print(f"❌ Market Order Failed (Likely not enough liquidity): {e}")
            return None


    def get_markets(self):
        return self.client.get_markets()
    
    def get_order_book(self, token: str):
        """
        Get order books for multiple tokens.
        Returns a list of order book responses, one for each token.
        """
        try:
            book = self.client.get_order_book(token)
            return book
        except Exception as e:
            print(f"[{self.label}] ❌ Failed to fetch order book for {token}: {e}")
            return None

# if __name__ == "__main__":
#     import os
#     from dotenv import load_dotenv
#     load_dotenv()
#     trader_node = TraderNode(private_key = os.getenv("INTERVIEW_PRIVATE_MAGIC_KEY"), sig_type = 1, funder = os.getenv("INTERVIEW_PROXY_ADDRESS"), label = "Test Node")
#     print(trader_node.get_holdings())
#     print(trader_node.get_)