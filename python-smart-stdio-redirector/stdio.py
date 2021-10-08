import io
import os
import sys

import contextlib
import functools
import threading


# noinspection PyPep8Naming
class kill_stderr(contextlib.redirect_stderr, contextlib.ContextDecorator):

    def __new__(cls, func=None):
        if func is not None:  # as decorator
            return cls()(func)
        return super().__new__(cls)

    __new__.__text_signature__ = '($cls, func=None, /)'

    def __init__(self):
        super().__init__(open(os.devnull, mode='w'))

    __doc__ = """
    
    Context manager that kills stderr in context.
    Can be used as decorator.

    example usage:

        As context manager: simply used as context manager
            >>> from tqdm.std import tqdm
            >>> with kill_stderr():
            ...     for _ in tqdm(range(1)):
            ...         pass
            ...

        As decorator : make function work without stderr output.
            >>> from tqdm.std import tqdm
            >>> @kill_stderr:  # also available as @kill_stderr():
            ... def simple_function():
            ...     for _ in tqdm(range(1)):
            ...         pass
            ...
            >>> simple_function()

    """


class StdoutCatcher(contextlib.ContextDecorator, contextlib.AbstractContextManager):  # can be converted as string

    _stream = "stdout"

    def __new__(cls, func=None):
        if func is not None:  # as direct decorator
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                with cls() as obj:
                    func(*args, **kwargs)
                return str(obj)
            return wrapper  # return not new object but decorator
        self = object.__new__(cls)
        self.__stream = cls._stream
        self.__lock = threading.RLock()
        self.__target = None
        self.__wrapper = io.StringIO()
        return self

    __new__.__text_signature__ = '($cls, func=None, /)'

    def __enter__(self):
        if self.__target is None:
            with self.__lock:
                if self.__target is None:
                    # Double-checked
                    self.__target = getattr(sys, self.__stream)
                    setattr(sys, self.__stream, self.__wrapper)
        return self

    open = __enter__

    def __exit__(self, exc_type=None, exc_inst=None, exc_tb=None):
        if self.__target is not None:
            with self.__lock:
                if self.__target is not None:
                    setattr(sys, self.__stream, self.__target)
                    self.__target = None
        return

    close = __exit__

    def __str__(self):
        return self.__wrapper.getvalue()

    getvalue = __str__

    def __repr__(self):
        value = self.__str__()
        if not value:
            return "<%s object at %s (empty)>" % (type(self).__name__, hex(id(self)))
        return value

    def __call__(self, func):
        wrapper = super().__call__(func)
        wrapper.__output__ = self.__wrapper
        return wrapper

    __doc__ = """
    
    Context manager that catches stdout in context, and can be converted to string

    example usage:

        As context manager: simply used as context manager
            >>> output = StdoutCatcher()
            >>> with output:
            ...     print("Sample outputs")
            ...
            >>> str(output)
            "Sample outputs\n"

        As direct decorator: make function return stdout output string, instead of printing it.
            >>> @StdoutCatcher
            ... def simple_function():
            ...     print("Sample outputs")
            ...     return "Truncated return value"
            ...
            >>> simple_function()
            "Sample outputs\n"

        As initialized decorator: make function continuously stack stdout outputs to object, instead of printing it.
            >>> output = StdoutCatcher()
            >>> @output
            ... def simple_function():
            ...     print("Sample outputs")
            ...     return "Return value"
            ...
            >>> simple_function()
            "Return value"
            >>> simple_function()
            "Return value"
            >>> str(output)
            "Sample outputs\nSample outputs\n"

    """
    
class StderrCatcher(StdoutCatcher):

    _stream = "stderr"


# alias
catch_stdout = StdoutCatcher
catch_stderr = StderrCatcher
