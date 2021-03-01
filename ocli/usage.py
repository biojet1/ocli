from . import flag


# def usage2(cli):
#     ######
#     indent_increment = 2
#     max_help_position = 24
#     if width is None:
#         import shutil

#         width = shutil.get_terminal_size().columns
#         width -= 2
#         # self._max_help_position = min(max_help_position,
#         #                               max(width - 20, indent_increment * 2))
#     ######
#     _current_indent = 0
#     _level = 0

#     # def _indent(self):
#     #     nonlocal _current_indent, _level
#     #     _current_indent += indent_increment
#     #     _level += 1

#     # def _dedent(self):
#     #     nonlocal _current_indent, _level
#     #     _current_indent -= indent_increment
#     #     assert _current_indent >= 0, "Indent decreased below 0."
#     #     _level -= 1

#     ######
#     from collections import OrderedDict

#     args = OrderedDict()
#     params = dict()
#     # collect the params
#     for c in cli.__class__.__mro__:
#         for k, v in c.__dict__.items():
#             p, a = None, None
#             if k == "_o_params":
#                 p = v
#             elif k == "_o_args":
#                 a = v
#             elif not k.startswith("__") and callable(v):
#                 p = v.__dict__.get("_o_params")
#                 a = v.__dict__.get("_o_args")
#             if p:  # 'p' is a dict
#                 for k, v in p.items():
#                     if k not in params:
#                         params[k] = v
#             if a:  # 'a' is a list
#                 for v in a:
#                     k = v.get("tag", False)
#                     if k not in args:
#                         args[k] = v
#     d = dict((id(v), v) for k, v in params.items())
#     c = {}
#     for k, v in params.items():
#         c.setdefault(id(v), []).append(k)
#     # sort longer first
#     for k, v in c.items():
#         (len(v) > 1) and v.sort(key=lambda v: (len(v), v), reverse=True)
#     for k, v in d.items():
#         # print(c[k])
#         print(
#             ", ".join("--{}".format(x) if len(x) > 1 else "-{}".format(x) for x in c[k])
#         )
#         print("\t\t{}".format(v["help"]))

#     # TODO: usage group args opt epilogue description
#     import pprint

#     print("Usage")
#     # pprint.pprint(params)
#     # pprint.pprint(d)
#     # pprint.pprint(c)

#     return args, params


def usage(cli, **kwargs):
    from .opt import enum_args, collect_params
    from argparse import ArgumentParser

    parser = ArgumentParser(add_help=False, **kwargs)

    for _ in collect_params(cli):
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

    for v in enum_args(cli):
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


class Usage:
    @flag("help", "h", help="show this help message and exit")
    def help(self, *args, **kwargs):
        usage(self, **kwargs)
        from sys import exit

        exit()


def help(opt):
    def collect_params(opt):
        mem = set()
        col = {}
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
        for v in col.values():
            yield v

    def fun(*arg):
        from argparse import ArgumentParser

        parser = ArgumentParser(add_help=False)

        for _ in collect_params(opt):
            v, a = _[0], _[1:]
            if v.get("help") is False:
                continue
            a = [
                "{}{}".format(len(_) > 1 and "--" or "-", _.replace("_", "-"))
                for _ in a
            ]

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

    return fun


class Help:
    def options(self, opt):
        opt.flag("help", "h", help="show this help message and exit", call=help(opt))
        try:
            m = super().options
        except AttributeError:
            pass
        else:
            return m(opt)
