from __future__ import annotations

from typing import Protocol

# So, here's the new idea: Trivia nodes.
#
# Basically everything that is valid JSON data will be part of the node's attributes,
# but everything else (such as whitespace, newlines, comments, trailing commas) will be
# in a list of what I'm calling "trivia nodes". Every single json data node (booleans,
# numbers, etc.) will have a property `trailing_trivia_nodes`, which will list all the
# trivia nodes found after the said node.
#
# There's just one slight thing to take care of: Since there can be whitespace, comments
# etc. in the beginning of an array/object/file before any of the content, they require
# different trivia node handling, they'll have a `leading_trivia_nodes` property too.
# These three nodes I'll be calling "scope" nodes.


class Json5Node(Protocol):
    """Sets the expectation from a JSON5 node: be able to convert back to source."""

    def to_json5(self) -> str:
        ...

    def to_json(self) -> str:
        ...


class Json5Primitive:
    """Base class for primitive JSON types such as booleans, null, integers etc."""

    def __init__(
        self,
        source: str,
        value: object,
        trailing_trivia_nodes: list[Json5Trivia],
    ) -> None:
        self.source = source
        self.value = value
        self.trailing_trivia_nodes = trailing_trivia_nodes

    def to_json5(self) -> str:
        return self.source + "".join(
            trivia.source for trivia in self.trailing_trivia_nodes
        )

    def to_json(self) -> str:
        return self.source


class Json5Null(Json5Primitive):
    def __init__(self, trailing_trivia_nodes: list[Json5Trivia]) -> None:
        super().__init__(
            source="null",
            value=None,
            trailing_trivia_nodes=trailing_trivia_nodes,
        )


class Json5Boolean(Json5Primitive):
    def __init__(
        self,
        source: str,
        value: bool,
        trailing_trivia_nodes: list[Json5Trivia],
    ) -> None:
        super().__init__(source, value, trailing_trivia_nodes)


class Json5Integer(Json5Primitive):
    def __init__(
        self,
        source: str,
        value: int,
        trailing_trivia_nodes: list[Json5Trivia],
    ) -> None:
        super().__init__(source, value, trailing_trivia_nodes)


class Json5Container:
    """
    Base class for "container nodes", i.e. nodes that contain other nodes.

    This distinction is required because container nodes can have leading trivia
    nodes, while primitive nodes like ints and booleans cannot.

    Examples of container nodes include files, arrays and objects.
    """

    def __init__(
        self,
        leading_trivia_nodes: list[Json5Trivia],
        trailing_trivia_nodes: list[Json5Trivia],
    ) -> None:
        self.leading_trivia_nodes = leading_trivia_nodes
        self.trailing_trivia_nodes = trailing_trivia_nodes

    def to_json5(self) -> str:
        """Converts the node back to its original source."""
        raise NotImplementedError

    def to_json(self) -> str:
        raise NotImplementedError


class Json5Array(Json5Container):
    def __init__(
        self,
        leading_trivia_nodes: list[Json5Trivia],
        trailing_trivia_nodes: list[Json5Trivia],
    ) -> None:
        super().__init__(leading_trivia_nodes, trailing_trivia_nodes)
        self.members: list[Json5Node] = []

    def to_json5(self) -> str:
        """Converts the node back to its original source."""
        return (
            "["
            + "".join(trivia.source for trivia in self.leading_trivia_nodes)
            + ",".join(member.to_json5() for member in self.members)
            + "".join(trivia.source for trivia in self.trailing_trivia_nodes)
            + "]"
        )

    def to_json(self) -> str:
        """Converts the node back to its original source."""
        return "[" + ",".join(member.to_json() for member in self.members) + "]"


class Json5Object(Json5Container):
    def __init__(
        self,
        leading_trivia_nodes: list[Json5Trivia],
        trailing_trivia_nodes: list[Json5Trivia],
    ) -> None:
        super().__init__(leading_trivia_nodes, trailing_trivia_nodes)
        self.data: dict[Json5Primitive, Json5Primitive] = {}

    def to_json5(self) -> str:
        """Converts the node back to its original source."""
        return (
            "{"
            + "".join(trivia.source for trivia in self.leading_trivia_nodes)
            + ",".join(
                f"{key.to_json5()}:{value.to_json5()}"
                for key, value in self.data.items()
            )
            + "".join(trivia.source for trivia in self.trailing_trivia_nodes)
            + "}"
        )

    def to_json(self) -> str:
        """Converts the node back to its original source."""
        return (
            "{"
            + ",".join(
                f"{key.to_json()}:{value.to_json()}" for key, value in self.data.items()
            )
            + "}"
        )


class Json5Trivia:
    """Base class for "trivial" information like whitespace, newlines and comments."""

    def __init__(self, source: str) -> None:
        self.source = source


class Json5Comment(Json5Trivia):
    """JSON5 single line comments, eg. `// foo`."""


class Json5Whitespace(Json5Trivia):
    """Any run of continuous whitespace characters in a JSON5 file."""


class Json5Newline(Json5Trivia):
    """Newline character in a JSON5 file."""
