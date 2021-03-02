def flag(*args, **kwargs):
    if not kwargs.get("dest"):
        for v in args:
            if v:
                kwargs["dest"] = v
                break

    def fun(cls):
        d = cls.__dict__
        a = d.get("_o_params")
        if a is None:
            a = {}
            setattr(cls, "_o_params", a)
        for x in args:
            if x not in a:
                a[x] = kwargs
        return cls

    return fun


def param(*args, **kwargs):
    if not kwargs.get("type"):
        kwargs["type"] = str
    return flag(*args, **kwargs)


def arg(*args, **kwargs):
    for v in args:
        if v.isidentifier():
            # if v.isalnum():
            kwargs["dest"] = v
        else:  # v in ('+', '*', True)
            kwargs["required"] = v
    if "requires" in kwargs:
        kwargs["required"] = kwargs["requires"]
    if "dest" not in kwargs:
        append = kwargs.get("append")
        if append and append is not True:
            kwargs["dest"] = append

    def fun(cls):
        d = cls.__dict__
        a = d.get("_o_args")
        if a is None:
            a = []
            setattr(cls, "_o_args", a)
        if "dest" not in kwargs:
            # kwargs["dest"] = id(kwargs)
            kwargs["dest"] = cls.__name__
            # kwargs["dest"] = cls.__qualname__
        a.append(kwargs)
        return cls

    return fun


def sub_command(value, parent):
    submap = parent._o_sub
    klass = submap[select(value, list(submap.keys()))]
    app = klass()
    app._o_parent = parent
    return app.main(parent._o_argv)


def sub(cmd_map, **kwargs):
    if "choices" not in kwargs:
        kwargs["choices"] = cmd_map.keys()
    if "call" not in kwargs:
        kwargs["call"] = "_o_walk_sub"
    fn = arg(**kwargs)

    def fun(cls):
        cls._o_sub = cmd_map
        return fn(cls)

    return fun


# TODO: impose required
# TODO: default from __getattr__


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


def all_params(cli):
    for c in cli.__class__.__mro__:
        d = c.__dict__.get("_o_params")
        if d:
            for k, v in d.items():
                yield k, v
        for m, v in c.__dict__.items():
            if not m.startswith("__") and callable(v):
                d = v.__dict__.get("_o_params")
                if d:
                    for k, v in d.items():
                        if "call" not in v:
                            v["call"] = m
                        yield k, v


def all_args(cli):
    for c in cli.__class__.__mro__:
        for a in c.__dict__.get("_o_args", ()):
            yield a
        for k, v in c.__dict__.items():
            if not k.startswith("__") and callable(v):
                for a in v.__dict__.get("_o_args", ()):
                    if "call" not in k:
                        a["call"] = k
                    yield a


def enum_params(cli, mem=None):
    if mem is None:
        mem = set()
    for k, v in all_params(cli):
        if k in mem:
            continue
        else:
            mem.add(k)
        x = id(v)
        if x in mem:
            continue
        else:
            mem.add(x)
        yield v


def collect_params(cli):
    mem = set()
    col = {}
    for k, v in all_params(cli):
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
    for v in col.values():
        yield v


def enum_args(cli, mem=None):
    if mem is None:
        mem = set()
    for a in all_args(cli):
        append = a.get("append")
        if append or a.get("required") in ("+", "*"):
            yield a
            break  # the arg with 'append' is the final arg

        k = a["dest"]
        if k in mem:
            continue
        else:
            mem.add(k)
        yield a


def walk(cli, argv, skip_first=None):
    seen = set()
    seen_a = {}
    seen_p = {}
    # import pprint

    def next_arg(argv, before):
        try:
            return next(argv)
        except StopIteration:
            raise RuntimeError("Expected argument after {!r}".format(before))

    def find_param(name, arg, flag=None):
        for k, a in all_params(cli):
            if k == name:
                if len(k) == 1 if flag else len(k) > 1:
                    return a
        raise RuntimeError("Unknown option {!r}".format(arg))

    def find_arg(arg):
        for a in enum_args(cli, seen):
            return a
        raise RuntimeError("Unexpected argument {!r}".format(arg))

    def push(cur, val):
        if "choices" in cur:
            val = cur.get("select", select)(val, cur["choices"])
        kind = cur.get("type")
        if kind:
            val = kind(val)
        # if "choices" in cur:
        #     val = cur.get("select", select)(val, cur["choices"])
        # - call
        call = cur.get("call")
        if not call:
            pass
        elif isinstance(call, str):
            return getattr(cli, call)(val)
        else:
            return call(val)
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
        call = cur.get("call")
        if call:
            return getattr(cli, call)(state)
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
        x = id(cur)
        if x in seen_a:
            seen_a[x] += 1
        else:
            seen_a[x] = 1
        push(cur, arg)

    def short(cur, chrs, index, argv):
        x = id(cur)
        if x in seen_a:
            seen_p[x] += 1
        else:
            seen_p[x] = 1
        index += 1
        if "type" in cur:  # params
            # print(cur['type'], chrs, index, index < len(chrs))
            push(cur, chrs[index:] if index < len(chrs) else next_arg(argv, chrs))
        else:  # flag
            # print(cur['type'], chrs, index, index < len(chrs))
            push_flag(cur, True)
            if index < len(chrs):
                short(find_param(chrs[index], chrs, True), chrs, index, argv)

    def long(arg, cur, value=None, argv=None):
        x = id(cur)
        if x in seen_a:
            seen_p[x] += 1
        else:
            seen_p[x] = 1
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
    cli._o_argv = argv = iter(argv)
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
            short(find_param(arg[1], arg, True), arg, 1, argv)
        else:
            plain(find_arg(arg), arg)
        # get next argument
        arg = next(argv, None)

    for v in enum_params(cli):
        # print("enum_params", v)
        n = seen_p.get(id(v), 0)
        if n > 0:  # provided
            pass
        elif hasattr(cli, v["dest"]):
            pass
        elif "required" in v:
            raise RuntimeError("{} is required".format(v["dest"]))
        elif "default" in v:
            # print("default", n, v)
            setattr(cli, v["dest"], v["default"])
        elif "append" in v:
            setattr(cli, v["dest"], [])

    for a in enum_args(cli):
        # print("enum_args", a)
        n = seen_a.get(id(a), 0)
        required = a.get("required")
        if required is None:
            if n < 1:
                if hasattr(cli, a["dest"]):
                    pass
                elif "default" in a:
                    if "call" in a:
                        getattr(cli, a["dest"])(a["default"])
                        continue
                    setattr(cli, a["dest"], a["default"])
        elif required == "+":
            if n < 1:
                raise RuntimeError("{!r} needs atleast one argument".format(a["dest"]))
        elif required == "*":
            if n < 1:
                if "call" not in a:
                    setattr(cli, a["dest"], [])
        else:
            assert required is True, "Unexpected required value"
            if n < 1:
                raise RuntimeError("{!r} needed".format(a["dest"]))
