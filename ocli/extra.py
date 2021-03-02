from .opt import param


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


class HttpHelper(object):
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
        if opt.pop_string("http", "H"):
            self.http_name = opt.value
        else:
            try:
                m = super().option
            except AttributeError:
                pass
            else:
                m(opt)


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


class BasicLog:
    log_level = "INFO"
    log_format = "%(levelname)s: %(message)s"

    @param("log_format", help="use log format")
    def _o_log_format(self, value):
        import logging

        fmt = logging.Formatter(value)
        logging.getLogger().handlers[0].setFormatter(fmt)

    @param("log_level", help="use log level")
    def _o_log_level(self, value):
        import logging

        n = getattr(logging, value.upper(), None)
        if not isinstance(n, int):
            raise ValueError("Invalid log level: %s" % (value,))
        logging.getLogger().setLevel(n)

    def ready(self, *args, **kwargs):
        import logging

        logging.basicConfig(
            **dict(
                level=getattr(logging, self.log_level.upper()), format=self.log_format
            )
        )
        super().ready(*args, **kwargs)


class LogOpt:
    log_level = "INFO"
    log_format = "%(levelname)s: %(message)s"

    def options(self, opt):
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


class DryRunOpt:
    def options(self, opt):
        dry_run = getattr(self, "dry_run", None)

        if dry_run is True:
            opt.flag("act", "a", dest="dry_run", help="not a trial run", const=False)
        elif dry_run is False:
            opt.flag("dry_run", "n", dest="dry_run", help="perform a trial run")
        super().options(opt)
