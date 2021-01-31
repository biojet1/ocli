from .opt import flag, param, arg, walk, sub
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


__all__ = ("flag", "param", "arg", "sub", "Main")
