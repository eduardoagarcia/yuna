"""Compiler for converting expressions to bytecode."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from yuna.script.instructions import Bytecode, Instruction, OpCode


class CompilerError(Exception):
    """Raised when compilation fails."""


@dataclass
class Literal:
    """Literal value node."""

    value: Any


@dataclass
class Variable:
    """Variable reference node."""

    name: str


@dataclass
class BinaryOp:
    """Binary operation node."""

    op: str
    left: Node
    right: Node


@dataclass
class UnaryOp:
    """Unary operation node."""

    op: str
    operand: Node


@dataclass
class Assignment:
    """Variable assignment node."""

    name: str
    value: Node


@dataclass
class Conditional:
    """Conditional expression node."""

    condition: Node
    then_branch: Node
    else_branch: Node | None = None


Node = Literal | Variable | BinaryOp | UnaryOp | Assignment | Conditional


class ScriptCompiler:
    """Compiles expression trees to bytecode.

    Responsibilities:
    - Convert AST nodes to bytecode instructions
    - Manage constant pool
    - Generate jump instructions for control flow
    - Validate expressions for safety

    Usage:
        compiler = ScriptCompiler()

        # Compile simple expression: x + 10
        ast = BinaryOp(op="+", left=Variable("x"), right=Literal(10))
        bytecode = compiler.compile(ast=ast)

        # Execute
        vm = VirtualMachine()
        result = vm.execute(bytecode=bytecode, context={"x": 5})  # Returns 15
    """

    def __init__(self) -> None:
        self._instructions: list[Instruction] = []
        self._constants: list[Any] = []

    def compile(self, ast: Node) -> Bytecode:
        """Compile AST to bytecode.

        Args:
            ast: Abstract syntax tree node to compile

        Returns:
            Compiled bytecode

        Raises:
            CompilerError: If compilation fails
        """
        self._instructions = []
        self._constants = []

        self._compile_node(node=ast)
        self._emit(opcode=OpCode.HALT)

        return Bytecode(
            instructions=self._instructions.copy(), constants=self._constants.copy()
        )

    def _compile_node(self, node: Node) -> None:
        """Compile single AST node."""
        if isinstance(node, Literal):
            const_index = self._add_constant(value=node.value)
            self._emit(opcode=OpCode.LOAD_CONST, arg=const_index)

        elif isinstance(node, Variable):
            self._emit(opcode=OpCode.LOAD_VAR, arg=node.name)

        elif isinstance(node, BinaryOp):
            self._compile_node(node=node.left)
            self._compile_node(node=node.right)

            op_map = {
                "+": OpCode.ADD,
                "-": OpCode.SUB,
                "*": OpCode.MUL,
                "/": OpCode.DIV,
                "%": OpCode.MOD,
                "==": OpCode.EQ,
                "!=": OpCode.NE,
                "<": OpCode.LT,
                "<=": OpCode.LE,
                ">": OpCode.GT,
                ">=": OpCode.GE,
                "and": OpCode.AND,
                "or": OpCode.OR,
            }

            if node.op not in op_map:
                raise CompilerError(f"Unknown operator: {node.op}")

            self._emit(opcode=op_map[node.op])

        elif isinstance(node, UnaryOp):
            self._compile_node(node=node.operand)

            if node.op == "not":
                self._emit(opcode=OpCode.NOT)
            else:
                raise CompilerError(f"Unknown unary operator: {node.op}")

        elif isinstance(node, Assignment):
            self._compile_node(node=node.value)
            self._emit(opcode=OpCode.DUP)
            self._emit(opcode=OpCode.STORE_VAR, arg=node.name)

        elif isinstance(node, Conditional):
            self._compile_node(node=node.condition)

            else_label = len(self._instructions) + 1
            end_label = 0

            self._emit(opcode=OpCode.JUMP_IF_FALSE, arg=0)
            else_jump_index = len(self._instructions) - 1

            self._compile_node(node=node.then_branch)

            if node.else_branch is not None:
                self._emit(opcode=OpCode.JUMP, arg=0)
                end_jump_index = len(self._instructions) - 1
                else_label = len(self._instructions)
                self._instructions[else_jump_index].arg = else_label

                self._compile_node(node=node.else_branch)
                end_label = len(self._instructions)
                self._instructions[end_jump_index].arg = end_label
            else:
                else_label = len(self._instructions)

            self._instructions[else_jump_index].arg = else_label

        else:
            raise CompilerError(f"Unknown node type: {type(node)}")

    def _emit(self, opcode: OpCode, arg: Any = None) -> None:
        """Emit instruction."""
        self._instructions.append(Instruction(opcode=opcode, arg=arg))

    def _add_constant(self, value: Any) -> int:
        """Add constant to pool and return index."""
        if value in self._constants:
            return self._constants.index(value)

        self._constants.append(value)
        return len(self._constants) - 1
