"""Example of extending primitives."""

from alert_axolotl_evo.evolution import evolve
from alert_axolotl_evo.config import Config
from alert_axolotl_evo.primitives import register_function, register_terminal

# Register custom function
register_function("multiply", lambda a, b: a * b, arity=2)
register_function("divide", lambda a, b: a / b if b != 0 else 0, arity=2)

# Register custom terminals
register_terminal(300)
register_terminal("Custom alert message!")

if __name__ == "__main__":
    config = Config()
    config.evolution.pop_size = 30
    config.evolution.generations = 20
    evolve(config=config)

