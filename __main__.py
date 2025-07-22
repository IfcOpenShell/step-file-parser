import sys
import json
import argparse
from . import parse, ValidationError

def main():
    parser = argparse.ArgumentParser(description="Parse and validate STEP file.")
    parser.add_argument("filename", help="The STEP file to validate.")
    parser.add_argument("--progress", action="store_true", help="Show progress during validation.")
    parser.add_argument("--json", action="store_true", help="Output errors in JSON format.")
    parser.add_argument("--only-header", action="store_true", help="Validate only the header section.")
    
    args = parser.parse_args()
        
    try:
        parse(
            filename=args.filename,
            with_progress = args.progress,
            with_tree = False,
            only_header=args.only_header,
        )
        if not args.json:
            print("Valid", file=sys.stderr)
        exit(0)
    except ValidationError as exc:
        if not args.json:
            print(exc, file=sys.stderr)
        else:
            json.dump([e.asdict() for e in getattr(exc, "errors", [exc])], sys.stdout, indent=2)
        exit(1)

if __name__ == '__main__':
    main()    
