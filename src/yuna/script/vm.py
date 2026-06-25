"""Stack-based virtual machine for bytecode execution."""

from __future__ import annotations

from typing import Any

from yuna.script.instructions import Bytecode, OpCode


class VMTimeout(Exception):
    """Raised when VM execution exceeds timeout."""


class VMMemoryLimit(Exception):
    """Raised when VM exceeds memory limit."""


class VMError(Exception):
    """Raised when VM encounters execution error."""


class VirtualMachine:
    """Stack-based bytecode virtual machine with safety limits.

    Responsibilities:
    - Execute bytecode instructions
    - Enforce execution timeout
    - Enforce memory limits
    - Maintain execution stack and variables
    - Prevent dangerous operations

    Security features:
    - No file I/O operations
    - No network operations
    - No dangerous builtins access
    - Instruction count timeout
    - Stack size limit
    - Variable count limit

    Usage:
        vm = VirtualMachine(max_instructions=1000, max_stack_size=100)
        result = vm.execute(bytecode=bytecode, context={"x": 10})
    """

    def __init__(
        self, max_instructions: int = 10000, max_stack_size: int = 1000
    ) -> None:
        self.max_instructions = max_instructions
        self.max_stack_size = max_stack_size
        self._reset()

    def _reset(self) -> None:
        """Reset VM state for new execution."""
        self._stack: list[Any] = []
        self._variables: dict[str, Any] = {}
        self._instruction_count = 0
        self._pc = 0

    def execute(self, bytecode: Bytecode, context: dict[str, Any] | None = None) -> Any:
        """Execute bytecode program.

        Args:
            bytecode: Compiled bytecode to execute
            context: Initial variable context

        Returns:
            Final value on top of stack, or None if stack is empty

        Raises:
            VMTimeout: If execution exceeds max_instructions
            VMMemoryLimit: If stack exceeds max_stack_size
            VMError: If execution encounters an error
        """
        self._reset()
        if context:
            self._variables.update(context)

        instructions = bytecode.instructions
        constants = bytecode.constants

        while self._pc < len(instructions):
            if self._instruction_count >= self.max_instructions:
                raise VMTimeout(
                    f"Execution exceeded {self.max_instructions} instructions"
                )

            instruction = instructions[self._pc]
            self._instruction_count += 1
            self._pc += 1

            if instruction.opcode == OpCode.LOAD_CONST:
                self._push(constants[instruction.arg])

            elif instruction.opcode == OpCode.LOAD_VAR:
                if instruction.arg not in self._variables:
                    raise VMError(f"Undefined variable: {instruction.arg}")
                self._push(self._variables[instruction.arg])

            elif instruction.opcode == OpCode.STORE_VAR:
                if len(self._variables) >= 1000:
                    raise VMMemoryLimit("Too many variables")
                value = self._pop()
                self._variables[instruction.arg] = value

            elif instruction.opcode == OpCode.POP:
                self._pop()

            elif instruction.opcode == OpCode.DUP:
                value = self._peek()
                self._push(value)

            elif instruction.opcode == OpCode.ADD:
                b = self._pop()
                a = self._pop()
                self._push(a + b)

            elif instruction.opcode == OpCode.SUB:
                b = self._pop()
                a = self._pop()
                self._push(a - b)

            elif instruction.opcode == OpCode.MUL:
                b = self._pop()
                a = self._pop()
                self._push(a * b)

            elif instruction.opcode == OpCode.DIV:
                b = self._pop()
                a = self._pop()
                if b == 0:
                    raise VMError("Division by zero")
                self._push(a / b)

            elif instruction.opcode == OpCode.MOD:
                b = self._pop()
                a = self._pop()
                if b == 0:
                    raise VMError("Modulo by zero")
                self._push(a % b)

            elif instruction.opcode == OpCode.EQ:
                b = self._pop()
                a = self._pop()
                self._push(a == b)

            elif instruction.opcode == OpCode.NE:
                b = self._pop()
                a = self._pop()
                self._push(a != b)

            elif instruction.opcode == OpCode.LT:
                b = self._pop()
                a = self._pop()
                self._push(a < b)

            elif instruction.opcode == OpCode.LE:
                b = self._pop()
                a = self._pop()
                self._push(a <= b)

            elif instruction.opcode == OpCode.GT:
                b = self._pop()
                a = self._pop()
                self._push(a > b)

            elif instruction.opcode == OpCode.GE:
                b = self._pop()
                a = self._pop()
                self._push(a >= b)

            elif instruction.opcode == OpCode.AND:
                b = self._pop()
                a = self._pop()
                self._push(a and b)

            elif instruction.opcode == OpCode.OR:
                b = self._pop()
                a = self._pop()
                self._push(a or b)

            elif instruction.opcode == OpCode.NOT:
                a = self._pop()
                self._push(not a)

            elif instruction.opcode == OpCode.JUMP:
                self._pc = instruction.arg

            elif instruction.opcode == OpCode.JUMP_IF_FALSE:
                condition = self._pop()
                if not condition:
                    self._pc = instruction.arg

            elif instruction.opcode == OpCode.RETURN:
                return self._pop() if self._stack else None

            elif instruction.opcode == OpCode.HALT:
                break

            else:
                raise VMError(f"Unknown opcode: {instruction.opcode}")

        return self._pop() if self._stack else None

    def _push(self, value: Any) -> None:
        """Push value onto stack."""
        if len(self._stack) >= self.max_stack_size:
            raise VMMemoryLimit(f"Stack overflow (max {self.max_stack_size})")
        self._stack.append(value)

    def _pop(self) -> Any:
        """Pop value from stack."""
        if not self._stack:
            raise VMError("Stack underflow")
        return self._stack.pop()

    def _peek(self) -> Any:
        """Peek at top of stack without popping."""
        if not self._stack:
            raise VMError("Stack underflow")
        return self._stack[-1]

    def get_stack(self) -> list[Any]:
        """Get current stack contents (for debugging)."""
        return self._stack.copy()

    def get_variables(self) -> dict[str, Any]:
        """Get current variables (for debugging)."""
        return self._variables.copy()

    def get_instruction_count(self) -> int:
        """Get number of instructions executed."""
        return self._instruction_count
