from sexp import SExpressionParser


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
        # A complete RFC expression, independent of exploratory Lisp fixtures.
        base_data = '(certificate (issuer 6:héllo) [text/plain]"abc" #00ff# |YWJj|)'
        self.complex_data = "(" + base_data * repeat_factor + ")"

        # Data for specific parsing scenarios
        nesting_depth = 200 * repeat_factor
        self.deeply_nested_data = "(" * nesting_depth + "a" + ")" * nesting_depth

        list_length = 500 * repeat_factor
        self.long_list_data = f"({' '.join(['item'] * list_length)})"

    def time_parse_all_complex(self, repeat_factor):
        """
        Time parsing a realistic, complex S-expression file.
        """
        SExpressionParser(self.complex_data).parse()

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
