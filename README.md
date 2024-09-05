# Symbolic Expressions

This is an S-Expressions parser (only the parser) of `draft-rivest-sexp-09`, a

`se` is designed to parse S-expressions from a file. S-expressions are a
notation for nested list data, used in various domains such as Lisp programming
and certain cryptographic systems.

## Features

- Supports parsing of basic S-expression elements, including:
  - Verbatim strings (e.g., `3:abc`)
  - Quoted strings (e.g., `"abc"`)
  - Hexadecimal strings (e.g., `#616263#` for "abc")
  - Base64 strings (e.g., `|YWJj|` for "abc")
  - Lists (e.g., `(a b c)`)
- Handles nested lists and mixed data types.
- Flexible error handling for incorrect input formats.

## Requirements

- Python 3.12+
- No additional external libraries are required for basic parsing.
- The script uses standard Python libraries (`argparse`, `re`, `base64`).

## Usage

## Project Management with UV

uv installation:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

run application via uv:

```bash
# se as application is defined in pyproject.toml; Python versioning will be handled by uv>=0.4.5.
uv run se data/input1.lisp
```

### Example Input File

The input file should contain valid S-expressions. Below is an example
of an S-expression file content:

```lisp
(define (factorial n)
  (if (= n 0)
      1
      (* n (factorial (- n 1)))))

("hello world"
  5:abcde
  #68656c6c6f#
  |SGVsbG8gd29ybGQ=|
  (inner-list "string in a list" 7:example))

(test-data
  (name "John Doe")
  (age 35)
  (base64-data |U29tZSByYW5kb20gZGF0YQ==|)
  (hex-data #48656c6c6f#)
  (sublist (item1 3:foo) (item2 3:bar)))

( () (nested (1:1 2:22 3:333)) )
```

### Example Output

After running the script on the above example file, you will get the
following output (simplified for clarity):

```python
['define', ['factorial', 'n'],
  ['if', ['=', 'n', 0], 1,
  ['*', 'n', ['factorial', ['-', 'n', 1]]]]]
['hello world', 'abcde', 'hello', 'Hello world',
  ['inner-list', 'string in a list', 'example']]
['test-data', ['name', 'John Doe'], ['age', 35],
  ['base64-data', 'Some random data'], ['hex-data', 'Hello'],
  ['sublist', ['item1', 'foo'], ['item2', 'bar']]]
[[], ['nested', [1, 1], [2, 22], [3, 333]]]
```

## Error Handling

If the input file is not found or contains invalid S-expression syntax,
the script will output an appropriate error message. For example:

```bash
Error: The file 'nonexistent_file.txt' was not found.
```

If any parsing error occurs, the script will print the error along
with the position in the file where the error was encountered.

## License

This project is licensed under the MIT License. Feel free to use
and modify the code as needed.
