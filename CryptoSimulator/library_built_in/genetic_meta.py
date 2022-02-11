from typing import List, Tuple, Any


def initialPopulationfunc():
    '''
    some random search heuristic
    '''
    pass


def fitnessfunc(solution):
    '''
    Evaluate the quality of the solution
    '''
    pass

def selectionfunc(selection):
    '''
    tournament or roulette
    '''
    pass


def recombinationfunc(elems):
    '''
    crossover or random pick
    '''
    pass

def mutationfunc():
    '''
    may be some tabu search explotation
    '''
    pass


def stopcriteria(gen,solutions):
    '''
    it may be good enough or time or iterations
    '''
    pass


def genetic_flow(populatefunc, fitnessfunc, stopcriteriafunc, selectionfunc, recombinationfunc, mutationfunc):
    elem = populatefunc()
    i = 1
    while True:
        print(f"Gen {i}")
        i+=1
        ranked : List[Tuple[float,Any]] = list(map(fitnessfunc, elem))
        ranked = sorted(ranked, key=lambda x: x[0],reverse=True)
        if best := stopcriteriafunc(i,ranked):
            return best
        select = selectionfunc(ranked)
        select = list(map(lambda s:s[1],select))
        new_gen = recombinationfunc(select)
        mutated = mutationfunc(new_gen)
        elem = mutated
