def initialPopulationfunc():
    '''
    some random search heuristic
    '''
    pass


def fitnessfunc(obj, solution):
    pass


def selectionfunc(selection, ):
    '''
    tournament or roulette
    '''
    pass


def recombinationfunc():
    '''
    half or whatever combiantioon
    '''
    pass


def mutationfunc():
    '''
    may be some tabu search explotation
    '''
    pass

def stopcriteria():
    '''
    it may be good enough or time or iterations
    '''
    pass

def genetic_flow(populate, fitness, stopcriteria, selection, recombination, mutationfunc):
    elem = populate()
    while True:
        ranked = map(fitness, elem)
        if best := stopcriteria(ranked):
            return best
        selection = selection(ranked)
        new_gen = recombination(selection)
        mutated = mutationfunc(new_gen)
        elem = mutated