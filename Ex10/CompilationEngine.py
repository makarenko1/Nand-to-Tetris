"""This file is part of nand2tetris, as taught in The Hebrew University,
and was written by Aviv Yaish according to the specifications given in  
https://www.nand2tetris.org (Shimon Schocken and Noam Nisan, 2017)
and as allowed by the Creative Common Attribution-NonCommercial-ShareAlike 3.0 
Unported License (https://creativecommons.org/licenses/by-nc-sa/3.0/).
"""
import typing

UNARY_OPERATORS = {"-", "~", "^", "#"}
BINARY_OPERATORS = {"+", "-", "*", "/", "&amp;", "|", "&lt;", "&gt;", "="}
KEYWORD_CONSTANTS = {"true", "false", "null", "this"}


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
        self.__indent = 0
        self.__tokenizer = input_stream
        self.__output_stream = output_stream

    def _compile_type(self) -> None:
        """Compiles a type, which is either a keyword or an identifier."""
        token_type = self.__tokenizer.token_type()
        if token_type == "KEYWORD":
            self._compile_token_case_keyword()
        else:  # case identifier
            self._compile_token_case_identifier()

    def _compile_token_case_keyword(self) -> None:
        """Compiles a keyword and advances the tokenizer."""
        keyword = self.__tokenizer.keyword().lower()
        self._write_to_stream("<keyword> {} </keyword>".format(keyword))
        self.__tokenizer.advance()

    def _compile_token_case_symbol(self) -> None:
        """Compiles a keyword and advances the tokenizer."""
        symbol = self.__tokenizer.symbol()
        self._write_to_stream("<symbol> {} </symbol>".format(symbol))
        self.__tokenizer.advance()

    def _compile_token_case_identifier(self) -> None:
        """Compiles an identifier and advances the tokenizer."""
        identifier = self.__tokenizer.identifier()
        self._write_to_stream(
            "<identifier> {} </identifier>".format(identifier))
        self.__tokenizer.advance()

    def _compile_token_case_integer_constant(self) -> None:
        """Compiles an integer constant and advances the tokenizer."""
        int_val = self.__tokenizer.int_val()
        self._write_to_stream(
            "<integerConstant> {} </integerConstant>".format(str(int_val)))
        self.__tokenizer.advance()

    def _compile_token_case_string_constant(self) -> None:
        """Compiles a string constant and advances the tokenizer."""
        string_val = self.__tokenizer.string_val()
        self._write_to_stream(
            "<stringConstant> {} </stringConstant>".format(string_val))
        self.__tokenizer.advance()

    def compile_class(self) -> None:
        """Compiles a complete class."""
        self._write_to_stream("<class>")
        self.__indent += 1
        self._compile_token_case_keyword()  # compile class
        self._compile_token_case_identifier()  # compile <class_name>
        self._compile_token_case_symbol()  # compile }
        self._compile_class_variables()
        self._compile_class_methods()
        self._compile_token_case_symbol()  # compile }
        self.__indent -= 1
        self._write_to_stream("</class>")

    def _compile_class_variables(self) -> None:
        """Compiles all the class variables (zero or more)."""
        while self.__tokenizer.token_type() == "KEYWORD" and (
                self.__tokenizer.keyword() == "FIELD" or
                self.__tokenizer.keyword() == "STATIC"):
            self.compile_class_var_dec()

    def _compile_class_methods(self) -> None:
        """Compiles all the class methods (zero or more)."""
        while self.__tokenizer.token_type() != "SYMBOL" or \
                self.__tokenizer.symbol() != "}":
            self.compile_subroutine()

    def compile_class_var_dec(self) -> None:
        """Compiles a static declaration or a field declaration."""
        self._write_to_stream("<classVarDec>")
        self.__indent += 1
        self._compile_var_dec_helper()
        self.__indent -= 1
        self._write_to_stream("</classVarDec>")

    def compile_subroutine(self) -> None:
        """
        Compiles a complete method, function, or constructor.
        You can assume that classes with constructors have at least one field,
        you will understand why this is necessary in project 11.
        """
        self._write_to_stream("<subroutineDec>")
        self.__indent += 1
        # compile <constructor/function/method>
        self._compile_token_case_keyword()
        self._compile_type()  # compile return type (void/type)
        self._compile_token_case_identifier()  # compile <name>
        self._compile_token_case_symbol()  # compile (
        self.compile_parameter_list()
        self._compile_token_case_symbol()  # compile )
        self._compile_subroutine_body()
        self.__indent -= 1
        self._write_to_stream("</subroutineDec>")

    def _compile_subroutine_variables(self) -> None:
        """Compiles all the subroutine variables (zero or more)."""
        while self.__tokenizer.token_type() == "KEYWORD" and \
                self.__tokenizer.keyword() == "VAR":
            self.compile_var_dec()

    def _compile_subroutine_body(self) -> None:
        """Compiles a subroutine body."""
        self._write_to_stream("<subroutineBody>")
        self.__indent += 1
        self._compile_token_case_symbol()  # compile {
        self._compile_subroutine_variables()
        self.compile_statements()
        self._compile_token_case_symbol()  # compile }
        self.__indent -= 1
        self._write_to_stream("</subroutineBody>")

    def compile_parameter_list(self) -> None:
        """Compiles a (possibly empty) parameter list, not including the 
        enclosing "()".
        """
        self._write_to_stream("<parameterList>")
        self.__indent += 1
        first_parameter = True
        while self.__tokenizer.token_type() != "SYMBOL" or \
                self.__tokenizer.symbol() != ")":
            if not first_parameter:
                self._compile_token_case_symbol()  # compile ,
            self._compile_type()  # compile type
            self._compile_token_case_identifier()  # compile <var_name>
            first_parameter = False
        self.__indent -= 1
        self._write_to_stream("</parameterList>")

    def compile_var_dec(self) -> None:
        """Compiles a var declaration."""
        self._write_to_stream("<varDec>")
        self.__indent += 1
        self._compile_var_dec_helper()
        self.__indent -= 1
        self._write_to_stream("</varDec>")

    def _compile_var_dec_helper(self) -> None:
        """Compiles a static, a field, or a var declaration."""
        self._compile_token_case_keyword()  # compile static/field/var
        self._compile_type()  # compile type
        self._compile_token_case_identifier()  # compile <var_name>
        # Compile the remaining variable names (zero or more):
        while self.__tokenizer.token_type() != "SYMBOL" or \
                self.__tokenizer.symbol() != ";":
            self._compile_token_case_symbol()  # compile ,
            self._compile_token_case_identifier()  # compile <var_name>
        self._compile_token_case_symbol()  # compile ;

    def compile_statements(self) -> None:
        """Compiles a sequence of statements (zero or more), not including the
        enclosing "{}".
        """
        self._write_to_stream("<statements>")
        self.__indent += 1
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
        self.__indent -= 1
        self._write_to_stream("</statements>")

    def compile_let(self) -> None:
        """Compiles a let statement."""
        self._write_to_stream("<letStatement>")
        self.__indent += 1
        self._compile_token_case_keyword()  # compile let
        self._compile_token_case_identifier()  # compile <var_name>
        # If array:
        if self.__tokenizer.token_type() == "SYMBOL" and \
                self.__tokenizer.symbol() == "[":
            self._compile_case_array_entry()
        self._compile_token_case_symbol()  # compile =
        self.compile_expression()
        self._compile_token_case_symbol()  # compile ;
        self.__indent -= 1
        self._write_to_stream("</letStatement>")

    def _compile_case_array_entry(self) -> None:
        """Compiles '[expression]'."""
        self._compile_token_case_symbol()  # compile [
        self.compile_expression()
        self._compile_token_case_symbol()  # compile ]

    def compile_if(self) -> None:
        """Compiles a if statement, possibly with a trailing else clause."""
        self._write_to_stream("<ifStatement>")
        self.__indent += 1
        self._compile_if_case_if()
        # Compile an 'else' clause (if there is one):
        if self.__tokenizer.token_type() == "KEYWORD" and \
                self.__tokenizer.keyword() == "ELSE":
            self._compile_if_case_else()
        self.__indent -= 1
        self._write_to_stream("</ifStatement>")

    def _compile_if_case_if(self) -> None:
        """Compiles the 'if' clause in the ifStatement."""
        self._compile_token_case_keyword()  # compile if
        self._compile_token_case_symbol()  # compile (
        self.compile_expression()
        self._compile_token_case_symbol()  # compile )
        self._compile_token_case_symbol()  # compile {
        self.compile_statements()
        self._compile_token_case_symbol()  # compile }

    def _compile_if_case_else(self) -> None:
        """Compiles the 'else' clause in the ifStatement."""
        self._compile_token_case_keyword()  # compile_else
        self._compile_token_case_symbol()  # compile {
        self.compile_statements()
        self._compile_token_case_symbol()  # compile }

    def compile_while(self) -> None:
        """Compiles a while statement."""
        self._write_to_stream("<whileStatement>")
        self.__indent += 1
        self._compile_token_case_keyword()  # compile while
        self._compile_token_case_symbol()  # compile (
        self.compile_expression()
        self._compile_token_case_symbol()  # compile )
        self._compile_token_case_symbol()  # compile {
        self.compile_statements()
        self._compile_token_case_symbol()  # compile }
        self.__indent -= 1
        self._write_to_stream("</whileStatement>")

    def compile_do(self) -> None:
        """Compiles a do statement."""
        self._write_to_stream("<doStatement>")
        self.__indent += 1
        self._compile_token_case_keyword()  # compile do
        self._compile_token_case_identifier()  # compile <subroutine_name>
        # If the call is <class_name/var_name>.<subroutine_name>(expr._list):
        if self.__tokenizer.token_type() == "SYMBOL" and \
                self.__tokenizer.symbol() == ".":
            self._compile_token_case_symbol()  # compile .
            self._compile_token_case_identifier()  # compile <subroutine_name>
        self._compile_token_case_symbol()  # compile (
        self.compile_expression_list()
        self._compile_token_case_symbol()  # compile )
        self._compile_token_case_symbol()  # compile ;
        self.__indent -= 1
        self._write_to_stream("</doStatement>")

    def compile_return(self) -> None:
        """Compiles a return statement."""
        self._write_to_stream("<returnStatement>")
        self.__indent += 1
        self._compile_token_case_keyword()  # compile return
        # Compile an expression (if there is one):
        if self.__tokenizer.token_type() != "SYMBOL" or \
                self.__tokenizer.symbol() != ";":
            self.compile_expression()
        self._compile_token_case_symbol()  # compile ;
        self.__indent -= 1
        self._write_to_stream("</returnStatement>")

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

    def compile_expression(self) -> None:
        """Compiles an expression."""
        self._write_to_stream("<expression>")
        self.__indent += 1
        self.compile_term()
        # If the next token is a binary operator, and there are more terms,
        # continue compiling:
        while self.__tokenizer.token_type() == "SYMBOL" and \
                self.__tokenizer.symbol() in BINARY_OPERATORS and \
                self._is_next_token_term():
            self._compile_token_case_symbol()  # compile operator
            self.compile_term()
        self.__indent -= 1
        self._write_to_stream("</expression>")

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
        self._write_to_stream("<term>")
        self.__indent += 1
        token_type = self.__tokenizer.token_type()
        # integerConstant or stringConstant or keyWordConstant:
        if token_type == "INT_CONST":
            self._compile_token_case_integer_constant()
        elif token_type == "STRING_CONST":
            self._compile_token_case_string_constant()
        elif token_type == "KEYWORD" and self.__tokenizer.keyword().lower() in \
                KEYWORD_CONSTANTS:
            self._compile_token_case_keyword()
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
        self.__indent -= 1
        self._write_to_stream("</term>")

    def _compile_term_case_parenthesis_expression(self) -> None:
        """Compiles the parenthesis expression term."""
        self._compile_token_case_symbol()  # compile (
        self.compile_expression()
        self._compile_token_case_symbol()  # compile )

    def _compile_term_case_unary(self) -> None:
        """Compiles the unary operation term."""
        self._compile_token_case_symbol()  # compile operator
        self.compile_term()

    def _compile_term_case_identifier(self) -> None:
        """Compiles the three cases of an identifier term: <var_name> or
        <var_name>[expression] or subroutineCall."""
        self._compile_token_case_identifier()
        if self.__tokenizer.token_type() == "SYMBOL" and \
                self.__tokenizer.symbol() == "[":
            self._compile_case_array_entry()
        elif self.__tokenizer.token_type() == "SYMBOL" and \
                self.__tokenizer.symbol() == "(":
            self._compile_subroutine_call_first()
        elif self.__tokenizer.token_type() == "SYMBOL" and \
                self.__tokenizer.symbol() == ".":
            self._compile_subroutine_call_second()

    def _compile_subroutine_call_first(self) -> None:
        """Compiles (expression_list) for the <subroutine_name>(expression_list)
        subroutine call."""
        self._compile_token_case_symbol()  # compile (
        self.compile_expression_list()
        self._compile_token_case_symbol()  # compile )

    def _compile_subroutine_call_second(self) -> None:
        """Compiles .<subroutine_name>(expression_list) for the
        <class_name>/<var_name>.<subroutine_name>(expression_list) subroutine
        call."""
        self._compile_token_case_symbol()  # compile .
        self._compile_token_case_identifier()  # compile <subroutine_name>
        self._compile_subroutine_call_first()

    def compile_expression_list(self) -> None:
        """Compiles a (possibly empty) comma-separated list of expressions."""
        self._write_to_stream("<expressionList>")
        self.__indent += 1
        first_expression = True
        while self.__tokenizer.token_type() != "SYMBOL" or \
                self.__tokenizer.symbol() != ")":
            if not first_expression:
                self._compile_token_case_symbol()  # compile ,
            self.compile_expression()
            first_expression = False
        self.__indent -= 1
        self._write_to_stream("</expressionList>")

    def _write_to_stream(self, line: str) -> None:
        """Writes the given line to the output stream."""
        self.__output_stream.write("  " * self.__indent + line + "\n")
