class Core:
    "The based class fror your command line app"

    def ready(self, **kwargs):
        # type: (Any) -> Any
        "Called before walk options. Subclass should call super().ready(*args, **kwargs)"

    def start(self, **kwargs):
        # type: (Any) -> Core
        "Start point of app."
        " Called after walk options."
        " .main(...) --> ready(...) --> start(...)."
        return self

    def options(self, opt):
        # type: (Opt) -> None
        pass

    def main(self, argv=None, skip_first=None, **_kwargs):
        # type: (Optional[Sequence[str]], Union[bool, None] , Any) -> Core
        "Entry point of app"
        self.ready(**_kwargs)
        opt = Opt(self)
        self.options(opt)
        if argv is None:
            import sys

            opt.walk(sys.argv, skip_first=skip_first)
        else:
            opt.walk(argv, skip_first=skip_first)
        del opt
        # NOTE: if .start did not do anything may be it has 'yield' statement
        return self.start(**_kwargs)

    def _o_walk_sub(self, which, **kwargs):
        # type: (str, Any) -> Any
        klass = kwargs["cmd_map"][which]
        sub = klass()
        sub._o_parent = self
        # print(list(kwargs["opt"].argv))
        return sub.main(kwargs["opt"].iargv, skip_first=False)


class Base(Core):
    def options(self, opt):
        # type: (Opt) -> None
        super().options(
            opt.flag(
                "help",
                "h",
                help="show this help message and exit",
                call=help,
                kwargs={"opt": opt},
            )
        )


class Opt:
    __slots__ = ("cli", "o_params", "o_args", "inc", "iargv", "prog")

    def __init__(self, cli):
        # type: (Core) -> None
        self.cli = cli  # type: Core
        self.inc = 0
        from collections import OrderedDict

        self.o_params = OrderedDict()  # type: Dict[str, Dict[str, Any]]
        self.o_args = OrderedDict()  # type: Dict[Union[str, bool, int], Dict[str, str]]
        self.prog = None  # type: Optional[str]
        # self.o_args = OrderedDict()  # type: Dict[Union[str, bool, int], ARG]

    def flag(self, *args, **kwargs):
        # type: (str, Any) -> Opt
        if not kwargs.get("dest"):
            for v in args:
                if v:
                    kwargs["dest"] = v
                    break
        o = self.o_params
        for x in args:
            x = x.replace("-", "_")
            if x not in o:
                o[x] = kwargs
        return self

    def param(self, *args, **kwargs):
        # type: (str, Any) -> Opt
        if not kwargs.get("type"):
            kwargs["type"] = str
        append = kwargs.get("append")
        if append and isinstance(append, str) and not kwargs.get("dest"):
            kwargs["dest"] = append
            kwargs["append"] = True
        return self.flag(*args, **kwargs)

    def arg(self, *args, **kwargs):
        # type: (str, Any) -> Opt
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

        dest = kwargs.get("dest")  # type: Optional[str]
        append = kwargs.get(
            "append"
        )  # type: Union[Optional[Literal['+']], Optional[Literal['*']], Optional[Literal[True]]]
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
        # type: (dict, str, Any) -> Opt
        if "choices" not in kwargs:
            kwargs["choices"] = cmd_map.keys()
        if "call" not in kwargs:
            kwargs["call"] = "_o_walk_sub"
            kwargs["dest"] = "command"  # TODO: use metavar like
        kwargs["kwargs"] = dict(cmd_map=cmd_map, opt=self)
        return self.arg(**kwargs)

    def walk(self, argv, skip_first=None):
        # type: (Union[Sequence[str], Iterator[str]], Optional[bool]) -> None
        cli = self.cli
        _params = self.o_params
        _args = list(self.o_args.items())
        _ctx = {}

        def next_arg(argv, before):
            # type: (Iterator[str], str) -> str
            try:
                return next(argv)
            except StopIteration:
                raise RuntimeError("Expected argument after {!r}".format(before))

        def find_param(name, arg, flag=0):
            # type: (str, str, int) -> Dict[str, str]
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
            raise RuntimeError("Unknown option {!r} of argument {!r}".format(name, arg))

        def find_arg(arg):
            # type: (str) -> Dict[str, str]
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
            # type: (Mapping[str, Any], str) -> bool
            call = cur.get("call")  # type: Union[ Callable[[str], None], str, None]
            if not call:
                return False
            try:
                fn = getattr(cli, call) if isinstance(call, str) else call
            except Exception:
                raise RuntimeError(
                    "from argument {!r} get {!r} failed".format(arg, call)
                )
            try:
                kwa = cur.get("kwargs", {})
                fn(v, **kwa)
            except SystemExit:
                raise
            except Exception as ex:
                raise RuntimeError(
                    "from argument {!r} call {!r} failed: {!r}".format(
                        arg, call, [fn, v]
                    )
                ) from ex
            return True

        def push(cur, val):
            # type: (Dict[str, Any], Any) -> None
            if "choices" in cur:
                val = cur.get("select", _select)(val, cur["choices"])
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
            # dest = cur.get("dest")
            dest = cur["dest"]
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
            # type: (Dict[str, Any], Any) -> None
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
                    val = cur.get("const") or 0
                    assert isinstance(val, int)
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
            # type: (Dict[str, Any], Any) -> None
            push(cur, arg)

        def short(cur, chrs, index, argv):
            # type: (Dict[str, Any], str, int, Iterator[str]) -> None
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
            # type: (str, Dict[str, Any], Union[bool, None, str], Optional[Iterator[str]]) -> None
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
        self.iargv = iargv = iter(argv)
        # skip prog name
        if skip_first is not False:
            arg = next(iargv, None)
            if arg:
                try:
                    self.prog
                except AttributeError:
                    self.prog = arg
        # get first argument
        arg = next(iargv, None)
        while arg is not None:
            # print('ARG', arg, cli)
            if dd or ("-" == arg):
                plain(find_arg(arg), arg)
            elif "--" == arg:
                dd = True
            elif arg.startswith("--"):
                if "=" in arg:  # --name=value
                    t = arg.partition("=")
                    long(arg, find_param(t[0][2:].replace("-", "_"), arg), t[2], iargv)
                elif arg.startswith("--no-"):  # --no-name
                    long(arg, find_param(arg[5:].replace("-", "_"), arg), False)
                elif arg.startswith("--no"):  # --noname
                    long(arg, find_param(arg[4:].replace("-", "_"), arg), False)
                else:  # --name
                    long(arg, find_param(arg[2:].replace("-", "_"), arg), None, iargv)
            elif arg.startswith("-"):  # -qhoFILE == -q -h -o FILE
                short(find_param(arg[1], arg, 1), arg, 1, iargv)
            else:
                plain(find_arg(arg), arg)
            # get next argument
            arg = next(iargv, None)
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
            required = a.get("required")  # type: Optional[Union[str, bool]]
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


def _select(val, choices):
    # type: (str, Sequence[str]) -> str
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


def help(*arg, opt):
    # type: (bool, Opt) -> None
    def collect_params():
        # _type: () -> Generator[None, List[Union [str, Dict[str, Any]]], None]
        mem = set()
        col = {}  # _type: Dict[int, List[Union [str, Dict[str, Any]]] ]
        for k, v in opt.o_params.items():
            if k in mem:
                continue
            else:
                mem.add(k)
            x = id(v)
            if x in col:
                col[x].append(k)
            else:
                col[x] = [v, k]
        # print(col.values())
        for w in col.values():
            yield w

    from argparse import ArgumentParser

    parser = ArgumentParser(add_help=False, prog=opt.prog)

    for _ in collect_params():
        v, a = _[0], _[1:]
        if v.get("help") is False:
            continue
        a = ["{}{}".format(len(_) > 1 and "--" or "-", _.replace("_", "-")) for _ in a]

        if v.get("type"):
            w = dict(
                dest=v.get("dest"),
                type=v.get("type"),
                choices=v.get("choices"),
                default=v.get("default"),
                help=v.get("help"),
            )
            x = v.get("required")
            if x is True:
                w["required"] = x

            # print("PARM", a, w)
            parser.add_argument(*a, **w)
        else:
            w = dict(dest=v.get("dest"), help=v.get("help"), action="store_true")
            # print("FLAG", a, w)
            parser.add_argument(*a, **w)

    for _, v in opt.o_args.items():
        w = dict(
            help=v.get("help"),
            type=v.get("type"),
            choices=v.get("choices"),
        )
        x = v.get("required")
        if x is True:
            w["nargs"] = 1
        elif x in ("+", "*"):
            w["nargs"] = x

        parser.add_argument(v["dest"], **w)

    parser.print_help()
    from sys import exit

    exit()


from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import *
    from typing import TypedDict

    ARG = TypedDict(
        "ARG",
        {
            "dest": Optional[str],
            "append": Union[
                Optional[Literal["+"]], Optional[Literal["*"]], Optional[Literal[True]]
            ],
            "call": Optional[Callable[[str], None]],
        },
    )

__all__ = ("Base", "Opt")
