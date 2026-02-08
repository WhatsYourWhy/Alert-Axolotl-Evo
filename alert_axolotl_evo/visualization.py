"""Visualization and gamified narrative functions."""

import hashlib
import logging
import random
from collections import Counter
from typing import Any, Dict, Tuple

from alert_axolotl_evo.tree import tree_hash


def print_ascii_tree(tree: Any, prefix: str = "", is_last: bool = True) -> str:
    """Render a tree with box-drawing characters."""
    connector = "└─ " if is_last else "├─ "
    lines = [f"{prefix}{connector}{tree[0]}" if isinstance(tree, tuple) else f"{prefix}{connector}{tree}"]
    if isinstance(tree, tuple):
        child_prefix = f"{prefix}{'   ' if is_last else '│  '}"
        children = list(tree[1:])
        for idx, child in enumerate(children):
            lines.append(print_ascii_tree(child, child_prefix, idx == len(children) - 1))
    return "\n".join(lines)


def generate_name(tree: Any) -> str:
    """Generate a fun, deterministic name based on tree structure."""
    tree_str = str(tree)
    gt_count = tree_str.count("'>'")
    avg_count = tree_str.count("'avg'")
    and_count = tree_str.count("'and'")
    if gt_count >= 3:
        return "Spikezilla the Threshold Tyrant"
    if avg_count >= 3:
        return "Smoothie the Eternal Averager"
    if and_count >= 3:
        return "Bloaty McRedundantface"
    choices = [
        "Guardian Gremlin",
        "Chaos Critter",
        "Alert Axolotl",
        "Siren Salamander",
        "Whispering Watcher",
    ]
    seed = int(hashlib.sha256(tree_str.encode("utf-8")).hexdigest(), 16)
    rng = random.Random(seed)
    return rng.choice(choices)


def log_funeral(tree: Any, gen: int) -> None:
    """Print a dramatic funeral for culled individuals."""
    name = generate_name(tree)
    cause = random.choice(["terminal bloat", "false-alarm fever", "overfitted hubris", "anomaly blindness"])
    last_words = str(tree)[:60] + ("..." if len(str(tree)) > 60 else "")
    logger = logging.getLogger("evo")
    logger.info("RIP %s (hash:%s) [gen %s]", name, tree_hash(tree), gen)
    logger.info("Cause of demise: %s", cause)
    logger.info("Last words: %s", last_words)
    logger.info("Trash-talk: 'Maybe try being useful next time.'")


def announce_birth(tree: Any) -> None:
    """Announce the birth of a new individual."""
    name = generate_name(tree)
    logging.getLogger("evo").info("A new beast awakens: %s (hash:%s)", name, tree_hash(tree))


def generate_pattern_name(subtree_hash: str, subtree: Tuple) -> str:
    """
    Generate a fun, deterministic name for a discovered pattern.
    
    Args:
        subtree_hash: Hash of the pattern
        subtree: The actual subtree tuple
        
    Returns:
        Fun pattern name
    """
    tree_str = str(subtree)
    
    # Special pattern types get epic names
    if "'window_avg'" in tree_str and "'stddev'" in tree_str:
        return "The Smooth Operator"
    if "'and'" in tree_str and tree_str.count("'>'") >= 2:
        return "The Multi-Threshold Guardian"
    if "'percentile'" in tree_str:
        return "The Percentile Prophet"
    if "'window_avg'" in tree_str and "'window_max'" in tree_str:
        return "The Window Wizard"
    if "'stddev'" in tree_str and "'>'" in tree_str:
        return "The Deviation Detector"
    if "'window_min'" in tree_str and "'window_max'" in tree_str:
        return "The Range Ranger"
    if "'or'" in tree_str and tree_str.count("'>'") >= 2:
        return "The Flexible Filter"
    
    # Generate deterministic name from hash
    pattern_names = [
        "The Pattern Prodigy",
        "The Algorithm Alchemist", 
        "The Logic Luminary",
        "The Structure Sage",
        "The Code Conjurer",
        "The Pattern Pioneer",
        "The Algorithm Architect",
        "The Logic Legend",
        "The Structure Sorcerer",
        "The Pattern Prophet",
    ]
    
    seed = int(hashlib.sha256(subtree_hash.encode()).hexdigest(), 16)
    rng = random.Random(seed)
    return rng.choice(pattern_names)


def get_pattern_personality(subtree: Tuple) -> Dict[str, str]:
    """
    Determine pattern personality based on structure.
    
    Args:
        subtree: Pattern subtree tuple
        
    Returns:
        Dictionary with {archetype, trait, catchphrase}
    """
    tree_str = str(subtree)
    
    personality = {
        "archetype": "The Guardian",
        "trait": "reliable",
        "catchphrase": "I detect anomalies!"
    }
    
    if "'window_avg'" in tree_str:
        personality["archetype"] = "The Smooth Operator"
        personality["trait"] = "patient"
        personality["catchphrase"] = "Let me smooth that out for you..."
    
    if "'stddev'" in tree_str:
        personality["archetype"] = "The Statistician"
        personality["trait"] = "analytical"
        personality["catchphrase"] = "The numbers don't lie!"
    
    if "'and'" in tree_str and tree_str.count("'and'") >= 2:
        personality["archetype"] = "The Perfectionist"
        personality["trait"] = "demanding"
        personality["catchphrase"] = "All conditions must be met!"
    
    if "'or'" in tree_str:
        personality["archetype"] = "The Flexible"
        personality["trait"] = "adaptable"
        personality["catchphrase"] = "Any way works for me!"
    
    if "'percentile'" in tree_str:
        personality["archetype"] = "The Percentile Prophet"
        personality["trait"] = "wise"
        personality["catchphrase"] = "I see the distribution!"
    
    if "'window_max'" in tree_str or "'window_min'" in tree_str:
        personality["archetype"] = "The Window Watcher"
        personality["trait"] = "observant"
        personality["catchphrase"] = "I watch the trends!"
    
    return personality


def announce_pattern_discovery(pattern_hash: str, pattern_name: str, 
                               count: int, avg_fitness: float) -> None:
    """
    Dramatically announce a newly discovered pattern.
    
    Args:
        pattern_hash: Hash of the pattern
        pattern_name: Fun name for the pattern
        count: Number of times pattern appears
        avg_fitness: Average fitness of trees containing this pattern
    """
    logger = logging.getLogger("pattern_discovery")
    
    logger.info("🔍 *PATTERN DISCOVERED* 🔍")
    logger.info("  Name: %s", pattern_name)
    logger.info("  Appearances: %d champions", count)
    logger.info("  Average Fitness: %.2f", avg_fitness)
    
    if count >= 10:
        logger.info("  Status: 🌟 LEGENDARY PATTERN 🌟")
    elif count >= 5:
        logger.info("  Status: ⭐ CHAMPION PATTERN ⭐")
    else:
        logger.info("  Status: 💫 RISING PATTERN 💫")


def announce_pattern_promotion(pattern_name: str, stage: str) -> None:
    """
    Celebrate pattern promotion through the lifecycle.
    
    Args:
        pattern_name: Fun name for the pattern
        stage: Lifecycle stage ("candidate", "probation", "promoted", "pruned")
    """
    logger = logging.getLogger("pattern_discovery")
    
    if stage == "candidate":
        logger.info("🎯 %s has been identified as a CANDIDATE!", pattern_name)
        logger.info("   It will be tested in the next generation...")
    
    elif stage == "probation":
        logger.info("🧪 %s enters PROBATION!", pattern_name)
        logger.info("   The system is watching... waiting...")
    
    elif stage == "promoted":
        logger.info("🎉 *PROMOTION CEREMONY* 🎉")
        logger.info("   %s has been PERMANENTLY REGISTERED!", pattern_name)
        logger.info("   It is now part of the primitive library!")
        logger.info("   🏆 All hail the new algorithm! 🏆")
    
    elif stage == "pruned":
        logger.info("💀 %s has been PRUNED", pattern_name)
        logger.info("   'Twas not meant to be...")


def display_pattern_leaderboard(patterns: Dict[str, Any], top_n: int = 5) -> None:
    """
    Display a fun leaderboard of most effective patterns.
    
    Args:
        patterns: Patterns dictionary from discover_structural_patterns()
        top_n: Number of top patterns to display
    """
    logger = logging.getLogger("pattern_discovery")
    
    metadata = patterns.get("subtree_metadata", {})
    hash_to_tree = patterns.get("hash_to_tree", {})
    
    if not metadata:
        logger.info("No patterns to rank yet.")
        return
    
    # Sort by effectiveness (count * avg_fitness)
    ranked = []
    for hash_val, meta in metadata.items():
        if meta["count"] > 0:
            avg_fit = meta["fitness_sum"] / meta["count"]
            effectiveness = meta["count"] * avg_fit
            subtree = hash_to_tree.get(hash_val)
            if subtree:
                pattern_name = generate_pattern_name(hash_val, subtree)
                ranked.append((hash_val, pattern_name, meta["count"], avg_fit, effectiveness))
    
    ranked.sort(key=lambda x: x[4], reverse=True)  # Sort by effectiveness
    ranked = ranked[:top_n]
    
    logger.info("\n🏆 PATTERN LEADERBOARD 🏆")
    logger.info("=" * 50)
    
    medals = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣"]
    for idx, (hash_val, pattern_name, count, avg_fit, _) in enumerate(ranked):
        medal = medals[idx] if idx < len(medals) else f"{idx+1}️⃣"
        logger.info("%s %s", medal, pattern_name)
        logger.info("   Appearances: %d | Avg Fitness: %.2f", count, avg_fit)


def print_pattern_discovery_summary(patterns: Dict[str, Any]) -> None:
    """
    Print a fun summary of pattern discovery results.
    
    Args:
        patterns: Patterns dictionary from discover_structural_patterns()
    """
    logger = logging.getLogger("pattern_discovery")
    
    exact_count = len(patterns.get("exact_subtrees", Counter()))
    abstract_count = len(patterns.get("abstract_algorithms", Counter()))
    total_structures = len(patterns.get("hash_to_tree", {}))
    
    logger.info("\n" + "="*60)
    logger.info("🔬 PATTERN DISCOVERY COMPLETE 🔬")
    logger.info("="*60)
    logger.info("📊 Statistics:")
    logger.info("   Exact Patterns Found: %d", exact_count)
    logger.info("   Abstract Algorithms: %d", abstract_count)
    logger.info("   Total Unique Structures: %d", total_structures)
    
    exact_subtrees = patterns.get("exact_subtrees", Counter())
    hash_to_tree = patterns.get("hash_to_tree", {})
    
    if exact_subtrees:
        top_exact = exact_subtrees.most_common(1)[0]
        logger.info("\n🌟 Most Common Exact Pattern:")
        logger.info("   Appears %d times", top_exact[1])
        if top_exact[0] in hash_to_tree:
            subtree_str = str(hash_to_tree[top_exact[0]])[:80]
            logger.info("   Structure: %s", subtree_str)
    
    abstract_algorithms = patterns.get("abstract_algorithms", Counter())
    if abstract_algorithms:
        top_abstract = abstract_algorithms.most_common(1)[0]
        logger.info("\n🧠 Most Common Algorithm:")
        logger.info("   Appears %d times", top_abstract[1])
        logger.info("   (This pattern works across different metrics!)")
    
    logger.info("\n💡 The system is learning... evolving... becoming smarter!")
    logger.info("="*60)


def announce_macro_promotion(name: str, lift: float, subtree: Tuple) -> None:
    """
    Dramatically announce a macro promotion to the active library.
    
    Args:
        name: Name of the promoted macro
        lift: Shrunken lift value (performance improvement)
        subtree: The subtree structure being promoted
    """
    logger = logging.getLogger("promotion_manager")
    
    logger.info("\n" + "="*60)
    logger.info("🎉 *MACRO PROMOTION CEREMONY* 🎉")
    logger.info("="*60)
    logger.info("✨ %s has been PROMOTED to the Active Library! ✨", name)
    logger.info("📈 Performance Lift: %.2fx", lift)
    
    # Generate a fun name for the macro
    from alert_axolotl_evo.visualization import generate_pattern_name
    try:
        pattern_name = generate_pattern_name(name, subtree)
        logger.info("🏷️  Pattern Name: %s", pattern_name)
    except Exception:
        pass
    
    # Show subtree structure (truncated)
    subtree_str = str(subtree)[:100]
    logger.info("🔧 Structure: %s", subtree_str)
    
    if lift >= 1.10:
        logger.info("🌟 Status: EXCEPTIONAL PERFORMANCE 🌟")
    elif lift >= 1.05:
        logger.info("⭐ Status: STRONG PERFORMANCE ⭐")
    else:
        logger.info("💫 Status: PROMISING PATTERN 💫")
    
    logger.info("🎊 The macro is now available for all future generations! 🎊")
    logger.info("="*60)


def announce_macro_retirement(name: str, reason: str) -> None:
    """
    Announce the retirement of a macro from the active library.
    
    Args:
        name: Name of the retired macro
        reason: Reason for retirement ("ghost" or "harmful")
    """
    logger = logging.getLogger("promotion_manager")
    
    if reason == "ghost":
        logger.info("👻 %s has been RETIRED (Ghost: unused for 15+ generations)", name)
        logger.info("   'Twas a noble macro, but its time has passed...")
    elif reason == "harmful":
        logger.info("💀 %s has been RETIRED (Harmful: lift < 0.99)", name)
        logger.info("   The system has learned it was not helpful...")
    else:
        logger.info("🔄 %s has been RETIRED (%s)", name, reason)
    
    logger.info("   It will be removed from the active library.")


def display_macro_library(active_library: Dict) -> None:
    """
    Display the current active macro library in a fun format.
    
    Args:
        active_library: Dictionary of active macros (name -> PatternVariant)
    """
    logger = logging.getLogger("promotion_manager")
    
    if not active_library:
        logger.info("📚 Macro Library: Empty (no macros promoted yet)")
        return
    
    logger.info("\n" + "="*60)
    logger.info("📚 ACTIVE MACRO LIBRARY 📚")
    logger.info("="*60)
    logger.info("Total Active Macros: %d", len(active_library))
    
    # Sort by lift (performance)
    ranked = []
    for name, variant in active_library.items():
        lift = variant.stats.get_shrunken_lift()
        ranked.append((name, lift, variant.stats.present_count, variant.stats.last_seen_gen))
    
    ranked.sort(key=lambda x: x[1], reverse=True)  # Sort by lift
    
    logger.info("\n🏆 Rankings (by Performance Lift):")
    medals = ["🥇", "🥈", "🥉"]
    for idx, (name, lift, count, last_gen) in enumerate(ranked):
        medal = medals[idx] if idx < len(medals) else f"{idx+1}."
        logger.info("%s %s", medal, name)
        logger.info("   Lift: %.3fx | Uses: %d | Last Seen: Gen %d", lift, count, last_gen)
    
    logger.info("="*60)

