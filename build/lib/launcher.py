import sys

def main() -> int:
    if len(sys.argv) != 2 or sys.argv[1].lower() != "lau":
        print("Usage: pyde lau")
        return 1

    from main import main as launch

    return launch() or 0


if __name__ == "__main__":
    raise SystemExit(main())