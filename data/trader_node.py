from py_clob_client.client import ClobClient
from py_clob_client.clob_types import BalanceAllowanceParams, TradeParams, BookParams, OrderArgs, OrderType, ApiCreds
import requests
from typing import List
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



    def get_trades(self):
        trade_params = TradeParams(
            maker_address=self.client.get_address()
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
            human_balance = raw_balance / 1_000_000
            return human_balance
        except Exception as e:
            print(f"[{self.label}] Failed to fetch balance: {e}")
            return 0.0


    def get_open_orders(self):
        return self.client.get_orders()

    def kill_limit_orders(self):
        return self.client.cancel_all()


    def cancel_specific_order(self, order_id: str):
        return self.client.cancel(order_id)

    
    def create_limit_order(self, market_node: MarketNode, outcome_index: int, side: str, price: float, size: float):
        try:
            token_id = market_node.clob_token_ids[outcome_index]
            
            order_args = OrderArgs(
                price=price,
                size=size,
                side=side,
                token_id=token_id
            )
            
            ord = self.client.create_order(order_args)
            resp = self.client.post_order(ord, OrderType.GTC)
            print(f"Limit Order Placed! ID: {resp.get('orderID')}")
            return resp
        except Exception as e:
            print(f"Limit Order Failed: {e}")
            return None   

    def place_market_order(self, market_node: MarketNode, outcome_index: int, side: str, size: float):

        try:
            token_id = market_node.clob_token_ids[outcome_index]
            aggressive_price = 0.99 if side == "BUY" else 0.01
            

            order_args = OrderArgs(
                price=aggressive_price,
                size=size,
                side=side,
                token_id=token_id
            )
            
            ord = self.client.create_order(order_args)
            resp = self.client.post_order(ord, OrderType.FOK)
            print(f"Market Order Executed! ID: {resp.get('orderID')}")
            return resp
        except Exception as e:
            print(f"Market Order Failed (Likely not enough liquidity): {e}")
            return None


    
    def get_order_book(self, token: str):
        """
        Get order books for multiple tokens.
        Returns a list of order book responses, one for each token.
        """
        try:
            book = self.client.get_order_book(token)
            return book
        except Exception as e:
            print(f"[{self.label}] Failed to fetch order book for {token}: {e}")
            return None
