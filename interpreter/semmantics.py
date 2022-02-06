from ast_crypto import ArgList, FunDef
from visitor import visitor


class SemmanticCheck:
    @visitor
    def s_check(self, node: ArgList):
        '''
        # Todos los argumentos definidos en una misma función tienen que ser diferentes entre sí, aunque pueden ser iguales a
        # variables definidas globalmente o a argumentos definidos en otras funciones.
        # En el cuerpo de una función, los nombres de los argumentos ocultan los nombres de variables iguales.
        '''
        pass

    @visitor
    def s_check(self, node: FunDef):
        '''
        Una función puede tener distintas definiciones siempre que tengan distinta cantidad de argumentos.
        # No se pueden redefinir las funciones predefinidas.
        '''
        pass

    @visitor
    def s_check(self,node :):
        '''
        # Los nombres de variables y funciones no comparten el mismo
        '''
        pass


    @visitor
    def s_check(self,node :):
        '''
        # Toda variable y función tiene que haber sido definida antes de ser usada
        '''
        pass



class Context:
    def check_var(var: str) -> bool:
        pass

    def check_fun(fun: str, args: int) -> bool:
        pass

    def define_var(var: str) -> bool:
        pass

    def define_fun(fun: str, args: List[str]) -> bool:
        pass

    def create_child_context():
        pass
