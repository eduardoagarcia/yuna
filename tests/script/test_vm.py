"""Tests for bytecode virtual machine."""

import pytest
from faker import Faker

from yuna.script.instructions import Bytecode, Instruction, OpCode
from yuna.script.vm import (
    VirtualMachine,
    VMError,
    VMMemoryLimit,
    VMTimeout,
)

fake = Faker()


def test_vm_creation() -> None:
    vm = VirtualMachine()

    assert vm is not None


def test_execute_load_const() -> None:
    vm = VirtualMachine()
    bytecode = Bytecode(
        instructions=[
            Instruction(opcode=OpCode.LOAD_CONST, arg=0),
            Instruction(opcode=OpCode.HALT),
        ],
        constants=[42],
    )

    result = vm.execute(bytecode=bytecode)

    assert result == 42


def test_execute_arithmetic_add() -> None:
    vm = VirtualMachine()
    bytecode = Bytecode(
        instructions=[
            Instruction(opcode=OpCode.LOAD_CONST, arg=0),
            Instruction(opcode=OpCode.LOAD_CONST, arg=1),
            Instruction(opcode=OpCode.ADD),
            Instruction(opcode=OpCode.HALT),
        ],
        constants=[10, 20],
    )

    result = vm.execute(bytecode=bytecode)

    assert result == 30


def test_execute_arithmetic_sub() -> None:
    vm = VirtualMachine()
    bytecode = Bytecode(
        instructions=[
            Instruction(opcode=OpCode.LOAD_CONST, arg=0),
            Instruction(opcode=OpCode.LOAD_CONST, arg=1),
            Instruction(opcode=OpCode.SUB),
            Instruction(opcode=OpCode.HALT),
        ],
        constants=[50, 20],
    )

    result = vm.execute(bytecode=bytecode)

    assert result == 30


def test_execute_arithmetic_mul() -> None:
    vm = VirtualMachine()
    bytecode = Bytecode(
        instructions=[
            Instruction(opcode=OpCode.LOAD_CONST, arg=0),
            Instruction(opcode=OpCode.LOAD_CONST, arg=1),
            Instruction(opcode=OpCode.MUL),
            Instruction(opcode=OpCode.HALT),
        ],
        constants=[6, 7],
    )

    result = vm.execute(bytecode=bytecode)

    assert result == 42


def test_execute_arithmetic_div() -> None:
    vm = VirtualMachine()
    bytecode = Bytecode(
        instructions=[
            Instruction(opcode=OpCode.LOAD_CONST, arg=0),
            Instruction(opcode=OpCode.LOAD_CONST, arg=1),
            Instruction(opcode=OpCode.DIV),
            Instruction(opcode=OpCode.HALT),
        ],
        constants=[84, 2],
    )

    result = vm.execute(bytecode=bytecode)

    assert result == 42.0


def test_execute_division_by_zero_raises_error() -> None:
    vm = VirtualMachine()
    bytecode = Bytecode(
        instructions=[
            Instruction(opcode=OpCode.LOAD_CONST, arg=0),
            Instruction(opcode=OpCode.LOAD_CONST, arg=1),
            Instruction(opcode=OpCode.DIV),
            Instruction(opcode=OpCode.HALT),
        ],
        constants=[10, 0],
    )

    with pytest.raises(VMError, match="Division by zero"):
        vm.execute(bytecode=bytecode)


def test_execute_modulo() -> None:
    vm = VirtualMachine()
    bytecode = Bytecode(
        instructions=[
            Instruction(opcode=OpCode.LOAD_CONST, arg=0),
            Instruction(opcode=OpCode.LOAD_CONST, arg=1),
            Instruction(opcode=OpCode.MOD),
            Instruction(opcode=OpCode.HALT),
        ],
        constants=[17, 5],
    )

    result = vm.execute(bytecode=bytecode)

    assert result == 2


def test_execute_modulo_by_zero_raises_error() -> None:
    vm = VirtualMachine()
    bytecode = Bytecode(
        instructions=[
            Instruction(opcode=OpCode.LOAD_CONST, arg=0),
            Instruction(opcode=OpCode.LOAD_CONST, arg=1),
            Instruction(opcode=OpCode.MOD),
            Instruction(opcode=OpCode.HALT),
        ],
        constants=[10, 0],
    )

    with pytest.raises(VMError, match="Modulo by zero"):
        vm.execute(bytecode=bytecode)


def test_execute_comparison_eq() -> None:
    vm = VirtualMachine()
    bytecode = Bytecode(
        instructions=[
            Instruction(opcode=OpCode.LOAD_CONST, arg=0),
            Instruction(opcode=OpCode.LOAD_CONST, arg=1),
            Instruction(opcode=OpCode.EQ),
            Instruction(opcode=OpCode.HALT),
        ],
        constants=[10, 10],
    )

    result = vm.execute(bytecode=bytecode)

    assert result is True


def test_execute_comparison_ne() -> None:
    vm = VirtualMachine()
    bytecode = Bytecode(
        instructions=[
            Instruction(opcode=OpCode.LOAD_CONST, arg=0),
            Instruction(opcode=OpCode.LOAD_CONST, arg=1),
            Instruction(opcode=OpCode.NE),
            Instruction(opcode=OpCode.HALT),
        ],
        constants=[10, 20],
    )

    result = vm.execute(bytecode=bytecode)

    assert result is True


def test_execute_comparison_lt() -> None:
    vm = VirtualMachine()
    bytecode = Bytecode(
        instructions=[
            Instruction(opcode=OpCode.LOAD_CONST, arg=0),
            Instruction(opcode=OpCode.LOAD_CONST, arg=1),
            Instruction(opcode=OpCode.LT),
            Instruction(opcode=OpCode.HALT),
        ],
        constants=[5, 10],
    )

    result = vm.execute(bytecode=bytecode)

    assert result is True


def test_execute_comparison_le() -> None:
    vm = VirtualMachine()
    bytecode = Bytecode(
        instructions=[
            Instruction(opcode=OpCode.LOAD_CONST, arg=0),
            Instruction(opcode=OpCode.LOAD_CONST, arg=1),
            Instruction(opcode=OpCode.LE),
            Instruction(opcode=OpCode.HALT),
        ],
        constants=[10, 10],
    )

    result = vm.execute(bytecode=bytecode)

    assert result is True


def test_execute_comparison_gt() -> None:
    vm = VirtualMachine()
    bytecode = Bytecode(
        instructions=[
            Instruction(opcode=OpCode.LOAD_CONST, arg=0),
            Instruction(opcode=OpCode.LOAD_CONST, arg=1),
            Instruction(opcode=OpCode.GT),
            Instruction(opcode=OpCode.HALT),
        ],
        constants=[20, 10],
    )

    result = vm.execute(bytecode=bytecode)

    assert result is True


def test_execute_comparison_ge() -> None:
    vm = VirtualMachine()
    bytecode = Bytecode(
        instructions=[
            Instruction(opcode=OpCode.LOAD_CONST, arg=0),
            Instruction(opcode=OpCode.LOAD_CONST, arg=1),
            Instruction(opcode=OpCode.GE),
            Instruction(opcode=OpCode.HALT),
        ],
        constants=[10, 10],
    )

    result = vm.execute(bytecode=bytecode)

    assert result is True


def test_execute_logical_and() -> None:
    vm = VirtualMachine()
    bytecode = Bytecode(
        instructions=[
            Instruction(opcode=OpCode.LOAD_CONST, arg=0),
            Instruction(opcode=OpCode.LOAD_CONST, arg=1),
            Instruction(opcode=OpCode.AND),
            Instruction(opcode=OpCode.HALT),
        ],
        constants=[True, True],
    )

    result = vm.execute(bytecode=bytecode)

    assert result is True


def test_execute_logical_or() -> None:
    vm = VirtualMachine()
    bytecode = Bytecode(
        instructions=[
            Instruction(opcode=OpCode.LOAD_CONST, arg=0),
            Instruction(opcode=OpCode.LOAD_CONST, arg=1),
            Instruction(opcode=OpCode.OR),
            Instruction(opcode=OpCode.HALT),
        ],
        constants=[False, True],
    )

    result = vm.execute(bytecode=bytecode)

    assert result is True


def test_execute_logical_not() -> None:
    vm = VirtualMachine()
    bytecode = Bytecode(
        instructions=[
            Instruction(opcode=OpCode.LOAD_CONST, arg=0),
            Instruction(opcode=OpCode.NOT),
            Instruction(opcode=OpCode.HALT),
        ],
        constants=[False],
    )

    result = vm.execute(bytecode=bytecode)

    assert result is True


def test_execute_load_var() -> None:
    vm = VirtualMachine()
    bytecode = Bytecode(
        instructions=[
            Instruction(opcode=OpCode.LOAD_VAR, arg="x"),
            Instruction(opcode=OpCode.HALT),
        ],
        constants=[],
    )

    result = vm.execute(bytecode=bytecode, context={"x": 42})

    assert result == 42


def test_execute_load_undefined_var_raises_error() -> None:
    vm = VirtualMachine()
    bytecode = Bytecode(
        instructions=[
            Instruction(opcode=OpCode.LOAD_VAR, arg="x"),
            Instruction(opcode=OpCode.HALT),
        ],
        constants=[],
    )

    with pytest.raises(VMError, match="Undefined variable"):
        vm.execute(bytecode=bytecode)


def test_execute_store_var() -> None:
    vm = VirtualMachine()
    bytecode = Bytecode(
        instructions=[
            Instruction(opcode=OpCode.LOAD_CONST, arg=0),
            Instruction(opcode=OpCode.STORE_VAR, arg="x"),
            Instruction(opcode=OpCode.LOAD_VAR, arg="x"),
            Instruction(opcode=OpCode.HALT),
        ],
        constants=[42],
    )

    result = vm.execute(bytecode=bytecode)

    assert result == 42


def test_execute_pop() -> None:
    vm = VirtualMachine()
    bytecode = Bytecode(
        instructions=[
            Instruction(opcode=OpCode.LOAD_CONST, arg=0),
            Instruction(opcode=OpCode.LOAD_CONST, arg=1),
            Instruction(opcode=OpCode.POP),
            Instruction(opcode=OpCode.HALT),
        ],
        constants=[10, 20],
    )

    result = vm.execute(bytecode=bytecode)

    assert result == 10


def test_execute_dup() -> None:
    vm = VirtualMachine()
    bytecode = Bytecode(
        instructions=[
            Instruction(opcode=OpCode.LOAD_CONST, arg=0),
            Instruction(opcode=OpCode.DUP),
            Instruction(opcode=OpCode.ADD),
            Instruction(opcode=OpCode.HALT),
        ],
        constants=[21],
    )

    result = vm.execute(bytecode=bytecode)

    assert result == 42


def test_execute_jump() -> None:
    vm = VirtualMachine()
    bytecode = Bytecode(
        instructions=[
            Instruction(opcode=OpCode.JUMP, arg=3),
            Instruction(opcode=OpCode.LOAD_CONST, arg=0),
            Instruction(opcode=OpCode.HALT),
            Instruction(opcode=OpCode.LOAD_CONST, arg=1),
            Instruction(opcode=OpCode.HALT),
        ],
        constants=[999, 42],
    )

    result = vm.execute(bytecode=bytecode)

    assert result == 42


def test_execute_jump_if_false_true_condition() -> None:
    vm = VirtualMachine()
    bytecode = Bytecode(
        instructions=[
            Instruction(opcode=OpCode.LOAD_CONST, arg=0),
            Instruction(opcode=OpCode.JUMP_IF_FALSE, arg=4),
            Instruction(opcode=OpCode.LOAD_CONST, arg=1),
            Instruction(opcode=OpCode.HALT),
            Instruction(opcode=OpCode.LOAD_CONST, arg=2),
            Instruction(opcode=OpCode.HALT),
        ],
        constants=[True, 42, 999],
    )

    result = vm.execute(bytecode=bytecode)

    assert result == 42


def test_execute_jump_if_false_false_condition() -> None:
    vm = VirtualMachine()
    bytecode = Bytecode(
        instructions=[
            Instruction(opcode=OpCode.LOAD_CONST, arg=0),
            Instruction(opcode=OpCode.JUMP_IF_FALSE, arg=4),
            Instruction(opcode=OpCode.LOAD_CONST, arg=1),
            Instruction(opcode=OpCode.HALT),
            Instruction(opcode=OpCode.LOAD_CONST, arg=2),
            Instruction(opcode=OpCode.HALT),
        ],
        constants=[False, 999, 42],
    )

    result = vm.execute(bytecode=bytecode)

    assert result == 42


def test_execute_return() -> None:
    vm = VirtualMachine()
    bytecode = Bytecode(
        instructions=[
            Instruction(opcode=OpCode.LOAD_CONST, arg=0),
            Instruction(opcode=OpCode.RETURN),
            Instruction(opcode=OpCode.LOAD_CONST, arg=1),
            Instruction(opcode=OpCode.HALT),
        ],
        constants=[42, 999],
    )

    result = vm.execute(bytecode=bytecode)

    assert result == 42


def test_execute_empty_bytecode() -> None:
    vm = VirtualMachine()
    bytecode = Bytecode(instructions=[Instruction(opcode=OpCode.HALT)], constants=[])

    result = vm.execute(bytecode=bytecode)

    assert result is None


def test_stack_underflow_raises_error() -> None:
    vm = VirtualMachine()
    bytecode = Bytecode(
        instructions=[Instruction(opcode=OpCode.POP), Instruction(opcode=OpCode.HALT)],
        constants=[],
    )

    with pytest.raises(VMError, match="Stack underflow"):
        vm.execute(bytecode=bytecode)


def test_timeout_enforcement() -> None:
    vm = VirtualMachine(max_instructions=10)
    instructions = [Instruction(opcode=OpCode.LOAD_CONST, arg=0) for _ in range(20)]
    instructions.append(Instruction(opcode=OpCode.HALT))
    bytecode = Bytecode(instructions=instructions, constants=[1])

    with pytest.raises(VMTimeout, match="exceeded"):
        vm.execute(bytecode=bytecode)


def test_stack_overflow_raises_error() -> None:
    vm = VirtualMachine(max_stack_size=5)
    instructions = [Instruction(opcode=OpCode.LOAD_CONST, arg=0) for _ in range(10)]
    instructions.append(Instruction(opcode=OpCode.HALT))
    bytecode = Bytecode(instructions=instructions, constants=[1])

    with pytest.raises(VMMemoryLimit, match="Stack overflow"):
        vm.execute(bytecode=bytecode)


def test_too_many_variables_raises_error() -> None:
    vm = VirtualMachine()
    instructions = []
    for i in range(1001):
        instructions.append(Instruction(opcode=OpCode.LOAD_CONST, arg=0))
        instructions.append(Instruction(opcode=OpCode.STORE_VAR, arg=f"var_{i}"))
    instructions.append(Instruction(opcode=OpCode.HALT))
    bytecode = Bytecode(instructions=instructions, constants=[1])

    with pytest.raises(VMMemoryLimit, match="Too many variables"):
        vm.execute(bytecode=bytecode)


def test_get_stack() -> None:
    vm = VirtualMachine()
    bytecode = Bytecode(
        instructions=[
            Instruction(opcode=OpCode.LOAD_CONST, arg=0),
            Instruction(opcode=OpCode.LOAD_CONST, arg=1),
            Instruction(opcode=OpCode.RETURN),
        ],
        constants=[10, 20],
    )

    vm.execute(bytecode=bytecode)
    stack = vm.get_stack()

    assert stack == [10]


def test_get_variables() -> None:
    vm = VirtualMachine()
    bytecode = Bytecode(
        instructions=[
            Instruction(opcode=OpCode.LOAD_CONST, arg=0),
            Instruction(opcode=OpCode.STORE_VAR, arg="x"),
            Instruction(opcode=OpCode.HALT),
        ],
        constants=[42],
    )

    vm.execute(bytecode=bytecode)
    variables = vm.get_variables()

    assert variables == {"x": 42}


def test_get_instruction_count() -> None:
    vm = VirtualMachine()
    bytecode = Bytecode(
        instructions=[
            Instruction(opcode=OpCode.LOAD_CONST, arg=0),
            Instruction(opcode=OpCode.LOAD_CONST, arg=1),
            Instruction(opcode=OpCode.ADD),
            Instruction(opcode=OpCode.HALT),
        ],
        constants=[10, 20],
    )

    vm.execute(bytecode=bytecode)
    count = vm.get_instruction_count()

    assert count == 4


def test_unknown_opcode_raises_error() -> None:
    vm = VirtualMachine()
    bytecode = Bytecode(
        instructions=[Instruction(opcode=OpCode.CALL), Instruction(opcode=OpCode.HALT)],
        constants=[],
    )

    with pytest.raises(VMError, match="Unknown opcode"):
        vm.execute(bytecode=bytecode)


def test_dup_on_empty_stack_raises_error() -> None:
    vm = VirtualMachine()
    bytecode = Bytecode(
        instructions=[Instruction(opcode=OpCode.DUP), Instruction(opcode=OpCode.HALT)],
        constants=[],
    )

    with pytest.raises(VMError, match="Stack underflow"):
        vm.execute(bytecode=bytecode)
