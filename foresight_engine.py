"""
Veritas Foresight — Narrative Resonance Engine v1.0
Based on TimeNavigationEngine concept by Шукач & Орфей (Oct 2025)

Philosophy:
    An argument is not just a logical construct —
    it is a vector in the probability space of possible futures.
    When you define a future, you begin to collapse it into being.

    This engine does not predict. It measures resonance.
"""

import random
import math
from dataclasses import dataclass, field
from typing import List, Dict, Optional
from datetime import datetime


@dataclass
class Future:
    """A possible future scenario."""
    name: str
    keywords: List[str]        # words that resonate with this future
    core_logic: str            # the fundamental assumption of this future
    probability: float = 1.0
    description: str = ''


@dataclass
class ResonanceSnapshot:
    """One iteration of the engine — a moment in time."""
    iteration: int
    timestamp: str
    argument: str
    probabilities_before: Dict[str, float]
    realized_future: str
    feedback_argument: str
    probabilities_after: Dict[str, float]
    field_context: List[str] = field(default_factory=list)  # hot topics from RSS


class ForesightEngine:
    """
    Narrative resonance simulator.

    How it works:
        1. You provide an argument (a claim, a narrative, a hypothesis)
        2. The engine checks how this argument resonates with possible futures
        3. Probabilities shift — some futures become more likely, others less
        4. A future is realized (stochastically)
        5. The realized future generates a feedback argument
        6. This feedback reshapes the probability field
        7. Repeat → observe how narratives self-reinforce or collapse

    The engine does not predict. It shows resonance.
    """

    # Default scenarios — can be overridden
    DEFAULT_FUTURES = [
        Future(
            name='Tech-Acceleration',
            keywords=['ai', 'quantum', 'singularity', 'agi', 'automation',
                      'intelligence', 'neural', 'model', 'compute', 'data'],
            core_logic='technology accelerates beyond human control',
            description='Rapid technological acceleration, AI dominance, post-human transition',
            probability=1.0
        ),
        Future(
            name='Green-Symbiosis',
            keywords=['climate', 'renewable', 'sustainable', 'ecology', 'green',
                      'solar', 'energy', 'nature', 'carbon', 'transition'],
            core_logic='humanity cooperates with natural systems',
            description='Ecological transition, distributed energy, human-nature balance',
            probability=1.0
        ),
        Future(
            name='Control-Consolidation',
            keywords=['surveillance', 'control', 'authoritarian', 'restrict',
                      'censor', 'monitor', 'power', 'government', 'limit', 'ban'],
            core_logic='centralized control tightens over information and people',
            description='Surveillance expansion, information control, authoritarian consolidation',
            probability=1.0
        ),
        Future(
            name='Fragmentation',
            keywords=['war', 'conflict', 'crisis', 'collapse', 'protest',
                      'revolution', 'divide', 'polariz', 'chaos', 'instability'],
            core_logic='global systems fragment into competing blocs',
            description='Geopolitical fragmentation, resource conflicts, institutional collapse',
            probability=1.0
        ),
        Future(
            name='Resilient-Adaptation',
            keywords=['community', 'local', 'resilient', 'adapt', 'cooperat',
                      'decentraliz', 'mutual', 'network', 'grassroot', 'bottom-up'],
            core_logic='communities adapt through decentralized cooperation',
            description='Bottom-up resilience, community networks, adaptive institutions',
            probability=1.0
        ),
    ]

    def __init__(self, futures: List[Future] = None, seed: Optional[int] = None):
        if seed is not None:
            random.seed(seed)
        self.futures = [Future(**vars(f)) for f in (futures or self.DEFAULT_FUTURES)]
        self.history: List[ResonanceSnapshot] = []
        self.iteration = 0
        self._normalize()

    def _normalize(self):
        """Normalize probabilities to sum to 1.0."""
        total = sum(f.probability for f in self.futures)
        if total <= 0:
            n = len(self.futures)
            for f in self.futures:
                f.probability = 1.0 / n
            return
        for f in self.futures:
            f.probability /= total

    def calculate_resonance(self, future: Future, argument: str,
                             field_context: List[str] = None,
                             headlines: List[str] = None) -> float:
        """
        How strongly does this argument resonate with this future?

        Resonance = keyword overlap + field context boost + logic contradiction check
        Returns a multiplier: >1.0 amplifies, <1.0 suppresses.
        """
        arg_lower = argument.lower()
        field_lower = [t.lower() for t in (field_context or [])]

        # Base resonance from keyword matching
        keyword_hits = sum(1 for kw in future.keywords if kw.lower() in arg_lower)
        base_resonance = 1.0 + (keyword_hits * 0.25)  # each keyword adds 25%

        # Field context boost — if hot topics align with future keywords
        field_hits = sum(
            1 for kw in future.keywords
            for topic in field_lower
            if kw.lower() in topic or topic in kw.lower()
        )
        field_boost = 1.0 + (field_hits * 0.15)

        # Contradiction check — explicit negation of core logic
        core_words = future.core_logic.lower().split()
        negation_patterns = [f"not {w}" for w in core_words] + \
                            [f"no {w}" for w in core_words] + \
                            [f"against {w}" for w in core_words]
        if any(pat in arg_lower for pat in negation_patterns):
            return 0.2  # strong suppression

        return min(base_resonance * field_boost, 3.5)  # cap at 3.5x

    def match_headlines(self, future: Future, headlines: List[str]) -> List[str]:
        """
        Find headlines from RSS that resonate with this future.
        Returns list of matching headlines (max 3).
        """
        if not headlines:
            return []
        matched = []
        for h in headlines:
            h_lower = h.lower()
            hits = sum(1 for kw in future.keywords if kw.lower() in h_lower)
            if hits >= 1:
                matched.append((hits, h))
        # Sort by hit count, return top 3
        matched.sort(reverse=True)
        return [h for _, h in matched[:3]]

    def apply_argument(self, argument: str, field_context: List[str] = None,
                       noise: float = 0.05):
        """
        Apply an argument to the probability field.
        noise = randomness in resonance (imperfect influence)
        """
        for f in self.futures:
            r = self.calculate_resonance(f, argument, field_context)
            n = 1.0 + random.uniform(-noise, noise)
            f.probability *= r * n
        self._normalize()

    def collapse(self) -> Future:
        """
        Stochastic collapse — select a future based on current probabilities.
        Not deterministic: higher probability = more likely, not certain.
        """
        weights = [f.probability for f in self.futures]
        return random.choices(self.futures, weights=weights, k=1)[0]

    def generate_feedback(self, realized: Future) -> str:
        """
        The realized future speaks back — generates a new argument
        that reflects what was actualized.
        This is the self-reinforcing loop (Cassandra effect).
        """
        kw = random.choice(realized.keywords)
        r = random.random()

        templates = [
            f"The trend toward {realized.core_logic} is accelerating — focus on {kw}",
            f"Evidence of {kw} confirms the {realized.name} trajectory",
            f"Prioritize {kw} and related strategies for {realized.name}",
            f"The {realized.name} scenario is gaining momentum through {kw}",
        ]
        return random.choice(templates)

    def step(self, argument: str = None, field_context: List[str] = None) -> ResonanceSnapshot:
        """
        One full iteration:
            1. Apply external argument (if any)
            2. Record probabilities
            3. Collapse to realized future
            4. Generate feedback
            5. Apply feedback (self-reinforcement)
            6. Record result
        """
        self.iteration += 1
        field_context = field_context or []

        # Apply external argument
        if argument:
            self.apply_argument(argument, field_context, noise=0.05)

        probs_before = {f.name: round(f.probability, 4) for f in self.futures}

        # Collapse
        realized = self.collapse()

        # Generate and apply feedback
        feedback = self.generate_feedback(realized)
        self.apply_argument(feedback, field_context, noise=0.08)

        probs_after = {f.name: round(f.probability, 4) for f in self.futures}

        snapshot = ResonanceSnapshot(
            iteration=self.iteration,
            timestamp=datetime.utcnow().isoformat(),
            argument=argument or '(internal feedback only)',
            probabilities_before=probs_before,
            realized_future=realized.name,
            feedback_argument=feedback,
            probabilities_after=probs_after,
            field_context=field_context,
        )
        self.history.append(snapshot)
        return snapshot

    def run(self, argument: str, steps: int = 5,
            field_context: List[str] = None) -> List[ResonanceSnapshot]:
        """
        Run multiple iterations with one initial argument.
        After step 1, only feedback drives the system.
        """
        results = []
        for i in range(steps):
            arg = argument if i == 0 else None
            results.append(self.step(arg, field_context))
        return results

    def reset(self):
        """Reset probabilities to equal distribution."""
        for f in self.futures:
            f.probability = 1.0
        self._normalize()
        self.history = []
        self.iteration = 0

    def get_state(self, headlines: List[str] = None) -> Dict:
        """Current state of the probability field."""
        return {
            'iteration': self.iteration,
            'futures': [
                {
                    'name': f.name,
                    'probability': round(f.probability, 4),
                    'probability_pct': round(f.probability * 100, 1),
                    'description': f.description,
                    'core_logic': f.core_logic,
                    'matched_headlines': self.match_headlines(f, headlines or []),
                }
                for f in sorted(self.futures, key=lambda x: x.probability, reverse=True)
            ],
            'dominant': max(self.futures, key=lambda x: x.probability).name,
            'entropy': self._calculate_entropy(),
        }

    def _calculate_entropy(self) -> float:
        """
        Shannon entropy of the probability distribution.
        High entropy = many futures roughly equal (uncertainty).
        Low entropy = one future dominates (convergence).
        """
        probs = [f.probability for f in self.futures if f.probability > 0]
        return round(-sum(p * math.log2(p) for p in probs), 4)
