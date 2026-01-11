# Fun Examples - Alert Axolotl Evo

This document showcases the gamified and fun aspects of Alert Axolotl Evo.

## Champion Names

The system generates deterministic, fun names based on tree structure:

### Special Names (Based on Patterns)
- **Spikezilla the Threshold Tyrant**: Trees with 3+ `>` operators
- **Smoothie the Eternal Averager**: Trees with 3+ `avg` functions
- **Bloaty McRedundantface**: Trees with 3+ `and` operators

### Random Names (From Pool)
- Guardian Gremlin
- Chaos Critter
- Alert Axolotl
- Siren Salamander
- Whispering Watcher

## Funeral Logs

When individuals are culled, they get dramatic funeral announcements:

### Causes of Demise
- **terminal bloat**: Tree grew too large
- **false-alarm fever**: Too many false positives
- **overfitted hubris**: Over-complex tree that doesn't generalize
- **anomaly blindness**: Missed too many anomalies

### Example Funeral
```
RIP Bloaty McRedundantface (hash:g9j8k7) [gen 5]
Cause of demise: terminal bloat
Last words: ('if_alert', ('and', ('>', ('avg', 'latency'), 100), ('<', ('avg'...
Trash-talk: 'Maybe try being useful next time.'
```

## Champion Announcements

Each generation, the top performers are announced:

```
=== Generation 10 ===
Spikezilla the Threshold Tyrant faces the anomaly horde... fitness 8.45
Guardian Gremlin faces the anomaly horde... fitness 7.23
Smoothie the Eternal Averager faces the anomaly horde... fitness 6.12
→ 🐉 ROARS VICTORIOUSLY!
```

When fitness exceeds 0.9:
```
💥⚡🌟🔥 *CRASH* Anomaly detected! 🌟🔥⚡💥
```

## ASCII Tree Visualizations

Evolved rules are displayed as beautiful ASCII trees:

```
└─ if_alert
   ├─ >
   │  ├─ avg
   │  │  └─ latency
   │  └─ 100
   └─ High alert!
```

More complex example:
```
└─ if_alert
   ├─ and
   │  ├─ >
   │  │  ├─ avg
   │  │  │  └─ latency
   │  │  └─ 100
   │  └─ <
   │     ├─ max
   │     │  └─ latency
   │     └─ 200
   └─ Danger zone!
```

## Birth Announcements

New individuals are announced with flair:

```
A new beast awakens: Guardian Gremlin (hash:a3f2c1)
A new beast awakens: Alert Axolotl (hash:b4e3d2)
A new beast awakens: Siren Salamander (hash:c5f4e3)
```

## Example Evolution Run

Here's what a typical run looks like:

```python
from alert_axolotl_evo.evolution import evolve
from alert_axolotl_evo.config import Config

config = Config()
config.evolution.pop_size = 30
config.evolution.generations = 20
evolve(config=config)
```

Output will include:
- Birth announcements for new individuals
- Generation-by-generation champion displays
- Funeral logs for culled individuals
- Final champion announcement with full tree visualization

## Fun Tree Examples

### Simple Threshold Rule
```python
("if_alert", (">", ("avg", "latency"), 100), "High alert!")
```
**Name**: Spikezilla the Threshold Tyrant (if many `>` operators)

### Complex Logical Rule
```python
("if_alert", 
  ("and",
    (">", ("avg", "latency"), 100),
    ("<", ("max", "latency"), 200)
  ),
  "Danger zone!"
)
```
**Name**: Bloaty McRedundantface (if many `and` operators)

### Statistical Rule
```python
("if_alert",
  (">", ("stddev", "latency"), 20),
  "Anomaly detected!"
)
```
**Name**: Smoothie the Eternal Averager (if many `avg` functions)

## The Fun Factor

What makes Alert Axolotl Evo fun:

1. **Personality**: Each tree gets a unique, deterministic name
2. **Drama**: Funerals with causes of death and trash-talk
3. **Visual Appeal**: ASCII tree visualizations
4. **Gamification**: Champions, battles, evolution narrative
5. **Deterministic**: Same tree = same name (reproducible fun!)

The system maintains its playful nature while being a serious genetic programming tool for evolving alert rules.

