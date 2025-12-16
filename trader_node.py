from py_clob_client.client import ClobClient
from py_clob_client.clob_types import ApiCreds
from py_clob_client.clob_types import BalanceAllowanceParams, TradeParams
import requests

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