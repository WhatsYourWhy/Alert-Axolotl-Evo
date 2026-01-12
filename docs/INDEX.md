# Documentation Index

Navigation guide for Alert-Axolotl-Evo documentation, organized by audience and topic.

## Quick Navigation by Audience

### For End Users
- **[README.md](../README.md)**: Quick start, installation, basic usage
- **[USAGE.md](../USAGE.md)**: Practical usage guide with real-world examples
- **[docs/FITNESS_ALIGNMENT.md](FITNESS_ALIGNMENT.md)**: Understanding fitness scores and operational guarantees (User Guide section)

### For Developers
- **[ARCHITECTURE.md](../ARCHITECTURE.md)**: System architecture and design documentation
- **[docs/design_contract.md](design_contract.md)**: Design constraints for AI assistants
- **[docs/FITNESS_ALIGNMENT.md](FITNESS_ALIGNMENT.md)**: Implementation details and code locations (Developer Guide section)
- **[docs/FITNESS_ALIGNMENT_VALIDATION.md](FITNESS_ALIGNMENT_VALIDATION.md)**: Testing and validation methodology

### For Researchers
- **[ARCHITECTURE.md](../ARCHITECTURE.md)**: System architecture and design philosophy
- **[docs/FITNESS_ALIGNMENT.md](FITNESS_ALIGNMENT.md)**: Formal specification (Researcher Guide section)
- **[META_EVOLUTION.md](../META_EVOLUTION.md)**: Meta-evolution system documentation
- **[RESULTS.md](../RESULTS.md)**: Experiment results and discoveries

## Documentation by Topic

### Getting Started
- **[README.md](../README.md)**: Overview, installation, quick start
- **[USAGE.md](../USAGE.md)**: Practical usage examples

### System Architecture
- **[ARCHITECTURE.md](../ARCHITECTURE.md)**: Complete architecture documentation
  - Design contract and constraints
  - System components and data flow
  - Extension points
  - Testing strategy
- **[docs/design_contract.md](design_contract.md)**: Design contract for AI assistants
  - Non-negotiable goals
  - Architecture boundaries
  - Required invariants
  - Safe contribution checklist

### Fitness Alignment
- **[docs/FITNESS_ALIGNMENT.md](FITNESS_ALIGNMENT.md)**: Comprehensive alignment documentation
  - What is fitness alignment
  - Five-layer architecture
  - Operational constraints mapping
  - Implementation details
  - For different audiences
- **[docs/FITNESS_ALIGNMENT_VALIDATION.md](FITNESS_ALIGNMENT_VALIDATION.md)**: Validation guide
  - Baseline verification
  - Testing alignment mechanisms
  - Detecting alignment drift
  - Troubleshooting
- **[docs/FITNESS_ALIGNMENT_CHANGELOG.md](FITNESS_ALIGNMENT_CHANGELOG.md)**: Historical evolution
  - Phase-by-phase development
  - Threshold evolution
  - Lessons learned

### Data Loading
- **[docs/DATA_LOADING_REVIEW.md](DATA_LOADING_REVIEW.md)**: Data loading system review
  - CSV/JSON loading
  - Auto-labeling
  - Data provenance

### Advanced Features
- **[META_EVOLUTION.md](../META_EVOLUTION.md)**: Meta-evolution system
  - Evolving better evolution parameters
  - Self-improving system
- **[USAGE.md](../USAGE.md)**: Advanced usage examples
  - Self-improving evolution
  - Economic learning (Promotion Manager)
  - Custom data loaders

### Results and Examples
- **[RESULTS.md](../RESULTS.md)**: Experiment results and discoveries
- **[examples/fun_examples.md](../examples/fun_examples.md)**: Fun gamification examples
- **[examples/output_sample.txt](../examples/output_sample.txt)**: Sample evolution output

### Project Management
- **[CHANGELOG.md](../CHANGELOG.md)**: Version history and migration guide
- **[LICENSE](../LICENSE)**: License terms

## Documentation Relationships

```
README.md
├── Quick start and overview
├── Links to: ARCHITECTURE.md, USAGE.md, docs/FITNESS_ALIGNMENT.md
└── Installation and basic usage

ARCHITECTURE.md
├── System architecture overview
├── References: docs/design_contract.md, docs/FITNESS_ALIGNMENT.md
└── Extension points and testing

docs/FITNESS_ALIGNMENT.md
├── Main alignment documentation
├── References: docs/FITNESS_ALIGNMENT_VALIDATION.md, docs/FITNESS_ALIGNMENT_CHANGELOG.md
└── Links to code: alert_axolotl_evo/fitness.py

docs/FITNESS_ALIGNMENT_VALIDATION.md
├── Validation methodology
└── References: docs/FITNESS_ALIGNMENT.md, tests/test_fitness.py

docs/FITNESS_ALIGNMENT_CHANGELOG.md
├── Historical evolution
└── References: docs/FITNESS_ALIGNMENT.md, ARCHITECTURE.md

USAGE.md
├── Practical usage guide
├── References: docs/FITNESS_ALIGNMENT.md
└── Real-world examples

docs/design_contract.md
├── Design constraints
└── Referenced by: ARCHITECTURE.md
```

## Key Concepts Cross-Reference

### Fitness Alignment
- **Main Doc**: [docs/FITNESS_ALIGNMENT.md](FITNESS_ALIGNMENT.md)
- **Validation**: [docs/FITNESS_ALIGNMENT_VALIDATION.md](FITNESS_ALIGNMENT_VALIDATION.md)
- **History**: [docs/FITNESS_ALIGNMENT_CHANGELOG.md](FITNESS_ALIGNMENT_CHANGELOG.md)
- **Code**: `alert_axolotl_evo/fitness.py`
- **Config**: `alert_axolotl_evo/config.py` (FitnessAlignmentConfig)

### Evolutionary Economics
- **Main Doc**: [ARCHITECTURE.md](../ARCHITECTURE.md) (Promotion Manager section)
- **Design Contract**: [docs/design_contract.md](design_contract.md)
- **Usage**: [USAGE.md](../USAGE.md) (Self-Improving Evolution section)

### System Architecture
- **Main Doc**: [ARCHITECTURE.md](../ARCHITECTURE.md)
- **Design Contract**: [docs/design_contract.md](design_contract.md)
- **Five Layers**: [docs/FITNESS_ALIGNMENT.md](FITNESS_ALIGNMENT.md) (Five-Layer Architecture section)

## Finding What You Need

### "How do I get started?"
→ [README.md](../README.md) → [USAGE.md](../USAGE.md)

### "How does fitness alignment work?"
→ [docs/FITNESS_ALIGNMENT.md](FITNESS_ALIGNMENT.md)

### "How do I validate alignment is working?"
→ [docs/FITNESS_ALIGNMENT_VALIDATION.md](FITNESS_ALIGNMENT_VALIDATION.md)

### "What are the design constraints?"
→ [docs/design_contract.md](design_contract.md) → [ARCHITECTURE.md](../ARCHITECTURE.md)

### "How do I extend the system?"
→ [ARCHITECTURE.md](../ARCHITECTURE.md) (Extension Points section)

### "What changed in alignment over time?"
→ [docs/FITNESS_ALIGNMENT_CHANGELOG.md](FITNESS_ALIGNMENT_CHANGELOG.md)

### "How do I use the Promotion Manager?"
→ [USAGE.md](../USAGE.md) (Self-Improving Evolution section)

### "Where is the code for X?"
- Fitness alignment: `alert_axolotl_evo/fitness.py`
- Configuration: `alert_axolotl_evo/config.py`
- Evolution loop: `alert_axolotl_evo/evolution.py`
- Promotion Manager: `alert_axolotl_evo/promotion.py`

## Documentation Maintenance

This index should be updated when:
- New documentation files are added
- Documentation structure changes
- New cross-references are needed
- Documentation relationships change

See [docs/FITNESS_ALIGNMENT.md](FITNESS_ALIGNMENT.md) for documentation update protocol.
