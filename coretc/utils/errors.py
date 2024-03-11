import functools, warnings

from rich import print

# Credit to Patrizio Bertoni & endolith at StackOverflow:
# https://stackoverflow.com/questions/2536307/decorators-in-the-python-standard-lib-deprecated-specifically
def deprecated(func):
    """This is a decorator which can be used to mark functions
    as deprecated. It will result in a warning being emitted
    when the function is used."""
    @functools.wraps(func)
    def new_func(*args, **kwargs):
        warnings.simplefilter('always', DeprecationWarning)  # turn off filter
        warnings.warn("Call to deprecated function {}.".format(func.__name__),
                      category=DeprecationWarning,
                      stacklevel=2)
        warnings.simplefilter('default', DeprecationWarning)  # reset filter
        return func(*args, **kwargs)
    return new_func

def incomplete(func):
    '''This is a decorator which is used to mark functions whose 
    functionality is not yet fully implemented
    '''

    print(f'Call to incomplete function [red]{func}[/red]')

    @functools.wraps(func)
    def new_func(*args, **kwargs):
        return func(*args, **kwargs)
    
    return new_func
