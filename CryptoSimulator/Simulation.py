import inspect
from itertools import chain

from CryptoSimulator.library_built_in.sim_ops import leave
from interpreter import SimulationInterpreter


class Simulation:
    def __init__(self, endtime):
        self.wallet: list = []
        self.traders: list = []
        self.leaved: set = set()
        self.time = 1
        self.end_time = endtime
        self.verbose = True

    def visualize_coins(self):
        import numpy as np
        import pandas as pd
        import seaborn as sns
        import matplotlib.pyplot as plt
        sns.set_theme(style="whitegrid")

        times = np.arange(self.time, self.end_time, 20)
        # https://youtrack.jetbrains.com/issue/PY-52137 time wasted ON DEBUG
        values = []
        for t in times:
            self.time = t
            arr = []
            for coin in self.wallet:
                coin.update_parameters()
                arr.append(coin.value)
            values.append(np.array(arr))
        values = np.array(values)
        data = pd.DataFrame(values, index=times, columns=list(map(lambda x: x.name, self.wallet)))
        sns.lineplot(data=data)
        plt.show()

    def load(self, filepath):
        simulation_file = open(filepath)
        code = simulation_file.read()
        simulation_file.close()

        # may add builtins by reflection
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
        self.wallet, self.traders = interpr.interpret_simulation(code, self)

    def reset(self):
        self.time = 1
        self.verbose = True
        self.leaved.clear()
        for coin in self.wallet:
            coin.value = coin.base_value
        for trader in self.traders:
            trader.money = trader.initial_money
            trader.wallet.clear()

    def run(self):
        # self.visualize_coins()
        self.wallet[2].update_parameters()
        traders = list(self.traders)[3:4]
        for trader in traders:
            trader.initialize()
        while self.time < self.end_time:
            for trader in traders:
                if trader not in self.leaved:
                    trader.trade()

            for coin in self.wallet:
                coin.update_parameters()
            self.time += 10

        for trader in traders:
            if trader not in self.leaved:
                try:
                    leave(my=trader, market=self)
                except:
                    pass


if __name__ == "__main__":
    s = Simulation(1000)
    s.load("./SimulationCode.sim")
    s.run()
