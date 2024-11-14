import sys
import time
from . import parse, ValidationError

if __name__ == "__main__":
    args = [x for x in sys.argv[1:] if not x.startswith("-")]
    flags = [x for x in sys.argv[1:] if x.startswith("-")]

    fn = args[0]
    start_time = time.time()

    try:
        parse(filename=fn, with_progress="--progress" in flags, with_tree=False)
        if "--json" not in flags:
            print("Valid", file=sys.stderr)
        exit(0)
    except ValidationError as exc:
        if "--json" not in flags:
            print(exc, file=sys.stderr)
        else:
            import sys
            import json

            json.dump(exc.asdict(), sys.stdout)
        exit(1)
