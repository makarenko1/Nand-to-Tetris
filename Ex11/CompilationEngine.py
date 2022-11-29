"""This file is part of nand2tetris, as taught in The Hebrew University,
and was written by Aviv Yaish according to the specifications given in  
https://www.nand2tetris.org (Shimon Schocken and Noam Nisan, 2017)
and as allowed by the Creative Common Attribution-NonCommercial-ShareAlike 3.0 
Unported License (https://creativecommons.org/licenses/by-nc-sa/3.0/).
"""
import typing
from SymbolTable import SymbolTable
from VMWriter import VMWriter

UNARY_OPERATORS = {"-": "NEG", "~": "NOT", "^": "SHIFTLEFT", "#": "SHIFTRIGHT"}
BINARY_OPERATORS = {"+": "ADD", "-": "SUB", "*": "", "/": "", "&": "AND",
                    "|": "OR", "<": "LT", ">": "GT", "=": "EQ"}
KEYWORD_CONSTANTS = {"true": "CONST", "false": "CONST", "null": "CONST",
                     "this": "POINTER"}

SEGMENT_BY_KIND = {"STATIC": "STATIC", "FIELD": "THIS", "ARG": "ARG",
                   "VAR": "LOCAL"}


class CompilationEngine:
    """Gets input from a JackTokenizer and emits its parsed structure into an
    output stream.
    """

    def __init__(self, input_stream: "JackTokenizer", output_stream) -> None:
        """
        Creates a new compilation engine with the given input and output. The
        next routine called must be compileClass()
        :param input_stream: The input stream.
        :param output_stream: The output stream.
        """
        self.__tokenizer = input_stream
        self.__symbol_table = SymbolTable()
        self.__vm_writer = VMWriter(output_stream)
        self.__if_label_num = 0
        self.__while_label_num = 0

    def _compile_type(self) -> str:
        """Compiles a type, which is either a keyword or an identifier."""
        token_type = self.__tokenizer.token_type()
        if token_type == "KEYWORD":
            return self._compile_token_case_keyword()
        return self._compile_token_case_identifier()

    def _compile_token_case_keyword(self) -> str:
        """Compiles a keyword and advances the tokenizer."""
        keyword = self.__tokenizer.keyword().lower()
        self.__tokenizer.advance()
        return keyword

    def _compile_token_case_symbol(self) -> str:
        """Compiles a keyword and advances the tokenizer."""
        symbol = self.__tokenizer.symbol()
        self.__tokenizer.advance()
        return symbol

    def _compile_token_case_identifier(self) -> str:
        """Compiles an identifier and advances the tokenizer."""
        identifier = self.__tokenizer.identifier()
        self.__tokenizer.advance()
        return identifier

    def _compile_token_case_integer_constant(self) -> int:
        """Compiles an integer constant and advances the tokenizer."""
        int_val = self.__tokenizer.int_val()
        self.__tokenizer.advance()
        return int_val

    def _compile_token_case_string_constant(self) -> str:
        """Compiles a string constant and advances the tokenizer."""
        string_val = self.__tokenizer.string_val()
        self.__tokenizer.advance()
        return string_val

    def _get_if_labels(self) -> typing.Tuple[str, str]:
        """Returns the if labels."""
        label_if_false = "IF_FALSE{}".format(self.__if_label_num)
        label_if_end = "IF_END{}".format(self.__if_label_num)
        self.__if_label_num += 1
        return label_if_false, label_if_end

    def _get_while_labels(self) -> typing.Tuple[str, str]:
        """Returns the while labels."""
        label_while_exp = "WHILE_EXP{}".format(self.__while_label_num)
        label_while_end = "WHILE_END{}".format(self.__while_label_num)
        self.__while_label_num += 1
        return label_while_exp, label_while_end

    def compile_class(self) -> None:
        """Compiles a complete class."""
        self.__tokenizer.advance()  # compile class
        class_name = self._compile_token_case_identifier()  # <class_name>
        self.__symbol_table.write_class_name(class_name)
        self.__tokenizer.advance()  # compile {
        self._compile_class_variables()
        self._compile_class_methods(class_name)
        self.__tokenizer.advance()  # compile }

    def _compile_class_variables(self) -> None:
        """Compiles all the class variables (zero or more)."""
        while self.__tokenizer.token_type() == "KEYWORD" and (
                self.__tokenizer.keyword() == "FIELD" or
                self.__tokenizer.keyword() == "STATIC"):
            self.compile_class_var_dec()

    def _compile_class_methods(self, class_name: str) -> None:
        """Compiles all the class methods (zero or more)."""
        while self.__tokenizer.token_type() != "SYMBOL" or \
                self.__tokenizer.symbol() != "}":
            self.compile_subroutine(class_name)

    def compile_class_var_dec(self) -> None:
        """Compiles a static declaration or a field declaration."""
        self.compile_var_dec()

    def compile_subroutine(self, class_name: typing.Optional[str] = None) -> \
            None:
        """
        Compiles a complete method, function, or constructor.
        You can assume that classes with constructors have at least one field,
        you will understand why this is necessary in project 11.
        """
        self.__symbol_table.start_subroutine()
        # compile <constructor/function/method>
        type_keyword = self._compile_token_case_keyword()
        if type_keyword == "method":
            self.__symbol_table.define("this", class_name, "ARG")
        self._compile_type()  # compile return type
        name = self._compile_token_case_identifier()  # compile <name>
        if class_name is not None:
            name = "{}.{}".format(class_name, name)
        self.__tokenizer.advance()  # compile (
        self.compile_parameter_list()
        self.__tokenizer.advance()  # compile )
        self._compile_subroutine_body(type_keyword, name)

    def _compile_subroutine_variables(self) -> None:
        """Compiles all the subroutine variables (zero or more)."""
        while self.__tokenizer.token_type() == "KEYWORD" and \
                self.__tokenizer.keyword() == "VAR":
            self.compile_var_dec()

    def _compile_subroutine_body(self, type_keyword: str, name: str) -> None:
        """Compiles a subroutine body."""
        self.__tokenizer.advance()  # compile {
        self._compile_subroutine_variables()
        n_locals = self.__symbol_table.var_count("VAR")
        self.__vm_writer.write_function(name, n_locals)
        if type_keyword == "constructor":
            index = self.__symbol_table.var_count("FIELD")
            self.__vm_writer.write_push("CONST", index)
            self.__vm_writer.write_call("Memory.alloc", 1)
            self.__vm_writer.write_pop("POINTER", 0)
        elif type_keyword == "method":
            self.__vm_writer.write_push("ARG", 0)
            self.__vm_writer.write_pop("POINTER", 0)
        self.compile_statements()
        self.__tokenizer.advance()  # compile }

    def compile_parameter_list(self) -> None:
        """Compiles a (possibly empty) parameter list, not including the 
        enclosing "()".
        """
        first_parameter = True
        while self.__tokenizer.token_type() != "SYMBOL" or \
                self.__tokenizer.symbol() != ")":
            if not first_parameter:
                self.__tokenizer.advance()  # compile ,
            type_str = self._compile_type()  # compile type
            name = self._compile_token_case_identifier()  # compile <var_name>
            self.__symbol_table.define(name, type_str, "ARG")
            first_parameter = False

    def compile_var_dec(self) -> None:
        """Compiles a var declaration."""
        kind = self._compile_token_case_keyword().upper()  # static/field/var
        type_str = self._compile_type()  # compile type
        name = self._compile_token_case_identifier()  # compile <var_name>
        self.__symbol_table.define(name, type_str, kind)
        # Compile the remaining variable names (zero or more):
        while self.__tokenizer.token_type() != "SYMBOL" or \
                self.__tokenizer.symbol() != ";":
            self.__tokenizer.advance()  # compile ,
            name = self._compile_token_case_identifier()  # compile <var_name>
            self.__symbol_table.define(name, type_str, kind)
        self.__tokenizer.advance()  # compile ;

    def compile_statements(self) -> None:
        """Compiles a sequence of statements (zero or more), not including the
        enclosing "{}".
        """
        while self.__tokenizer.token_type() != "SYMBOL" or \
                self.__tokenizer.symbol() != "}":
            if self.__tokenizer.keyword() == "LET":
                self.compile_let()
            elif self.__tokenizer.keyword() == "IF":
                self.compile_if()
            elif self.__tokenizer.keyword() == "WHILE":
                self.compile_while()
            elif self.__tokenizer.keyword() == "DO":
                self.compile_do()
            else:
                self.compile_return()

    def compile_let(self) -> None:
        """Compiles a let statement."""
        self.__tokenizer.advance()  # compile let
        name = self._compile_token_case_identifier()  # compile <var_name>
        segment = SEGMENT_BY_KIND[self.__symbol_table.kind_of(name)]
        index = self.__symbol_table.index_of(name)
        # If array:
        if self.__tokenizer.token_type() == "SYMBOL" and \
                self.__tokenizer.symbol() == "[":
            self._compile_let_case_array_entry(segment, index)
        else:
            self.__tokenizer.advance()  # compile =
            self.compile_expression()
            self.__vm_writer.write_pop(segment, index)
        self.__tokenizer.advance()  # compile ;

    def _compile_let_case_array_entry(self, segment: str, index: int) -> None:
        """Compiles '[expression]=expression'."""
        self.__tokenizer.advance()  # compile [
        self.compile_expression()
        self.__tokenizer.advance()  # compile ]
        self.__tokenizer.advance()  # compile =
        self.__vm_writer.write_push(segment, index)
        self.__vm_writer.write_arithmetic("ADD")
        self.compile_expression()
        self.__vm_writer.write_pop("TEMP", 0)
        self.__vm_writer.write_pop("POINTER", 1)
        self.__vm_writer.write_push("TEMP", 0)
        self.__vm_writer.write_pop("THAT", 0)

    def compile_if(self) -> None:
        """Compiles a if statement, possibly with a trailing else clause."""
        label_if_false, label_if_end = self._get_if_labels()
        self._compile_if_case_if(label_if_false, label_if_end)
        # Compile an 'else' clause (if there is one):
        if self.__tokenizer.token_type() == "KEYWORD" and \
                self.__tokenizer.keyword() == "ELSE":
            self._compile_if_case_else()
        self.__vm_writer.write_label(label_if_end)

    def _compile_if_case_if(self, label_if_false: str, label_if_end: str) -> \
            None:
        """Compiles the 'if' clause in the ifStatement."""
        self.__tokenizer.advance()  # compile if
        self.__tokenizer.advance()  # compile (
        self.compile_expression()
        self.__tokenizer.advance()  # compile )
        self.__tokenizer.advance()  # compile {
        self.__vm_writer.write_if(label_if_false)
        self.compile_statements()
        self.__vm_writer.write_goto(label_if_end)
        self.__vm_writer.write_label(label_if_false)
        self.__tokenizer.advance()  # compile }

    def _compile_if_case_else(self) -> None:
        """Compiles the 'else' clause in the ifStatement."""
        self.__tokenizer.advance()  # compile else
        self.__tokenizer.advance()  # compile {
        self.compile_statements()
        self.__tokenizer.advance()  # compile }

    def compile_while(self) -> None:
        """Compiles a while statement."""
        label_while_exp, label_while_end = self._get_while_labels()
        self.__tokenizer.advance()  # compile while
        self.__tokenizer.advance()  # compile (
        self.__vm_writer.write_label(label_while_exp)
        self.compile_expression()
        self.__tokenizer.advance()  # compile )
        self.__tokenizer.advance()  # compile {
        self.__vm_writer.write_if(label_while_end)
        self.compile_statements()
        self.__vm_writer.write_goto(label_while_exp)
        self.__vm_writer.write_label(label_while_end)
        self.__tokenizer.advance()  # compile }

    def compile_do(self) -> None:
        """Compiles a do statement."""
        self.__tokenizer.advance()  # compile do
        self.compile_term()
        self.__vm_writer.write_pop("TEMP", 0)
        self.__tokenizer.advance()  # compile ;

    def compile_return(self) -> None:
        """Compiles a return statement."""
        self.__tokenizer.advance()  # compile return
        # Compile an expression (if there is one):
        if self.__tokenizer.token_type() != "SYMBOL" or \
                self.__tokenizer.symbol() != ";":
            self.compile_expression()
        else:
            self.__vm_writer.write_push("CONST", 0)
        self.__vm_writer.write_return()
        self.__tokenizer.advance()  # compile ;

    def compile_expression(self) -> None:
        """Compiles an expression."""
        self.compile_term()
        # If the next token is a binary operator, and there are more terms,
        # continue compiling:
        while self.__tokenizer.token_type() == "SYMBOL" and \
                self.__tokenizer.symbol() in BINARY_OPERATORS and \
                self._is_next_token_term():
            operator = self._compile_token_case_symbol()  # compile operator
            self.compile_term()
            self._compile_binary_operator(operator)

    def _compile_binary_operator(self, operator) -> None:
        """Compiles a binary operator."""
        if operator == "*":
            self.__vm_writer.write_call("Math.multiply", 2)
        elif operator == "/":
            self.__vm_writer.write_call("Math.divide", 2)
        else:
            self.__vm_writer.write_arithmetic(BINARY_OPERATORS[operator])

    def _is_next_token_term(self) -> bool:
        """Returns True iff the next token is a term."""
        token_and_type = self.__tokenizer.get_next_token()
        if token_and_type is None:
            return False
        token, token_type = token_and_type
        return (token_type == "KEYWORD" and token in KEYWORD_CONSTANTS) or \
            token_type == "INT_CONST" or token_type == "STRING_CONST" or \
            token_type == "IDENTIFIER" or token == "(" or token in \
            UNARY_OPERATORS

    def compile_expression_list(self) -> int:
        """Compiles a (possibly empty) comma-separated list of expressions.
        Returns the number of expressions in the list."""
        num_expressions = 0
        first_expression = True
        while self.__tokenizer.token_type() != "SYMBOL" or \
                self.__tokenizer.symbol() != ")":
            if not first_expression:
                self.__tokenizer.advance()  # compile ,
            self.compile_expression()
            num_expressions += 1
            first_expression = False
        return num_expressions

    def compile_term(self) -> None:
        """Compiles a term. 
        This routine is faced with a slight difficulty when
        trying to decide between some of the alternative parsing rules.
        Specifically, if the current token is an identifier, the routing must
        distinguish between a variable, an array entry, and a subroutine call.
        A single look-ahead token, which may be one of "[", "(", or "." suffices
        to distinguish between the three possibilities. Any other token is not
        part of this term and should not be advanced over.
        """
        token_type = self.__tokenizer.token_type()
        # integerConstant or stringConstant or keyWordConstant:
        if token_type == "INT_CONST":
            self._compile_term_case_int_const()
        elif token_type == "STRING_CONST":
            self._compile_term_case_string_const()
        elif token_type == "KEYWORD" and self.__tokenizer.keyword().lower() in \
                KEYWORD_CONSTANTS:
            self._compile_term_case_keyword_const()
        # <var_name> or <var_name>[expression] or subroutineCall:
        elif token_type == "IDENTIFIER":
            self._compile_term_case_identifier()
        # (expression):
        elif token_type == "SYMBOL" and self.__tokenizer.symbol() == "(":
            self._compile_term_case_parenthesis_expression()
        # unary_operator term
        elif token_type == "SYMBOL" and self.__tokenizer.symbol() in \
                UNARY_OPERATORS:
            self._compile_term_case_unary()

    def _compile_term_case_int_const(self) -> None:
        """Compiles an int constant term."""
        int_const = self._compile_token_case_integer_constant()
        self.__vm_writer.write_push("CONST", int_const)

    def _compile_term_case_string_const(self) -> None:
        """Compiles a string constant term."""
        str_const = self._compile_token_case_string_constant()
        self.__vm_writer.write_push("CONST", len(str_const))
        self.__vm_writer.write_call("String.new", 1)
        for character in str_const:
            self.__vm_writer.write_push("CONST", ord(character))
            self.__vm_writer.write_call("String.appendChar", 2)

    def _compile_term_case_keyword_const(self) -> None:
        """Compiles a keyword constant term."""
        keyword_const = self._compile_token_case_keyword().lower()
        segment = KEYWORD_CONSTANTS[keyword_const]
        self.__vm_writer.write_push(segment, 0)
        if keyword_const == "true":
            self.__vm_writer.write_arithmetic("NOT")

    def _compile_term_case_parenthesis_expression(self) -> None:
        """Compiles a parenthesis expression term."""
        self.__tokenizer.advance()  # compile (
        self.compile_expression()
        self.__tokenizer.advance()  # compile )

    def _compile_term_case_unary(self) -> None:
        """Compiles an unary operation term."""
        operator = self._compile_token_case_symbol()  # compile operator
        self.compile_term()  # compile argument term.
        self.__vm_writer.write_arithmetic(UNARY_OPERATORS[operator])

    def _compile_term_case_identifier(self) -> None:
        """Compiles the three cases of an identifier term: <var_name> or
        <var_name>[expression] or subroutineCall."""
        name = self._compile_token_case_identifier()
        if self.__tokenizer.token_type() == "SYMBOL" and \
                self.__tokenizer.symbol() == "[":
            self._compile_term_case_array_entry(name)
        elif self.__tokenizer.token_type() == "SYMBOL" and \
                self.__tokenizer.symbol() == ".":
            self._compile_subroutine_call_first(name)
        elif self.__tokenizer.token_type() == "SYMBOL" and \
                self.__tokenizer.symbol() == "(":
            self._compile_subroutine_call_second(name)
        else:
            self._compile_term_case_variable(name)

    def _compile_term_case_array_entry(self, name: str) -> None:
        """Compiles '[expression]'."""
        segment = SEGMENT_BY_KIND[self.__symbol_table.kind_of(name)]
        index = self.__symbol_table.index_of(name)
        self.__tokenizer.advance()  # compile [
        self.compile_expression()
        self.__vm_writer.write_push(segment, index)
        self.__vm_writer.write_arithmetic("ADD")
        self.__vm_writer.write_pop("POINTER", 1)
        self.__vm_writer.write_push("THAT", 0)
        self.__tokenizer.advance()  # compile ]

    def _compile_subroutine_call_first(self, class_name_or_object_name: str) ->\
            None:
        """Compiles the first variation of a subroutine call."""
        self.__tokenizer.advance()  # compile .
        class_name, n_args = self._get_class_name_and_num_args(
            class_name_or_object_name)
        subroutine_name = self._compile_token_case_identifier()
        full_subroutine_name = "{}.{}".format(class_name, subroutine_name)
        self.__tokenizer.advance()  # compile (
        n_args += self.compile_expression_list()
        self.__vm_writer.write_call(full_subroutine_name, n_args)
        self.__tokenizer.advance()  # compile )

    def _get_class_name_and_num_args(self, class_name_or_object_name) -> \
            typing.Tuple[str, int]:
        """Returns a tuple of class name and initial number of arguments (1 if
        'this' was added, 0 otherwise)."""
        class_name = self.__symbol_table.type_of(class_name_or_object_name)
        if class_name is None:  # the given name is a class name.
            return class_name_or_object_name, 0
        segment = SEGMENT_BY_KIND[self.__symbol_table.kind_of(
            class_name_or_object_name)]
        index = self.__symbol_table.index_of(class_name_or_object_name)
        self.__vm_writer.write_push(segment, index)
        return class_name, 1

    def _compile_subroutine_call_second(self, subroutine_name: str) -> None:
        """Compiles the second variation of a subroutine call."""
        self.__tokenizer.advance()  # compile (
        self.__vm_writer.write_push("POINTER", 0)
        class_name = self.__symbol_table.get_class_name()
        full_subroutine_name = "{}.{}".format(class_name, subroutine_name)
        n_args = self.compile_expression_list() + 1
        self.__vm_writer.write_call(full_subroutine_name, n_args)
        self.__tokenizer.advance()  # compile )

    def _compile_term_case_variable(self, name) -> None:
        """Compiles a variable term."""
        segment = SEGMENT_BY_KIND[self.__symbol_table.kind_of(name)]
        index = self.__symbol_table.index_of(name)
        self.__vm_writer.write_push(segment, index)
