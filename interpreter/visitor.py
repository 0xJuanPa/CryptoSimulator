from functools import wraps


def visitor(func):
    '''
    # inspired by https://stackoverflow.com/a/49916437/7585708 and conferences
    Self-contained implementation of visitor pattern using annotations
    '''

    import inspect

    func_sig_params = inspect.signature(func).parameters
    p: inspect.Parameter = list(func_sig_params.values())[1]
    annotation = p.annotation
    if annotation is inspect.Parameter.empty:
        raise Exception("Arg Has to be annotated")
    funcname = f"{func.__module__}.{func.__qualname__}"

    visitor.storage = getattr(visitor, "storage", None) or dict()
    visitor.storage[(funcname, annotation)] = func

    """
      https://stackoverflow.com/questions/9132178/what-is-the-point-of-accept-method-in-visitor-pattern
      The visitor pattern's visit/accept constructs are a necessary evil due to C-like languages' (C#, Java, etc.) semantics. 
      The goal of the visitor pattern is to use double-dispatch to route your call as you'd expect from reading the code.
    
      --- Usefull for callstack, also to control the way of one class want to visits its childs
        I think I can manage with something of functols, forget the lintner and for my pourpose this is fine
      """

    @wraps(func)
    def wrapper(self, node, *args, **kwargs):
        if (mocked := visitor.storage.get((funcname, type(self)), None)) is not None:
            self, node = node, self
        else:
            mocked = visitor.storage.get((funcname, type(node)), None)
        return mocked(self, node, *args, **kwargs)

    # accept method creation on the type
    setattr(annotation, func.__name__, wrapper)
    return wrapper
