import argparse
from s_expression.parser import SExpression, SExpressionParser


def parse_sexpressions_from_file(file_path: str) -> list[SExpression]:
    with open(file_path, "r") as f:
        content = f.read()

    parser = SExpressionParser(content)
    sexpressions: list[SExpression] = []

    # Parse all S-expressions from the file until the end
    while parser.index < len(parser.text):
        sexpressions.append(parser.parse())

    return sexpressions


def main() -> None:
    parser = argparse.ArgumentParser(description="Parse S-expressions from a file.")
    parser.add_argument(
        "filename",
        type=str,
        help="The path to the file containing the S-expressions",
    )

    args = parser.parse_args()

    try:
        sexprs = parse_sexpressions_from_file(args.filename)
        for sexpr in sexprs:
            print(sexpr)
    except FileNotFoundError:
        print(f"Error: The file '{args.filename}' was not found.")
    except Exception as e:
        print(f"An error occurred: {e}")


if __name__ == "__main__":
    main()
