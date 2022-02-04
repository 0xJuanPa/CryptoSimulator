from toolchain.regx_engine import RegxEngine, RegxPattern

rex: RegxPattern = RegxEngine.compile("([^a-z])*")

m = rex.match("AAAAZZZ")

print()
