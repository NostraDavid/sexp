from typing import List, Union

# An S-expression is either a string (atom) or a list of S-expressions.
SExpression = Union[str, List["SExpression"]]
