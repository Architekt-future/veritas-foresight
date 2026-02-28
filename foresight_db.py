"""
Veritas Foresight — Supabase Storage v1.0
Persistent storage for custom future scenarios.
"""

import os
import json
import urllib.request
import urllib.error
from typing import List, Dict, Optional

SUPABASE_URL = os.environ.get('SUPABASE_URL', '')
SUPABASE_KEY = os.environ.get('SUPABASE_KEY', '')

DEFAULT_FUTURES = [
    {
        'name': 'Tech-Acceleration',
        'keywords': ['ai', 'quantum', 'singularity', 'agi', 'automation',
                     'intelligence', 'neural', 'model', 'compute', 'data'],
        'core_logic': 'technology accelerates beyond human control',
        'description': 'Rapid technological acceleration, AI dominance, post-human transition',
        'is_default': True,
        'is_active': True,
    },
    {
        'name': 'Green-Symbiosis',
        'keywords': ['climate', 'renewable', 'sustainable', 'ecology', 'green',
                     'solar', 'energy', 'nature', 'carbon', 'transition'],
        'core_logic': 'humanity cooperates with natural systems',
        'description': 'Ecological transition, distributed energy, human-nature balance',
        'is_default': True,
        'is_active': True,
    },
    {
        'name': 'Control-Consolidation',
        'keywords': ['surveillance', 'control', 'authoritarian', 'restrict',
                     'censor', 'monitor', 'power', 'government', 'limit', 'ban'],
        'core_logic': 'centralized control tightens over information and people',
        'description': 'Surveillance expansion, information control, authoritarian consolidation',
        'is_default': True,
        'is_active': True,
    },
    {
        'name': 'Fragmentation',
        'keywords': ['war', 'conflict', 'crisis', 'collapse', 'protest',
                     'revolution', 'divide', 'polariz', 'chaos', 'instability'],
        'core_logic': 'global systems fragment into competing blocs',
        'description': 'Geopolitical fragmentation, resource conflicts, institutional collapse',
        'is_default': True,
        'is_active': True,
    },
    {
        'name': 'Resilient-Adaptation',
        'keywords': ['community', 'local', 'resilient', 'adapt', 'cooperat',
                     'decentraliz', 'mutual', 'network', 'grassroot', 'bottom-up'],
        'core_logic': 'communities adapt through decentralized cooperation',
        'description': 'Bottom-up resilience, community networks, adaptive institutions',
        'is_default': True,
        'is_active': True,
    },
]


def _headers():
    return {
        'apikey': SUPABASE_KEY,
        'Authorization': f'Bearer {SUPABASE_KEY}',
        'Content-Type': 'application/json',
        'Prefer': 'return=representation',
    }


def _request(method: str, path: str, body: dict = None) -> dict:
    url = f'{SUPABASE_URL}/rest/v1/{path}'
    data = json.dumps(body).encode() if body else None
    req = urllib.request.Request(url, data=data, headers=_headers(), method=method)
    try:
        with urllib.request.urlopen(req, timeout=8) as resp:
            raw = resp.read().decode()
            return json.loads(raw) if raw.strip() else []
    except urllib.error.HTTPError as e:
        raise Exception(f'Supabase {method} {path}: {e.code} {e.read().decode()}')


def is_configured() -> bool:
    return bool(SUPABASE_URL and SUPABASE_KEY)


def seed_defaults():
    """Insert default futures if table is empty."""
    if not is_configured():
        return
    existing = _request('GET', 'futures?is_default=eq.true&select=name')
    if existing:
        return
    for f in DEFAULT_FUTURES:
        try:
            _request('POST', 'futures', {
                'name': f['name'],
                'keywords': f['keywords'],
                'core_logic': f['core_logic'],
                'description': f['description'],
                'is_default': f['is_default'],
                'is_active': f['is_active'],
            })
        except Exception:
            pass  # already exists


def get_all_futures() -> List[Dict]:
    """Get all futures (default + custom), ordered by created_at."""
    if not is_configured():
        return DEFAULT_FUTURES
    try:
        rows = _request('GET', 'futures?select=*&order=is_default.desc,created_at.asc')
        return rows if rows else DEFAULT_FUTURES
    except Exception:
        return DEFAULT_FUTURES


def get_active_futures() -> List[Dict]:
    """Get only active futures for simulation."""
    if not is_configured():
        return DEFAULT_FUTURES
    try:
        rows = _request('GET', 'futures?is_active=eq.true&select=*&order=is_default.desc,created_at.asc')
        return rows if rows else DEFAULT_FUTURES
    except Exception:
        return DEFAULT_FUTURES


def create_future(name: str, keywords: List[str], core_logic: str,
                  description: str = '') -> Dict:
    """Create a new custom future scenario."""
    if not is_configured():
        raise Exception('Supabase not configured')
    if not name or not keywords or not core_logic:
        raise Exception('name, keywords and core_logic are required')
    result = _request('POST', 'futures', {
        'name': name.strip(),
        'keywords': [k.strip().lower() for k in keywords if k.strip()],
        'core_logic': core_logic.strip(),
        'description': description.strip(),
        'is_default': False,
        'is_active': True,
    })
    return result[0] if isinstance(result, list) else result


def toggle_future(future_id: str, is_active: bool) -> Dict:
    """Enable or disable a future scenario (both default and custom)."""
    if not is_configured():
        raise Exception('Supabase not configured')
    # No is_default filter — allow toggling any future
    result = _request('PATCH', f'futures?id=eq.{future_id}', {'is_active': is_active})
    return result[0] if isinstance(result, list) and result else {}


def delete_future(future_id: str):
    """Delete a custom future (only non-default)."""
    if not is_configured():
        raise Exception('Supabase not configured')
    _request('DELETE', f'futures?id=eq.{future_id}&is_default=eq.false')
