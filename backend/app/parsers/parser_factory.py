from typing import Dict, Type
from .base_parser import BaseParser
from .generic_parser import GenericParser


class ParserFactory:
    """
    Factory for creating appropriate PDF parsers based on bank type.

    To add a new bank-specific parser:
    1. Create a new parser class that inherits from BaseParser
    2. Implement the parse() method with bank-specific logic
    3. Register it here using ParserFactory.register()

    Example:
        class ChaseParser(BaseParser):
            def parse(self):
                # Chase-specific parsing logic
                pass

        ParserFactory.register("chase", ChaseParser)
    """

    _parsers: Dict[str, Type[BaseParser]] = {
        "generic": GenericParser,
    }

    @classmethod
    def register(cls, bank_type: str, parser_class: Type[BaseParser]):
        """
        Register a new parser for a specific bank type

        Args:
            bank_type: Identifier for the bank (e.g., 'chase', 'amex', 'citi')
            parser_class: Parser class that inherits from BaseParser
        """
        cls._parsers[bank_type.lower()] = parser_class

    @classmethod
    def get_parser(cls, bank_type: str, file_path: str) -> BaseParser:
        """
        Get an appropriate parser instance for the given bank type

        Args:
            bank_type: Type of bank statement
            file_path: Path to the PDF file

        Returns:
            Instance of the appropriate parser

        Raises:
            ValueError: If bank_type is not registered
        """
        bank_type = bank_type.lower()

        if bank_type not in cls._parsers:
            # Fall back to generic parser
            print(f"Warning: No specific parser for '{bank_type}', using generic parser")
            bank_type = "generic"

        parser_class = cls._parsers[bank_type]
        return parser_class(file_path)

    @classmethod
    def list_supported_banks(cls) -> list:
        """Get list of supported bank types"""
        return list(cls._parsers.keys())
