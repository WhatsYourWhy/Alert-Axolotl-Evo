"""
Long Economy Test

Runs a disciplined long test to verify the economy actually works:
- Stable batch size (>= min_promo_batch)
- Small warmup (2 ticks)
- Enough ticks to hit MIN_SAMPLES (20)
- Verify: at least one promotion, at least one eviction, stable library size
"""
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO, format='%(message)s')

from alert_axolotl_evo.config import Config
from alert_axolotl_evo.self_improving import SelfImprovingEvolver

def run_long_economy_test():
    print("=== Long Economy Test ===")
    print("Goal: Verify economy promotes, evicts, and maintains budget\n")
    
    # Setup with parameters that should trigger market activity
    evolver = SelfImprovingEvolver(
        results_dir=Path("test_long_economy_results"),
        adapt_data=False,  # Disable to keep data stable
        enable_promotion_manager=True,
        library_budget=5,  # Small budget to force evictions
        min_promo_batch=4,  # Match expected champion count
        promo_warmup_ticks=2,  # Small warmup
    )
    
    # Config: enough generations to get stable champions
    config = Config()
    config.evolution.pop_size = 50
    config.evolution.generations = 10  # More generations = more champions
    config.data.mock_size = 50
    config.operators.mutation_rate = 0.3  # Moderate mutation for variety
    
    print(f"Configuration:")
    print(f"  Library Budget: {evolver.promotion_manager.LIBRARY_BUDGET}")
    print(f"  Min Promo Batch: {evolver.min_promo_batch}")
    print(f"  Warmup Ticks: {evolver.promo_warmup_ticks}")
    print(f"  Generations per Run: {config.evolution.generations}")
    print(f"  Target Ticks: 25 (should accumulate {25 * 4} = 100+ observations)\n")
    
    # Run enough ticks to accumulate evidence
    # MIN_SAMPLES = 20, so we need patterns to appear in multiple runs
    num_ticks = 25
    
    print("Running evolution ticks...")
    print("Tick | Status | Active | Promoted | Candidates")
    print("-" * 60)
    
    previous_promoted = 0
    for i in range(num_ticks):
        run_data = evolver.run_and_learn(config, run_id=f"tick_{i}")
        
        tick = evolver.economy_tick
        if evolver.promotion_manager:
            active_count = len(evolver.promotion_manager.active_library)
            budget = evolver.promotion_manager.LIBRARY_BUDGET
            current_promoted = len(evolver.promoted_macros)
            newly_promoted = current_promoted - previous_promoted
            previous_promoted = current_promoted
            
            # Count candidates
            candidate_count = sum(
                len([v for v in variants.values() if v.status == "candidate"])
                for variants in evolver.promotion_manager.families.values()
            )
            
            status = f"{newly_promoted} promoted" if newly_promoted > 0 else "Stable"
            print(f"{tick:4d} | {status:8s} | {active_count}/{budget} | {current_promoted:8d} | {candidate_count:10d}")
    
    print("\n" + "="*60)
    print("FINAL MARKET STATUS")
    print("="*60)
    
    # Print detailed market status
    evolver.print_market_status()
    
    # Verify invariants
    print("\n" + "="*60)
    print("ECONOMY VERIFICATION")
    print("="*60)
    
    pm = evolver.promotion_manager
    checks = {
        "At least one promotion": len(evolver.promoted_macros) > 0,
        "Library within budget": len(pm.active_library) <= pm.LIBRARY_BUDGET,
        "Candidates being tracked": sum(
            len([v for v in variants.values() if v.status == "candidate"])
            for variants in pm.families.values()
        ) > 0,
        "Economy tick advanced": evolver.economy_tick >= num_ticks,
    }
    
    # Check for evictions (harder to verify directly, but library should stabilize)
    if len(pm.active_library) == pm.LIBRARY_BUDGET and len(evolver.promoted_macros) > pm.LIBRARY_BUDGET:
        checks["Evictions occurred (promoted > budget)"] = True
    else:
        checks["Evictions occurred (promoted > budget)"] = False
    
    all_passed = True
    for check, passed in checks.items():
        status = "[PASS]" if passed else "[FAIL]"
        print(f"{status} {check}")
        if not passed:
            all_passed = False
    
    print("\n" + "="*60)
    if all_passed:
        print("[PASS] ECONOMY TEST PASSED: All invariants verified")
    else:
        print("[PARTIAL] ECONOMY TEST: Some checks failed (may need more ticks)")
    print("="*60)
    
    return all_passed

if __name__ == "__main__":
    run_long_economy_test()
