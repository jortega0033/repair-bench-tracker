# Entry point: argument parsing for the planned commands; none is built yet.
import argparse
import sys

from . import __version__

# command name -> parent ticket that builds it
PARENTS = {"init": 2, "demo": 2, "serve": 2, "check": 5, "report": 6}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="repair_bench", description="Offline repair desk.")
    parser.add_argument("--version", action="version", version=f"repair_bench {__version__}")
    sub = parser.add_subparsers(dest="command", metavar="command")
    for name in PARENTS:
        p = sub.add_parser(name, help=f"{name} (not implemented yet)")
        p.add_argument("--data-dir", required=True)
        if name == "serve":
            p.add_argument("--port", type=int, default=8769)
    return parser


def main(argv=None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command is None:
        parser.print_help()
        return 0
    print(f"not implemented yet: see #{PARENTS[args.command]}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
