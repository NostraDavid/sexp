from sexp.parser import Hex

def test_initial_example():
    """
    Test the initial example S-expression parsing.

    Turn 0x03 into a string '0x03', and parse it back again.
    """
    hex = Hex(0x03)
    assert hex.value == 0x03
    assert str(hex) == '0x03'
    assert repr(hex) == '0x03'

    # Simulate parsing the string back to Hex
    parsed_hex = Hex.from_string(str(hex))
    assert isinstance(parsed_hex, Hex)
    assert parsed_hex.value == 0x03
