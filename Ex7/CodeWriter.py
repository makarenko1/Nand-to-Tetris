"""This file is part of nand2tetris, as taught in The Hebrew University,
and was written by Aviv Yaish according to the specifications given in  
https://www.nand2tetris.org (Shimon Schocken and Noam Nisan, 2017)
and as allowed by the Creative Common Attribution-NonCommercial-ShareAlike 3.0 
Unported License (https://creativecommons.org/licenses/by-nc-sa/3.0/).
"""
import typing

ARITHMETIC_TRANSLATE = {"add": "+", "sub": "-", "neg": "-", "eq": "JEQ",
                        "gt": "JGT", "lt": "JLT", "and": "&", "or": "|",
                        "not": "!", "shiftleft": "<<", "shiftright": ">>"}
UNARY = ["neg", "not", "shiftleft", "shiftright"]
NON_COMPARISON_BINARY = ["add", "sub", "and", "or"]
COMPARISON_BINARY = ["eq", "gt", "lt"]
SEGMENTS = {"local": "LCL", "argument": "ARG", "this": "THIS",
            "that": "THAT", "pointer": 3, "temp": 5, "static": 16}
STACK_START = 256


class CodeWriter:
    """Translates VM commands into Hack assembly code."""

    def __init__(self, output_stream: typing.TextIO) -> None:
        """Initializes the CodeWriter.

        Args:
            output_stream (typing.TextIO): output stream.
        """
        self.output_stream = output_stream
        self.filename = ""
        self.label_num = 0

    def set_file_name(self, filename: str) -> None:
        """Informs the code writer that the translation of a new VM file is
        started.

        Args:
            filename (str): The name of the VM file.
        """
        self.filename = filename
        self.label_num = 0
        lines = ["@{}".format(STACK_START),
                 "D=A",
                 "@SP",
                 "M=D"]
        self._write_to_stream(lines)

    def write_arithmetic(self, command: str) -> None:
        """Writes the assembly code that is the translation of the given
        arithmetic command.

        Args:
            command (str): an arithmetic command.
        """
        lines = list()
        if command in UNARY:
            CodeWriter._get_last_stack_address(lines)
            lines.append("M={}M".format(ARITHMETIC_TRANSLATE[command]))
        else:
            self._write_arithmetic_case_binary(command, lines)
        self._write_to_stream(lines)

    def write_push_pop(self, command: str, segment: str, index: int) -> None:
        """Writes the assembly code that is the translation of the given
        command, where command is either C_PUSH or C_POP.

        Args:
            command (str): "C_PUSH" or "C_POP".
            segment (str): the memory segment to operate on.
            index (int): the index in the memory segment.
        """
        lines = list()
        self._get_data_address(segment, index, lines)
        if command == "C_PUSH":
            CodeWriter._write_case_push(lines, segment)
        else:
            CodeWriter._write_case_pop(lines, segment)
        self._write_to_stream(lines)

    # HELP METHODS:

    @staticmethod
    def _pop_stack_and_decrement_stack_pointer(lines):
        """Pops stack to D (sets D to the data in the last stack address) and
        decrements the stack pointer (SP) by one."""
        lines.extend(["@SP",
                      "AM=M-1",
                      "D=M"])

    @staticmethod
    def _get_last_stack_address(lines):
        """Sets A to be the last occupied stack address."""
        lines.extend(["@SP",
                      "A=M-1"])

    def _check_first_positive_second_negative(self, command, lines):
        """Checks if the first number to compare is positive and the second is
        negative."""
        # R15 is already in D.
        lines.extend(["@CONTINUE1_{}.{}".format(self.label_num,
                                                self.filename),
                      "D;JGT",
                      "@R14",
                      "D=M",
                      "@CONTINUE1_{}.{}".format(self.label_num,
                                                self.filename),
                      "D;JLT"])
        CodeWriter._get_last_stack_address(lines)
        if command == "lt":
            lines.append("M=-1")
        else:
            lines.append("M=0")
        lines.extend(["@CONTINUE3_{}.{}".format(self.label_num,
                                                self.filename),
                      "0;JMP",
                      "(CONTINUE1_{}.{})".format(self.label_num,
                                                 self.filename)])

    def _check_first_negative_second_positive(self, command, lines):
        """Checks if the first number to compare is negative and the second is
        positive."""
        lines.extend(["@R15",
                      "D=M",
                      "@CONTINUE2_{}.{}".format(self.label_num,
                                                self.filename),
                      "D;JLT",
                      "@R14",
                      "D=M",
                      "@CONTINUE2_{}.{}".format(self.label_num,
                                                self.filename),
                      "D;JGT"])
        CodeWriter._get_last_stack_address(lines)
        if command == "lt":
            lines.append("M=0")
        else:
            lines.append("M=-1")
        lines.extend(["@CONTINUE3_{}.{}".format(self.label_num,
                                                self.filename),
                      "0;JMP",
                      "(CONTINUE2_{}.{})".format(self.label_num,
                                                 self.filename)])

    def _compare_for_same_sign(self, command, lines):
        """Compares two numbers if they have the same sign."""
        # R15 is already in D.
        lines.extend(["@R14",
                      "D=D-M",
                      "@TRUE{}.{}".format(self.label_num, self.filename),
                      "D;{}".format(ARITHMETIC_TRANSLATE[command])])
        CodeWriter._get_last_stack_address(lines)
        lines.extend(["M=0",
                      "@CONTINUE3_{}.{}".format(self.label_num, self.filename),
                      "0;JMP",
                      "(TRUE{}.{})".format(self.label_num, self.filename)])
        CodeWriter._get_last_stack_address(lines)
        lines.extend(["M=-1",
                      "(CONTINUE3_{}.{})".format(self.label_num,
                                                 self.filename)])

    def _write_arithmetic_case_comparison(self, command, lines):
        """The helper method for the write_arithmetic method for the case that
        the current command is a comparison binary command."""
        lines.extend(["@R14",
                      "M=D"])
        CodeWriter._get_last_stack_address(lines)
        lines.extend(["D=M",
                      "@R15",
                      "M=D"])
        if command != "eq":
            self._check_first_positive_second_negative(command, lines)
            self._check_first_negative_second_positive(command, lines)
            lines.extend(["@R15",
                          "D=M"])
        self._compare_for_same_sign(command, lines)
        self.label_num += 1

    def _write_arithmetic_case_binary(self, command, lines):
        """The helper method for the write_arithmetic method for the case that
        the current command is a binary command."""
        CodeWriter._pop_stack_and_decrement_stack_pointer(lines)
        if command in NON_COMPARISON_BINARY:
            lines.extend(["A=A-1",
                          "M=M{}D".format(ARITHMETIC_TRANSLATE[command])])
        else:
            self._write_arithmetic_case_comparison(command, lines)

    def _get_data_address(self, segment, index, lines):
        """The helper method for the write_push_pop method. Sets D to be the
        address of the segment data (in case of the constant segment, D
        contains the data itself)."""
        if segment == "constant":
            lines.append("@{}".format(index))
        elif segment == "static":
            lines.extend(["@{}.{}".format(self.filename, str(index))])
        elif segment == "pointer" or segment == "temp":
            lines.append("@{}".format(SEGMENTS[segment] + index))
        else:
            lines.extend(["@{}".format(index),
                          "D=A",
                          "@{}".format(SEGMENTS[segment]),
                          "A=D+M"])
        lines.append("D=A")

    @staticmethod
    def _write_case_push(lines, segment):
        """The helper method for the write_push_pop method in case of a push
        operation."""
        if segment != "constant":
            lines[-1] = "D=M"  # Set D to be the data itself.
        lines.extend(["@SP",
                      "A=M",
                      "M=D",
                      "@SP",
                      "M=M+1"])

    @staticmethod
    def _write_case_pop(lines, segment):
        """The helper method for the write_push_pop method in case of a pop
        operation."""
        assert segment != "constant"
        lines.extend(["@R13",
                      "M=D"])
        CodeWriter._pop_stack_and_decrement_stack_pointer(lines)
        lines.extend(["@R13",
                      "A=M",
                      "M=D"])

    def _write_to_stream(self, lines):
        """Writes every line in the lines sequence to the output stream."""
        for line in lines:
            self.output_stream.write(line + "\n")
