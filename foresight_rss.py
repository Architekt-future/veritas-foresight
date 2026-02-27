"""
Veritas Foresight — Context Bridge v1.0
Lightweight RSS reader that builds current information field context.
Independent from Veritas Protocol — no shared dependencies.

Feeds the ForesightEngine with hot topics from the real world,
so argument resonance is grounded in what's actually happening now.
"""

import urllib.request
import re
from typing import List, Dict
from datetime import datetime, timezone


# RSS feeds — same philosophy as Veritas Context Engine
# but trimmed for speed and independence
RSS_FEEDS = [
    'https://feeds.bbci.co.uk/news/world/rss.xml',
    'https://rss.nytimes.com/services/xml/rss/nyt/World.xml',
    'https://feeds.reuters.com/reuters/worldNews',
    'https://www.theguardian.com/world/rss',
    'https://feeds.skynews.com/feeds/rss/world.xml',
]

# Topic clusters for keyword extraction
TOPIC_CLUSTERS = {
    'ai_tech':      ['ai', 'artificial intelligence', 'openai', 'chatgpt', 'gemini',
                     'quantum', 'neural', 'model', 'algorithm', 'data'],
    'geopolitics':  ['war', 'nato', 'ukraine', 'russia', 'china', 'taiwan',
                     'sanctions', 'missile', 'troops', 'ceasefire'],
    'climate':      ['climate', 'carbon', 'renewable', 'solar', 'flood',
                     'wildfire', 'emissions', 'green', 'energy transition'],
    'economy':      ['inflation', 'recession', 'fed', 'interest rate', 'gdp',
                     'market', 'stock', 'dollar', 'trade', 'tariff'],
    'politics_us':  ['trump', 'biden', 'congress', 'senate', 'white house',
                     'election', 'democrat', 'republican', 'administration'],
    'crisis':       ['crisis', 'emergency', 'collapse', 'protest', 'riot',
                     'coup', 'conflict', 'humanitarian', 'refugee'],
    'health':       ['pandemic', 'virus', 'vaccine', 'who', 'outbreak',
                     'health', 'hospital', 'disease', 'treatment'],
    'surveillance': ['surveillance', 'privacy', 'data breach', 'hack',
                     'leak', 'espionage', 'intelligence', 'fbi', 'cia'],
}


def _fetch_feed(url: str, timeout: int = 6) -> str:
    """Fetch RSS feed content."""
    try:
        req = urllib.request.Request(
            url,
            headers={'User-Agent': 'Veritas-Foresight/1.0 RSS Reader'}
        )
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.read().decode('utf-8', errors='replace')
    except Exception:
        return ''


def _extract_headlines(xml: str, max_items: int = 10) -> List[str]:
    """Extract headlines from RSS XML."""
    titles = re.findall(r'<title><!\[CDATA\[(.*?)\]\]></title>', xml)
    if not titles:
        titles = re.findall(r'<title>(.*?)</title>', xml)
    # Skip feed title (usually first item)
    return [t.strip() for t in titles[1:max_items+1] if t.strip()]


def _extract_topics(headlines: List[str]) -> List[str]:
    """Extract hot topics from headlines."""
    text = ' '.join(headlines).lower()
    found = []
    for topic, keywords in TOPIC_CLUSTERS.items():
        hits = sum(1 for kw in keywords if kw in text)
        if hits >= 1:
            found.append(topic)
    return found


def get_field_context(max_feeds: int = 3) -> Dict:
    """
    Build current information field context from RSS.

    Returns:
        headlines: list of current headlines
        hot_topics: detected topic clusters
        crisis_level: 0-10 estimate of current crisis intensity
        timestamp: when this was fetched
    """
    all_headlines = []

    for feed_url in RSS_FEEDS[:max_feeds]:
        xml = _fetch_feed(feed_url)
        if xml:
            headlines = _extract_headlines(xml)
            all_headlines.extend(headlines)

    if not all_headlines:
        return {
            'headlines': [],
            'hot_topics': [],
            'crisis_level': 0,
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'status': 'no_data',
        }

    # Deduplicate roughly
    seen = set()
    unique_headlines = []
    for h in all_headlines:
        key = h[:40].lower()
        if key not in seen:
            seen.add(key)
            unique_headlines.append(h)

    hot_topics = _extract_topics(unique_headlines)

    # Crisis level — count crisis-related headlines
    crisis_keywords = ['war', 'crisis', 'collapse', 'emergency', 'attack',
                       'killed', 'conflict', 'explosion', 'threat', 'coup']
    crisis_hits = sum(
        1 for h in unique_headlines
        if any(kw in h.lower() for kw in crisis_keywords)
    )
    crisis_level = min(round(crisis_hits / max(len(unique_headlines), 1) * 10, 1), 10.0)

    return {
        'headlines': unique_headlines[:15],
        'hot_topics': hot_topics,
        'crisis_level': crisis_level,
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'status': 'ok',
        'feeds_fetched': max_feeds,
    }


def get_topics_for_engine(context: Dict = None) -> List[str]:
    """
    Get flat list of topic strings for ForesightEngine.
    If no context provided, fetches fresh.
    """
    if context is None:
        context = get_field_context()
    topics = context.get('hot_topics', [])
    headlines = context.get('headlines', [])[:5]
    # Add first words of top headlines as additional signal
    extra = []
    for h in headlines:
        words = [w.lower() for w in h.split() if len(w) > 4]
        extra.extend(words[:3])
    return topics + extra
