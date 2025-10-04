# modules/parser_config.py
from enum import Enum

class ParserType(str, Enum):
    PLAYWRIGHT = "playwright"
    LINKEDIN_SOUP = "linkedin_soup"
    HYBRID = "hybrid"

# Default active parser
ACTIVE_PARSER = ParserType.PLAYWRIGHT
