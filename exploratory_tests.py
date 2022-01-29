import os

from toolchain.automaton import Automaton, State
from toolchain.frontend_generator import Grammar

g = Grammar()

## Ejemplo de conferenica lr1
S, E, A = g.symbol_emit(*"S,E,A".split(","))
i, plus, eq = g.symbol_emit(("intg", "intg", ""), ("+", "+", ""), ("=", "=", ""))

S > E
E > A + eq + A | i
A > i + plus+  A | i

current_path = os.path.dirname(__file__)
#g.write_lr1_parser(current_path)

# Ejemplo de la conferencia de automatas
nfa = Automaton()
q0 = State()
q1 = State()
q2 = State()
q3 = State(final=True)
nfa.add_state(q0, q1, q2, q3)
q0["a"] = q0
q0["b"] = q0
q0[None] = q1
q1["a"] = q2
q2["a"] = q3
q2["b"] = q3

dfa = nfa.get_dfa()

print()
