"""
Promotion Manager v4.
Features: O(P) Stats Update, Statistical Shrinkage, Introspection Expansion.
"""
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Dict, List, Tuple, Any, Optional

from alert_axolotl_evo.tree import merkle_hash, node_count
from alert_axolotl_evo.primitives import FUNCTIONS


@dataclass
class PatternStats:
    present_count: int = 0
    present_fitness_sum: float = 0.0
    absent_count: int = 0
    absent_fitness_sum: float = 0.0
    last_seen_gen: int = 0

    def get_shrunken_lift(self, k: float = 50.0) -> float:
        """
        Calculates Causal Lift with shrinkage (n / n+k) to suppress noise.
        
        Returns lift ratio: avg_fitness_when_present / avg_fitness_when_absent
        Shrunk towards 1.0 based on sample size to prevent overfitting to small samples.
        """
        if self.absent_count < 5 or self.present_count < 1:
            return 1.0

        avg_present = self.present_fitness_sum / self.present_count
        avg_absent = self.absent_fitness_sum / self.absent_count
        
        if avg_absent == 0:
            return 1.0
        
        raw_lift = avg_present / avg_absent
        confidence_factor = self.present_count / (self.present_count + k)
        
        # Dampen lift towards 1.0 based on sample size
        return 1.0 + (raw_lift - 1.0) * confidence_factor


@dataclass
class PatternVariant:
    family_hash: str  # Normalized hash (vars -> __VAR__)
    exact_hash: str   # Exact hash (specific instance)
    subtree: Tuple
    stats: PatternStats = field(default_factory=PatternStats)
    status: str = "candidate"  # candidate | active | retired
    registry_name: Optional[str] = None


class PromotionManager:
    def __init__(self, compiler, library_budget: int = 50):
        """
        Args:
            compiler: PrimitiveCompiler instance
            library_budget: Maximum number of active macros (hard cap)
        """
        self.compiler = compiler
        self.LIBRARY_BUDGET = library_budget
        self.families: Dict[str, Dict[str, PatternVariant]] = defaultdict(dict)
        self.active_library: Dict[str, PatternVariant] = {}
        
        # Tuning parameters
        self.MIN_SHRUNKEN_LIFT = 1.02  # Must be 2% better than average
        self.MIN_NODES = 4  # Filter trivial fragments
        self.MIN_SAMPLES = 20  # Minimum observations before promotion
        self.MIN_EVIDENCE_FOR_GHOST = 5  # Minimum total observations before ghost pruning (prevents "never got a chance" evictions)
        self.MIN_EVIDENCE_FOR_HARM = 10  # Minimum total observations before harmful pruning (prevents fluke early demotions)

    def process_generation_results(
        self, 
        champions: List[Dict], 
        current_gen: int,
        evidence_valid: bool = True,
    ):
        """
        Updates stats using Complement Method (Total - Present = Absent).
        Efficiency: O(Present_Variants) instead of O(All_Variants * Champions).
        
        Args:
            champions: List of {tree, fitness} dicts from this generation
            current_gen: Current generation number (monotonic economic time index)
            evidence_valid: True if breakdown is valid for stats collection.
                If False, this method should be a no-op (caller should skip).
        """
        # Guard: don't process invalid evidence
        if not evidence_valid:
            return
        
        # Micro-batch guard: prevent noise from tiny batches
        if len(champions) < 2:
            return
        gen_total_fit = sum(c['fitness'] for c in champions)
        gen_total_count = len(champions)
        
        # Track presence for this specific generation
        # Map: exact_hash -> [count, fit_sum]
        variant_gen_stats = defaultdict(lambda: [0, 0.0])
        
        for champ in champions:
            # 1. Expand Macros (Fix: use FUNCTIONS registry as source of truth)
            expanded_tree = self._inline_expand_macros(champ['tree'], FUNCTIONS)
            
            # 2. Extract Subtrees
            subtrees = self._extract_subtrees_with_hashes(expanded_tree)
            
            # 3. Mark Presence (Set ensures we count once per tree)
            seen_in_tree = set()
            for fam, ex, sub in subtrees:
                if ex in seen_in_tree:
                    continue
                seen_in_tree.add(ex)
                
                # Register new candidate if first seen
                if ex not in self.families[fam]:
                    self.families[fam][ex] = PatternVariant(fam, ex, sub)
                
                # Update transient stats
                variant_gen_stats[ex][0] += 1
                variant_gen_stats[ex][1] += champ['fitness']

        # 4. Batch Update Stats (Complement Method)
        all_variants = [v for f in self.families.values() for v in f.values()]
        for v in all_variants:
            if v.status == "retired":
                continue
            
            if v.exact_hash in variant_gen_stats:
                # PRESENT: Add observed values
                p_cnt, p_fit = variant_gen_stats[v.exact_hash]
                v.stats.present_count += p_cnt
                v.stats.present_fitness_sum += p_fit
                v.stats.last_seen_gen = current_gen
                
                # ABSENT: Add complements (Total - Present)
                v.stats.absent_count += (gen_total_count - p_cnt)
                v.stats.absent_fitness_sum += (gen_total_fit - p_fit)
            else:
                # ABSENT FROM ALL (this generation)
                v.stats.absent_count += gen_total_count
                v.stats.absent_fitness_sum += gen_total_fit

    def promote_and_prune(self, current_gen: int, register_fn, unregister_fn) -> List[str]:
        """
        Promote candidates to active library and prune underperformers.
        
        Args:
            current_gen: Current generation number
            register_fn: Function to register primitives (signature: name, func, arity, needs_context)
            unregister_fn: Function to unregister primitives (signature: name)
            
        Returns:
            List of names that were promoted this round
        """
        promoted = []

        # 1. Rank Families by Best Variant
        candidates = []
        for fam, variants in self.families.items():
            best = self._get_best_variant(variants)
            if not best:
                continue
            
            lift = best.stats.get_shrunken_lift()
            if (lift >= self.MIN_SHRUNKEN_LIFT and 
                best.stats.present_count >= self.MIN_SAMPLES and
                best.status == "candidate"):
                candidates.append((lift, best))

        candidates.sort(key=lambda x: x[0], reverse=True)

        # 2. Promote / Challenge
        for score, variant in candidates:
            if len(self.active_library) < self.LIBRARY_BUDGET:
                # Budget available - promote directly
                self._activate(variant, register_fn)
                promoted.append(variant.registry_name)
            else:
                # Budget full - challenger must beat worst by 10% margin
                worst = self._get_worst_active()
                if worst and score > (worst.stats.get_shrunken_lift() * 1.10):
                    self._retire(worst, unregister_fn)
                    self._activate(variant, register_fn)
                    promoted.append(variant.registry_name)

        # 3. Prune Ghosts / Harmful
        # Only prune active_library entries (never candidates - they haven't earned library space yet)
        for name, variant in list(self.active_library.items()):
            # Calculate total observations (present + absent) for evidence checks
            total_obs = variant.stats.present_count + variant.stats.absent_count
            
            # Ghost pruning: pattern hasn't been seen for 15+ ticks
            # BUT: only apply ghost logic if pattern has minimum total observations
            # This prevents "never got a chance" evictions during sparse periods
            has_min_evidence_for_ghost = total_obs >= self.MIN_EVIDENCE_FOR_GHOST
            is_ghost = has_min_evidence_for_ghost and (current_gen - variant.stats.last_seen_gen) > 15
            
            # Harmful: pattern is actively worse than average
            # BUT: only apply harmful logic if pattern has minimum total observations
            # This prevents fluke early demotions due to shrinkage wobble with low samples
            has_min_evidence_for_harm = total_obs >= self.MIN_EVIDENCE_FOR_HARM
            is_harmful = has_min_evidence_for_harm and variant.stats.get_shrunken_lift(k=20) < 0.99
            
            if is_ghost or is_harmful:
                self._retire(variant, unregister_fn)
        
        # Defensive invariant: library should never exceed budget
        assert len(self.active_library) <= self.LIBRARY_BUDGET, \
            f"Library budget violation: {len(self.active_library)} > {self.LIBRARY_BUDGET}"
        
        return promoted

    # --- Helpers ---

    def _activate(self, variant, register_fn):
        """Activate a variant and register it as a macro."""
        # Deterministic Name: macro_{fam4}_{ex4}
        base = f"macro_{variant.family_hash[:4]}_{variant.exact_hash[:4]}"
        if base in self.active_library:
            # Collision - append more hash
            base += f"_{variant.exact_hash[4:6]}"
        
        variant.registry_name = base
        variant.status = "active"
        
        # COMPILE IT
        func = self.compiler.compile_macro(variant.subtree)
        register_fn(base, func, arity=0, needs_context=True)
        self.active_library[base] = variant

    def _retire(self, variant, unregister_fn):
        """Retire a variant and unregister it."""
        if variant.registry_name:
            unregister_fn(variant.registry_name)
            del self.active_library[variant.registry_name]
        variant.status = "retired"
        variant.registry_name = None

    def _get_best_variant(self, variants):
        """Get the variant with highest shrunken lift in a family."""
        valid = [v for v in variants.values() if v.status != "retired"]
        return max(valid, key=lambda v: v.stats.get_shrunken_lift()) if valid else None

    def _get_worst_active(self):
        """Get the active variant with lowest shrunken lift."""
        if not self.active_library:
            return None
        return min(self.active_library.values(), key=lambda v: v.stats.get_shrunken_lift())

    def _inline_expand_macros(self, tree, registry):
        """
        Recursively expand macros using .subtree_definition attribute.
        
        CRITICAL INVARIANT: Only macros have subtree_definition.
        This function will only expand functions that:
        1. Have needs_context=True
        2. Have subtree_definition attribute
        
        This ensures non-macro context-aware functions (if added later) are not expanded.
        """
        if not isinstance(tree, tuple):
            return tree
        
        func_obj = registry.get(tree[0])
        # The Introspection Hook - only macros have subtree_definition
        if func_obj and getattr(func_obj, "needs_context", False) and hasattr(func_obj, "subtree_definition"):
            # Expand the macro's subtree
            return self._inline_expand_macros(func_obj.subtree_definition, registry)
            
        # Not a macro, recurse on children
        return (tree[0],) + tuple(self._inline_expand_macros(c, registry) for c in tree[1:])

    def _extract_subtrees_with_hashes(self, tree):
        """
        Recursive walker. Returns list of (fam_hash, ex_hash, subtree).
        
        Only extracts subtrees meeting MIN_NODES complexity threshold.
        """
        results = []
        
        def _walk(node):
            # Must be a tuple (function) and meet min complexity
            if isinstance(node, tuple):
                if node_count(node) >= self.MIN_NODES:
                    # Compute hashes
                    ex_hash = merkle_hash(node, normalize_vars=False)
                    fam_hash = merkle_hash(node, normalize_vars=True)
                    results.append((fam_hash, ex_hash, node))
                
                # Recurse on children
                for child in node[1:]:
                    _walk(child)
        
        _walk(tree)
        return results
