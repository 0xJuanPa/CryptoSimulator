from interpreter.simulation_interpreter import SimulationInterpreter

interpreter =  SimulationInterpreter()
interpreter.interpret_simulation("""

func hello (a,b,c,d) { x = 1+2*3; }



""")