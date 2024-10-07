import pytest
import argparse

from pytest_mock import MockerFixture
from s_expression import (
    parse_sexpressions_from_file,
    main,
)


def test_parse_sexpressions_from_file(mocker: MockerFixture):
    """
    Test parse_sexpressions_from_file reads the file and parses S-expressions correctly.
    """
    mock_content = "(atom1) (atom2)"
    mocker.patch("builtins.open", mocker.mock_open(read_data=mock_content))
    mocker.patch(
        "s_expression.parser.SExpressionParser.parse", side_effect=["atom1", "atom2"]
    )
    result = parse_sexpressions_from_file("dummy_path")
    assert result == ["atom1", "atom2"]


def test_parse_sexpressions_from_file_file_not_found():
    """
    Test parse_sexpressions_from_file raises FileNotFoundError if the file does not exist.
    """
    with pytest.raises(FileNotFoundError):
        parse_sexpressions_from_file("non_existent_file.txt")


def test_main(mocker: MockerFixture, capsys: pytest.CaptureFixture[str]):
    """
    Test main function handles arguments and prints S-expressions correctly.
    """
    mocker.patch(
        "argparse.ArgumentParser.parse_args",
        return_value=argparse.Namespace(filename="dummy_path"),
    )
    mocker.patch("builtins.open", mocker.mock_open(read_data="(atom1) (atom2)"))
    mocker.patch(
        "s_expression.parser.SExpressionParser.parse", side_effect=["atom1", "atom2"]
    )
    main()
    captured = capsys.readouterr()
    assert "atom1" in captured.out
    assert "atom2" in captured.out


def test_main_file_not_found(mocker: MockerFixture, capsys: pytest.CaptureFixture[str]):
    """
    Test main function handles FileNotFoundError correctly.
    """
    mocker.patch(
        "argparse.ArgumentParser.parse_args",
        return_value=argparse.Namespace(filename="non_existent_file.txt"),
    )
    main()
    captured = capsys.readouterr()
    assert "Error: The file 'non_existent_file.txt' was not found." in captured.out


def test_main_parsing_error(mocker: MockerFixture, capsys: pytest.CaptureFixture[str]):
    """
    Test main function handles generic parsing errors correctly.
    """
    mocker.patch(
        "argparse.ArgumentParser.parse_args",
        return_value=argparse.Namespace(filename="dummy_path"),
    )
    mocker.patch("builtins.open", mocker.mock_open(read_data="invalid_content"))
    mocker.patch(
        "s_expression.parser.SExpressionParser.parse",
        side_effect=Exception("Parsing error"),
    )
    main()
    captured = capsys.readouterr()
    assert "An error occurred: Parsing error" in captured.out
