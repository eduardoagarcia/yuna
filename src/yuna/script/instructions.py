"""Bytecode instruction set for safe scripting."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto
from typing import Any


class OpCode(Enum):
    """Instruction opcodes for bytecode VM.

    Stack-based virtual machine with safe operations only.
    No file I/O, network access, or dangerous operations allowed.
    """

    LOAD_CONST = auto()
    LOAD_VAR = auto()
    STORE_VAR = auto()
    POP = auto()
    DUP = auto()
    ADD = auto()
    SUB = auto()
    MUL = auto()
    DIV = auto()
    MOD = auto()
    EQ = auto()
    NE = auto()
    LT = auto()
    LE = auto()
    GT = auto()
    GE = auto()
    AND = auto()
    OR = auto()
    NOT = auto()
    JUMP = auto()
    JUMP_IF_FALSE = auto()
    CALL = auto()
    RETURN = auto()
    HALT = auto()


@dataclass
class Instruction:
    """Single bytecode instruction.

    Attributes:
        opcode: Operation to perform
        arg: Optional argument (constant index, variable name, jump offset)
    """

    opcode: OpCode
    arg: Any = None

    def __repr__(self) -> str:
        if self.arg is not None:
            return f"{self.opcode.name}({self.arg!r})"
        return self.opcode.name


@dataclass
class Bytecode:
    """Compiled bytecode program.

    Attributes:
        instructions: List of instructions to execute
        constants: Constant pool (literals used in program)
    """

    instructions: list[Instruction]
    constants: list[Any]

    def __repr__(self) -> str:
        lines = []
        for i, instruction in enumerate(self.instructions):
            lines.append(f"{i:04d}  {instruction}")
        return "\n".join(lines)
