from pathlib import Path
from sexp_old.parser import SExpressionParser

# The benchmark file is in benchmarks/, so the project root is one level up.
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"


class SExpressionParserSuite:
    """
    Benchmark suite for the SExpressionParser.
    """

    params = [1, 10, 100]
    param_names = ["repeat_factor"]

    def setup(self, repeat_factor):
        """
        Set up the data needed for the benchmarks.
        This method is run once for each combination of parameters.
        """
        if not DATA_DIR.is_dir():
            raise FileNotFoundError(
                f"Data directory not found. Expected at: {DATA_DIR}"
            )

        data_files = sorted(list(DATA_DIR.glob("*.lisp")))
        if not data_files:
            raise FileNotFoundError(f"No .lisp files found in {DATA_DIR}")

        # A sample S-expression with various types from all data files
        base_data = "".join(p.read_text() for p in data_files)
        self.complex_data = base_data * repeat_factor

        # Data for specific parsing scenarios
        nesting_depth = 200 * repeat_factor
        self.deeply_nested_data = "()" * nesting_depth + "a" + ")" * nesting_depth

        list_length = 500 * repeat_factor
        self.long_list_data = f"({' '.join(['item'] * list_length)})"

    def time_parse_all_complex(self, repeat_factor):
        """
        Time parsing a realistic, complex S-expression file.
        """
        parser = SExpressionParser(self.complex_data)
        while parser.index < len(parser.text):
            parser.parse()

    def time_parse_deeply_nested(self, repeat_factor):
        """
        Time parsing a deeply nested S-expression.
        This benchmarks recursion depth and stack management.
        """
        SExpressionParser(self.deeply_nested_data).parse()

    def time_parse_long_list(self, repeat_factor):
        """
        Time parsing an S-expression with a very long list of atoms.
        This benchmarks iteration and atom parsing performance.
        """
        SExpressionParser(self.long_list_data).parse()
