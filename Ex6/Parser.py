"""This file is part of nand2tetris, as taught in The Hebrew University,
and was written by Aviv Yaish according to the specifications given in  
https://www.nand2tetris.org (Shimon Schocken and Noam Nisan, 2017)
and as allowed by the Creative Common Attribution-NonCommercial-ShareAlike 3.0 
Unported License (https://creativecommons.org/licenses/by-nc-sa/3.0/).
"""
import re
import typing

A_COMMAND = "A_COMMAND"
C_COMMAND = "C_COMMAND"
L_COMMAND = "L_COMMAND"


class Parser:
    """Encapsulates access to the input code. Reads and assembly language 
    command, parses it, and provides convenient access to the commands 
    components (fields and symbols). In addition, removes all white space and 
    comments.
    """

    def __init__(self, input_file: typing.TextIO) -> None:
        """Opens the input file and gets ready to parse it.

        Args:
            input_file (typing.TextIO): input file.
        """
        input_lines = input_file.read().splitlines()
        for i in range(0, len(input_lines)):
            # Remove white spaces and tabs:
            input_lines[i] = "".join(input_lines[i].split())
            input_lines[i] = "".join(input_lines[i].split("\t"))
            # Remove comments:
            input_lines[i] = input_lines[i].split("//")[0]
            input_lines[i] = input_lines[i].split("/**")[0]
            input_lines[i] = input_lines[i].split("*")[0]
        # Remove blank lines:
        self.__input = [line for line in input_lines if line]
        # Set the first command to read to be the first line in the input:
        self.__current_command = 0

    def has_more_commands(self) -> bool:
        """Are there more commands in the input?

        Returns:
            bool: True if there are more commands, False otherwise.
        """
        return self.__current_command <= (len(self.__input) - 1)

    def advance(self) -> None:
        """Reads the next command from the input and makes it the current
        command. Should be called only if has_more_commands() is true.
        """
        if self.has_more_commands():
            self.__current_command += 1

    def command_type(self) -> str:
        """
        Returns:
            str: the type of the current command:
            "A_COMMAND" for @Xxx where Xxx is either a symbol or a decimal
            number
            "C_COMMAND" for dest=comp;jump
            "L_COMMAND" (actually, pseudo-command) for (Xxx) where Xxx is a
            symbol
        """
        current_command = self.__input[self.__current_command]
        if current_command[0] == "@":
            return A_COMMAND
        elif current_command[0] == "(" and current_command[-1] == ")":
            return L_COMMAND
        return C_COMMAND

    def symbol(self) -> str:
        """
        Returns:
            str: the symbol or decimal Xxx of the current command @Xxx or
            (Xxx). Should be called only when command_type() is "A_COMMAND" or 
            "L_COMMAND".
        """
        command_type = self.command_type()
        assert command_type == A_COMMAND or command_type == L_COMMAND
        current_command = self.__input[self.__current_command]
        if command_type == A_COMMAND:
            return current_command[1:]
        return current_command[1:-1]

    def dest(self) -> str:
        """
        Returns:
            str: the dest mnemonic in the current C-command. Should be called 
            only when commandType() is "C_COMMAND".
        """
        assert self.command_type() == C_COMMAND
        current_command = self.__input[self.__current_command]
        if "=" in current_command:
            return current_command.split("=")[0]
        return ""

    def comp(self) -> str:
        """
        Returns:
            str: the comp mnemonic in the current C-command. Should be called 
            only when commandType() is "C_COMMAND".
        """
        assert self.command_type() == C_COMMAND
        current_command = self.__input[self.__current_command]
        if "=" in current_command:
            current_command = current_command.split("=")[1]
        if ";" in current_command:
            current_command = current_command.split(";")[0]
        return current_command

    def jump(self) -> str:
        """
        Returns:
            str: the jump mnemonic in the current C-command. Should be called 
            only when commandType() is "C_COMMAND".
        """
        assert self.command_type() == C_COMMAND
        current_command = self.__input[self.__current_command]
        if ";" in current_command:
            return current_command.split(";")[1]
        return ""

    def is_shift_operation(self) -> bool:
        """
        Returns: True if the current operation is a shift operation, false
        otherwise.
        """
        current_command = self.__input[self.__current_command]
        return ">>" in current_command or "<<" in current_command

    def set_to_zero(self):
        """Sets the counter of the current command to zero."""
        self.__current_command = 0
