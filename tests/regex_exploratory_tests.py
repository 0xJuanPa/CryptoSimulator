from toolchain.regx_engine import RegxEngine, RegxPattern

rex: RegxPattern = RegxEngine.compile("([A-Z])*")

m = rex.match("AAAAZZZ")

print()
