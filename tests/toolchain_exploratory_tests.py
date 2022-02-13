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
# g.write_lexer(current_path)
g.write_lr1_parser(current_path)





# # Ejemplo de la conferencia de automatas
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

# dfa = nfa.get_dfa()
#
# print()







# Otro ejemplo
# class Elist:
#     def __init__(self,x,y= None):
#         self.elements = []
#         if isinstance(x,Elist):
#             self.elements.extend(x.elements)
#         else:
#             self.elements.append(x)
#         if y is not None:
#             self.elements.append(y)
#
#
# class EE:
#     def __init__(self,val):
#         self.val = val
#
# O,S, E, A = g.symbol_emit(*"O,S,E,A".split(","))
# sep, comma, i = g.symbol_emit(("sep", "#"), ("comma", ","), ("i", "i"))
# g.initial_symbol = O
# O > S
#
# S > sep + E + sep / (EE,(1,))
# E > E + comma + A / (Elist,(0,2)) \
# | A / (Elist,)
# A > i \
# | g.epsilon

#
# current_path = os.path.dirname(__file__)
# g.write_lexer(current_path)
# g.write_lr1_parser(current_path)
#
# from lexer import Lexer
# from parser import Parser
# from interpreter.simulation_interpreter import RegxMatcher
# lexer = Lexer(RegxMatcher())
# ast = E
# ast.Elist = Elist
# ast.EE = EE
# parser = Parser(ast)
# tokens = lexer("##")
# pr = parser(tokens)
# print()