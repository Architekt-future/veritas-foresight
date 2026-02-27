"""
Veritas Foresight — Flask API v1.0
Narrative resonance simulator as a web service.
"""

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import os
from foresight_engine import ForesightEngine, Future
from foresight_rss import get_field_context, get_topics_for_engine

app = Flask(__name__, static_folder='.')
CORS(app)

@app.route('/api/health')
def health():
    return jsonify({'status': 'online', 'service': 'Veritas Foresight', 'version': 'v1.0'})


@app.route('/api/field', methods=['GET'])
def field():
    """Get current information field context from RSS."""
    try:
        context = get_field_context(max_feeds=3)
        return jsonify(context)
    except Exception as e:
        return jsonify({'error': str(e), 'status': 'error'}), 500


@app.route('/api/simulate', methods=['POST'])
def simulate():
    """
    Run a narrative resonance simulation.
    Body: { argument, steps(1-10), use_field, seed, futures }
    """
    try:
        data = request.get_json(force=True) or {}
        argument = data.get('argument', '').strip()
        if not argument:
            return jsonify({'error': 'argument is required'}), 400

        steps = max(1, min(int(data.get('steps', 5)), 10))
        use_field = data.get('use_field', True)
        seed = data.get('seed', None)

        futures = None
        if data.get('futures'):
            try:
                futures = [Future(**f) for f in data['futures']]
            except Exception:
                pass

        field_context_data = {}
        field_topics = []
        if use_field:
            try:
                field_context_data = get_field_context(max_feeds=3)
                field_topics = get_topics_for_engine(field_context_data)
            except Exception:
                pass

        engine = ForesightEngine(futures=futures, seed=seed)
        results = engine.run(argument, steps=steps, field_context=field_topics)
        final_state = engine.get_state()

        history = [{
            'iteration': s.iteration,
            'argument': s.argument,
            'realized': s.realized_future,
            'feedback': s.feedback_argument,
            'probs_before': s.probabilities_before,
            'probs_after': s.probabilities_after,
        } for s in results]

        return jsonify({
            'argument': argument,
            'steps': steps,
            'final_state': final_state,
            'history': history,
            'field_context': {
                'hot_topics': field_context_data.get('hot_topics', []),
                'crisis_level': field_context_data.get('crisis_level', 0),
                'headlines_count': len(field_context_data.get('headlines', [])),
                'status': field_context_data.get('status', 'not_fetched'),
            },
            'status': 'ok',
        })

    except Exception as e:
        return jsonify({'error': str(e), 'status': 'error'}), 500


@app.route('/api/step', methods=['POST'])
def step():
    """Single step with client-side state."""
    try:
        data = request.get_json(force=True) or {}
        argument = data.get('argument', '').strip()

        field_topics = []
        if data.get('use_field', True):
            try:
                ctx = get_field_context(max_feeds=2)
                field_topics = get_topics_for_engine(ctx)
            except Exception:
                pass

        engine = ForesightEngine()
        current_probs = data.get('current_probs', {})
        if current_probs:
            for f in engine.futures:
                if f.name in current_probs:
                    f.probability = float(current_probs[f.name])
            engine._normalize()

        snap = engine.step(argument or None, field_topics)
        state = engine.get_state()

        return jsonify({
            'iteration': snap.iteration,
            'argument': snap.argument,
            'realized': snap.realized_future,
            'feedback': snap.feedback_argument,
            'probs_before': snap.probabilities_before,
            'probs_after': snap.probabilities_after,
            'state': state,
            'status': 'ok',
        })

    except Exception as e:
        return jsonify({'error': str(e), 'status': 'error'}), 500


@app.route('/')
def index():
    return send_from_directory('.', 'index.html')


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10001))
    app.run(host='0.0.0.0', port=port, debug=False)
