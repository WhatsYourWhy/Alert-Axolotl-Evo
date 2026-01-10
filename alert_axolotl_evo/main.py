"""Entry point with CLI."""

import argparse
from pathlib import Path

from alert_axolotl_evo.config import add_config_args, load_config, merge_cli_args
from alert_axolotl_evo.evolution import evolve


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Alert Axolotl Evo: Genetic programming for alert rules")
    parser = add_config_args(parser)
    parser.add_argument("--load-checkpoint", type=Path, help="Path to checkpoint file to resume from")
    parser.add_argument("--save-checkpoint", type=Path, help="Path to save checkpoint file")
    parser.add_argument("--export-rule", type=Path, help="Path to export final champion rule")
    
    args = parser.parse_args()
    
    # Load config from file if provided, otherwise use defaults
    if args.config:
        config = load_config(args.config)
    else:
        config = load_config()  # Will try to load config.yaml or return defaults
    
    # Merge CLI arguments into config
    config = merge_cli_args(config, args)
    
    evolve(
        config=config,
        checkpoint_path=args.load_checkpoint,
        save_checkpoint_path=args.save_checkpoint,
        export_rule_path=args.export_rule,
    )


if __name__ == "__main__":
    main()

