"""Python-specific AST entity extraction using tree-sitter.

This module is the **core deterministic extraction engine** (Tier 1).  It
walks the concrete syntax tree produced by tree-sitter and emits structured
dataclasses describing every class, function, import, decorator, call-site,
API endpoint, and ORM / data-model found in a single Python source file.

No LLM calls are made — every decision is based purely on AST node types,
node text, and a small set of well-known framework patterns.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import tree_sitter

logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────────────────────────────────────
# Data-classes — extraction results
# ──────────────────────────────────────────────────────────────────────────────


@dataclass
class Parameter:
    """A single function / method parameter."""

    name: str
    type_annotation: str | None = None
    default: str | None = None


@dataclass
class ExtractedCall:
    """A call expression found inside a function / method body."""

    function_name: str  # e.g. "module.func" or "self.method"
    line: int


@dataclass
class ExtractedFunction:
    """A free function or a method bound to a class."""

    name: str
    qualified_name: str
    parameters: list[Parameter] = field(default_factory=list)
    return_type: str | None = None
    decorators: list[str] = field(default_factory=list)
    docstring: str | None = None
    calls: list[ExtractedCall] = field(default_factory=list)
    is_async: bool = False
    is_method: bool = False
    is_static: bool = False
    is_classmethod: bool = False
    is_property: bool = False
    line_start: int = 0
    line_end: int = 0
    body_source: str = ""


@dataclass
class ExtractedClass:
    """A class definition."""

    name: str
    qualified_name: str
    bases: list[str] = field(default_factory=list)
    methods: list[ExtractedFunction] = field(default_factory=list)
    decorators: list[str] = field(default_factory=list)
    docstring: str | None = None
    line_start: int = 0
    line_end: int = 0
    is_dataclass: bool = False


@dataclass
class ExtractedImport:
    """An ``import`` or ``from … import …`` statement."""

    module: str
    names: list[str] = field(default_factory=list)
    is_from: bool = False
    alias: str | None = None
    line: int = 0


@dataclass
class ExtractedEndpoint:
    """An HTTP API endpoint detected via decorator inspection."""

    method: str  # GET, POST, PUT, DELETE, PATCH, …
    path: str  # "/api/users"
    handler_function: str
    decorators: list[str] = field(default_factory=list)
    line: int = 0


@dataclass
class ExtractedDataModel:
    """An ORM model or data-transfer object (DTO)."""

    class_name: str
    table_name: str | None = None
    fields: list[str] = field(default_factory=list)
    framework: str = ""  # "sqlalchemy", "django", "pydantic"
    line_start: int = 0
    line_end: int = 0


@dataclass
class PythonExtractionResult:
    """Aggregated extraction result for a single Python source file."""

    file_path: str
    module_name: str
    classes: list[ExtractedClass] = field(default_factory=list)
    functions: list[ExtractedFunction] = field(default_factory=list)  # top-level only
    imports: list[ExtractedImport] = field(default_factory=list)
    endpoints: list[ExtractedEndpoint] = field(default_factory=list)
    data_models: list[ExtractedDataModel] = field(default_factory=list)
    module_docstring: str | None = None


# ──────────────────────────────────────────────────────────────────────────────
# Well-known patterns used by the extractor
# ──────────────────────────────────────────────────────────────────────────────

_ROUTE_METHODS: set[str] = {"get", "post", "put", "delete", "patch", "options", "head"}

_ORM_BASES_SQLALCHEMY: set[str] = {"Base", "DeclarativeBase", "DeclarativeMeta"}
_ORM_BASES_DJANGO: set[str] = {"Model", "models.Model"}
_ORM_BASES_PYDANTIC: set[str] = {"BaseModel", "BaseSettings"}

_DATACLASS_DECORATORS: set[str] = {"dataclass", "dataclasses.dataclass"}

# ──────────────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────────────


def _node_text(node: tree_sitter.Node, source_bytes: bytes) -> str:
    """Return the source text spanned by *node*."""
    return source_bytes[node.start_byte : node.end_byte].decode("utf-8", errors="replace")


def _line(node: tree_sitter.Node) -> int:
    """Return the 1-indexed starting line of *node*."""
    return node.start_point[0] + 1


def _end_line(node: tree_sitter.Node) -> int:
    """Return the 1-indexed ending line of *node*."""
    return node.end_point[0] + 1


def _children_of_type(node: tree_sitter.Node, *types: str) -> list[tree_sitter.Node]:
    """Return direct children whose ``type`` is in *types*."""
    return [c for c in node.children if c.type in types]


def _first_child_of_type(node: tree_sitter.Node, *types: str) -> tree_sitter.Node | None:
    """Return the first direct child whose ``type`` is in *types*, or ``None``."""
    for c in node.children:
        if c.type in types:
            return c
    return None


def _collect_nodes(root: tree_sitter.Node, *types: str) -> list[tree_sitter.Node]:
    """Recursively collect all descendant nodes whose ``type`` is in *types*."""
    results: list[tree_sitter.Node] = []
    stack = list(root.children)
    while stack:
        node = stack.pop()
        if node.type in types:
            results.append(node)
        stack.extend(node.children)
    return results


# ──────────────────────────────────────────────────────────────────────────────
# Main extractor
# ──────────────────────────────────────────────────────────────────────────────


class PythonASTExtractor:
    """Extracts structured code entities from a Python tree-sitter AST.

    All extraction is deterministic (Tier 1) — no LLM is involved.
    """

    def __init__(self) -> None:
        self._source_bytes: bytes = b""

    # ------------------------------------------------------------------
    # Top-level entry point
    # ------------------------------------------------------------------

    def extract_all(
        self,
        tree: tree_sitter.Tree,
        source: str,
        file_path: str,
    ) -> PythonExtractionResult:
        """Extract every supported entity from *tree*.

        Args:
            tree: The tree-sitter parse tree.
            source: The raw source text (UTF-8 string).
            file_path: Path of the file being analysed (used in qualified names).

        Returns:
            A :class:`PythonExtractionResult` aggregating all findings.
        """
        self._source_bytes = source.encode("utf-8")
        root = tree.root_node
        module_name = self._file_path_to_module(file_path)

        try:
            imports = self.extract_imports(root)
            classes = self.extract_classes(root, module_name)
            functions = self.extract_functions(root, module_name)
            endpoints = self.extract_api_endpoints(root, module_name)
            data_models = self.extract_orm_models(classes)
            module_docstring = self._extract_module_docstring(root)

            logger.debug(
                "Extracted from %s: %d classes, %d functions, %d imports, "
                "%d endpoints, %d data-models",
                file_path,
                len(classes),
                len(functions),
                len(imports),
                len(endpoints),
                len(data_models),
            )

            return PythonExtractionResult(
                file_path=file_path,
                module_name=module_name,
                classes=classes,
                functions=functions,
                imports=imports,
                endpoints=endpoints,
                data_models=data_models,
                module_docstring=module_docstring,
            )
        except Exception:
            logger.exception("Extraction failed for %s", file_path)
            raise

    # ------------------------------------------------------------------
    # Classes
    # ------------------------------------------------------------------

    def extract_classes(
        self,
        root: tree_sitter.Node,
        module_name: str = "",
    ) -> list[ExtractedClass]:
        """Extract all top-level class definitions from the AST root.

        Decorated classes (``decorated_definition`` wrapping a
        ``class_definition``) are handled transparently.
        """
        classes: list[ExtractedClass] = []

        for node in root.children:
            class_node: tree_sitter.Node | None = None
            outer_node = node  # may be a decorated_definition

            if node.type == "class_definition":
                class_node = node
            elif node.type == "decorated_definition":
                inner = _first_child_of_type(node, "class_definition")
                if inner is not None:
                    class_node = inner

            if class_node is None:
                continue

            try:
                cls = self._extract_single_class(class_node, outer_node, module_name)
                classes.append(cls)
            except Exception:
                logger.warning(
                    "Skipping class at line %d due to extraction error",
                    _line(class_node),
                    exc_info=True,
                )

        return classes

    def _extract_single_class(
        self,
        class_node: tree_sitter.Node,
        outer_node: tree_sitter.Node,
        module_name: str,
    ) -> ExtractedClass:
        """Build an :class:`ExtractedClass` from a ``class_definition`` node."""
        name_node = _first_child_of_type(class_node, "identifier")
        name = _node_text(name_node, self._source_bytes) if name_node else "<anonymous>"
        qualified = f"{module_name}.{name}" if module_name else name

        bases = self._extract_bases(class_node)
        decorators = self.extract_decorators(outer_node)
        body = _first_child_of_type(class_node, "block")
        docstring = self.extract_docstring(body) if body else None
        methods = self._extract_methods(body, qualified) if body else []

        is_dc = any(d in _DATACLASS_DECORATORS for d in decorators)

        return ExtractedClass(
            name=name,
            qualified_name=qualified,
            bases=bases,
            methods=methods,
            decorators=decorators,
            docstring=docstring,
            line_start=_line(outer_node),
            line_end=_end_line(class_node),
            is_dataclass=is_dc,
        )

    def _extract_bases(self, class_node: tree_sitter.Node) -> list[str]:
        """Return the list of base-class names from the ``argument_list``."""
        arg_list = _first_child_of_type(class_node, "argument_list")
        if arg_list is None:
            return []
        bases: list[str] = []
        for child in arg_list.children:
            if child.type in ("identifier", "attribute"):
                bases.append(_node_text(child, self._source_bytes))
        return bases

    # ------------------------------------------------------------------
    # Functions (top-level only)
    # ------------------------------------------------------------------

    def extract_functions(
        self,
        root: tree_sitter.Node,
        module_name: str = "",
    ) -> list[ExtractedFunction]:
        """Extract top-level (non-method) functions from the AST root."""
        functions: list[ExtractedFunction] = []

        for node in root.children:
            func_node: tree_sitter.Node | None = None
            outer_node = node

            if node.type == "function_definition":
                func_node = node
            elif node.type == "decorated_definition":
                inner = _first_child_of_type(node, "function_definition")
                if inner is not None:
                    func_node = inner

            if func_node is None:
                continue

            try:
                fn = self._extract_single_function(
                    func_node, outer_node, module_name, is_method=False
                )
                functions.append(fn)
            except Exception:
                logger.warning(
                    "Skipping function at line %d due to extraction error",
                    _line(func_node),
                    exc_info=True,
                )

        return functions

    # ------------------------------------------------------------------
    # Methods (inside a class body)
    # ------------------------------------------------------------------

    def _extract_methods(
        self,
        body_node: tree_sitter.Node,
        class_qualified: str,
    ) -> list[ExtractedFunction]:
        """Extract methods from a class body ``block`` node."""
        methods: list[ExtractedFunction] = []
        if body_node is None:
            return methods

        for node in body_node.children:
            func_node: tree_sitter.Node | None = None
            outer_node = node

            if node.type == "function_definition":
                func_node = node
            elif node.type == "decorated_definition":
                inner = _first_child_of_type(node, "function_definition")
                if inner is not None:
                    func_node = inner

            if func_node is None:
                continue

            try:
                fn = self._extract_single_function(
                    func_node, outer_node, class_qualified, is_method=True
                )
                methods.append(fn)
            except Exception:
                logger.warning(
                    "Skipping method at line %d due to extraction error",
                    _line(func_node),
                    exc_info=True,
                )

        return methods

    # ------------------------------------------------------------------
    # Single-function extraction (shared by top-level & methods)
    # ------------------------------------------------------------------

    def _extract_single_function(
        self,
        func_node: tree_sitter.Node,
        outer_node: tree_sitter.Node,
        parent_qualified: str,
        *,
        is_method: bool,
    ) -> ExtractedFunction:
        """Build an :class:`ExtractedFunction` from a ``function_definition``."""
        name_node = _first_child_of_type(func_node, "identifier")
        name = _node_text(name_node, self._source_bytes) if name_node else "<anonymous>"
        qualified = f"{parent_qualified}.{name}" if parent_qualified else name

        decorators = self.extract_decorators(outer_node)
        params = self._extract_parameters(func_node)
        return_type = self._extract_return_type(func_node)
        body = _first_child_of_type(func_node, "block")
        docstring = self.extract_docstring(body) if body else None
        calls = self.extract_calls(func_node)

        is_async = func_node.parent is not None and any(
            c.type == "async" for c in (func_node.parent.children if func_node.parent else [])
        )
        # Fallback: check if the node text starts with "async"
        if not is_async:
            # tree-sitter Python grammar may represent async as a sibling keyword
            # in decorated_definition or directly before function_definition
            node_src = _node_text(outer_node, self._source_bytes)
            is_async = node_src.lstrip().startswith("async ")

        is_static = "staticmethod" in decorators
        is_classmethod = "classmethod" in decorators
        is_property = "property" in decorators

        body_source = _node_text(body, self._source_bytes) if body else ""

        return ExtractedFunction(
            name=name,
            qualified_name=qualified,
            parameters=params,
            return_type=return_type,
            decorators=decorators,
            docstring=docstring,
            calls=calls,
            is_async=is_async,
            is_method=is_method,
            is_static=is_static,
            is_classmethod=is_classmethod,
            is_property=is_property,
            line_start=_line(outer_node),
            line_end=_end_line(func_node),
            body_source=body_source,
        )

    # ------------------------------------------------------------------
    # Parameters
    # ------------------------------------------------------------------

    def _extract_parameters(self, func_node: tree_sitter.Node) -> list[Parameter]:
        """Extract parameters from the ``parameters`` child of a function def."""
        params_node = _first_child_of_type(func_node, "parameters")
        if params_node is None:
            return []

        params: list[Parameter] = []
        for child in params_node.children:
            if child.type in ("identifier",):
                params.append(Parameter(name=_node_text(child, self._source_bytes)))

            elif child.type == "typed_parameter":
                pname_node = _first_child_of_type(child, "identifier")
                ptype_node = _first_child_of_type(child, "type")
                pname = _node_text(pname_node, self._source_bytes) if pname_node else "?"
                ptype = _node_text(ptype_node, self._source_bytes) if ptype_node else None
                params.append(Parameter(name=pname, type_annotation=ptype))

            elif child.type == "default_parameter":
                pname_node = _first_child_of_type(child, "identifier")
                pname = _node_text(pname_node, self._source_bytes) if pname_node else "?"
                # Default value is the last meaningful child
                default_val = self._extract_default_value(child)
                params.append(Parameter(name=pname, default=default_val))

            elif child.type == "typed_default_parameter":
                pname_node = _first_child_of_type(child, "identifier")
                ptype_node = _first_child_of_type(child, "type")
                pname = _node_text(pname_node, self._source_bytes) if pname_node else "?"
                ptype = _node_text(ptype_node, self._source_bytes) if ptype_node else None
                default_val = self._extract_default_value(child)
                params.append(Parameter(name=pname, type_annotation=ptype, default=default_val))

            elif child.type in ("list_splat_pattern", "dictionary_splat_pattern"):
                raw = _node_text(child, self._source_bytes)
                params.append(Parameter(name=raw))

        return params

    def _extract_default_value(self, param_node: tree_sitter.Node) -> str | None:
        """Return the text of the default-value expression inside a parameter node."""
        # In tree-sitter Python, default_parameter / typed_default_parameter
        # stores the default after the '=' token.
        saw_eq = False
        for child in param_node.children:
            if child.type == "=":
                saw_eq = True
                continue
            if saw_eq:
                return _node_text(child, self._source_bytes)
        return None

    # ------------------------------------------------------------------
    # Return type
    # ------------------------------------------------------------------

    def _extract_return_type(self, func_node: tree_sitter.Node) -> str | None:
        """Extract the return-type annotation (``-> X``) from a function def."""
        ret_type_node = _first_child_of_type(func_node, "type")
        if ret_type_node is not None:
            return _node_text(ret_type_node, self._source_bytes)
        return None

    # ------------------------------------------------------------------
    # Imports
    # ------------------------------------------------------------------

    def extract_imports(self, root: tree_sitter.Node) -> list[ExtractedImport]:
        """Extract all import statements from the module root."""
        imports: list[ExtractedImport] = []

        for node in _collect_nodes(root, "import_statement", "import_from_statement"):
            try:
                imp = self._extract_single_import(node)
                if imp is not None:
                    imports.append(imp)
            except Exception:
                logger.warning(
                    "Skipping import at line %d due to extraction error",
                    _line(node),
                    exc_info=True,
                )

        return imports

    def _extract_single_import(self, node: tree_sitter.Node) -> ExtractedImport | None:
        """Build an :class:`ExtractedImport` from an import node."""
        if node.type == "import_statement":
            return self._extract_plain_import(node)
        if node.type == "import_from_statement":
            return self._extract_from_import(node)
        return None

    def _extract_plain_import(self, node: tree_sitter.Node) -> ExtractedImport:
        """Handle ``import foo.bar`` and ``import foo as f``."""
        alias: str | None = None
        module_parts: list[str] = []

        for child in node.children:
            if child.type == "dotted_name":
                module_parts.append(_node_text(child, self._source_bytes))
            elif child.type == "aliased_import":
                dotted = _first_child_of_type(child, "dotted_name")
                if dotted:
                    module_parts.append(_node_text(dotted, self._source_bytes))
                alias_node = _first_child_of_type(child, "identifier")
                if alias_node:
                    alias = _node_text(alias_node, self._source_bytes)

        module = module_parts[0] if module_parts else ""
        return ExtractedImport(
            module=module,
            names=[],
            is_from=False,
            alias=alias,
            line=_line(node),
        )

    def _extract_from_import(self, node: tree_sitter.Node) -> ExtractedImport:
        """Handle ``from foo.bar import Baz, Qux`` and ``from . import x``."""
        module = ""
        names: list[str] = []
        alias: str | None = None

        # Gather module name (may include relative dots)
        module_node = _first_child_of_type(node, "dotted_name", "relative_import")
        if module_node is not None:
            module = _node_text(module_node, self._source_bytes)

        # Gather imported names
        for child in node.children:
            if child.type == "dotted_name" and child != module_node:
                names.append(_node_text(child, self._source_bytes))
            elif child.type == "aliased_import":
                dotted = _first_child_of_type(child, "dotted_name", "identifier")
                if dotted:
                    names.append(_node_text(dotted, self._source_bytes))
                alias_id = None
                saw_as = False
                for ac in child.children:
                    if ac.type == "as":
                        saw_as = True
                    elif saw_as and ac.type == "identifier":
                        alias_id = ac
                        break
                if alias_id:
                    alias = _node_text(alias_id, self._source_bytes)
            elif child.type == "wildcard_import":
                names.append("*")
            elif child.type == "identifier" and _node_text(child, self._source_bytes) not in (
                "from",
                "import",
            ):
                # Plain identifier imported name (e.g., ``from os import path``)
                names.append(_node_text(child, self._source_bytes))

        return ExtractedImport(
            module=module,
            names=names,
            is_from=True,
            alias=alias,
            line=_line(node),
        )

    # ------------------------------------------------------------------
    # Decorators
    # ------------------------------------------------------------------

    def extract_decorators(self, node: tree_sitter.Node) -> list[str]:
        """Return decorator strings for a ``decorated_definition`` or function/class node.

        If *node* is a ``decorated_definition`` the decorators are its leading
        ``decorator`` children.  Otherwise an empty list is returned.
        """
        if node.type != "decorated_definition":
            return []

        decorators: list[str] = []
        for child in node.children:
            if child.type == "decorator":
                # Drop the leading '@' character
                raw = _node_text(child, self._source_bytes).lstrip("@").strip()
                decorators.append(raw)

        return decorators

    # ------------------------------------------------------------------
    # Call extraction
    # ------------------------------------------------------------------

    def extract_calls(self, func_node: tree_sitter.Node) -> list[ExtractedCall]:
        """Collect every call expression inside *func_node*'s body."""
        body = _first_child_of_type(func_node, "block")
        if body is None:
            return []

        calls: list[ExtractedCall] = []
        for call_node in _collect_nodes(body, "call"):
            try:
                fn_child = call_node.children[0] if call_node.children else None
                if fn_child is None:
                    continue
                fn_name = _node_text(fn_child, self._source_bytes)
                calls.append(ExtractedCall(function_name=fn_name, line=_line(call_node)))
            except Exception:
                logger.debug(
                    "Could not extract call at line %d", _line(call_node), exc_info=True
                )

        return calls

    # ------------------------------------------------------------------
    # Docstrings
    # ------------------------------------------------------------------

    def extract_docstring(self, body_node: tree_sitter.Node | None) -> str | None:
        """Return the docstring from a ``block`` node, or ``None``.

        The docstring is the first ``expression_statement`` in the body whose
        sole child is a ``string`` literal.
        """
        if body_node is None:
            return None

        for child in body_node.children:
            if child.type == "expression_statement":
                string_node = _first_child_of_type(child, "string")
                if string_node is not None:
                    raw = _node_text(string_node, self._source_bytes)
                    return self._clean_docstring(raw)
                break  # only the very first expr_stmt counts
        return None

    def _extract_module_docstring(self, root: tree_sitter.Node) -> str | None:
        """Extract a module-level docstring (first expression_statement at root)."""
        for child in root.children:
            if child.type == "expression_statement":
                string_node = _first_child_of_type(child, "string")
                if string_node is not None:
                    raw = _node_text(string_node, self._source_bytes)
                    return self._clean_docstring(raw)
                break
            # Skip comments and other non-expression nodes
            if child.type not in ("comment",):
                break
        return None

    @staticmethod
    def _clean_docstring(raw: str) -> str:
        """Strip surrounding triple-quotes and leading whitespace."""
        for q in ('"""', "'''", '"', "'"):
            if raw.startswith(q) and raw.endswith(q) and len(raw) >= 2 * len(q):
                raw = raw[len(q) : -len(q)]
                break
        return raw.strip()

    # ------------------------------------------------------------------
    # API endpoints
    # ------------------------------------------------------------------

    def extract_api_endpoints(
        self,
        root: tree_sitter.Node,
        module_name: str = "",
    ) -> list[ExtractedEndpoint]:
        """Detect HTTP endpoints from decorators such as ``@app.get("/path")``.

        Recognised patterns::

            @app.get("/path")
            @router.post("/path")
            @app.route("/path", methods=["GET"])
            @blueprint.route("/path")
        """
        endpoints: list[ExtractedEndpoint] = []

        for node in root.children:
            if node.type != "decorated_definition":
                continue

            func_node = _first_child_of_type(node, "function_definition")
            if func_node is None:
                continue

            fn_name_node = _first_child_of_type(func_node, "identifier")
            handler = _node_text(fn_name_node, self._source_bytes) if fn_name_node else ""

            for dec_node in _children_of_type(node, "decorator"):
                ep = self._parse_endpoint_decorator(dec_node, handler)
                if ep is not None:
                    endpoints.append(ep)

        return endpoints

    def _parse_endpoint_decorator(
        self,
        dec_node: tree_sitter.Node,
        handler: str,
    ) -> ExtractedEndpoint | None:
        """Try to interpret a single decorator as an HTTP endpoint."""
        dec_text = _node_text(dec_node, self._source_bytes).lstrip("@").strip()

        # Pattern: @app.get("/path") or @router.post("/path")
        for method_name in _ROUTE_METHODS:
            pattern = re.compile(
                rf"(\w+)\.{method_name}\s*\(\s*[\"']([^\"']+)[\"']",
                re.IGNORECASE,
            )
            match = pattern.search(dec_text)
            if match:
                return ExtractedEndpoint(
                    method=method_name.upper(),
                    path=match.group(2),
                    handler_function=handler,
                    decorators=[dec_text],
                    line=_line(dec_node),
                )

        # Pattern: @app.route("/path", methods=["GET", "POST"])
        route_pattern = re.compile(
            r"(\w+)\.route\s*\(\s*[\"']([^\"']+)[\"']",
            re.IGNORECASE,
        )
        route_match = route_pattern.search(dec_text)
        if route_match:
            methods_match = re.search(r"methods\s*=\s*\[([^\]]+)\]", dec_text)
            http_methods: list[str] = ["GET"]
            if methods_match:
                http_methods = [
                    m.strip().strip("\"'").upper()
                    for m in methods_match.group(1).split(",")
                ]
            for m in http_methods:
                return ExtractedEndpoint(
                    method=m,
                    path=route_match.group(2),
                    handler_function=handler,
                    decorators=[dec_text],
                    line=_line(dec_node),
                )

        return None

    # ------------------------------------------------------------------
    # ORM / data models
    # ------------------------------------------------------------------

    def extract_orm_models(self, classes: list[ExtractedClass]) -> list[ExtractedDataModel]:
        """Detect ORM models and data-transfer objects from extracted classes.

        A class is considered a data model when its bases include a known
        ORM / DTO superclass (e.g. ``Base``, ``Model``, ``BaseModel``).
        """
        models: list[ExtractedDataModel] = []

        for cls in classes:
            framework = self._detect_framework(cls)
            if framework is None:
                continue

            table_name = self._detect_table_name(cls)
            fields = self._extract_model_fields(cls)

            models.append(
                ExtractedDataModel(
                    class_name=cls.name,
                    table_name=table_name,
                    fields=fields,
                    framework=framework,
                    line_start=cls.line_start,
                    line_end=cls.line_end,
                )
            )

        return models

    @staticmethod
    def _detect_framework(cls: ExtractedClass) -> str | None:
        """Return the framework string if *cls* looks like an ORM/DTO model."""
        base_set = set(cls.bases)
        if base_set & _ORM_BASES_SQLALCHEMY:
            return "sqlalchemy"
        if base_set & _ORM_BASES_DJANGO:
            return "django"
        if base_set & _ORM_BASES_PYDANTIC:
            return "pydantic"
        if cls.is_dataclass:
            return "dataclass"
        return None

    @staticmethod
    def _detect_table_name(cls: ExtractedClass) -> str | None:
        """Attempt to find ``__tablename__`` in the class body source."""
        for method in cls.methods:
            # methods is not the right place — but the body source of the class
            # is not directly stored.  We rely on a regex over the combined
            # method bodies (which is a rough heuristic).
            pass

        # Fallback: look at the class docstring (unlikely) or return None
        # A better implementation would store the class body; for now we scan
        # method body_source for __tablename__.
        for method in cls.methods:
            match = re.search(r"__tablename__\s*=\s*[\"']([^\"']+)[\"']", method.body_source)
            if match:
                return match.group(1)
        return None

    @staticmethod
    def _extract_model_fields(cls: ExtractedClass) -> list[str]:
        """Return field names from a data-model class.

        For Pydantic / dataclass models, fields are typed class-level
        attributes.  We approximate by looking at ``__init__`` parameters
        or methods with ``self.<field>`` assignments.
        """
        fields: list[str] = []
        init_method = next((m for m in cls.methods if m.name == "__init__"), None)
        if init_method is not None:
            for param in init_method.parameters:
                if param.name != "self":
                    fields.append(param.name)
            return fields

        # For Pydantic / dataclass: field names appear as typed attributes
        # in the body.  We scan method-less body via a quick heuristic:
        # any ``self.x`` assignment inside any method.
        seen: set[str] = set()
        for method in cls.methods:
            for match in re.finditer(r"self\.(\w+)\s*=", method.body_source):
                field_name = match.group(1)
                if field_name not in seen and not field_name.startswith("_"):
                    fields.append(field_name)
                    seen.add(field_name)

        return fields

    # ------------------------------------------------------------------
    # Utilities
    # ------------------------------------------------------------------

    @staticmethod
    def _file_path_to_module(file_path: str) -> str:
        """Convert a file path to a dot-separated module name.

        ``src/backend/parsing/python.py`` → ``src.backend.parsing.python``
        """
        # Normalise separators
        path = file_path.replace("\\", "/")
        # Strip leading ./
        if path.startswith("./"):
            path = path[2:]
        # Remove .py extension
        if path.endswith(".py"):
            path = path[:-3]
        # Remove trailing /__init__
        if path.endswith("/__init__"):
            path = path[: -len("/__init__")]
        return path.replace("/", ".")
