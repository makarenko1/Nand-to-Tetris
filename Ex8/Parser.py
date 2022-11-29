"""This file is part of nand2tetris, as taught in The Hebrew University,
and was written by Aviv Yaish according to the specifications given in  
https://www.nand2tetris.org (Shimon Schocken and Noam Nisan, 2017)
and as allowed by the Creative Common Attribution-NonCommercial-ShareAlike 3.0 
Unported License (https://creativecommons.org/licenses/by-nc-sa/3.0/).
"""
import typing

ARITHMETIC_COMMANDS = ["add", "sub", "neg", "eq", "gt", "lt", "and", "or",
                       "not", "shiftleft", "shiftright"]


class Parser:
    """
    Handles the parsing of a single .vm file, and encapsulates access to the
    input code. It reads VM commands, parses them, and provides convenient 
    access to their components. 
    In addition, it removes all white space and comments.
    """

    def __init__(self, input_file: typing.TextIO) -> None:
        """Gets ready to parse the input file.

        Args:
            input_file (typing.TextIO): input file.
        """
        input_lines = input_file.read().splitlines()
        for i in range(0, len(input_lines)):
            input_lines[i] = Parser._clean_line(i, input_lines)
        self.__input = [line for line in input_lines if line]
        self.__current_command = 0

    def has_more_commands(self) -> bool:
        """Are there more commands in the input?

        Returns:
            bool: True if there are more commands, False otherwise.
        """
        return self.__current_command <= (len(self.__input) - 1)

    def advance(self) -> None:
        """Reads the next command from the input and makes it the current 
        command. Should be called only if has_more_commands() is true. Initially
        there is no current command.
        """
        if self.has_more_commands():
            self.__current_command += 1

    def command_type(self) -> str:
        """
        Returns:
            str: the type of the current VM command.
            "C_ARITHMETIC" is returned for all arithmetic commands.
            For other commands, can return:
            "C_PUSH", "C_POP", "C_LABEL", "C_GOTO", "C_IF", "C_FUNCTION",
            "C_RETURN", "C_CALL".
        """
        current_command = self.__input[self.__current_command]
        if current_command in ARITHMETIC_COMMANDS:
            return "C_ARITHMETIC"
        current_command = current_command.split()[0]
        if current_command == "push":
            return "C_PUSH"
        elif current_command == "pop":
            return "C_POP"
        elif current_command == "label":
            return "C_LABEL"
        elif current_command == "goto":
            return "C_GOTO"
        elif current_command == "if-goto":
            return "C_IF"
        elif current_command == "function":
            return "C_FUNCTION"
        elif current_command == "return":
            return "C_RETURN"
        else:
            return "C_CALL"

    def arg1(self) -> str:
        """
        Returns:
            str: the first argument of the current command. In case of 
            "C_ARITHMETIC", the command itself (add, sub, etc.) is returned. 
            Should not be called if the current command is "C_RETURN".
        """
        current_command = self.__input[self.__current_command]
        if self.command_type() == "C_ARITHMETIC":
            return current_command
        return current_command.split()[1]

    def arg2(self) -> int:
        """
        Returns:
            int: the second argument of the current command. Should be
            called only if the current command is "C_PUSH", "C_POP", 
            "C_FUNCTION" or "C_CALL".
        """
        current_command = self.__input[self.__current_command]
        return int(current_command.split()[2])

    # HELP METHODS:

    @staticmethod
    def _clean_line(i, input_lines):
        """Removes all the white spaces (before and after every command), tabs
        and comments."""
        input_lines[i] = input_lines[i].strip()
        input_lines[i] = input_lines[i].strip("\t")
        input_lines[i] = input_lines[i].split("//")[0]
        input_lines[i] = input_lines[i].strip()
        return input_lines[i]
