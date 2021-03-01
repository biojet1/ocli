import unittest
from sys import path
from shlex import split
from ocli import Base

from ocli.opt import all_args, all_params

# from ocli.usage import usage

print(path)


class Test(unittest.TestCase):
    def check(self, Class, cmd, env):
        x = Class()
        x.main(split(cmd))
        d = dict((k, v) for (k, v) in x.__dict__.items() if not k.startswith("_o_"))
        self.assertEqual(d, env, cmd)
        self.check_args(x)

    def check_successes(self, Class, *args):
        for cmd, env in args:
            self.check(Class, "cmd " + cmd, env)

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
        class App(Base):
            def options(self, opt):
                super().options(opt.arg(append="paths", default=[]))

            def start(self, *args, **kwargs):
                return self

        self.check(App, r"prog A B C", dict(paths=["A", "B", "C"]))
        self.check(App, r"prog", dict(paths=[]))


if __name__ == "__main__":
    unittest.main()
