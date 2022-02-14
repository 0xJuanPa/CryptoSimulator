import argparse
import inspect
import os
from importlib.machinery import SourceFileLoader
from pathlib import Path

from CryptoSimulator.library_built_in.sim_ops import leave
from interpreter import SimulationInterpreter
from interpreter.tree_interpreter import TrowableReturnContainer


class Simulation:
    def __init__(self):
        self.wallet: list = []
        self.traders: list = []
        self.leaved: set = set()
        self.init_time = 1
        self.time = 1
        self.end_time = 1
        self.step_size = 10
        self.verbose = True

    def set_params(self, coins, traders, *, init_time=1, endtime, step_size=10):
        self.wallet: list = coins
        self.traders: list = traders
        self.leaved: set = set()
        self.init_time = init_time
        self.time = init_time
        self.end_time = endtime
        self.step_size = step_size

    @staticmethod
    def _plot(names, values):
        # https://youtrack.jetbrains.com/issue/PY-52137 time wasted ON DEBUG
        import pandas as pd
        import seaborn as sns
        import matplotlib.pyplot as plt
        sns.set_theme(style="whitegrid")
        times, values = map(list, zip(*values))
        data = pd.DataFrame(values, index=times, columns=names)
        sns.lineplot(data=data)
        plt.figure()

    @staticmethod
    def _view():
        import matplotlib.pyplot as plt
        plt.show()

    @staticmethod
    def _reflected_load(path, predicate) -> dict:
        currentdir = os.path.dirname(__file__)
        agents = Path(os.path.join(currentdir, path)).glob("*.py")
        loaded = dict()
        for file in agents:
            module = SourceFileLoader(str(file), str(file)).load_module()
            for name, class_ in inspect.getmembers(module, predicate):
                name: str
                if not name.startswith("_"):
                    loaded[name] = class_
        return loaded

    @staticmethod
    def load(simulation_file):
        agent_templates = Simulation._reflected_load("agents", inspect.isclass)
        builtins = Simulation._reflected_load("library_built_in", inspect.isfunction)
        code = simulation_file.read()
        simulation_file.close()
        sim_opts = filter(lambda p: p.kind == inspect.Parameter.KEYWORD_ONLY,
                          inspect.signature(Simulation.set_params).parameters.values())
        sim_opts = set(map(lambda p: p.name, sim_opts))
        interpr = SimulationInterpreter(builtins, agent_templates, sim_opts)
        sim = Simulation()
        coins, traders, opts = interpr.interpret_simulation(code, sim)
        sim.set_params(coins, traders, **opts)
        return sim

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
        traders = list(self.traders)
        for trader in traders:
            trader.initialize()
        coins_values = []
        traders_values = []
        while self.time < self.end_time:
            c_v = []
            for coin in self.wallet:
                coin.update_parameters()
                c_v.append(coin.value)
            coins_values.append((self.time, c_v))
            t_v = []
            for trader in traders:
                if trader not in self.leaved:
                    trader.trade()
                    t_v.append(trader.money)
            traders_values.append((self.time, t_v))
            self.time += self.step_size

        coins_name = list(map(lambda x: x.name, self.wallet))
        Simulation._plot(coins_name, coins_values)

        traders_name = list(map(lambda x: x.name, traders))
        Simulation._plot(traders_name, traders_values)

        t_v = []
        for trader in traders:
            try:
                leave(my=trader, market=self)
            except TrowableReturnContainer:
                pass
            t_v.append(trader.money)
        traders_values.append((self.time, t_v))
        Simulation._view()


if __name__ == "__main__":
    argsparser = argparse.ArgumentParser()
    argsparser.add_argument('file', help="CryptoLang Simulation File", type=argparse.FileType('r'))
    args = argsparser.parse_args()
    s = Simulation.load(args.file)
    s.run()
