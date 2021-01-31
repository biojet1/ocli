import unittest
from shlex import split
from ocli import *
from ocli.opt import *
from ocli.usage import usage


class Test(unittest.TestCase):
    def check(self, Class, cmd, env):
        x = Class()
        self.assertEqual(x.main(split(cmd)).__dict__, env, cmd)
        self.check_args(x)
        # print(usage(x))

    def check_successes(self, Class, *args):
        for cmd, env in args:
            x = Class()
            x.main(split("cmd " + cmd))
            self.assertEqual(x.__dict__, env, cmd)

    def check_failures(self, Class, *args, exception=RuntimeError):
        for cmd in args:
            x = Class()
            with self.assertRaises(exception, msg=cmd):
                x.main(split("cmd " + cmd))

    def check_args(self, inst):
        for a in all_args(inst):
            self.assertIn(a.get("required"), [None, True, "+", "*"])
            self.assertIsInstance(a.get("call", ""), (str,))
            self.assertIsInstance(a.get("dest", ""), (str,))
            self.assertIsInstance(a.get("choices", []), (list, tuple))
            self.assertIsInstance(a.get("append", ""), (str, bool))
            self.assertNotIsInstance(a.get("type", str), (str, int, list, tuple, bool))
            for v in a.keys():
                self.assertIn(
                    v,
                    [
                        "required",
                        "type",
                        "call",
                        "dest",
                        "choices",
                        "append",
                        "default",
                    ],
                )

    def check_params(self, inst):
        for a in all_params(inst):
            self.assertIn(a.get("required"), [None, True, "+", "*"])
            self.assertIsInstance(a.get("call", ""), (str,))
            self.assertIsInstance(a.get("dest", ""), (str,))
            self.assertIsInstance(a.get("choices", []), (list, tuple))
            self.assertIsInstance(a.get("append", ""), (str, bool))
            self.assertNotIsInstance(a.get("type", str), (str, int, list, tuple, bool))
            for v in a.keys():
                self.assertIn(
                    v,
                    [
                        "required",
                        "type",
                        "call",
                        "dest",
                        "choices",
                        "append",
                        "default",
                    ],
                )

    def test_arg_append(self):
        @arg(append="paths", default=[])
        class App(Main):
            def start(self, *args, **kwargs):
                return self

        self.check(App, r"prog A B C", dict(paths=["A", "B", "C"]))
        self.check(App, r"prog", dict(paths=[]))

    def test_arg_named(self):
        @arg("alpha")
        @arg("blue", default="ao")
        @arg("green")
        @arg("red")
        class App(Main):
            def start(self, *args, **kwargs):
                return self

        self.check(App, "prog R G B", dict(red="R", green="G", blue="B"))
        self.check(App, "prog R", dict(red="R", blue="ao"))

    def test_arg_named_append(self):
        @arg(append="others")
        @arg("second")
        @arg("first")
        class App(Main):
            def start(self, *args, **kwargs):
                return self

        self.check(
            App, "prog 1 2 A B C", dict(first="1", second="2", others=["A", "B", "C"])
        )
        self.check(App, "prog 1 2", dict(first="1", second="2"))
        self.check(App, "prog 1", dict(first="1"))
        self.check(App, "prog", dict())

    def test_params(self):
        @param("lemon", "l", dest="melon")
        @param("banana", "b")
        @param("apple", "a")
        class App(Main):
            def start(self, *args, **kwargs):
                return self

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
        @flag("lemon", "l", dest="melon")
        @flag("banana", "b", const=123)
        @flag("apple", "a", const="APPLE")
        @flag("ringo", "r", const="RINGO", dest="apple")
        class App(Main):
            def start(self, *args, **kwargs):
                return self

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
        @param("float", "f", type=float)
        @param("integer", "N", type=int)
        @arg(type=lambda x: x.split(), append="etc")
        class App(Main):
            def start(self, *args, **kwargs):
                return self

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
        @param("float", "f", type=float)
        @flag("lemon", "l", dest="melon")
        @flag("banana", "b")
        @arg(append="others")
        @arg("second", type=int)
        @arg("first")
        class App(Main):
            def start(self, *args, **kwargs):
                return self

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
        @param("float", "f", type=float, dest="num")
        @param("int", "i", type=int, dest="num")
        @param("bool", "b", type=bool, dest="num")
        @flag("apple", "A", dest="num")
        @flag("banana", "B", dest="num")
        class App(Main):
            @arg()
            def many(self, v):
                self.value = v

        self.check_failures(App, "--b 0", "--bool")
        self.check_failures(App, "-iA", exception=ValueError)
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
        class App(Main):
            @arg()
            def many(self, v):
                self.value = v

        self.check_failures(App, "A B C", "A B")
        self.check_successes(App, (r"W", dict(value="W")))

    def test_call_nargs_star(self):
        class App(Main):
            @arg("*")
            def many(self, v):
                try:
                    self.value += v
                except AttributeError:
                    self.value = v

        self.check_failures(App, "-A B C", "A --B")
        self.check_successes(App, (r"W X Y", dict(value="WXY")))
        self.check_successes(App, (r"W X", dict(value="WX")))
        self.check_successes(App, (r"W", dict(value="W")))
        self.check_successes(App, (r"", dict()))

    def test_call_nargs_plus(self):
        class App(Main):
            @arg()
            def first(self, v):
                v = "(a:" + v + ")"
                try:
                    self.a += v
                except AttributeError:
                    self.a = v

            @arg()
            def second(self, v):
                v = "(b:" + v + ")"
                try:
                    self.b += v
                except AttributeError:
                    self.b = v

            @arg("+")
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

    def test_call_required(self):
        class App(Main):
            @arg()
            def first(self, v):
                v = "(a:" + v + ")"
                try:
                    self.a += v
                except AttributeError:
                    self.a = v

            @arg(required=True)
            def second(self, v):
                v = "(b:" + v + ")"
                try:
                    self.b += v
                except AttributeError:
                    self.b = v

            @arg("+")
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

    def test_TestOptionalsSingleDash(self):
        @param("x")
        class App(Main):
            def start(self, *args, **kwargs):
                return self

        self.check_failures(
            App,
            "-x",
            "a",
            "--foo",
            # "-x --foo", "-x -y"
        )
        self.check_successes(
            App,
            (r"", dict()),
            (r"-x a", dict(x="a")),
            (r"-xa", dict(x="a")),
            (r"-x -1", dict(x="-1")),
            (r"-x-a", dict(x="-a")),
        )


class TestParse:
    def test_successes(self):
        for cmd, env in self.successes:
            x = self.Class()
            x.main(split("cmd " + cmd))
            self.assertEqual(x.__dict__, env, cmd)
        # print(usage(x))

    def test_failures(self):
        for cmd in self.failures:
            x = self.Class()
            # x.main(split("cmd " + cmd))
            # print(cmd)
            with self.assertRaises(RuntimeError, msg=cmd):
                x.main(split("cmd " + cmd))


NS = dict


class TestOptionalsSingleDashCombined(TestParse, unittest.TestCase):
    """Test an Optional with a single-dash option string"""

    # argument_signatures = [
    #     Sig('-x', action='store_true'),
    #     Sig('-yyy', action='store_const', const=42),
    #     Sig('-z'),
    # ]
    @flag("x", default=False)
    @flag("yyy", const=42)
    @param("z")
    class Class(Main):
        pass

    failures = [
        "a",
        "--foo",
        "-xa",
        "-x --foo",
        "-x -z",
        # "-z -x",
        "-yx",
        "-yz a",
        "-yyyx",
        "-yyyza",
        "-xyza",
        ## plus
        "-y",
        "-yyy",
    ]
    successes = [
        ("", NS(x=False)),
        (
            "-x",
            NS(x=True),
        ),
        ("-za", NS(x=False, z="a")),
        ("-z a", NS(x=False, z="a")),
        ("-xza", NS(x=True, z="a")),
        ("-xz a", NS(x=True, z="a")),
        ("-x -za", NS(x=True, z="a")),
        ("-x -z a", NS(x=True, z="a")),
        # ("-y", NS(x=False, yyy=42, z=None)),
        # ("-yyy", NS(x=False, yyy=42, z=None)),
        # ("-x -yyy -za", NS(x=True, yyy=42, z="a")),
        # ("-x -yyy -z a", NS(x=True, yyy=42, z="a")),
    ]


class TestOptionalsSingleDashLong(TestParse, unittest.TestCase):
    """Test an Optional with a multi-character single-dash option string"""

    @param("foo", default=None)
    class Class(Main):
        pass

    # argument_signatures = [Sig('-foo')]
    failures = ["-foo", "a", "--foo", "-foo --foo", "-foo -y", "-fooa"]
    successes = [
        ("", NS(foo=None)),
        ("--foo a", NS(foo="a")),
        ("--foo -1", NS(foo="-1")),
        # ('-fo a', NS(foo='a')),
        # ('-f a', NS(foo='a')),
    ]


if __name__ == "__main__":
    unittest.main()
