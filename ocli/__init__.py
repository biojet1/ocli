from .opt import flag, param, arg, walk, sub
from .usage import Usage, Help


class Base(Help):
    "The based class fror your command line app"

    def ready(self, *args, **kwargs):
        "Called before walk options. Subclass should call super().ready(*args, **kwargs)"

    def start(self, *args, **kwargs):
        "Start point of app."
        " Called after walk options."
        " .main(...) --> ready(...) --> start(...)."
        return self

    def _o_walk_sub(self, which, **kwargs):
        klass = kwargs["cmd_map"][which]
        sub = klass()
        sub._o_parent = self
        # print(list(kwargs["opt"].argv))
        return sub.main(kwargs["opt"].argv, skip_first=False)

    def options(self, opt, *args, **kwargs):
        try:
            f = super().options
        except AttributeError:
            return opt
        else:
            return f(opt)

    def main(self, argv=None, skip_first=None, **kwargs):
        "Entry point of app"
        if argv is None:
            from sys import argv
        self.ready(**kwargs)
        opt = Opt(self)
        self.options(opt)
        opt.walk(argv, skip_first=skip_first)
        # NOTE: if .start did not do anything may be it has 'yield' statement
        return self.start(**kwargs)


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


__all__ = ("flag", "param", "arg", "sub", "Main", "Base")


class Opt:
    __slots__ = ("cli", "o_params", "o_args", "inc", "argv")

    def __init__(self, cli):
        self.cli = cli
        self.inc = 0
        from collections import OrderedDict

        self.o_params = OrderedDict()
        self.o_args = OrderedDict()

    def flag(self, *args, **kwargs):
        o = self.o_params
        if not kwargs.get("dest"):
            for v in args:
                if v:
                    kwargs["dest"] = v
                    break
        for x in args:
            if x not in o:
                o[x] = kwargs
        return self

    def param(self, *args, **kwargs):
        if not kwargs.get("type"):
            kwargs["type"] = str
        return self.flag(*args, **kwargs)

    def arg(self, *args, **kwargs):
        o = self.o_args
        if True in o:
            return self
        for v in args:
            if v.isidentifier():
                # if v.isalnum():
                kwargs["dest"] = v
            else:  # v in ('+', '*', True)
                kwargs["required"] = v
        if "requires" in kwargs:
            kwargs["required"] = kwargs["requires"]

        dest = kwargs.get("dest")
        append = kwargs.get("append")
        call = kwargs.get("call")
        required = kwargs.get("required")
        if dest is None and append and append is not True:
            kwargs["dest"] = dest = append
        if dest is None and call:
            kwargs["dest"] = "arg:call:{!r}".format(call)
        k = True if (append or required in ("+", "*")) else (dest or id(kwargs))
        assert "append" not in kwargs or isinstance(
            kwargs["append"], (bool, str)
        ), ".arg append must string or True"
        # assert "dest" in kwargs, ".arg needs 'dest'"

        o[k] = kwargs
        return self

    def sub(self, cmd_map, *args, **kwargs):
        if "choices" not in kwargs:
            kwargs["choices"] = cmd_map.keys()
        if "call" not in kwargs:
            kwargs["call"] = "_o_walk_sub"
            kwargs["dest"] = "command"  # OTDO: use metavar like
        kwargs["kwargs"] = dict(cmd_map=cmd_map, opt=self)
        return self.arg(**kwargs)

    def walk(self, argv, skip_first=None):
        cli = self.cli
        _params = self.o_params
        _args = list(self.o_args.items())
        _ctx = {}
        # seen = set()
        # seen_a = {}
        # seen_p = {}
        # import pprint

        def next_arg(argv, before):
            try:
                return next(argv)
            except StopIteration:
                raise RuntimeError("Expected argument after {!r}".format(before))

        def find_param(name, arg, flag=None):
            for k, a in _params.items():
                if k == name:
                    if len(k) == 1 if flag else len(k) > 1:
                        if "seen" in a:
                            a["seen"] += 1
                        else:
                            a["seen"] = 1
                        return a
            if flag:
                raise RuntimeError("Unknown option {!r} in {!r}".format(name, arg))
            raise RuntimeError("Unknown option {!r}".format(arg))

        def find_arg(arg):
            if _args:
                k, v = _args.pop(0)
                # print("find_arg",  k, v, arg)
                if k is True:
                    _ctx["end"] = v
                return v
            elif "end" in _ctx:
                return _ctx["end"]
            raise RuntimeError("Unexpected argument {!r}".format(arg))

        # def try_call(call, v):
        #     (getattr(cli, call) if isinstance(call, str) else call)(v)

        def try_call(cur, v):
            call = cur.get("call")
            if call:
                try:
                    fn = getattr(cli, call) if isinstance(call, str) else call
                except Exception:
                    raise RuntimeError(
                        "from argument {!r} get {!r} failed".format(arg, call)
                    )
                try:
                    fn(v, **cur.get("kwargs", {}))
                except SystemExit:
                    raise
                except Exception:
                    raise RuntimeError(
                        "from argument {!r} call {!r} failed".format(arg, call)
                    )
                return True

        def push(cur, val):
            if "choices" in cur:
                val = cur.get("select", select)(val, cur["choices"])
            kind = cur.get("type")
            if kind:
                try:
                    val = kind(val)
                except Exception as exc:
                    raise RuntimeError(
                        "parse {!r} failed. from argument {!r}".format(arg, val)
                    ) from exc
            # - call
            if try_call(cur, val):
                return
            dest = cur.get("dest")
            # - append
            if "append" in cur:
                x = getattr(cli, dest, None)
                if x is None:
                    setattr(cli, dest, [val])
                else:
                    x.append(val)
                return
            setattr(cli, dest, val)

        def push_flag(cur, state):
            # - call
            if try_call(cur, state):
                return
            dest = cur["dest"]
            # - append
            append = cur.get("append")
            if append:
                if dest:
                    pass
                elif append and append is not True:
                    dest = append
                val = cur.get("const")
                x = getattr(cli, dest, None)
                if x is None:
                    if state is False:
                        pass
                    else:
                        setattr(cli, dest, [val])
                else:
                    if state is False:
                        try:
                            x.remove(val)
                        except ValueError:
                            pass
                    else:
                        x.append(val)
                return
            # - count
            count = cur.get("count")
            if count:
                if dest:
                    pass
                elif count and count is not True:
                    dest = count
                x = getattr(cli, dest, None)
                if x is None:
                    val = cur.get("const", 0)
                    if state is False:
                        setattr(cli, dest, val - 1)
                    else:
                        setattr(cli, dest, val + 1)
                else:
                    if state is False:
                        setattr(cli, dest, x - 1)
                    else:
                        setattr(cli, dest, x + 1)
                return
            # - set
            if "const" in cur:
                return setattr(cli, dest, cur["const"])
            else:
                # print("state", dest, state, state is not False)
                return setattr(cli, dest, state is not False)

        def plain(cur, arg):
            push(cur, arg)

        def short(cur, chrs, index, argv):
            index += 1
            if "type" in cur:  # params
                # print(cur['type'], chrs, index, index < len(chrs))
                push(cur, chrs[index:] if index < len(chrs) else next_arg(argv, chrs))
            else:  # flag
                # print(cur['type'], chrs, index, index < len(chrs))
                push_flag(cur, True)
                if index < len(chrs):
                    short(find_param(chrs[index], chrs, index), chrs, index, argv)

        def long(arg, cur, value=None, argv=None):
            if "type" in cur:  # params
                if value is False:
                    raise RuntimeError(
                        "{!r} takes an argument and not negatable".format(arg)
                    )
                elif value is not None:
                    push(cur, value)  # --name=VALUE
                elif argv is not None:
                    push(cur, next_arg(argv, arg))  # --name VALUE
                else:
                    raise RuntimeError("{!r} takes an argument".format(arg))
            elif value:
                raise RuntimeError("{!r} does not takes an argument".format(arg))
            else:  # flag
                assert value in (None, False)
                push_flag(cur, value)

        dd = None
        self.argv = argv = iter(argv)
        # skip prog name
        skip_first is False or next(argv, None)
        # get first argument
        arg = next(argv, None)
        while arg is not None:
            # print('ARG', arg, cli)
            if dd or ("-" == arg):
                plain(find_arg(arg), arg)
            elif "--" == arg:
                dd = True
            elif arg.startswith("--"):
                if "=" in arg:  # --name=value
                    t = arg.partition("=")
                    long(arg, find_param(t[0][2:].replace("-", "_"), arg), t[2], argv)
                elif arg.startswith("--no-"):  # --no-name
                    long(arg, find_param(arg[5:].replace("-", "_"), arg), False)
                elif arg.startswith("--no"):  # --noname
                    long(arg, find_param(arg[4:].replace("-", "_"), arg), False)
                else:  # --name
                    long(arg, find_param(arg[2:].replace("-", "_"), arg), None, argv)
            elif arg.startswith("-"):  # -qhoFILE == -q -h -o FILE
                short(find_param(arg[1], arg, 1), arg, 1, argv)
            else:
                plain(find_arg(arg), arg)
            # get next argument
            arg = next(argv, None)
        for v in _params.values():
            # print("enum_params", v)
            if "seen" in v:  # provided
                pass
            # elif hasattr(cli, v["dest"]):
            elif v["dest"] in cli.__dict__:
                pass
            elif "required" in v:
                raise RuntimeError("{} is required".format(v["dest"]))
            elif "default" in v:
                # print("default", n, v)
                setattr(cli, v["dest"], v["default"])
            elif "append" in v:
                setattr(cli, v["dest"], [])

        for k, a in _args:
            # print("enum_args", a)
            required = a.get("required")
            if required is None:
                # if hasattr(cli, a["dest"]):
                if a["dest"] in cli.__dict__:
                    pass
                elif "default" in a:
                    if try_call(a, a["default"]):
                        continue
                    setattr(cli, a["dest"], a["default"])
            elif required == "+":
                raise RuntimeError("{!r} needs atleast one argument".format(a["dest"]))
            elif required == "*":
                if "call" not in a:
                    setattr(cli, a["dest"], [])
            else:
                assert required is True, "Unexpected required value"
                raise RuntimeError("{!r} needed".format(a["dest"]))


def select(val, choices):
    chosen = None
    for n in choices:
        if not n or not n.startswith(val):
            pass
        elif chosen:
            raise RuntimeError("{!r} matches {!r} and {!r}".format(val, n, chosen))
        else:
            chosen = n
    # print(klass)
    if chosen is None:
        raise RuntimeError("Invalid choice {!r} choose from {!r} ".format(val, choices))
    return chosen
