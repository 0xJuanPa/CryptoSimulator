# inspired by https://stackoverflow.com/a/49916437/7585708
def visitor(func):
    '''
    Self-contained implementation of visitor pattern using annotations with no accept method
    '''
    import inspect
    func_sig_params = inspect.signature(func).parameters
    p: inspect.Parameter = list(func_sig_params.values())[1]
    visitor.storage = getattr(visitor, "storage", None) or dict()
    annotation = p.annotation
    if annotation is inspect.Parameter.empty:
        raise Exception("Arg Has to Be annotated")
    funcname = f"{func.__module__}.{func.__qualname__}"
    visitor.storage[(funcname, annotation)] = func

    def wrapper(self, node):
        arg_type = type(node)
        mocked = visitor.storage[(funcname, arg_type)]
        return mocked(self, node)

    return wrapper