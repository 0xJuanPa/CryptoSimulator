from .ast_crypto import *
from .visitor import *


class TreeInterpreter:
    def __init__(self,globalContext):
        self.globalContext = globalContext


    def wrap(self, fun:FunDef):
        '''
        returns a python callable objects that wraps managed func for interops
        '''

        def wrapper(*args):

            self.interpret()

            pass

        return wrapper

    @visitor
    def interpret(self, node: FunCall):
        funcdef = None
        map = node.Args.exec

    @visitor
    def interpret(self, node: BinaryOp):
        first = node.first.interpret()
        second = node.second.interpret()
        match node.op.lexeme:
            case "+":
                res = first + second
        return res

    @visitor
    def interpret(self, node: UnaryOp):
        first = node.first.interpret()
        match node.op.lexeme:
            case "-":
                res = -first
            case "!":
                res = ~first
        return res

    @visitor
    def interpret(self, node: If):
        condition = node.condition.interpret()
        if condition:
            ret = node.then_body.interpret()
        elif node.else_body:
            ret = node.else_body.interpret()
        return ret

    @visitor
    def interpret(self, node: While):
        while True:
            condition = node.condition.interpret()
            if condition:
                ret = node.body.interpret()
            else:
                break
        return ret

    @visitor
    def interpret(self, node: StatementList):
        # manage ret here
        for st in node.elements:
            pass
