import json
from dataclasses import dataclass, field
from typing import List, Dict, Any

@dataclass
class MarketNode:
    """
    Represents a single tradable market contract.
    """
    id: str
    condition_id: str
    clob_token_ids: List[str]
    question: str
    outcomes: List[str]
    outcome_prices: List[str]
    uma_bond: str
    liquidity: float
    volume: float
    volume_24hr: float
    volume_1wk: float
    price_change_24hr: float
    end_date: str
    best_bid: float = 0.0
    best_ask: float = 0.0

    @property
    def tokens(self) -> Dict[str, str]:
        if len(self.outcomes) == len(self.clob_token_ids):
            return dict(zip(self.outcomes, self.clob_token_ids))
        return {}

    @property
    def primary_price(self) -> float:
        try:
            return float(self.outcome_prices[0])
        except (ValueError, IndexError, TypeError):
            return 0.0

@dataclass
class EventNode:
    """
    Represents the parent Event (Topic) containing one or more Markets.
    """
    id: str
    slug: str
    title: str
    description: str
    
    # Metadata
    created_at: str
    volume: float
    volume_24hr: float
    markets: List[MarketNode] = field(default_factory=list)

    @classmethod
    def from_json(cls, data: Dict[str, Any]):
        """
        Parses Polymarket API data, handling two distinct structural cases:
        1. Multi-Market Event (Standard): Root is Event, contains "markets" list.
        2. Single Market (Direct Lookup): Root is Market, contains nested "events" list.
        """
        
        # --- 1. Normalization Strategy ---
        # We need to determine where the Event Metadata lives and where the Market List lives.

        event_source: Dict[str, Any] = {}
        market_list_source: List[Dict[str, Any]] = []

        # Check: Is the root object the Event (Case B)?
        # We assume if "markets" exists and is a list, it's the Event view.
        if "markets" in data and isinstance(data["markets"], list):
            event_source = data
            market_list_source = data["markets"]
            
        # Check: Is the root object the Market (Case A)?
        # If no "markets" key, but we see "events" or "question", it's the Market view.
        else:
            # In this case, the Root IS the market. We wrap it in a list.
            market_list_source = [data]
            
            # The Event metadata is nested inside the 'events' list.
            # We try to grab the first event associated with this market.
            raw_events = data.get("events", [])
            if isinstance(raw_events, list) and len(raw_events) > 0:
                event_source = raw_events[0]
            else:
                # Fallback: If no parent event info is found, we use the root data 
                # (This is messy but prevents crashing on malformed data)
                event_source = data

        # --- Helper Functions ---
        def to_float(val):
            try:
                return float(val) if val is not None else 0.0
            except (ValueError, TypeError):
                return 0.0

        def safe_json_load(val):
            """Parses stringified JSON or returns the list if already parsed."""
            if isinstance(val, list):
                return val
            if isinstance(val, str):
                try:
                    return json.loads(val)
                except json.JSONDecodeError:
                    return []
            return []

        # --- 2. Process Markets ---
        market_nodes = []
        for m in market_list_source:
            market_nodes.append(MarketNode(
                id=str(m.get("id")),
                condition_id=str(m.get("conditionId")),
                clob_token_ids=safe_json_load(m.get("clobTokenIds")),
                
                # In Case A (Root=Market), 'question' is at root. 
                # In Case B (Root=Event), 'question' is in the market list item.
                # Since 'm' iterates over the correct source, this works for both.
                question=str(m.get("question") or m.get("title") or "Unknown Question"),
                
                outcomes=safe_json_load(m.get("outcomes")),
                outcome_prices=safe_json_load(m.get("outcomePrices")),
                uma_bond=str(m.get("umaBond")),
                
                liquidity=to_float(m.get("liquidity")),
                volume=to_float(m.get("volume")),
                volume_24hr=to_float(m.get("volume24hr")),
                volume_1wk=to_float(m.get("volume1wk")),
                price_change_24hr=to_float(m.get("oneDayPriceChange") or m.get("priceChange24h")),
                
                best_bid=to_float(m.get("bestBid")),
                best_ask=to_float(m.get("bestAsk")),
                end_date=str(m.get("endDate"))
            ))

        # --- 3. Return the Parent EventNode ---
        # We populate this using the 'event_source' we identified in Step 1.
        return cls(
            id=str(event_source.get("id")),
            slug=str(event_source.get("slug", "")),
            title=str(event_source.get("title", "Unknown Event")),
            description=str(event_source.get("description", "")),
            created_at=str(event_source.get("createdAt", "")),
            
            # Event-level volume metrics
            volume=to_float(event_source.get("volume")),
            volume_24hr=to_float(event_source.get("volume24hr")),
            
            markets=market_nodes
        )