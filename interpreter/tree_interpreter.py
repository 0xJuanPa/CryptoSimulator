from .ast_crypto import *
from .visitor import *


class TreeInterpreter:
    def __init__(self, global_context):
        self.global_context: Context = global_context

    def __call__(self, node):
        return self.interpret(node, self.global_context)

    def make_managed(self, fun):
        pass

    def wrap(self, fun: FunDef):
        '''
        returns a python callable objects that wraps managed func for interops
        '''

        def wrapper(*args):
            if len(args) != len(fun.params.elements):
                raise Exception("Runtime Exception diferent param signature")
            ctx = self.global_context.create_child_context()
            for identifier, val in zip(fun.params.elements, args):
                ctx[identifier.name] = val
            val = fun.interpret(self, ctx)
            return val

        return wrapper

    @visitor
    def interpret(self, node: OptList, ctx: Context):
        child = ctx.create_child_context()
        res = dict()
        for opt in node.elements:
            opt: Assign
            opt.interpret(self, child)
            res[opt.name.name] = child[opt.name.name]
        return res

    @visitor
    def interpret(self, node: Assign, ctx):
        res = node.value.interpret(self, ctx)
        ctx[node.name.name] = res

    @visitor
    def interpret(self, node: FunCall, ctx):
        func = node.name.interpret(self, ctx)
        args = []
        for expr in node.Args.elements:
            val = expr.interpret(self, ctx)
            args.append(val)
        child = ctx.create_child_context()
        if isinstance(func,FunDef):
            for param,value in zip(func.params.elements,args):
                child[param.name] = value
        else:
            # native func


    @visitor
    def interpret(self, node: BinaryOp, ctx):
        first = node.first.interpret(self, ctx)
        second = node.second.interpret(self, ctx)
        match node.op.lexeme:
            case "+":
                res = first + second
        return res

    @visitor
    def interpret(self, node: UnaryOp, ctx):
        first = node.first.interpret(self, ctx)
        match node.op.lexeme:
            case "-":
                res = -first
            case "!":
                res = ~first
        return res

    @visitor
    def interpret(self, node: If, ctx):
        condition = node.condition.interpret(self, ctx)
        if condition:
            ret = node.then_body.interpret(self, ctx)
        elif node.else_body:
            ret = node.else_body.interpret(self, ctx)
        return ret

    @visitor
    def interpret(self, node: While, ctx):
        while True:
            condition = node.condition.interpret(self, ctx)
            if condition:
                ret = node.body.interpret(self, ctx)
            else:
                break
        return ret

    @visitor
    def interpret(self, node: StatementList):
        # manage ret here
        for st in node.elements:
            pass

    @visitor
    def interpret(self, node: Identifier, ctx):
        res = ctx[node.name]
        return res

    @visitor
    def interpret(self, node: String, ctx):
        res = node.value
        return res

    @visitor
    def interpret(self, node: Number, ctx):
        res = node.value
        return res
