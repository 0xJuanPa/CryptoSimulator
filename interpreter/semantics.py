import inspect

from .ast_crypto import *
from .visitor import visitor


class SemanticStaticChecker:
    def __init__(self, built_ins, agents_subtypes: dict):
        self.built_ins: set[str] = set(built_ins)
        self.agents_subtypes: dict[str, tuple[set[str], set[str]]] = dict()
        for agentype, cls in agents_subtypes.items():
            options = inspect.signature(cls.__init__).parameters.values()
            option_set = set(map(lambda p: p.name, filter(lambda p: p.kind == inspect.Parameter.KEYWORD_ONLY, options)))
            behaviors = inspect.getmembers(cls, lambda c: inspect.isfunction(c) and not c.__name__.startswith("_"))
            behaviors_set = set(map(lambda t: t[0], behaviors))
            self.agents_subtypes[agentype] = (option_set, behaviors_set)
        self.global_ctx = Context()
        for built_in in self.built_ins:
            self.global_ctx[built_in] = None

    def __call__(self, node):
        self.s_check(node)

    @visitor
    def s_check(self, node: Simulation):
        for fun in node.funcs:
            fun.s_check(self, self.global_ctx)
            self.global_ctx[fun.name.name] = None
        for agent in node.agents:
            agent.s_check(self, self.global_ctx)

    @visitor
    def s_check(self, node: ArgList, ctx: Context):
        '''
        # Todos los argumentos definidos en una misma función tienen que ser diferentes entre sí
        Aunque pueden ser iguales a variables definidas globalmente
        # En el cuerpo de una función, los nombres de los argumentos no ocultan los nombres de variables iguales.
        '''
        names = set()
        for arg in node.elements:
            arg: Identifier
            if arg.name in self.built_ins:
                raise Exception("Invalid params, cant use built in param")
            if arg.name in names:
                raise Exception("Invalid params, at least two named equally")
            names.add(arg.name)
            ctx[arg.name] = None

    @visitor
    def s_check(self, node: StatementList, ctx: Context):
        for s in node.elements:
            s.s_check(self, ctx)

    @visitor
    def s_check(self, node: ExpresionList, ctx: Context):
        for s in node.elements:
            s.s_check(self, ctx)

    @visitor
    def s_check(self, node: AgentDec, ctx: Context):
        '''
        Checkeo de los agentes creamos los agentes segun sus tipos y opciones
        '''
        if node.name.name in self.built_ins:
            raise Exception("Cant use built in name")

        if node.name.name in ctx:
            raise Exception("Agent Already Defined")

        if node.subtype.name not in self.agents_subtypes:
            raise Exception("Agent subtype not exists")

        options = set()
        for opt in node.options.elements:
            opt: Assign
            opt.value.s_check(self, ctx)
            if opt.left.name in options:
                raise Exception("Already asigned option")
            options.add(opt.left.name)
            if opt.left.name not in self.agents_subtypes[node.subtype.name][0]:
                raise Exception("Agent subtype option not exists")

        defined = set()
        for beahvior in node.behavior_list.elements:
            beahvior: BehaviorDef
            if beahvior.name.name in defined:
                raise Exception("Redefining defined behavior")
            if len(beahvior.params.elements):
                raise Exception("Behaviors not allowed to have args")
            if beahvior.name.name not in self.agents_subtypes[node.subtype.name][1]:
                raise Exception("Unknown Behavior Impemented")
            if beahvior.name.name in self.built_ins:
                raise Exception("Invalid params, cant use built in name")
            child = ctx.create_child_context()
            beahvior.body.s_check(self, child)
            defined.add(beahvior.name.name)

    @visitor
    def s_check(self, node: FunDef, ctx: Context):
        '''
        No se admite sobrecarga
        No se pueden redefinir las funciones predefinidas.
        '''
        if node.name.name in self.built_ins:
            raise Exception("Invalid params, cant use built in param")
        child = ctx.create_child_context()
        if len(node.params.elements):
            node.params.s_check(self, child)
        node.body.s_check(self, child)

    @visitor
    def s_check(self, node: Assign, ctx: Context):
        '''
        Los nombres de variables y funciones si se comparten pq las funciones podrian ser 1st class citizen
        '''
        if isinstance(node.left, AttrRes):
            return
        elif node.left.name in self.built_ins:
            raise Exception("Invalid params, cant use built in param")
        node.value.s_check(self, ctx)
        ctx[node.left.name] = None

    @visitor
    def s_check(self, node: If, ctx: Context):
        '''
         Checkeo del if
        '''
        node.condition.s_check(self, ctx)
        node.then_body.s_check(self, ctx.create_child_context())
        if node.else_body is not None:
            node.else_body.s_check(self, ctx.create_child_context())

    @visitor
    def s_check(self, node: While, ctx: Context):
        '''
        Checkeo del while
        '''
        node.condition.s_check(self, ctx)
        node.body.s_check(self, ctx.create_child_context())

    @visitor
    def s_check(self, node: Ret, ctx: Context):
        '''
        Checkeo del ret
        '''
        if node.value is not None:
            node.value.s_check(self, ctx)

    @visitor
    def s_check(self, node: FunCall, ctx):
        '''
        # Toda función tiene que haber sido definida antes de ser usada
        '''
        if node.Args is not None:
            node.Args.s_check(self, ctx)
        node.name.s_check(self, ctx)

    @visitor
    def s_check(self, node: BinaryOp, ctx):
        '''
        # Binary Ops check
        '''
        node.first.s_check(self, ctx)
        node.second.s_check(self, ctx)

    @visitor
    def s_check(self, node: UnaryOp, ctx):
        '''
        # Binary Ops check
        '''
        node.first.s_check(self, ctx)

    @visitor
    def s_check(self, node: Identifier, ctx):
        '''
        # Identifier
        '''
        if node.name not in ctx:
            raise Exception("Function not defined")

    @visitor
    def s_check(self, node: AttrRes, ctx):
        pass

    @visitor
    def s_check(self, node: Literal, ctx):
        pass
