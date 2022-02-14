import inspect
from typing import List

from .ast_crypto import *
from .visitor import *


class TrowableReturnContainer(Exception):
    def __init__(self, value=None):
        self.value = value


class TrowableBreak(Exception):
    pass


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
            if len(args) != len(fun.params.elements):
                raise Exception("Runtime Exception diferent param signature")
            child = context.create_child_context()  # "my" with be a level up in contexts
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
            value = child[opt.left.name]
            res[opt.left.name] = self.make_native(value, ctx) if isinstance(value, FunDef) else value
        return res

    @visitor
    def interpret(self, node: Assign, ctx):
        res = node.value.interpret(self, ctx)
        if isinstance(node.left, AttrRes):
            instance = ctx[node.left.parent.name]
            setattr(instance, node.left.attr.name, res)
        else:
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
            same_level = ctx.create_same_level_context()
            for param, value in zip(func.params.elements, args):
                same_level[param.name] = value
            try:
                func.body.interpret(self, same_level)
            except TrowableReturnContainer as retcontainer:
                ret = retcontainer.value
            return ret
        else:
            ret = self.native_call(func, args, ctx)
        return ret

    def native_call(self, func, args, ctx):
        params: List[inspect.Parameter] = list(inspect.signature(func).parameters.values())
        kw = set(map(lambda p: p.name, filter(lambda p: p.kind == inspect.Parameter.KEYWORD_ONLY, params)))
        args = [self.make_native(x) if isinstance(x, FunDef) else x for x in args]  # if is a func arg make it native
        kwargs = dict()
        if "my" in kw:
            kwargs["my"] = ctx[TOKEN_TYPE.MY_KW]
        if "market" in kw:
            kwargs["market"] = ctx[TOKEN_TYPE.MARKET_KW]
        ret = func(*args, **kwargs)
        return ret

    @visitor
    def interpret(self, node: BinaryOp, ctx):
        first = node.first.interpret(self, ctx)
        second = node.second.interpret(self, ctx)
        # acording to python match this was made for cst and ast :V
        match node.op:
            case TOKEN_TYPE.PLUS:
                res = first + second
            case TOKEN_TYPE.MINUS:
                res = first - second
            case TOKEN_TYPE.MUL:
                res = first * second
            case TOKEN_TYPE.DIV:
                res = first / second
            case TOKEN_TYPE.FLOORDIV:
                res = first // second
            case TOKEN_TYPE.MOD:
                res = first % second
            case TOKEN_TYPE.EXP:
                res = first ** second
            case TOKEN_TYPE.EQ:
                res = first == second
            case TOKEN_TYPE.NEQ:
                res = first != second
            case TOKEN_TYPE.AND:  # and / or no short circuit may have to evaluate second inside this if one not shorts
                res = 1 if bool(first) and bool(second) else 0
            case TOKEN_TYPE.OR:
                res = 1 if bool(first) or bool(second) else 0
            case TOKEN_TYPE.GT:
                res = 1 if first > second else 0
            case TOKEN_TYPE.GE:
                res = 1 if first >= second else 0
            case TOKEN_TYPE.LT:
                res = 1 if first < second else 0
            case TOKEN_TYPE.LE:
                res = 1 if first <= second else 0
            case _:
                raise Exception("Operator not implemented")
        return res

    @visitor
    def interpret(self, node: UnaryOp, ctx):
        first = node.first.interpret(self, ctx)
        match node.op:
            case TOKEN_TYPE.MINUS:
                res = -first
            case TOKEN_TYPE.NOT:
                res = 0 if bool(first) else 1
            case _:
                raise Exception("Operator not implemented")
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
        try:
            while True:
                condition = node.condition.interpret(self, ctx)
                if condition:
                    node.body.interpret(self, ctx)
                else:
                    break
        except TrowableBreak:
            pass

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
    def interpret(self, node: Break, ctx):
        # crafting interpreters nice idea to stop execution flow
        raise TrowableBreak()

    @visitor
    def interpret(self, node: AttrRes, ctx):
        instance = ctx[node.parent.name]
        if isinstance(node.attr, Identifier):
            res = getattr(instance, node.attr.name)
        elif isinstance(node.attr, FunCall):
            func = getattr(type(instance), node.attr.name.name)
            args = []
            for expr in node.attr.Args.elements:
                val = expr.interpret(self, ctx)
                args.append(val)
            res = self.native_call(func, args, ctx)
        return res

    @visitor
    def interpret(self, node: Identifier, ctx):
        res = ctx[node.name]
        return res

    @visitor
    def interpret(self, node: Literal, ctx=None):
        res = node.value
        return res
