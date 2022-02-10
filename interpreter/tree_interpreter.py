from .ast_crypto import *
from .visitor import *


class TrowableReturnContainer(Exception):
    def __init__(self, value=None):
        self.value = value


class TreeInterpreter:
    def __init__(self, global_context):
        self.global_context: Context = global_context

    def __call__(self, node):
        return self.interpret(node, self.global_context)

    def make_native(self, fun: FunDef, context=None):
        '''
        returns a python callable objects that wraps managed func for interops
        '''
        if context is None:
            context = self.global_context

        def wrapper(*args):
            if len(args) != len(fun.params.elements if fun.params is not None else []):
                raise Exception("Runtime Exception diferent param signature")
            child = context.create_child_context() # my with be a level up in contexts
            if fun.params:
                for identifier, val in zip(fun.params.elements, args):
                    child[identifier.name] = val
            ret = None
            try:
                fun.body.interpret(self, child)
            except TrowableReturnContainer as retcontainer:
                ret = retcontainer.value
            return ret

        return wrapper

    @visitor
    def interpret(self, node: OptList, ctx: Context):
        child = ctx.create_child_context()
        res = dict()
        for opt in node.elements:
            opt: Assign
            opt.interpret(self, child)
            res[opt.left.name] = child[opt.left.name]
        return res

    @visitor
    def interpret(self, node: Assign, ctx):
        res = node.value.interpret(self, ctx)
        ctx[node.left.name] = res

    @visitor
    def interpret(self, node: FunCall, ctx):
        func = node.name.interpret(self, ctx)
        args = []
        ret = None
        for expr in node.Args.elements:
            val = expr.interpret(self, ctx)
            args.append(val)
        if isinstance(func, FunDef):
            child = ctx.create_child_context()
            for param, value in zip(func.params.elements, args):
                child[param.name] = value
            try:
                func.body.interpret(self, child)
            except TrowableReturnContainer as retcontainer:
                ret = retcontainer.value
            return ret
        else:
            ret = func(*args)
        return ret

    @visitor
    def interpret(self, node: BinaryOp, ctx):
        first = node.first.interpret(self, ctx)
        second = node.second.interpret(self, ctx)
        match node.op:
            case TOKEN_TYPE.PLUS:
                res = first + second
            case TOKEN_TYPE.AND:
                res = first & second
            case _:
                raise Exception("??")
        return res

    @visitor
    def interpret(self, node: UnaryOp, ctx):
        first = node.first.interpret(self, ctx)
        match node.op:
            case TOKEN_TYPE.MINUS:
                res = -first
            case TOKEN_TYPE.NOT:
                res = ~first
            case _:
                raise Exception("??")
        return res

    @visitor
    def interpret(self, node: If, ctx):
        condition = node.condition.interpret(self, ctx)
        if condition:
            node.then_body.interpret(self, ctx)
        elif node.else_body:
            node.else_body.interpret(self, ctx)

    @visitor
    def interpret(self, node: While, ctx):
        while True:
            condition = node.condition.interpret(self, ctx)
            if condition:
                node.body.interpret(self, ctx)
            else:
                break

    @visitor
    def interpret(self, node: StatementList, ctx):
        for st in node.elements:
            st.interpret(self, ctx)

    @visitor
    def interpret(self, node: Ret, ctx):
        # crafting interpreters nice idea to stop execution flow
        res = None
        if node.value:
            res = node.value.interpret(self, ctx)
        raise TrowableReturnContainer(res)

    @visitor
    def interpret(self, node: AttrRes, ctx):
        instance = ctx[node.parent.name]
        res = getattr(instance, node.attr.name)
        return res

    @visitor
    def interpret(self, node: Identifier, ctx):
        res = ctx[node.name]
        return res

    @visitor
    def interpret(self, node: Literal, ctx):
        res = node.value
        return res

