

class Help:
    def options(self, opt):
        # type: (Opt) -> Opt
        opt.flag(
            "help",
            "h",
            help="show this help message and exit",
            call=_help,
            kwargs={"opt": opt},
        )
        try:
            m = super().options
        except AttributeError:
            return opt
        else:
            return m(opt)


from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import *
    from . import Opt
