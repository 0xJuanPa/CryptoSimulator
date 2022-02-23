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
        self.repetitions = 1

    def set_params(self, coins, traders, *, init_time=1, endtime, step_size=10, repetitions=1):
        self.wallet: list = coins
        self.traders: list = traders
        self.leaved: set = set()
        self.init_time = init_time
        self.time = init_time
        self.end_time = endtime
        self.step_size = step_size
        self.repetitions = repetitions

    @staticmethod
    def _plot(names, values, graph_name=""):
        # https://youtrack.jetbrains.com/issue/PY-52137 time wasted ON DEBUG
        import pandas as pd
        import seaborn as sns
        import matplotlib.pyplot as plt
        plt.figure()
        sns.set_theme(style="whitegrid")
        times, values = map(list, zip(*values))
        data = pd.DataFrame(values, index=times, columns=names)
        sns.lineplot(data=data).set_title(graph_name)

    @staticmethod
    def _makefigs(only_view=False):
        import matplotlib.pyplot as plt
        from matplotlib.backends.backend_pdf import PdfPages
        if only_view:
            plt.show()
        else:
            filename = "plots.pdf"
            pp = PdfPages(filename)
            figs = [plt.figure(n) for n in plt.get_fignums()]
            for fig in figs:
                fig.savefig(pp, format='pdf')
            pp.close()

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
        self.time = self.init_time
        self.verbose = True
        self.leaved.clear()
        for coin in self.wallet:
            coin.value = coin.base_value
        for trader in self.traders:
            trader.money = trader.initial_money
            trader.wallet.clear()

    def run(self):
        traders = list(self.traders)
        print("Initializing Traders")
        for trader in traders:
            trader.initialize()
        coins_values = []
        traders_values = []
        traders_average = [0] * len(traders)
        coins_name = list(map(lambda x: x.name, self.wallet))
        traders_name = list(map(lambda x: x.name, traders))
        print("Traders Initialized")

        for index in range(self.repetitions):
            print(f"Running Simulation {index}")
            self.reset()
            coins_values.clear()
            traders_values.clear()
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
            t_v = []
            for i, trader in enumerate(traders):
                try:
                    leave(my=trader, market=self)
                except TrowableReturnContainer:
                    pass
                traders_average[i] += trader.money
                t_v.append(trader.money)
            traders_values.append((self.time, t_v))
            Simulation._plot(coins_name, coins_values, f"Coins Sim:{index}")
            Simulation._plot(traders_name, traders_values, f"Traders Sim:{index}")

        print("\n#### RESULTS ####")
        for trader, money in zip(traders, traders_average):
            print(f"{trader.name} : {money / self.repetitions}")
        print("Plotting")
        Simulation._makefigs()


if __name__ == "__main__":
    argsparser = argparse.ArgumentParser()
    argsparser.add_argument('file', help="CryptoLang Simulation File", type=argparse.FileType('r'))
    args = argsparser.parse_args()
    s = Simulation.load(args.file)
    s.run()
