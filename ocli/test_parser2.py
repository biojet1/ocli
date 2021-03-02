import unittest
from shlex import split
from ocli import Base


class Base(Base):
    def start(self, *args, **kwargs):
        return self


class Test(unittest.TestCase):
    def check(self, Class, cmd, env):
        x = Class()
        x.main(split(cmd))
        d = dict((k, v) for (k, v) in x.__dict__.items() if not k.startswith("_o_"))
        # d = x.__dict__
        self.assertEqual(d, env, cmd)
        # self.check_args(x)

    def check_successes(self, Class, *args):
        for cmd, env in args:
            self.check(Class, "cmd " + cmd, env)

    def check_failures(self, Class, *args, exception=RuntimeError):
        for cmd in args:
            x = Class()
            self.assertRaises(exception, (lambda: x.main(split("cmd " + cmd))))

    def test_arg_append(self):
        class App(Base):
            def options(self, opt):
                return super().options(opt.arg(append="paths", default=[]))

        self.check(App, r"prog A B C", dict(paths=["A", "B", "C"]))
        self.check(App, r"prog", dict(paths=[]))

    def test_arg_named(self):
        class App(Base):
            def options(self, opt):
                super().options(
                    opt.arg("red")
                    .arg("green")
                    .arg("blue", default="ao")
                    .arg("alpha")
                    .arg("cyan")
                    .arg("magenta")
                )

        self.check(
            App,
            "prog R G B A C M",
            dict(red="R", green="G", blue="B", alpha="A", cyan="C", magenta="M"),
        )
        self.check(App, "prog R G B", dict(red="R", green="G", blue="B"))
        self.check(App, "prog R", dict(red="R", blue="ao"))

    def test_arg_named_append(self):
        class App(Base):
            def options(self, opt):
                super().options(
                    opt.arg("first")
                    .arg("second")
                    .arg(append="others")
                    .arg(append="ignored")
                )

        self.check(
            App, "prog 1 2 A B C", dict(first="1", second="2", others=["A", "B", "C"])
        )
        self.check(App, "prog 1 2", dict(first="1", second="2"))
        self.check(App, "prog 1", dict(first="1"))
        self.check(App, "prog", dict())

    def test_params(self):
        class App(Base):
            def options(self, opt):
                super().options(
                    opt.param("apple", "a")
                    .param("banana", "b")
                    .param("lemon", "l", dest="melon")
                )

        app = App().main(split("prog -a A --banana B --lemon L -l M"))
        self.assertEqual(app.apple, "A")
        self.assertEqual(app.banana, "B")
        self.assertEqual(app.melon, "M")
        self.assertRaises(AttributeError, getattr, app, "lemon")
        app = App().main(split("prog -b B --lemon M --apple A"))
        self.assertEqual(app.apple, "A")
        self.assertEqual(app.banana, "B")
        self.assertEqual(app.melon, "M")
        self.assertRaises(AttributeError, getattr, app, "lemon")

    def test_flag(self):
        class App(Base):
            def options(self, opt):
                super().options(
                    opt.flag("ringo", "r", const="RINGO", dest="apple")
                    .flag("apple", "a", const="APPLE")
                    .flag("banana", "b", const=123)
                    .flag("lemon", "l", dest="melon")
                )

        for a in (
            r"-a --banana -l",
            r"--banana -al",
            r"-bal",
            r"-bl --apple",
        ):
            self.check(App, "prog " + a, dict(apple="APPLE", banana=123, melon=True))

        for a in (
            r"-lbr",
            r"--banana --lemon --ringo",
            r"-rbl",
            r"--lemon --banana --ringo",
        ):
            self.check(App, "prog " + a, dict(apple="RINGO", banana=123, melon=True))

    def test_parse(self):
        class App(Base):
            def options(self, opt):
                super().options(
                    opt.arg(type=lambda x: x.split(), append="etc")
                    .param("integer", "N", type=int)
                    .param("float", "f", type=float)
                )

        for a in (
            r"-N 340282366920938463463374607431768211456 -f1.25 'a b c'  '1 2 3'",
            r"-N340282366920938463463374607431768211456 'a b c' -f1.25  '1 2 3'",
            r"'a b c' -N340282366920938463463374607431768211456 --float=1.25 '1 2 3'",
        ):
            self.check(
                App,
                "prog " + a,
                dict(
                    integer=340282366920938463463374607431768211456,
                    float=1.25,
                    etc=[
                        ["a", "b", "c"],
                        ["1", "2", "3"],
                    ],
                ),
            )

    def test_mix(self):
        class App(Base):
            def options(self, opt):
                super().options(
                    opt.arg("first")
                    .arg("second", type=int)
                    .arg(append="others")
                    .flag("banana", "b")
                    .flag("lemon", "l", dest="melon")
                    .param("float", "f", type=float)
                )

        for a in (
            r"-f1.25 -l 1 2 UV WX YZ",
            r"1 2 UV -lf1.25 WX YZ",
            r"1 2 UV WX YZ -lf1.25",
        ):
            self.check(
                App,
                "prog " + a,
                dict(
                    melon=True,
                    float=1.25,
                    # banana=None,
                    first="1",
                    second=2,
                    others=["UV", "WX", "YZ"],
                ),
            )

    def test_multi_dest(self):
        class App(Base):
            def options(self, opt):
                super().options(
                    opt.flag("banana", "B", dest="num")
                    .flag("apple", "A", dest="num")
                    .param("bool", "b", type=bool, dest="num")
                    .param("int", "i", type=int, dest="num")
                    .param("float", "f", type=float, dest="num")
                )

        self.check_failures(App, "--b 0", "--bool")
        self.check_failures(App, "-iA", exception=(ValueError, RuntimeError))
        self.check_successes(App, (r"", dict()))
        self.check_successes(App, (r"-f1.5", dict(num=1.5)))
        self.check_successes(App, (r"--int 2", dict(num=2)))
        self.check_successes(App, (r"--bool ''", dict(num=False)))
        self.check_successes(App, (r"-b '0'", dict(num=True)))
        self.check_successes(App, (r"-b 0 -f 1.5 -i2", dict(num=2)))
        self.check_successes(App, (r"-i2 --float=1.5", dict(num=1.5)))
        self.check_successes(App, (r"-i2 --float=1.5 --apple", dict(num=True)))
        self.check_successes(App, (r"-i2 --float=1.5 -B", dict(num=True)))

    def test_call(self):
        class App(Base):
            def options(self, opt):
                super().options(opt.arg(call="many"))

            def many(self, v):
                self.value = v

        # class App(Main):
        #     @arg()

        self.check_failures(App, "A B C", "A B")
        self.check_successes(App, (r"W", dict(value="W")))

    def test_call_nargs_star(self):
        class App(Base):
            def options(self, opt):
                def many(v):
                    try:
                        self.value += v
                    except AttributeError:
                        self.value = v

                super().options(opt.arg(requires="*", call=many))

        self.check_failures(App, "-A B C", "A --B")
        self.check_successes(App, (r"W X Y", dict(value="WXY")))
        self.check_successes(App, (r"W X", dict(value="WX")))
        self.check_successes(App, (r"W", dict(value="W")))
        self.check_successes(App, (r"", dict()))

    def test_call_required(self):
        class App(Base):
            def options(self, opt):
                super().options(
                    opt.arg(call="first")
                    .arg(call="second", required=True)
                    .arg("+", call="rest")
                )

            def first(self, v):
                v = "(a:" + v + ")"
                try:
                    self.a += v
                except AttributeError:
                    self.a = v

            def second(self, v):
                v = "(b:" + v + ")"
                try:
                    self.b += v
                except AttributeError:
                    self.b = v

            def rest(self, v):
                v = "(r:" + v + ")"
                try:
                    self.r += v
                except AttributeError:
                    self.r = v

        self.check_failures(App, "A B C -x", "A B --foo", "W X", "", "W")
        self.check_successes(App, (r"W X Y", dict(a="(a:W)", b="(b:X)", r="(r:Y)")))
        self.check_successes(
            App, (r"W X Y Z", dict(a="(a:W)", b="(b:X)", r="(r:Y)(r:Z)"))
        )

    def test_inherit(self):
        class MultiDest(Base):
            def options(self, opt):
                super().options(
                    opt.flag("banana", "B", dest="num")
                    .flag("apple", "A", dest="num")
                    .param("bool", "b", type=bool, dest="num")
                    .param("int", "i", type=int, dest="num")
                    .param("float", "f", type=float, dest="num")
                )

        class Many(Base):
            def options(self, opt):
                def many(v):
                    try:
                        self.value += v
                    except AttributeError:
                        self.value = v

                super().options(opt.arg(requires="*", call=many))

        class Mix(Base):
            def options(self, opt):
                super().options(
                    opt.arg("first")
                    .arg("second", type=int)
                    .flag("banana", "b")
                    .flag("lemon", "l", dest="melon")
                    .param("float", "f", type=float)
                )

        class App(Mix, Many, MultiDest):
            pass

        # self.check_failures(App, "A B C -x", "A B --foo", "W X", "", "W")
        self.check_successes(
            App,
            (
                r"-bAi42 1 2 3 4 5 -f0",
                dict(banana=True, num=42, first="1", second=2, value="345", float=0),
            ),
        )
        # self.check_successes(
        #     App,
        #     (
        #         r"-bAi42 1 2 3 4 5 -f0",
        #         dict(banana=True, num=42, first="1", second=2, value="345", float=0),
        #     ),
        # )


if __name__ == "__main__":
    unittest.main()
