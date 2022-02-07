from interpreter import SimulationInterpreter


class Simulation:
    def __init__(self):
        self.coins = list()
        self.traders = list()

    def load(self, filepath):
        simulation_file = open(filepath)
        code = simulation_file.readlines()
        simulation_file.close()
        # TODO add built ins to scope
        interpr = SimulationInterpreter()
        self.coins,self.traders = interpr.interpret_simulation(code)


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