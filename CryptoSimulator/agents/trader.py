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

    @staticmethod
    def register_param(str,*,my):
        setattr(my, str, 0)
        my.optimized_attrs.append(str)

    @staticmethod
    def optimize(gens, *, market,my):
        print()
        def populatefunc():
            solutions = []
            for _ in range(my.population_size):
                sol = [random.uniform(0, 1) for _ in my.optimized_attrs]
                solutions.append(sol)
            return solutions

        def fitness(solution):
            market.verbose = False
            chunks = market.end_time // 20
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
                fit,sol = next(iter(solutions))
                print(f"Optimization completed {fit}")
                for attr, val in zip(my.optimized_attrs, sol):
                    setattr(my, attr, val)
                    print(f"{attr}={val}")
                return sol
            return None

        def selection(solutions):
            sel = len(solutions) // 5  # 20%
            newsel = list(itertools.islice(solutions, 0, sel))
            return newsel

        def recombination(solutions):
            # crossover strategy middle point
            new_gen = []
            for _ in range(my.population_size // 2):
                sol1 = random.choice(solutions)
                sol2 = random.choice(solutions)
                half = len(sol1) // 2
                # cross the roulettes
                new_sols1 = sol1[:half] + sol2[half:]
                new_sols2 = sol2[:half] + sol1[half:]
                new_gen.append(new_sols1)
                new_gen.append(new_sols2)
            return new_gen

        def mutation(solutions):
            mutated = []
            for sol in solutions:
                mut = [x + random.uniform(-0.1, 0.1) for x in sol]
                for i in range(len(mut)):
                    if mut[i] < 0:
                        mut[i] = 0
                    if mut[i] > 1:
                        mut[i] = 1
                mutated.append(mut)
            return mutated

        res = genetic_flow(populatefunc, fitness, stopcriteria, selection, recombination, mutation)
        print()