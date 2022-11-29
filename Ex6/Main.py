"""This file is part of nand2tetris, as taught in The Hebrew University,
and was written by Aviv Yaish according to the specifications given in  
https://www.nand2tetris.org (Shimon Schocken and Noam Nisan, 2017)
and as allowed by the Creative Common Attribution-NonCommercial-ShareAlike 3.0 
Unported License (https://creativecommons.org/licenses/by-nc-sa/3.0/).
"""
import os
import sys
import typing
from SymbolTable import SymbolTable
from Parser import Parser
from Code import Code

from Parser import A_COMMAND, C_COMMAND, L_COMMAND

FIRST_FREE_RAM_ADDRESS = 16


def assemble_file_first_pass(parser: Parser,
                             symbol_table: SymbolTable) -> None:
    """Passes the assembly program in the first time as is explained in the
    assemble_file function.

    Args:
        parser (Parser): the parser object.
        symbol_table (SymbolTable): the table of the form symbol->value.
    """
    rom_address = 0
    while parser.has_more_commands():
        if parser.command_type() == L_COMMAND:
            symbol = parser.symbol()
            symbol_table.add_entry(symbol, rom_address)
        else:
            rom_address += 1
        parser.advance()


def write_a_command(parser: Parser, symbol_table: SymbolTable,
                    ram_address: int, output_file: typing.TextIO) -> int:
    """Writes the A-Command string into the output file based on the current
    command that is an A-Command.

    Args:
        parser (Parser): the parser object.
        symbol_table (SymbolTable): the table of the form symbol->value.
        ram_address (int): the current first free RAM address.
        output_file (typing.TextIO): the file to write to.

    Returns:
          the updated first free RAM address.
    """
    string_to_write = "0"
    symbol = parser.symbol()
    if symbol.isnumeric():
        string_to_write += str("{0:015b}".format(int(symbol)))
    elif symbol_table.contains(symbol):
        string_to_write += str("{0:015b}".format(symbol_table.get_address(
            symbol)))
    else:
        symbol_table.add_entry(symbol, ram_address)
        string_to_write += str("{0:015b}".format(ram_address))
        ram_address += 1
    output_file.write(string_to_write + "\n")
    parser.advance()
    return ram_address


def write_c_command(parser: Parser, output_file: typing.TextIO) ->\
        None:
    """Writes the C-Command string into the output file based on the current
    command that is an A-Command.

    Args:
        parser (Parser): the parser object.
        output_file (typing.TextIO): the file to write to.

    """
    if parser.is_shift_operation():
        string_to_write = "101"
    else:
        string_to_write = "111"
    string_to_write += Code.comp(parser.comp())
    string_to_write += Code.dest(parser.dest())
    string_to_write += Code.jump(parser.jump())
    output_file.write(string_to_write + "\n")
    parser.advance()


def assemble_file_second_pass(parser: Parser,
                              symbol_table: SymbolTable,
                              output_file: typing.TextIO) -> None:
    """Passes the assembly program in the second time as is explained in the
    assemble_file function.

    Args:
        parser (Parser): the parser object.
        symbol_table (SymbolTable): the table of the form symbol->value.
        output_file (typing.TextIO): the file to write to.
    """
    ram_address = FIRST_FREE_RAM_ADDRESS
    while parser.has_more_commands():
        if parser.command_type() == A_COMMAND:
            ram_address = write_a_command(parser, symbol_table, ram_address,
                                          output_file)
        elif parser.command_type() == C_COMMAND:
            write_c_command(parser, output_file)
        else:  # case L-Command (label declaration)
            parser.advance()
            continue


def assemble_file(input_file: typing.TextIO, output_file: typing.TextIO) -> \
        None:
    """Assembles a single file.

    Args:
        input_file (typing.TextIO): the file to assemble.
        output_file (typing.TextIO): writes all output to this file.
    """
    # Your code goes here!
    #
    # You should use the two-pass implementation suggested in the book:
    #
    # *Initialization*
    # Initialize the symbol table with all the predefined symbols and their
    # pre-allocated RAM addresses, according to section 6.2.3 of the book.
    #
    # *First Pass*
    # Go through the entire assembly program, line by line, and build the
    # symbol table without generating any code. As you march through the
    # program lines, keep a running number recording the ROM address into
    # which the current command will be eventually loaded.
    # This number starts at 0 and is incremented by 1 whenever a C-instruction
    # or an A-instruction is encountered, but does not change when a label
    # pseudo-command or a comment is encountered. Each time a pseudo-command
    # (Xxx) is encountered, add a new entry to the symbol table, associating
    # Xxx with the ROM address that will eventually store the next command in
    # the program. This pass results in entering all the programs labels
    # along with their ROM addresses into the symbol table. The programs
    # variables are handled in the second pass.
    #
    # *Second Pass*
    # Now go again through the entire program, and parse each line.
    # Each time a symbolic A-instruction is encountered, namely, @Xxx where Xxx
    # is a symbol and not a number, look up Xxx in the symbol table.
    # If the symbol is found in the table, replace it with its numeric meaning
    # and complete the commands translation.
    # If the symbol is not found in the table, then it must represent a new
    # variable. To handle it, add the pair (Xxx,n) to the symbol table, where n
    # is the next available RAM address, and complete the commands translation.
    # The allocated RAM addresses are consecutive numbers, starting at address
    # 16 (just after the addresses allocated to the predefined symbols).
    # After the command is translated, write the translation to the output
    # file.
    symbol_table = SymbolTable()  # create a symbol table object
    parser = Parser(input_file)  # create a parser object
    assemble_file_first_pass(parser, symbol_table)
    parser.set_to_zero()
    assemble_file_second_pass(parser, symbol_table, output_file)


if "__main__" == __name__:
    # Parses the input path and calls assemble_file on each input file.
    # This opens both the input and the output files!
    # Both are closed automatically when the code finishes running.
    # If the output file does not exist, it is created automatically in the
    # correct path, using the correct filename.
    if not len(sys.argv) == 2:
        sys.exit("Invalid usage, please use: Assembler <input path>")
    argument_path = os.path.abspath(sys.argv[1])
    if os.path.isdir(argument_path):
        files_to_assemble = [
            os.path.join(argument_path, filename)
            for filename in os.listdir(argument_path)]
    else:
        files_to_assemble = [argument_path]
    for input_path in files_to_assemble:
        filename, extension = os.path.splitext(input_path)
        if extension.lower() != ".asm":
            continue
        output_path = filename + ".hack"
        with open(input_path, 'r') as input_file, \
                open(output_path, 'w') as output_file:
            assemble_file(input_file, output_file)
