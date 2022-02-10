import inspect
from itertools import chain

from interpreter import SimulationInterpreter


class Simulation:
    def __init__(self):
        self.wallet = list()
        self.traders = list()
        self.time = 0

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
        from library_built_in import sim_ops

        builtins = dict()
        for name, func in chain(inspect.getmembers(sim_ops, inspect.isfunction),
                                inspect.getmembers(prob, inspect.isfunction)):
            if not name.startswith("_"):
                builtins[name] = func

        interpr = SimulationInterpreter(builtins, agent_teplates)
        self.wallet, self.traders = interpr.interpret_simulation(code,self)

    def run(self, endTime):
        current_time = 0
        for trader in self.traders:
            while current_time < endTime:
                # to run simulation in traders mind it my have to be clonable or inmmutable
                trader.trade()
                for coin in self.wallet:
                    coin.updateParameters()


if __name__ == "__main__":
    s = Simulation()
    s.load("./SimulationCode.sim")
    s.run(1000)
