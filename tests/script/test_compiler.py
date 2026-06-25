"""Tests for script compiler."""

import pytest
from faker import Faker

from yuna.script.compiler import (
    Assignment,
    BinaryOp,
    CompilerError,
    Conditional,
    Literal,
    ScriptCompiler,
    UnaryOp,
    Variable,
)
from yuna.script.vm import VirtualMachine

fake = Faker()


def test_compiler_creation() -> None:
    compiler = ScriptCompiler()

    assert compiler is not None


def test_compile_literal() -> None:
    compiler = ScriptCompiler()
    ast = Literal(value=42)

    bytecode = compiler.compile(ast=ast)
    vm = VirtualMachine()
    result = vm.execute(bytecode=bytecode)

    assert result == 42


def test_compile_variable() -> None:
    compiler = ScriptCompiler()
    ast = Variable(name="x")

    bytecode = compiler.compile(ast=ast)
    vm = VirtualMachine()
    result = vm.execute(bytecode=bytecode, context={"x": 100})

    assert result == 100


def test_compile_binary_op_add() -> None:
    compiler = ScriptCompiler()
    ast = BinaryOp(op="+", left=Literal(value=10), right=Literal(value=20))

    bytecode = compiler.compile(ast=ast)
    vm = VirtualMachine()
    result = vm.execute(bytecode=bytecode)

    assert result == 30


def test_compile_binary_op_sub() -> None:
    compiler = ScriptCompiler()
    ast = BinaryOp(op="-", left=Literal(value=50), right=Literal(value=20))

    bytecode = compiler.compile(ast=ast)
    vm = VirtualMachine()
    result = vm.execute(bytecode=bytecode)

    assert result == 30


def test_compile_binary_op_mul() -> None:
    compiler = ScriptCompiler()
    ast = BinaryOp(op="*", left=Literal(value=6), right=Literal(value=7))

    bytecode = compiler.compile(ast=ast)
    vm = VirtualMachine()
    result = vm.execute(bytecode=bytecode)

    assert result == 42


def test_compile_binary_op_div() -> None:
    compiler = ScriptCompiler()
    ast = BinaryOp(op="/", left=Literal(value=84), right=Literal(value=2))

    bytecode = compiler.compile(ast=ast)
    vm = VirtualMachine()
    result = vm.execute(bytecode=bytecode)

    assert result == 42.0


def test_compile_binary_op_mod() -> None:
    compiler = ScriptCompiler()
    ast = BinaryOp(op="%", left=Literal(value=17), right=Literal(value=5))

    bytecode = compiler.compile(ast=ast)
    vm = VirtualMachine()
    result = vm.execute(bytecode=bytecode)

    assert result == 2


def test_compile_comparison_eq() -> None:
    compiler = ScriptCompiler()
    ast = BinaryOp(op="==", left=Literal(value=10), right=Literal(value=10))

    bytecode = compiler.compile(ast=ast)
    vm = VirtualMachine()
    result = vm.execute(bytecode=bytecode)

    assert result is True


def test_compile_comparison_ne() -> None:
    compiler = ScriptCompiler()
    ast = BinaryOp(op="!=", left=Literal(value=10), right=Literal(value=20))

    bytecode = compiler.compile(ast=ast)
    vm = VirtualMachine()
    result = vm.execute(bytecode=bytecode)

    assert result is True


def test_compile_comparison_lt() -> None:
    compiler = ScriptCompiler()
    ast = BinaryOp(op="<", left=Literal(value=5), right=Literal(value=10))

    bytecode = compiler.compile(ast=ast)
    vm = VirtualMachine()
    result = vm.execute(bytecode=bytecode)

    assert result is True


def test_compile_comparison_le() -> None:
    compiler = ScriptCompiler()
    ast = BinaryOp(op="<=", left=Literal(value=10), right=Literal(value=10))

    bytecode = compiler.compile(ast=ast)
    vm = VirtualMachine()
    result = vm.execute(bytecode=bytecode)

    assert result is True


def test_compile_comparison_gt() -> None:
    compiler = ScriptCompiler()
    ast = BinaryOp(op=">", left=Literal(value=20), right=Literal(value=10))

    bytecode = compiler.compile(ast=ast)
    vm = VirtualMachine()
    result = vm.execute(bytecode=bytecode)

    assert result is True


def test_compile_comparison_ge() -> None:
    compiler = ScriptCompiler()
    ast = BinaryOp(op=">=", left=Literal(value=10), right=Literal(value=10))

    bytecode = compiler.compile(ast=ast)
    vm = VirtualMachine()
    result = vm.execute(bytecode=bytecode)

    assert result is True


def test_compile_logical_and() -> None:
    compiler = ScriptCompiler()
    ast = BinaryOp(op="and", left=Literal(value=True), right=Literal(value=True))

    bytecode = compiler.compile(ast=ast)
    vm = VirtualMachine()
    result = vm.execute(bytecode=bytecode)

    assert result is True


def test_compile_logical_or() -> None:
    compiler = ScriptCompiler()
    ast = BinaryOp(op="or", left=Literal(value=False), right=Literal(value=True))

    bytecode = compiler.compile(ast=ast)
    vm = VirtualMachine()
    result = vm.execute(bytecode=bytecode)

    assert result is True


def test_compile_unary_not() -> None:
    compiler = ScriptCompiler()
    ast = UnaryOp(op="not", operand=Literal(value=False))

    bytecode = compiler.compile(ast=ast)
    vm = VirtualMachine()
    result = vm.execute(bytecode=bytecode)

    assert result is True


def test_compile_unknown_binary_op_raises_error() -> None:
    compiler = ScriptCompiler()
    ast = BinaryOp(op="**", left=Literal(value=2), right=Literal(value=3))

    with pytest.raises(CompilerError, match="Unknown operator"):
        compiler.compile(ast=ast)


def test_compile_unknown_unary_op_raises_error() -> None:
    compiler = ScriptCompiler()
    ast = UnaryOp(op="-", operand=Literal(value=10))

    with pytest.raises(CompilerError, match="Unknown unary operator"):
        compiler.compile(ast=ast)


def test_compile_assignment() -> None:
    compiler = ScriptCompiler()
    ast = Assignment(name="x", value=Literal(value=42))

    bytecode = compiler.compile(ast=ast)
    vm = VirtualMachine()
    result = vm.execute(bytecode=bytecode)

    assert result == 42
    assert vm.get_variables() == {"x": 42}


def test_compile_complex_expression() -> None:
    compiler = ScriptCompiler()
    ast = BinaryOp(
        op="+",
        left=BinaryOp(op="*", left=Literal(value=2), right=Literal(value=3)),
        right=Literal(value=4),
    )

    bytecode = compiler.compile(ast=ast)
    vm = VirtualMachine()
    result = vm.execute(bytecode=bytecode)

    assert result == 10


def test_compile_with_variables() -> None:
    compiler = ScriptCompiler()
    ast = BinaryOp(op="+", left=Variable(name="x"), right=Variable(name="y"))

    bytecode = compiler.compile(ast=ast)
    vm = VirtualMachine()
    result = vm.execute(bytecode=bytecode, context={"x": 10, "y": 20})

    assert result == 30


def test_compile_conditional_true_branch() -> None:
    compiler = ScriptCompiler()
    ast = Conditional(
        condition=Literal(value=True),
        then_branch=Literal(value=42),
        else_branch=Literal(value=999),
    )

    bytecode = compiler.compile(ast=ast)
    vm = VirtualMachine()
    result = vm.execute(bytecode=bytecode)

    assert result == 42


def test_compile_conditional_false_branch() -> None:
    compiler = ScriptCompiler()
    ast = Conditional(
        condition=Literal(value=False),
        then_branch=Literal(value=999),
        else_branch=Literal(value=42),
    )

    bytecode = compiler.compile(ast=ast)
    vm = VirtualMachine()
    result = vm.execute(bytecode=bytecode)

    assert result == 42


def test_compile_conditional_without_else() -> None:
    compiler = ScriptCompiler()
    ast = Conditional(condition=Literal(value=False), then_branch=Literal(value=999))

    bytecode = compiler.compile(ast=ast)
    vm = VirtualMachine()
    result = vm.execute(bytecode=bytecode)

    assert result is None


def test_compile_nested_conditionals() -> None:
    compiler = ScriptCompiler()
    ast = Conditional(
        condition=Literal(value=True),
        then_branch=Conditional(
            condition=Literal(value=False),
            then_branch=Literal(value=999),
            else_branch=Literal(value=42),
        ),
        else_branch=Literal(value=888),
    )

    bytecode = compiler.compile(ast=ast)
    vm = VirtualMachine()
    result = vm.execute(bytecode=bytecode)

    assert result == 42


def test_compile_constant_reuse() -> None:
    compiler = ScriptCompiler()
    ast = BinaryOp(op="+", left=Literal(value=10), right=Literal(value=10))

    bytecode = compiler.compile(ast=ast)

    assert len(bytecode.constants) == 1
    assert bytecode.constants[0] == 10


def test_compile_multiple_different_constants() -> None:
    compiler = ScriptCompiler()
    ast = BinaryOp(op="+", left=Literal(value=10), right=Literal(value=20))

    bytecode = compiler.compile(ast=ast)

    assert len(bytecode.constants) == 2
    assert 10 in bytecode.constants
    assert 20 in bytecode.constants


def test_compile_unknown_node_type_raises_error() -> None:
    compiler = ScriptCompiler()

    class UnknownNode:
        pass

    ast = UnknownNode()

    with pytest.raises(CompilerError, match="Unknown node type"):
        compiler.compile(ast=ast)  # type: ignore[arg-type]
