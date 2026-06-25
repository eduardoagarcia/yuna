"""Tests for bytecode instructions."""

from yuna.script.instructions import Bytecode, Instruction, OpCode


def test_instruction_repr_with_arg() -> None:
    instruction = Instruction(opcode=OpCode.LOAD_CONST, arg=0)

    result = repr(instruction)

    assert "LOAD_CONST" in result
    assert "0" in result


def test_instruction_repr_without_arg() -> None:
    instruction = Instruction(opcode=OpCode.HALT)

    result = repr(instruction)

    assert result == "HALT"


def test_bytecode_repr() -> None:
    bytecode = Bytecode(
        instructions=[
            Instruction(opcode=OpCode.LOAD_CONST, arg=0),
            Instruction(opcode=OpCode.HALT),
        ],
        constants=[42],
    )

    result = repr(bytecode)

    assert "LOAD_CONST" in result
    assert "HALT" in result
