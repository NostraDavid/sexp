import argparse

from se.parser import SExpression, SExpressionParser



def parse_sexpression_from_file(file_path: str) -> SExpression:
    with open(file_path, "r") as f:
        content = f.read()
    parser = SExpressionParser(content)
    return parser.parse()


def main() -> None:
    parser = argparse.ArgumentParser(description="Parse an S-expression from a file.")
    parser.add_argument(
        "filename",
        type=str,
        help="The path to the file containing the S-expression",
    )

    args = parser.parse_args()

    try:
        sexpr = parse_sexpression_from_file(args.filename)
        print(sexpr)
    except FileNotFoundError:
        print(f"Error: The file '{args.filename}' was not found.")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()
