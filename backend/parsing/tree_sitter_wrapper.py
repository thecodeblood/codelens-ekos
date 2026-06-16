"""Tree-sitter wrapper for multi-language code parsing.

Provides a clean interface around tree-sitter, managing language grammar
loading and source-code parsing.  Currently supports Python; additional
languages can be registered by extending ``_load_language``.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import tree_sitter
import tree_sitter_python as tspython
from tree_sitter import Language, Parser

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Supported language loaders
# ---------------------------------------------------------------------------

_LANGUAGE_LOADERS: dict[str, callable] = {
    "python": lambda: Language(tspython.language()),
}


class TreeSitterWrapper:
    """Manages tree-sitter language loading and parsing.

    Grammar objects are loaded lazily on first use and cached for the
    lifetime of the wrapper instance.

    Example::

        wrapper = TreeSitterWrapper()
        tree = wrapper.parse("def greet(): ...", language="python")
        print(tree.root_node.type)  # "module"
    """

    def __init__(self) -> None:
        self._languages: dict[str, Language] = {}
        self._parsers: dict[str, Parser] = {}
        logger.debug("TreeSitterWrapper initialised (lazy-load mode)")

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def parse(self, source_code: str, language: str = "python") -> tree_sitter.Tree:
        """Parse *source_code* into a tree-sitter concrete syntax tree.

        Args:
            source_code: The raw source text to parse.
            language: Target language identifier (default ``"python"``).

        Returns:
            A :class:`tree_sitter.Tree` representing the parsed AST.

        Raises:
            ValueError: If the requested language is not supported.
        """
        parser = self._get_parser(language)
        source_bytes = source_code.encode("utf-8")
        try:
            tree = parser.parse(source_bytes)
            logger.debug(
                "Parsed %d bytes of %s source (%d top-level children)",
                len(source_bytes),
                language,
                len(tree.root_node.children),
            )
            return tree
        except Exception:
            logger.exception("tree-sitter parse failed for %s source", language)
            raise

    def get_language(self, language: str) -> Language:
        """Return the cached :class:`Language` object, loading it if necessary.

        Args:
            language: Language identifier, e.g. ``"python"``.

        Returns:
            The :class:`tree_sitter.Language` grammar object.

        Raises:
            ValueError: If the language is not supported.
        """
        if language not in self._languages:
            self._languages[language] = self._load_language(language)
            logger.info("Loaded tree-sitter grammar for '%s'", language)
        return self._languages[language]

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _get_parser(self, language: str) -> Parser:
        """Return a parser configured for *language*, creating one if needed."""
        if language not in self._parsers:
            lang_obj = self.get_language(language)
            parser = Parser(lang_obj)
            self._parsers[language] = parser
        return self._parsers[language]

    @staticmethod
    def _load_language(language: str) -> Language:
        """Load the tree-sitter grammar for *language*.

        Raises:
            ValueError: When *language* has no registered loader.
        """
        loader = _LANGUAGE_LOADERS.get(language)
        if loader is None:
            supported = ", ".join(sorted(_LANGUAGE_LOADERS))
            raise ValueError(
                f"Unsupported language '{language}'. "
                f"Supported languages: {supported}"
            )
        try:
            return loader()
        except Exception:
            logger.exception("Failed to load grammar for '%s'", language)
            raise
