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
PRE_UNARY = ["neg", "not"]
POST_UNARY = ["shiftleft", "shiftright"]
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
        self.__output_stream = output_stream
        self.__filename = ""
        self.__current_function = ""
        self.__return_label_num = 0
        self.__comparison_label_num = 0

    def set_file_name(self, filename: str) -> None:
        """Informs the code writer that the translation of a new VM file is
        started.

        Args:
            filename (str): The name of the VM file.
        """
        self.__filename = filename

    def write_init(self) -> None:
        """Writes the assembly instructions that effect the bootstrap code that
        initializes the VM. This code must be placed at the beginning of the
        generated *.asm file."""
        lines = ["@{}".format(STACK_START),  # set the stack SM pointer.
                 "D=A",
                 "@SP",
                 "M=D"]
        self._write_to_stream(lines)
        self.write_call("Sys.init", 0)  # call Sys.init with 0 args.

    def write_arithmetic(self, command: str) -> None:
        """Writes the assembly code that is the translation of the given
        arithmetic command.

        Args:
            command (str): an arithmetic command.
        """
        lines = list()
        if command in PRE_UNARY:
            CodeWriter._get_last_stack_address(lines)
            lines.append("M={}M".format(ARITHMETIC_TRANSLATE[command]))
        elif command in POST_UNARY:
            CodeWriter._get_last_stack_address(lines)
            lines.append("M=M{}".format(ARITHMETIC_TRANSLATE[command]))
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

    def write_label(self, label: str) -> None:
        """Writes the assembly code that effects the label command.

        Args:
            label (str): the label to create.
        """
        self._write_to_stream(["({}${})".format(self.__current_function,
                                                label)])

    def write_goto(self, label: str) -> None:
        """Writes the assembly code that effects the goto command.

        Args:
            label (str): the label to go to.
        """
        lines = ["@{}${}".format(self.__current_function, label),
                 "0;JMP"]
        self._write_to_stream(lines)

    def write_if(self, label: str) -> None:
        """Writes the assembly code that effects the if-goto command.

        Args:
            label (str): the label to go to if the top value on the
            stack is True.
        """
        lines = list()
        self._pop_stack_and_decrement_stack_pointer(lines)
        lines.extend(["@{}${}".format(self.__current_function, label),
                      "D;JNE"])
        self._write_to_stream(lines)

    def write_function(self, function_name: str, num_vars: int) -> None:
        """Writes the assembly code that effects the function command.

        Args:
            function_name (str): the name of the function to implement.
            num_vars (int): the number of variables the function has.
        """
        self.__current_function = function_name
        lines = ["({})".format(function_name)]
        for i in range(num_vars):  # repeat nVars times: push 0.
            lines.append("@0")
            CodeWriter._write_case_push(lines, "constant")
        self._write_to_stream(lines)

    def write_call(self, function_name: str, num_args: int) -> None:
        """Writes the assembly code that effects the call command.

        Args:
            function_name (str): the name of the function to call.
            num_args (int): the number of arguments the function needs.
        """
        i = self.__return_label_num
        self.__return_label_num += 1
        lines = ["@{}$ret.{}".format(function_name, i)]  # push return address.
        self._write_case_push(lines, "constant")
        lines.extend(["@LCL"])  # push LCL.
        self._write_case_push(lines, "local")
        lines.extend(["@ARG"])  # push ARG.
        self._write_case_push(lines, "argument")
        lines.extend(["@THIS"])  # push THIS.
        self._write_case_push(lines, "this")
        lines.extend(["@THAT"])  # push THAT.
        self._write_case_push(lines, "that")
        lines.extend(["@SP",  # LCL = SP.
                      "D=M",
                      "@LCL",
                      "M=D",
                      "@{}".format(num_args + 5),  # ARG = SP-5-nArgs.
                      "D=D-A",  # SP is already in D.
                      "@ARG",
                      "M=D",
                      "@{}".format(function_name),  # goto f.
                      "0;JMP",
                      "({}$ret.{})".format(function_name, i)])
        self._write_to_stream(lines)

    def write_return(self) -> None:
        """Writes the assembly code that effects the return command."""
        lines = ["@LCL",  # frame = LCL (store into R14).
                 "D=M",
                 "@R14",
                 "M=D",
                 "@5",  # retAddr = *(frame-5) (store into R15).
                 "A=D-A",
                 "D=M",
                 "@R15",
                 "M=D",
                 "@ARG",  # *ARG = pop().
                 "A=M"]
        self._write_case_pop(lines, "argument")
        lines.extend(["@ARG",  # SP = ARG+1.
                      "D=M+1",
                      "@SP",
                      "M=D"])
        to_restore = ["@THAT", "@THIS", "@ARG", "@LCL"]
        for address in to_restore:  # restore THAT, THIS, ARG, LCL.
            lines.extend(["@R14",
                          "AM=M-1",
                          "D=M",
                          address,
                          "M=D"])
        lines.extend(["@R15",  # goto retAddr.
                      "A=M",
                      "0;JMP"])
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
        lines.extend(["@CONTINUE1_{}".format(self.__comparison_label_num),
                      "D;JGT",
                      "@R14",
                      "D=M",
                      "@CONTINUE1_{}".format(self.__comparison_label_num),
                      "D;JLT"])
        CodeWriter._get_last_stack_address(lines)
        if command == "lt":
            lines.append("M=-1")
        else:
            lines.append("M=0")
        lines.extend(["@CONTINUE3_{}".format(self.__comparison_label_num),
                      "0;JMP",
                      "(CONTINUE1_{})".format(self.__comparison_label_num)])

    def _check_first_negative_second_positive(self, command, lines):
        """Checks if the first number to compare is negative and the second is
        positive."""
        lines.extend(["@R15",
                      "D=M",
                      "@CONTINUE2_{}".format(self.__comparison_label_num),
                      "D;JLT",
                      "@R14",
                      "D=M",
                      "@CONTINUE2_{}".format(self.__comparison_label_num),
                      "D;JGT"])
        CodeWriter._get_last_stack_address(lines)
        if command == "lt":
            lines.append("M=0")
        else:
            lines.append("M=-1")
        lines.extend(["@CONTINUE3_{}".format(self.__comparison_label_num),
                      "0;JMP",
                      "(CONTINUE2_{})".format(self.__comparison_label_num)])

    def _compare_for_same_sign(self, command, lines):
        """Compares two numbers if they have the same sign."""
        # R15 is already in D.
        lines.extend(["@R14",
                      "D=D-M",
                      "@TRUE_{}".format(self.__comparison_label_num),
                      "D;{}".format(ARITHMETIC_TRANSLATE[command])])
        CodeWriter._get_last_stack_address(lines)
        lines.extend(["M=0",
                      "@CONTINUE3_{}".format(self.__comparison_label_num),
                      "0;JMP",
                      "(TRUE_{})".format(self.__comparison_label_num)])
        CodeWriter._get_last_stack_address(lines)
        lines.extend(["M=-1",
                      "(CONTINUE3_{})".format(self.__comparison_label_num)])

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
        self.__comparison_label_num += 1

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
            lines.extend(["@{}.{}".format(self.__filename, str(index))])
        elif segment == "pointer" or segment == "temp":
            lines.append("@{}".format(SEGMENTS[segment] + index))
        else:
            lines.extend(["@{}".format(index),
                          "D=A",
                          "@{}".format(SEGMENTS[segment]),
                          "A=D+M"])

    @staticmethod
    def _write_case_push(lines, segment):
        """The helper method for the write_push_pop method in case of a push
        operation."""
        if segment != "constant":
            lines.append("D=M")  # Set D to be the data itself.
        else:
            lines.append("D=A")
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
        lines.extend(["D=A",
                      "@R13",
                      "M=D"])
        CodeWriter._pop_stack_and_decrement_stack_pointer(lines)
        lines.extend(["@R13",
                      "A=M",
                      "M=D"])

    def _write_to_stream(self, lines):
        """Writes every line in the lines sequence to the output stream."""
        for line in lines:
            self.__output_stream.write(line + "\n")
