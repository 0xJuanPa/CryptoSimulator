import inspect
from itertools import chain

from interpreter import SimulationInterpreter


class Simulation:
    def __init__(self):
        self.coins = list()
        self.traders = list()

    def load(self, filepath):
        simulation_file = open(filepath)
        code = simulation_file.read()
        simulation_file.close()
        # TODO add builtins by reflection
        from agents import coin as coins
        from agents import trader as traders
        agent_teplates = dict()
        for name, clas in chain(coins.__dict__.items(), traders.__dict__.items()):
            name: str
            if not name.startswith("_"):
                agent_teplates[name] = clas

        from library_built_in import prob_distributions as prob
        builtins = dict()

        for name, func in chain(inspect.getmembers(prob,inspect.isfunction)):
            if not name.startswith("_"):
                builtins[name] = func

        interpr = SimulationInterpreter(builtins, agent_teplates)
        self.coins, self.traders = interpr.interpret_simulation(code)

    def run(self, endTime):
        current_time = 0

        while current_time < endTime:
            # to run simulation in traders mind it my have to be clonable or inmmutable
            for trader in self.traders:
                trader.trade(self.coins)

            for coin in self.coins:
                coin.validate()

            for coin in self.coins:
                coin.updateParameters()


def pick_cheaper():
    '''
    returns the cheaper coin
    '''
    pass

def get_expensier():
    '''
    returns the expensier coin
    '''

def get_random_coin():
    '''
    returns a random coin
    '''
    pass

def last_buy(coin):
    '''
    returns original purhase price, this make an agent non reactive only as now it keeps track
    '''
    pass

def buy(coin,amount):
    pass


def sell(coin,amount):
    pass


def leave():
    '''
    sells all coins and abandon the simulation
    '''
    pass



if __name__ == "__main__":
    s = Simulation()
    s.load("./SimulationCode.sim")
