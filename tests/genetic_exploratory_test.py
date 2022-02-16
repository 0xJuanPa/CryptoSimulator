import itertools
import random

from CryptoSimulator.library_built_in.genetic_meta import genetic_flow

# testing the genetic flow using a simple root finding problem
population_size = 100


def populate():
    res = [(random.uniform(-1000, 1000), random.uniform(-1000, 1000), random.uniform(-1000, 1000)) for _ in
           range(population_size)]
    return res

def func_obj(solution):
    x, y, z = solution
    # objetive function
    result = x ** 2 + 2 * y + z ** 3
    return result


def fitness(solution):
    result =  func_obj(solution)
    if result == 0:
        fitnesval = 10 ** 4
    else:
        fitnesval = 1 / abs(result)

    return fitnesval, solution


def stopcriteria(gen,solutions):
    if (val := next(iter(solutions))[0]) > 1000:
        return next(iter(solutions))[1]
    print(val)
    return None


def selection(solutions):
    sel = len(solutions) // 5  # 20%
    newsel = list(itertools.islice(solutions, 0, sel))
    return newsel


def recombination(solutions):
    # make sure to have enough parents to preserve diversity in this case combinations of 20 in 2 is (20*(20-1))/2 > 100
    # but mutation takes care on this
    new_gen = []
    for _ in range(population_size // 2):
        x = random.choice(solutions)
        y = random.choice(solutions)
        half = len(x) // 2
        new1 = x[:half] + y[half:]
        new2 = x[half:] + y[:half]
        new_gen.append(new1)
        new_gen.append(new2)

    return new_gen


def mutation(solutions):
    # oh we so need this, hill climbing would acelerate but i can get all population stuck in a local, tabu?
    mutated = []
    for sol in solutions:
        mut = [x + random.uniform(-5,5) for x in sol]
        mutated.append(mut)
    return mutated

## lets see
result = genetic_flow(populate, fitness, stopcriteria, selection, recombination, mutation)

# Gen 3638   [2.692911755498806, 1.558371139001558, -2.18054945681725] =>>  0.0004483105617261174 ranking 1000
# perrfect for me
print(f"{result} -> {func_obj(result)}")
