import requests
from typing import Literal, Optional, Dict, Any


def get_wallet_analytics(
    user: str,
    time_period: Literal["DAY", "WEEK", "MONTH", "ALL"] = "DAY"
) -> Optional[Dict[str, Any]]:
    """
    Get wallet performance analytics from Polymarket leaderboard API.
    
    Args:
        user: Proxy address (wallet address) to query
        time_period: Time period for analytics - one of DAY, WEEK, MONTH, ALL
    
    Returns:
        Dictionary with keys: pnl, vol, rank, userName
        Returns None if user not found or error occurs
    """
    url = "https://data-api.polymarket.com/v1/leaderboard"
    
    params = {
        "category": "OVERALL",
        "timePeriod": time_period,
        "orderBy": "PNL",
        "limit": 25,
        "user": user
    }
    
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        
        # The API returns a list of leaderboard entries
        # When a specific user is queried, it typically returns their entry
        if isinstance(data, list) and len(data) > 0:
            # Find the user's entry (should be in the list)
            user_entry = None
            for entry in data:
                if entry.get("user") == user or entry.get("walletAddress") == user:
                    user_entry = entry
                    break
            
            # If not found by matching, might be the only/first entry returned
            if not user_entry and len(data) == 1:
                user_entry = data[0]
            
            if user_entry:
                return {
                    "time_period": time_period,
                    "pnl": user_entry.get("pnl", 0),
                    "volume": user_entry.get("vol", 0),
                    "rank": user_entry.get("rank"),
                    "username": user_entry.get("userName")
                }
        
        # If we get here, user not found
        return None
        
    except requests.exceptions.RequestException as e:
        print(f"Error fetching wallet analytics: {e}")
        return None


def get_holdings(user: str):

        url = 'https://data-api.polymarket.com/positions'
        all_positions = []
        offset = 0
        limit = 500
        has_more = True

        params_base = {
            "user": user,
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
            print(f"Failed to fetch holdings: {e}")
            return None