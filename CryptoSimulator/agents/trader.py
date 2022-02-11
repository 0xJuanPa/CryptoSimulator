import itertools
import random

from CryptoSimulator.library_built_in.genetic_meta import genetic_flow


class TraderGenericTemplate:

    def __init__(self, name, *, initial_money):
        self.money = initial_money
        self.initial_money = initial_money
        self.wallet: dict[str, int] = dict()

    def trade(self):
        pass

    def initialize(self, simulation_scene):
        pass


class TraderGeneticTemplate(TraderGenericTemplate):
    def __init__(self, name, *, initial_money, generations=30, population_size=20):
        super().__init__(name, initial_money=initial_money)
        self.tuned_sell = 0
        self.tuned_buy = 0
        self._roulete = list()

        self.generations = generations
        self.population_size = population_size

    def tuned_buy_picker(self):
        pass

    def _elaborate_strategy(self, simulation):

        def populatefunc():
            solutions = []
            for _ in range(self.population_size):
                roulette = [random.uniform(0,1)]
                for _ in range(len(simulation.wallet) - 2):
                    roulette.append(random.uniform(0, 1-sum(roulette))) # n-1 numbers to split the probability
                sol = random.uniform(0,1),random.uniform(0,1), roulette
                solutions.append(sol)
            return solutions


        def fitness(solution):
            chunks = simulation.end_time // 10
            while simulation.time < simulation.end_time:
                self.trade()
                simulation.time += chunks
                for c in simulation.coins:
                    c.updateParameters()

            fitnesval = self.money
            return fitnesval, solution

        def stopcriteria(gen, solutions):
            if gen == self.generations:
                return next(iter(solutions))[1]
            return None

        def selection(solutions):
            sel = len(solutions) // 5  # 20%
            newsel = list(itertools.islice(solutions, 0, sel))
            return newsel

        def recombination(solutions):
            # crossover strategy
            new_gen = []
            for _ in range(self.population_size // 4):
                sol1 = random.choice(solutions)
                sol2 = random.choice(solutions)
                x = sol1[2]
                y = sol2[2]
                half = len(x) // 2
                # cross the roulettes
                new_roulete = x[:half] + y[half:]
                new_roulete2 = y[:half] + x[half:]
                new1 = sol1[0] , sol2[1] ,new_roulete
                new2 = sol2[0] , sol1[1], new_roulete2

                new3 = sol1[0] , sol2[1] ,new_roulete2
                new4 = sol2[0] , sol1[1], new_roulete
                new_gen.append(new1)
                new_gen.append(new2)
                new_gen.append(new3)
                new_gen.append(new4)
            return new_gen

        def mutation(solutions):
            mutated = []
            for sol in solutions:
                buy = sol[0] + random.uniform(-sol[0],sol[0])
                sell = sol[1] + random.uniform(-sol[1],sol[1])
                roulette = sol[2]
                mut = None
                mutated.append(mut)
            return mutated

        res = genetic_flow(populatefunc, fitness, stopcriteria, selection, recombination, mutation)
        self._roulete = res

    def initialize(self, simulation_scene):
        self._elaborate_strategy(simulation_scene)
