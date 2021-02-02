from .opt import flag, param, arg, walk, sub, enum_params
from .usage import Usage


class Main(Usage):
    "The based class fror your command line app"

    def ready(self, *args, **kwargs):
        "Called before walk options. Subclass should call super().ready(*args, **kwargs)"

    def main(self, argv=None, **kwargs):
        "Entry point of app"
        if argv is None:
            from sys import argv
        self.ready(**kwargs)
        walk(self, argv)
        # NOTE: if .start did not do anything may be it has 'yield' statement
        return self.start(**kwargs)

    def start(self, *args, **kwargs):
        "Start point of app."
        " Called after walk options."
        " .main(...) --> ready(...) --> start(...)."

    def _o_walk_sub(self, value, **kwargs):
        klass = self._o_sub[value]
        sub = klass()
        sub._o_parent = self
        sub.ready(**kwargs)
        walk(sub, self._o_argv, skip_first=False)
        return sub.start(**kwargs)

    # def __getattr__(self, name):
    #     # TODO: Document
    #     m = "__let_" not in name
    #     if m:
    #         m = getattr(self, "__let_" + name, None)
    #     if m:
    #         setattr(self, name, None)
    #         x = m()
    #         setattr(self, name, x)
    #         return x
    #     #
    #     try:
    #         m = super().__getattr__
    #     except AttributeError:
    #         raise AttributeError(name, self)
    #     else:
    #         return m(name)


__all__ = ("flag", "param", "arg", "sub", "Main")
