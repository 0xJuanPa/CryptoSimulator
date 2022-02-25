from collections import deque
from itertools import chain, repeat
from typing import Dict, List, Set, Callable, FrozenSet, Any, Iterable, Tuple


class State:
    def __init__(self, name=None, final: bool = False, content=None):
        self.name = name
        self.final: bool = final
        self.transitions: Dict[Any, State] | None = dict()
        self.epsilon_transitions: List[State] | None = list()
        self.content: Set | FrozenSet | Tuple = content

    def get_copy(self, prefix) -> "State":
        name = None if prefix is None else prefix + self.name
        res = State(name, self.final, self.content)
        return res

    def __repr__(self):
        res = f"{self.name} c:{self.content}"
        return res

    def get_transition_symbols(self):
        res = self.transitions.keys()
        return tuple(res)

    def __hash__(self):
        return hash(self.name)  # hash idempotent on int

    def __eq__(self, other: "State"):
        return hash(self) == hash(other)

    def __add__(self, other: "State"):
        name = None  # int(str(self.name) + str(other.name))
        content = self.content.__class__(
            chain(self.content, other.content)) if self.content and other.content else self.content or other.content
        res = State(name, self.final or other.final, content)
        return res

    def __radd__(self, other: "State"):
        if other == 0:
            return self.get_copy(None)
        return self + other

    def __getitem__(self, item):
        if item is None:
            return self.epsilon_transitions
        else:
            return self.transitions.get(item, None)

    def __setitem__(self, key, value):
        if key is None:
            self.epsilon_transitions.append(value)
        else:
            self.transitions[key] = value


class Automaton:
    def __init__(self):
        self.states: Set[State] = set()
        self.final_states: Set[State] = set()
        self.initial_state: State | None = None
        self.counter = 1

    def add_state(self, *to_Add):
        for st in to_Add:
            if st.name is None:
                st.name = self.counter
                self.counter += 1
            if st in self.states:
                # print('Wrn Renamed state Collition')
                st.name += self.counter
                self.counter += 1
                self.add_state(st)

            if self.initial_state is None:
                self.initial_state = st
            if st.final:
                self.final_states.add(st)
            self.states.add(st)

    def view(self):
        import graphviz
        import tempfile
        def repr_n(s):
            res = str(s.name) + "\n" + ("\n".join(map(repr, s.content)) if s.content else "")
            return res

        graph = graphviz.Digraph("fa", format="svg")
        graph.attr(rankdir="LR", outputMode="nodesfirst")
        graph.attr("node", shape="Mcircle")
        graph.node(repr_n(self.initial_state))
        for src in sorted(self.states, key=lambda s: s.name):
            src_rpr = repr_n(src)
            graph.attr("node", shape=("doublecircle" if src.final else "circle"))
            graph.node(src_rpr)
            for e, dst in chain(src.transitions.items(), zip(repeat(None), src.epsilon_transitions)):
                e_repr = str(e) if e is not None else "€"
                dst_rpr = repr_n(dst)
                graph.attr("node", shape=("doublecircle" if dst.final else "circle"))
                graph.node(dst_rpr)
                graph.edge(src_rpr, dst_rpr, label=e_repr)
        graph.unflatten().view(tempfile.mktemp(".gv"))

    def get_copy(self, prefix=None) -> "Automaton":
        new_automaton = Automaton()
        cpy_map = dict()
        for src in self.states:
            if (src_cpy := cpy_map.get(src, None)) is None:
                src_cpy = src.get_copy(prefix)
                cpy_map[src] = src_cpy
                new_automaton.add_state(src_cpy)
            for e, dst in chain(src.transitions.items(), zip(repeat(None), src.epsilon_transitions)):
                if (dst_cpy := cpy_map.get(dst, None)) is None:
                    dst_cpy = dst.get_copy(prefix)
                    cpy_map[dst] = dst_cpy
                    new_automaton.add_state(dst_cpy)
                src_cpy[e] = dst_cpy

        new_automaton.initial_state = cpy_map[self.initial_state]
        return new_automaton

    @staticmethod
    def _get_goto(states: Iterable[State], symbol) -> Tuple[State]:
        goto = tuple(sorted(set([st[symbol] for st in states if st[symbol] is not None]),key=hash))
        return goto

    @staticmethod
    def _get_epsilon_closure_of(states: Iterable[State]) -> Tuple[State]:
        visited = set()
        mdfs_stack = list(states)  # recursion not good in python
        while mdfs_stack:
            state = mdfs_stack.pop()
            visited.add(state)
            not_visited = list(filter(lambda s: s not in visited, state.epsilon_transitions))
            mdfs_stack.extend(not_visited)
        res = tuple(sorted(visited,key=hash))
        return res

    @staticmethod
    def powerset_construct(initial_value: Iterable[Any], goto_func: Callable[[Tuple, Any], Tuple],
                           closure_func: Callable[[Any], Tuple], state_maker: Callable[[Tuple], State],
                           transition_symbol_resolver: Callable[[Any], Any]) -> "Automaton":
        # Rabin–Scott powerset construction
        dfa = Automaton()
        start_closure = closure_func(initial_value)
        init_state = state_maker(start_closure)
        dfa.add_state(init_state)
        added: Dict[Tuple, State] = {start_closure: init_state}
        pending_closures = deque([start_closure])  # just to mantain the order for dbg

        while pending_closures:
            subset = pending_closures.popleft()
            state = added[subset]
            transition_symbols = transition_symbol_resolver(subset)
            for symbol in transition_symbols:
                goto = goto_func(subset, symbol)
                goto_closure = closure_func(goto)
                if (new_state := added.get(goto_closure, None)) is None:
                    pending_closures.append(goto_closure)
                    new_state = state_maker(goto_closure)
                    dfa.add_state(new_state)
                    added[goto_closure] = new_state
                state[symbol] = new_state
        return dfa

    def is_dfa(self) -> bool:
        res = all(map(lambda x: len(x.epsilon_transitions) == 0, self.states))
        return res

    def get_dfa(self) -> "Automaton":
        if self.is_dfa():
            return self
        transition_symbol_resolver: Callable[[Any], Any] = \
            lambda subset: sorted(set(chain.from_iterable(x.get_transition_symbols() for x in subset)),key=hash)
        state_maker: Callable[[Any], int | Any] = lambda subset: sum(subset)
        goto_func = self._get_goto
        closure_func = self._get_epsilon_closure_of
        initial_value = [self.initial_state]
        dfa = self.powerset_construct(initial_value, goto_func, closure_func, state_maker, transition_symbol_resolver)
        return dfa

    def __repr__(self):
        res = f"States {len(self.states)}, Finals {len(self.final_states)}, Initial {self.initial_state.name}"
        return res

    def __add__(self, other: "Automaton") -> "Automaton":
        prefix = len(self.states) + len(other.states)
        new_automaton = self.get_copy(prefix)
        copy_o = other.get_copy(prefix * 2)
        # concat automatons using epsilon transitions
        for final in new_automaton.final_states:
            final[None] = copy_o.initial_state
            final.final = False
        new_automaton.final_states.clear()
        new_automaton.add_state(*copy_o.states)
        return new_automaton

    def __or__(self, other: "Automaton") -> "Automaton":
        prefix = len(self.states) + len(other.states)
        new_automaton = self.get_copy(prefix)
        copy_o = other.get_copy(prefix * 2)
        new_automaton.add_state(*copy_o.states)
        # or automatons using epsilon transitions from dummy initial state
        dummy_init = State()
        new_automaton.add_state(dummy_init)
        dummy_init[None] = new_automaton.initial_state
        dummy_init[None] = copy_o.initial_state
        new_automaton.initial_state = dummy_init
        return new_automaton

    def lazy(self):
        new_automaton = self.get_copy()
        for final in new_automaton.final_states:
            new_automaton.initial_state[None] = final
        return new_automaton

    def repeat(self):
        new_automaton = self.get_copy()
        for final in new_automaton.final_states:
            final[None] = new_automaton.initial_state
        return new_automaton
