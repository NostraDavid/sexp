"""
ABNF parser
"""

from typing import Optional


class SexpParser:
    def __init__(self, text: str):
        self.text = text
        self.index = 0

    def at_end(self) -> bool:
        """Check if we've reached the end of input"""
        return self.index >= len(self.text)

    def peek(self) -> Optional[str]:
        """Look at current character without consuming it"""
        if self.at_end():
            return None
        return self.text[self.index]

    def consume(self) -> Optional[str]:
        """Consume and return current character"""
        if self.at_end():
            return None
        char = self.text[self.index]
        self.index += 1
        return char

    def parse_sp(self) -> bool:
        """Parse SP (space character) - %x20"""
        if self.peek() == " ":
            self.consume()
            return True
        return False
