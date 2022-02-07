from ast_crypto import *
from visitor import visitor





class SemanticStaticChecker:
    def __init__(self, built_ins, agents_subtypes: dict):
        self.built_ins: set[str] = built_ins
        self.agents_subtypes: dict[str, tuple[set[str], set[str]]] = agents_subtypes

    @visitor
    def s_check(self, node: ArgList, ctx: Context):
        '''
        # Todos los argumentos definidos en una misma función tienen que ser diferentes entre sí
        Aunque pueden ser iguales a variables definidas globalmente
        # En el cuerpo de una función, los nombres de los argumentos ocultan los nombres de variables iguales.
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
            s.s_check(ctx)

    @visitor
    def s_check(self, node: ExpresionList, ctx: Context):
        for s in node.elements:
            s.s_check(ctx)

    @visitor
    def s_check(self, node: AgentDec, ctx: Context):
        '''
        Checkeo de los agentes creamos los agentes segun sus tipos y opciones
        '''
        if node.name in self.built_ins:
            raise Exception("Cant use built in name")

        if node.name in ctx:
            raise Exception("Agent Already Defined")

        if node.type not in self.agents_subtypes:
            raise Exception("Agent subtype not exists")

        for opt in node.options.elements:
            if opt not in self.agents_subtypes[node.type][0]:
                raise Exception("Agent subtype option not exists")

        defined = set()
        for beahvior in node.behavior_list.elements:
            beahvior: FunDef
            if beahvior.params:
                raise Exception("Behaviors not allowed to have args")
            if beahvior.name not in self.agents_subtypes[node.type][1]:
                raise Exception("Unknown Behavior Impemented")
            if beahvior.name in defined:
                raise Exception("Redefining defined behavior")
            defined.add(beahvior.name)
            beahvior.s_check(ctx)

    @visitor
    def s_check(self, node: FunDef, ctx: Context):
        '''
        No se admite sobrecarga
        No se pueden redefinir las funciones predefinidas.
        '''
        if node.name in self.built_ins:
            raise Exception("Invalid params, cant use built in param")
        node.body.s_check(ctx.create_child_context())

    @visitor
    def s_check(self, node: Assign, ctx: Context):
        '''
        Los nombres de variables y funciones si se comparten pq las funciones podrian ser 1st class citizen
        '''
        if node.name in self.built_ins:
            raise Exception("Invalid params, cant use built in param")
        node.value.s_check(ctx)

    @visitor
    def s_check(self, node: If, ctx: Context):
        '''
         Checkeo del if
        '''
        node.condition.s_check(ctx)
        node.then_body.s_check(ctx.create_child_context())
        if node.else_body is not None:
            node.else_body.s_check(ctx.create_child_context())

    @visitor
    def s_check(self, node: While, ctx: Context):
        '''
        Checkeo del while
        '''
        node.condition.s_check(ctx)
        node.body.s_check(ctx.create_child_context())

    @visitor
    def s_check(self, node: Ret, ctx: Context):
        '''
        Checkeo del ret
        '''
        if node.value is not None:
            node.value.s_check(ctx)

    @visitor
    def s_check(self, node: FunCall, ctx):
        '''
        # Toda función tiene que haber sido definida antes de ser usada
        '''
        if node.name not in ctx:
            raise Exception("Function not defined")
        node.Args.s_check(ctx)

    @visitor
    def s_check(self, node: BinaryOp, ctx):
        '''
        # Binary Ops check
        '''
        node.first.s_check(ctx)
        node.second.s_check(ctx)

    @visitor
    def s_check(self, node: UnaryOp, ctx):
        '''
        # Binary Ops check
        '''
        node.first.s_check(ctx)
