#!/usr/bin/env python
# -*- coding: utf-8 -*-

from functools import update_wrapper


def decorator(dec):
    '''
    Decorate a decorator so that it inherits the docstrings
    and stuff from the function it's decorating.
    '''
    def wrap_dec(dec_func):
        decorated = dec(dec_func)

        def wrap_func(*args, **kwargs):
            result = decorated(*args, **kwargs)
            wrap_func.__dict__.update(decorated.__dict__)
            wrap_func.__dict__.update(dec.__dict__)
            wrap_func.__dict__.update(dec_func.__dict__)
            return result

        wrap_func.__doc__ = dec_func.__doc__
        wrap_func.__name__ = dec_func.__name__
        return wrap_func

    return wrap_dec


@decorator
def disable(func):
    '''
    Disable a decorator by re-assigning the decorator's name
    to this function. For example, to turn off memoization:

    >>> memo = disable

    '''
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)
    return wrapper


@decorator
def countcalls(func):
    '''Decorator that counts calls made to the function decorated.'''
    def wrapper(*args, **kwargs):
        wrapper.calls += 1
        return func(*args, **kwargs)
    wrapper.calls = 0

    return wrapper


@decorator
def memo(func):
    '''
    Memoize a function so that it caches all return values for
    faster future lookups.
    '''
    cache = {}

    def wrapper(*args, **kwargs):
        cached = cache.get(tuple(args), None)
        if cached:
            return cached
        res = cache[tuple(args)] = func(*args, **kwargs)
        return res

    return wrapper


@decorator
def n_ary(func):
    '''
    Given binary function f(x, y), return an n_ary function such
    that f(x, y, z) = f(x, f(y,z)), etc. Also allow f(x) = x.
    '''
    def wrapper(*args, **kwargs):
        args = list(args)
        while len(args) > 2:
            z = args.pop(-1)
            y = args.pop(-1)
            args.append(func(y, z))
        if len(args) == 1:
            args.append(args[0])
        return func(*args, **kwargs)

    return wrapper


def trace(arg):
    '''Trace calls made to function decorated.

    @trace("____")
    def fib(n):
        ....

    >>> fib(3)
     --> fib(3)
    ____ --> fib(2)
    ________ --> fib(1)
    ________ <-- fib(1) == 1
    ________ --> fib(0)
    ________ <-- fib(0) == 1
    ____ <-- fib(2) == 2
    ____ --> fib(1)
    ____ <-- fib(1) == 1
     <-- fib(3) == 3

    '''

    @decorator
    def dec(func):
        dec.lvl = 0

        def wrapper(*args, **kwargs):
            print(str(arg) * dec.lvl + '-->' + func.__name__ + '(' + str(*args) + ')')
            dec.lvl += 1
            res = func(*args, **kwargs)
            dec.lvl -= 1
            print(str(arg) * dec.lvl + '<--' + func.__name__ + '(' + str(*args) + ') == ' + str(res))
            return res

        return wrapper

    return dec


@memo
@countcalls
@n_ary
def foo(a, b):
    return a + b


@countcalls
@memo
@n_ary
def bar(a, b):
    return a * b


@countcalls
@trace("####")
@memo
def fib(n):
    """Some doc"""
    return 1 if n <= 1 else fib(n - 1) + fib(n - 2)


memo = disable
@memo
@countcalls
@n_ary
def foobar(a, b):
    return a + b + a * b


def main():
    print(foo(4, 3))
    print(foo(4, 3, 2))
    print(foo(4, 3))
    print("foo was called", foo.calls, "times")

    print(bar(4, 3))
    print(bar(4, 3, 2))
    print(bar(4, 3, 2, 1))
    print("bar was called", bar.calls, "times")

    print(fib.__doc__)
    fib(3)
    print(fib.calls, 'calls made')

    print(foobar(4, 3))
    print(foobar(4, 3, 2))
    print(foobar(4, 3))
    print("foobar was called", foobar.calls, "times")


if __name__ == '__main__':
    main()
