"""
Veritas Foresight — Flask API v1.1
Narrative resonance simulator with persistent custom futures via Supabase.
"""

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import os
from foresight_engine import ForesightEngine, Future
from foresight_rss import get_field_context, get_topics_for_engine
from foresight_db import (
    is_configured, seed_defaults,
    get_all_futures, get_active_futures,
    create_future, toggle_future, delete_future,
)
import urllib.request
import json as _json


def translate_to_english(text: str) -> str:
    """
    Translate text to English using Anthropic API if it appears non-English.
    Uses simple heuristic: if text contains non-ASCII chars — translate.
    Falls back to original text on any error.
    """
    api_key = os.environ.get('ANTHROPIC_API_KEY', '')
    if not api_key:
        return text

    # Quick heuristic — if mostly ASCII, skip translation
    non_ascii = sum(1 for c in text if ord(c) > 127)
    if non_ascii < len(text) * 0.1:
        return text  # already mostly English

    try:
        payload = {
            'model': 'claude-haiku-4-5-20251001',
            'max_tokens': 300,
            'messages': [{
                'role': 'user',
                'content': (
                    f'Translate the following text to English. '
                    f'Return ONLY the translation, nothing else:\n\n{text}'
                )
            }]
        }
        data = _json.dumps(payload).encode()
        req = urllib.request.Request(
            'https://api.anthropic.com/v1/messages',
            data=data,
            headers={
                'x-api-key': api_key,
                'anthropic-version': '2023-06-01',
                'content-type': 'application/json',
            },
            method='POST'
        )
        with urllib.request.urlopen(req, timeout=8) as resp:
            result = _json.loads(resp.read().decode())
            return result['content'][0]['text'].strip()
    except Exception:
        return text  # silent fallback

app = Flask(__name__, static_folder='.')
CORS(app)

# Seed default futures on startup
if is_configured():
    try:
        seed_defaults()
    except Exception:
        pass


# ── Health ─────────────────────────────────────────────────────────────────────

@app.route('/api/debug/futures')
def debug_futures():
    """Debug: show what get_active_futures returns."""
    from foresight_db import get_active_futures, is_configured
    rows = get_active_futures()
    return jsonify({
        'configured': is_configured(),
        'count': len(rows),
        'names': [r['name'] for r in rows],
        'is_defaults': [r.get('is_default', False) for r in rows],
    })

@app.route('/api/health')
def health():
    return jsonify({
        'status': 'online',
        'service': 'Veritas Foresight',
        'version': 'v1.1',
        'storage': 'supabase' if is_configured() else 'memory',
    })


# ── Field context ──────────────────────────────────────────────────────────────

@app.route('/api/field', methods=['GET'])
def field():
    try:
        context = get_field_context(max_feeds=3)
        return jsonify(context)
    except Exception as e:
        return jsonify({'error': str(e), 'status': 'error'}), 500


# ── Futures CRUD ───────────────────────────────────────────────────────────────

@app.route('/api/futures', methods=['GET'])
def list_futures():
    """Get all futures with active status."""
    try:
        rows = get_all_futures()
        return jsonify({'futures': rows, 'status': 'ok'})
    except Exception as e:
        return jsonify({'error': str(e), 'status': 'error'}), 500


@app.route('/api/futures', methods=['POST'])
def add_future():
    """
    Add a custom future scenario.
    Body: { name, keywords: [str], core_logic, description? }
    """
    try:
        data = request.get_json(force=True) or {}
        name = data.get('name', '').strip()
        keywords = data.get('keywords', [])
        core_logic = data.get('core_logic', '').strip()
        description = data.get('description', '').strip()

        if isinstance(keywords, str):
            keywords = [k.strip() for k in keywords.split(',') if k.strip()]

        if not name:
            return jsonify({'error': 'name is required'}), 400
        if not keywords:
            return jsonify({'error': 'keywords are required'}), 400
        if not core_logic:
            return jsonify({'error': 'core_logic is required'}), 400

        result = create_future(name, keywords, core_logic, description)
        return jsonify({'future': result, 'status': 'ok'})

    except Exception as e:
        return jsonify({'error': str(e), 'status': 'error'}), 500


@app.route('/api/futures/<future_id>/toggle', methods=['PATCH'])
def toggle(future_id):
    """Enable or disable a future. Body: { is_active: bool }"""
    try:
        data = request.get_json(force=True) or {}
        is_active = bool(data.get('is_active', True))
        result = toggle_future(future_id, is_active)
        return jsonify({'future': result, 'status': 'ok'})
    except Exception as e:
        return jsonify({'error': str(e), 'status': 'error'}), 500


@app.route('/api/futures/<future_id>', methods=['DELETE'])
def remove_future(future_id):
    """Delete a custom (non-default) future."""
    try:
        delete_future(future_id)
        return jsonify({'status': 'ok'})
    except Exception as e:
        return jsonify({'error': str(e), 'status': 'error'}), 500


# ── Simulation ─────────────────────────────────────────────────────────────────

@app.route('/api/simulate', methods=['POST'])
def simulate():
    """
    Run simulation using active futures from DB.
    Body: { argument, steps(1-10), use_field, seed }
    """
    try:
        data = request.get_json(force=True) or {}
        argument = data.get('argument', '').strip()
        if not argument:
            return jsonify({'error': 'argument is required'}), 400

        # Auto-translate non-English arguments for better keyword resonance
        argument_original = argument
        argument = translate_to_english(argument)

        steps = max(1, min(int(data.get('steps', 5)), 10))
        use_field = data.get('use_field', True)
        seed = data.get('seed', None)

        # Load active futures from DB
        rows = get_active_futures()
        if not rows:
            return jsonify({'error': 'no active futures — enable at least one'}), 400

        futures = [Future(
            name=r['name'],
            keywords=r['keywords'],
            core_logic=r['core_logic'],
            description=r.get('description', ''),
        ) for r in rows]

        # Field context
        field_context_data = {}
        field_topics = []
        if use_field:
            try:
                field_context_data = get_field_context(max_feeds=3)
                field_topics = get_topics_for_engine(field_context_data)
            except Exception:
                pass

        temperature = float(data.get('temperature', 1.0))
        temperature = max(0.1, min(temperature, 2.0))
        engine = ForesightEngine(futures=futures, seed=seed)
        results = engine.run(argument, steps=steps, field_context=field_topics, temperature=temperature)
        raw_headlines = field_context_data.get('headlines', [])
        final_state = engine.get_state(headlines=raw_headlines)

        history = [{
            'iteration': s.iteration,
            'argument': s.argument,
            'realized': s.realized_future,
            'feedback': s.feedback_argument,
            'probs_before': s.probabilities_before,
            'probs_after': s.probabilities_after,
        } for s in results]

        return jsonify({
            'argument': argument_original,
            'argument_translated': argument if argument != argument_original else None,
            'steps': steps,
            'final_state': final_state,
            'history': history,
            'field_context': {
                'hot_topics': field_context_data.get('hot_topics', []),
                'crisis_level': field_context_data.get('crisis_level', 0),
                'headlines': field_context_data.get('headlines', [])[:10],
                'headlines_count': len(field_context_data.get('headlines', [])),
                'status': field_context_data.get('status', 'not_fetched'),
            },
            'status': 'ok',
        })

    except Exception as e:
        return jsonify({'error': str(e), 'status': 'error'}), 500


# ── Battle mode ───────────────────────────────────────────────────────────────

@app.route('/api/battle', methods=['POST'])
def battle():
    """
    Battle mode: two opposing arguments compete.
    Body: { argument_a, argument_b, rounds(1-10), use_field }
    """
    try:
        data = request.get_json(force=True) or {}
        arg_a = data.get('argument_a', '').strip()
        arg_b = data.get('argument_b', '').strip()

        if not arg_a or not arg_b:
            return jsonify({'error': 'argument_a and argument_b are required'}), 400

        # Auto-translate non-English arguments
        arg_a_original, arg_b_original = arg_a, arg_b
        arg_a = translate_to_english(arg_a)
        arg_b = translate_to_english(arg_b)

        rounds = max(1, min(int(data.get('rounds', 5)), 10))
        use_field = data.get('use_field', True)

        rows = get_active_futures()
        if not rows:
            return jsonify({'error': 'no active futures'}), 400

        futures = [Future(
            name=r['name'],
            keywords=r['keywords'],
            core_logic=r['core_logic'],
            description=r.get('description', ''),
        ) for r in rows]

        field_context_data = {}
        field_topics = []
        if use_field:
            try:
                field_context_data = get_field_context(max_feeds=3)
                field_topics = get_topics_for_engine(field_context_data)
            except Exception:
                pass

        temperature = float(data.get('temperature', 1.0))
        temperature = max(0.1, min(temperature, 2.0))
        engine = ForesightEngine(futures=futures)
        result = engine.battle(arg_a, arg_b, rounds=rounds, field_context=field_topics, temperature=temperature)

        result['field_context'] = {
            'hot_topics': field_context_data.get('hot_topics', []),
            'crisis_level': field_context_data.get('crisis_level', 0),
            'headlines': field_context_data.get('headlines', [])[:10],
            'status': field_context_data.get('status', 'not_fetched'),
        }
        result['status'] = 'ok'
        return jsonify(result)

    except Exception as e:
        return jsonify({'error': str(e), 'status': 'error'}), 500


# ── Frontend ───────────────────────────────────────────────────────────────────

@app.route('/')
def index():
    return send_from_directory('.', 'index.html')


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10001))
    app.run(host='0.0.0.0', port=port, debug=False)
