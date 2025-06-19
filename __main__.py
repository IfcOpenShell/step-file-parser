import sys
import time
from . import parse, ValidationError

if __name__ == "__main__":
    args = [x for x in sys.argv[1:] if not x.startswith("-")]
    flags = [x for x in sys.argv[1:] if x.startswith("-")]

    filename = args[0]
    start_time = time.time()
    
    with_progress = "--progress" in flags
    json_output = "--json" in flags
    only_header = "--header-only" in flags
    validate_data_only = "--data-only" in flags
    
    
    # Sanity check: can't use both at once
    if only_header and validate_data_only:
        print("Cannot use both --header-only and --data-only at the same time", file=sys.stderr)
        sys.exit(2)

    try:
        parse(
            filename=filename,
            with_progress=with_progress,
            with_tree=False,
            only_header=only_header,
            validate_data_only=validate_data_only,
        )
        if not json_output:
            print("Valid", file=sys.stderr)
        exit(0)
    except ValidationError as exc:
        if not json_output:
            print(exc, file=sys.stderr)
        else:
            import sys
            import json

            json.dump(exc.asdict(), sys.stdout)
        exit(1)
