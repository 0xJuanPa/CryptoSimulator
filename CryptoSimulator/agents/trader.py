import itertools
import random

from CryptoSimulator.library_built_in.genetic_meta import genetic_flow


class TraderGenericTemplate:

    def __init__(self, name, *, initial_money):
        self.name = name
        self.money = initial_money
        self.initial_money = initial_money
        self.wallet: dict[str, int] = dict()

    def __hash__(self):
        return hash(self.name)

    def __eq__(self, other):
        return hash(self) == hash(other)

    def __repr__(self):
        res = f"Trader {self.name} money {self.money}"
        return res

    def trade(self):
        pass

    def initialize(self):
        pass


class TraderGeneticTemplate(TraderGenericTemplate):
    def __init__(self, name, *, initial_money, population_size=20):
        super().__init__(name, initial_money=initial_money)
        self.population_size = population_size
        self.optimized_attrs = []
        self.population_funcs = dict()
        self.mutation_funcs = dict()

    @staticmethod
    def register_param(str, *, my):
        setattr(my, str, 0)
        my.optimized_attrs.append(str)

    @staticmethod
    def register_generator(str, func, *, my):
        my.population_funcs[str] = func

    @staticmethod
    def register_mutator(str, func, *, my):
        my.mutation_funcs[str] = func

    @staticmethod
    def optimize(gens, step_div=20, selection_div=5, *, market, my):
        print()

        def populatefunc():
            solutions = []
            for _ in range(my.population_size):
                sol = []
                for param in my.optimized_attrs:
                    if param in my.population_funcs:
                        resp = my.population_funcs[param]()
                        sol.append(resp)
                    else:
                        sol.append(random.uniform(0, 1))
                solutions.append(sol)
            return solutions

        def fitness(solution):
            # run simulation in traders mind
            market.verbose = False
            chunks = market.end_time // step_div
            for attr, val in zip(my.optimized_attrs, solution):
                setattr(my, attr, val)
            while market.time < market.end_time:
                my.trade()
                market.time += chunks
                for c in market.wallet:
                    c.update_parameters()
            fitnesval = my.money
            market.reset()
            return fitnesval, solution

        def stopcriteria(gen, solutions):
            if gens == gen:
                fit, sol = next(iter(solutions))
                print(f"Optimization completed {fit}")
                for attr, val in zip(my.optimized_attrs, sol):
                    setattr(my, attr, val)
                    print(f"{attr}={val}")
                return sol
            return None

        def selection(solutions):
            sel = len(solutions) // selection_div  # default 5  # 20%
            newsel = list(itertools.islice(solutions, 0, sel))
            return newsel

        def recombination(solutions):
            # crossover strategy middle point
            new_gen = []
            for _ in range(my.population_size // 2):
                sol1 = random.choice(solutions)
                sol2 = random.choice(solutions)
                half = len(sol1) // 2
                new_sols1 = sol1[:half] + sol2[half:]
                new_sols2 = sol2[:half] + sol1[half:]
                new_gen.append(new_sols1)
                new_gen.append(new_sols2)
            return new_gen

        def mutation(solutions):
            mutated = []
            for sol in solutions:
                mut = []
                for param, val in zip(my.optimized_attrs, sol):
                    if param in my.mutation_funcs:
                        resp = my.mutation_funcs[param](val)
                        mut.append(resp)
                    else:
                        resp = val + random.uniform(-0.1, 0.1)
                        resp = min(max(resp, 0), 1)
                        mut.append(resp)
                mutated.append(mut)
            return mutated

        res = genetic_flow(populatefunc, fitness, stopcriteria, selection, recombination, mutation)
        print()
