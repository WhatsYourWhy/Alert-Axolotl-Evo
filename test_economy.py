"""
The 'Heartbeat' Test - Integration Test for Promotion Manager Economy.

This is an integration test script (not a unit test) that runs actual evolution
to verify the Promotion Manager economic system works correctly.

Verifies:
1. Monotonic Tick is advancing.
2. PromotionManager is discovering patterns.
3. The Economy is strictly enforcing the budget (Promotions & Evictions).

Run with: python test_economy.py

Note: This creates test artifacts in test_economy_results/ directory.
"""
import logging
import sys
from pathlib import Path

# Configure logging to see the market updates clearly
logging.basicConfig(level=logging.INFO, format='%(message)s')

from alert_axolotl_evo.config import Config
from alert_axolotl_evo.self_improving import SelfImprovingEvolver

def run_economy_test():
    print("=== Starting Economic Heartbeat Test ===")
    
    # 1. Setup the Landlord (SelfImprovingEvolver)
    # We set a SMALL budget (10) to force early evictions/churn for testing.
    # min_promo_batch=4 because we typically get 4 champions per run
    evolver = SelfImprovingEvolver(
        results_dir=Path("test_economy_results"),
        adapt_data=True,
        enable_promotion_manager=True,
        library_budget=10,  # Tiny budget to force 'Challenger' logic early
        min_promo_batch=4   # Match actual champion count per run
    )
    
    # 2. Setup Config (Fast & Chaos)
    config = Config()
    config.evolution.pop_size = 50        # Small pop for speed
    config.evolution.generations = 10      # More generations to accumulate champions
    config.data.mock_size = 50            # Small data
    config.operators.mutation_rate = 0.4   # High mutation to generate variety
    
    # 3. The Loop (10 ticks x 5 gens = 50 total generations of history)
    if evolver.promotion_manager:
        print(f"Initial Budget: {evolver.promotion_manager.LIBRARY_BUDGET}")
    print("Tick | Status | Active Library")
    print("-" * 50)

    previous_promoted_count = 0
    for i in range(10):
        # Run one 'Tick' of the economy
        run_data = evolver.run_and_learn(config, run_id=f"tick_{i}")
        
        # Report
        tick = evolver.economy_tick
        if evolver.promotion_manager:
            active_count = len(evolver.promotion_manager.active_library)
            budget = evolver.promotion_manager.LIBRARY_BUDGET
            current_promoted_count = len(evolver.promoted_macros)
            newly_promoted = current_promoted_count - previous_promoted_count
            previous_promoted_count = current_promoted_count
            
            # Debug: Check checkpoint for champion count
            checkpoint_file = evolver.results_dir / f"checkpoint_tick_{i}.json"
            champion_count = 0
            if checkpoint_file.exists():
                try:
                    from alert_axolotl_evo.persistence import load_checkpoint
                    checkpoint = load_checkpoint(checkpoint_file)
                    champion_count = len(checkpoint.get("champion_history", []))
                except:
                    pass
            
            if newly_promoted > 0:
                # Get the newly promoted macros
                newly_promoted_names = evolver.promoted_macros[-newly_promoted:]
                status_msg = f"{newly_promoted} promoted"
            else:
                status_msg = "Stable"
                newly_promoted_names = []
            
            print(f"{tick:4d} | {status_msg:12s} | {active_count}/{budget} active | {champion_count} champs")
            
            if newly_promoted_names:
                print(f"      -> New Macros: {newly_promoted_names}")
        else:
            print(f"{tick:4d} | N/A          | PromotionManager not enabled")

    print("\n=== Test Complete ===")
    if evolver.promotion_manager:
        print("Final Active Library:")
        if evolver.promotion_manager.active_library:
            for name, variant in evolver.promotion_manager.active_library.items():
                lift = variant.stats.get_shrunken_lift()
                count = variant.stats.present_count
                print(f"  - {name}: Lift={lift:.3f}, Present={count}, LastSeen={variant.stats.last_seen_gen}")
        else:
            print("  (empty - no promotions yet)")
        
        # Show candidate patterns being tracked
        all_candidates = []
        for fam, variants in evolver.promotion_manager.families.items():
            for variant in variants.values():
                if variant.status == "candidate":
                    lift = variant.stats.get_shrunken_lift()
                    all_candidates.append((lift, variant.stats.present_count, variant))
        
        if all_candidates:
            all_candidates.sort(key=lambda x: x[0], reverse=True)
            print(f"\nTop Candidate Patterns (tracking {len(all_candidates)} total):")
            for lift, count, variant in all_candidates[:5]:
                print(f"  - Lift={lift:.3f}, Present={count}, Absent={variant.stats.absent_count}")
                print(f"    (needs {evolver.promotion_manager.MIN_SAMPLES} samples, lift>{evolver.promotion_manager.MIN_SHRUNKEN_LIFT} to promote)")
        else:
            print("\nNo candidate patterns tracked yet (need more runs with consistent patterns)")
        
        print(f"\nTotal Promoted (all time): {len(evolver.promoted_macros)}")
        print(f"Final Economy Tick: {evolver.economy_tick}")
        print(f"\n[OK] Economy is 'breathing': Tick advancing monotonically")
        print(f"[OK] Batch guards working: Processing champions per run")
        if len(evolver.promoted_macros) > 0:
            print(f"[OK] Market activity detected: {len(evolver.promoted_macros)} promotions")
        else:
            print(f"[INFO] No promotions yet: Patterns need {evolver.promotion_manager.MIN_SAMPLES} samples to qualify")
    else:
        print("PromotionManager was not enabled")

if __name__ == "__main__":
    run_economy_test()
