from . import Core


class Counter(object):
    def __getattr__(self, name):
        return self.__dict__.setdefault(name, 0)

    def __contains__(self, name):
        return name in self.__dict__

    def __iter__(self):
        return iter(self.__dict__)

    def __getitem__(self, name):
        return self.__dict__.setdefault(name, 0)

    def __setitem__(self, key, value):
        self.__dict__[key] = value

    def __str__(self):
        return " ".join(
            sorted(self._format_entry(k, v) for (k, v) in self.__dict__.items())
        )

    def _format_value(self, value, key):
        return str(value)

    def _format_entry(self, key, value):
        return str(key) + " " + self._format_value(value, key) + ";"


class HttpHelper(Core):
    def __getattr__(self, name):
        if name == "http":
            x = getattr(self, "http_name", None)
            if not x:
                from os import environ

                x = environ.get("HTTP_NAME")
                if not x:
                    x = environ.get("USE_HTTP")
            if x == "r":
                import requests

                self.__dict__[name] = requests
            elif not x or x == "s":
                from requests import session

                self.__dict__[name] = session()
            else:
                from http_select import select

                self.__dict__[name] = select(x)
        else:
            try:
                m = super().__getattr__
            except AttributeError:
                raise AttributeError(name)
            else:
                return m(name)
        return self.__dict__[name]

    def option(self, opt):
        # type: (Opt) -> None
        super().options(opt.param("http_name", "H", help="use http requester"))


class Expando(object):
    # expando_map = dict(l_=list,m_=dict,s_=set,i_=int,t_=str,b_=bool,x_=Expando,v_=lambda:None)
    # def __getattr__2(self, name):
    #   r = next(v for k, v in self.expando_map.items() if name.startswith(k), None)
    #   if r:
    def __getattr__(self, name):
        if 0:
            pass
        elif name.startswith("l_"):
            self.__dict__[name] = []
        elif name.startswith("m_"):
            self.__dict__[name] = {}
        elif name.startswith("s_"):
            self.__dict__[name] = set()
        elif name.startswith("i_"):
            self.__dict__[name] = 0
        elif name.startswith("t_"):
            self.__dict__[name] = ""
        elif name.startswith("b_"):
            self.__dict__[name] = False
        elif name.startswith("v_"):
            self.__dict__[name] = None
        elif name.startswith("x_"):
            self.__dict__[name] = Expando()
        else:
            try:
                m = super().__getattr__
            except AttributeError:
                raise AttributeError(name)
            else:
                return m(name)
        return self.__dict__[name]


class LogOpt(Core):
    log_level = "INFO"
    log_format = "%(levelname)s: %(message)s"

    def options(self, opt):
        # type: (Opt) -> None
        import logging

        logging.basicConfig(
            **dict(
                level=getattr(logging, self.log_level.upper()), format=self.log_format
            )
        )

        def log_level(v):
            n = getattr(logging, v.upper(), None)
            if not isinstance(n, int):
                raise ValueError("Invalid log level: %s" % (v,))
            logging.getLogger().setLevel(n)

        def log_format(v):
            logging.getLogger().handlers[0].setFormatter(logging.Formatter(v))

        super().options(
            opt.param("log_level", help="use log level", call=log_level).param(
                "log_format", help="use log format", call=log_format
            )
        )


def opt_logging(opt, level="INFO", format="%(levelname)s: %(message)s"):
    import logging

    logging.basicConfig(**dict(format=format))

    def log_level(v):
        n = getattr(logging, v.upper(), None)
        if not isinstance(n, int):
            raise ValueError("Invalid log level: %s" % (v,))
        logging.getLogger().setLevel(n)

    def log_format(v):
        logging.getLogger().handlers[0].setFormatter(logging.Formatter(v))

    log_level(level)

    return opt.param("log_level", help="use log level", call=log_level).param(
        "log_format", help="use log format", call=log_format
    )


class DryRunOpt(Core):
    def options(self, opt):
        # type: (Opt) -> None
        dry_run = getattr(self, "dry_run", None)

        if dry_run is True:
            opt.flag("act", "a", dest="dry_run", help="not a trial run", const=False)
        elif dry_run is False:
            opt.flag("dry_run", "n", dest="dry_run", help="perform a trial run")
        super().options(opt)


def opt_dry_run(opt, initial=True):
    # type: (Core, Opt, bool) -> Opt
    if initial is True:
        opt.flag(
            "act",
            "a",
            dest="dry_run",
            help="not a trial run",
            const=False,
            default=True,
        )
    elif initial is False:
        opt.flag(
            "dry_run", "n", dest="dry_run", help="perform a trial run", default=False
        )
    return opt


from typing import TYPE_CHECKING

if TYPE_CHECKING:
    # from typing import *
    from . import Opt
