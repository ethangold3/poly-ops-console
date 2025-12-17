import requests
from typing import Optional, List
from concurrent.futures import ThreadPoolExecutor
from data.events_node import EventNode
from datetime import datetime, timedelta, timezone
from difflib import SequenceMatcher


def search_events(
    q: str,
    events_status: str = "active",
    limit_per_type: int = 10,  # Changed default to 10
    sort: str = "liquidity",
    ascending: bool = False,
    optimized: bool = True,
    events_tag: Optional[List[str]] = None,
    exclude_tag_id: Optional[List[int]] = None,
    enrich: bool = True  # New parameter to control enrichment
):
    """
    Search for events using the public search endpoint.
    Automatically enriches results with full event data by fetching each event's details.
    
    Args:
        q: Search query string (required)
        events_status: Status filter (default: "active")
        limit_per_type: Max results per type (default: 10, max recommended: 20)
        sort: Sort field (default: "openInterest")
        ascending: Sort direction (default: False)
        optimized: Use optimized search (default: True)
        events_tag: List of tag slugs to filter by
        exclude_tag_id: List of tag IDs to exclude
        enrich: Fetch full details for each result (default: True)
    
    Returns:
        List of full event dictionaries (if enrich=True) or summary dicts (if enrich=False)
    """
    url = 'https://gamma-api.polymarket.com/public-search'
    
    # Build parameters
    params = {
        'q': q,
        'events_status': events_status,
        'limit_per_type': limit_per_type,
        'sort': sort,
        'ascending': ascending,
        'optimized': optimized
    }
    
    if events_tag:
        params['events_tag'] = events_tag
    
    if exclude_tag_id:
        params['exclude_tag_id'] = exclude_tag_id
    
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        search_results = response.json()
        
        events = search_results.get('events', [])
        # Filter out closed events (optionally also ended)
        events = [
            e for e in events
            if not e.get("closed", False)
        ]
        
        # If enrichment is disabled, return raw search results
        if not enrich or not events:
            return events
        
        # Enrich with full event details (in parallel)
        print(f"Enriching {len(events)} search results with full data...")
        
        def fetch_full_event(event_tuple):
            """Helper function to fetch a single event's full details."""
            index, event = event_tuple
            slug = event.get('slug')
            
            if not slug:
                return index, event, None  # Keep summary if no slug
            
            try:
                detail_url = f"https://gamma-api.polymarket.com/events/slug/{slug}"
                detail_response = requests.get(detail_url, timeout=10)
                detail_response.raise_for_status()
                full_event = detail_response.json()
                return index, full_event, None
            except Exception as e:
                return index, event, str(e)  # Return summary on error
        
        # Use ThreadPoolExecutor for parallel fetching
        enriched_events = [None] * len(events)
        max_workers = min(5, len(events))  # Limit to 5 concurrent requests
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all tasks
            futures = {executor.submit(fetch_full_event, (i, event)): i 
                      for i, event in enumerate(events)}
            
            # Collect results as they complete
            completed = 0
            for future in futures:
                index, result, error = future.result()
                enriched_events[index] = result
                completed += 1
                
                if error:
                    print(f"  [{completed}/{len(events)}] ✗ {result.get('slug', 'unknown')}: {error}")
                else:
                    print(f"  [{completed}/{len(events)}] ✓ {result.get('title', 'Unknown')[:50]}")
        
        return enriched_events
        
    except requests.exceptions.RequestException as e:
        print(f"Error searching events: {e}")
        return []





def get_current_events(
    tag_slug: Optional[str] = None,
    sort_by: str = "liquidity", 
    liquidity_min: int = 5000, 
    featured: bool = False, 
    limit: int = 500,
    show_closed: bool = False,
    ascending = False):
    sort_map = {
        "volume": "volume",         
        "hot": "volume24hr",        
        "weekly": "volume1wk",    
        "liquidity": "liquidity",
        "open_interest": "openInterest",
        "newest": "createdAt",
        "starting": "startDate",
        "ending": "endDate",
        "competitive": "competitive", # Often used for 'tight' spreads or close odds
        "featured": "featuredOrder"   # Polymarket's curated order
    }
    api_sort_field = sort_map.get(sort_by, "volume")
    
    url = 'https://gamma-api.polymarket.com/events'
    all_events = []
    offset = 0
    max_per_request = 500
    
    # Base parameters that don't change
    params_base = {
        'order': api_sort_field,
        'liquidity_min': liquidity_min,
        'ascending': ascending
    }
    
    if tag_slug:
        params_base["tag_slug"] = tag_slug.lower()
    
    if featured:
        params_base["featured"] = featured
    
    if not show_closed:
        params_base["active"] = True
        params_base["closed"] = False
        params_base["archived"] = False

    try:
        while len(all_events) < limit:
            # Calculate how many to fetch this round
            remaining = limit - len(all_events)
            current_limit = min(remaining, max_per_request)
            
            # Build params for this request
            params = params_base.copy()
            params['limit'] = current_limit
            params['offset'] = offset
            
            response = requests.get(url, params=params)
            response.raise_for_status()
            batch = response.json()
            
            # If no results, we've reached the end
            if not batch or len(batch) == 0:
                break
            
            all_events.extend(batch)
            
            # If we got fewer than requested, there's no more data
            if len(batch) < current_limit:
                break
            
            offset += len(batch)
        
        return all_events
        
    except requests.exceptions.RequestException as e:
        print(f"Error fetching events: {e}")
        return all_events  # Return what we got so far

def is_match(query: str, text: str, threshold: float = 0.4) -> bool:
    """
    Returns True if 'query' fuzzy matches 'text'.
    Uses simple token matching + sequence matching for typos.
    """
    if not query or not text:
        return False
    
    query = query.lower()
    text = text.lower()
    
    # 1. Direct substring match (Fastest)
    if query in text:
        return True
        
    # 2. Fuzzy sequence match (Handles typos)
    # .ratio() returns a float between 0 and 1
    return SequenceMatcher(None, query, text).ratio() > threshold

def filter_events(
    events: list[EventNode], 
    min_vol: float = None, 
    min_liquidity: float = None, 
    volume_24hr_min: float = None, 
    expiring_soon: bool = None,  # True = Ends within 24 hours
    search_query: str = None
) -> list[EventNode]:
    
    filtered = []
    now = datetime.now(timezone.utc)

    for e in events:
        # --- 1. SEARCH QUERY (Fuzzy) ---
        if search_query:
            # Check Title
            match_title = is_match(search_query, e.title)
            
            # Check Markets (Questions)
            match_market = False
            for m in e.markets:
                if is_match(search_query, m.question):
                    match_market = True
                    break
            
            if not (match_title or match_market):
                continue

        # --- 2. NUMERIC FILTERS ---
        if min_vol is not None and e.volume < min_vol:
            continue

        if volume_24hr_min is not None and e.volume_24hr < volume_24hr_min:
            continue
            
        # For liquidity, we check if ANY market in the event meets the liquidity req
        # (Since events don't have liquidity, only markets do)
        if min_liquidity is not None:
            max_market_liq = max([m.liquidity for m in e.markets]) if e.markets else 0
            if max_market_liq < min_liquidity:
                continue

        # --- 3. TIME FILTERS ---
        if expiring_soon:
            # We need to look at market end dates. 
            # Note: You'll need to ensure your MarketNode parses 'endDate' (ISO string)
            has_expiring = False
            for m in e.markets:
                # Assuming m.end_date is an ISO string "2025-12-31T23:59..."
                # We interpret it safely:
                try:
                    # Python 3.11+ handles ISO parsing automatically
                    end_dt = datetime.fromisoformat(m.end_date.replace("Z", "+00:00"))
                    time_left = end_dt - now
                    if timedelta(hours=0) < time_left < timedelta(hours=48):
                        has_expiring = True
                        break
                except (ValueError, AttributeError):
                    continue
            
            if not has_expiring:
                continue

        # If it survived all checks, add it
        filtered.append(e)

    return filtered
