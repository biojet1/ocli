import argparse

parser = argparse.ArgumentParser(argument_default=argparse.SUPPRESS)
parser.add_argument("--foo", action="append", default=[])
parser.add_argument("--bar", type=float, default=7)
parser.add_argument("-x")
parser.add_argument("bar", nargs="?")


for s in (
    "",
    "BAR ",
    "BAR --foo A",
    "BAR --foo A --foo B",
    "BAR --bar 4.5",
):
    n = parser.parse_args(s.split())
    print(n)
