"""This file is part of nand2tetris, as taught in The Hebrew University,
and was written by Aviv Yaish according to the specifications given in  
https://www.nand2tetris.org (Shimon Schocken and Noam Nisan, 2017)
and as allowed by the Creative Common Attribution-NonCommercial-ShareAlike 3.0 
Unported License (https://creativecommons.org/licenses/by-nc-sa/3.0/).
"""
import typing
import re

# All the possible keywords and symbols:
KEYWORDS = {"class", "constructor", "function", "method", "field", "static",
            "var", "int", "char", "boolean", "void", "true", "false", "null",
            "this", "let", "do", "if", "else", "while", "return"}
SYMBOLS = {"{", "}", "(", ")", "[", "]", ".", ",", ";", "+", "-", "*", "/",
           "&", "|", "<", ">", "=", "~", "^", "#"}

# Regex for each category:
KEYWORD_REGEX = "class|constructor|function|method|field|static|var|int|char" \
                "|boolean|void|true|false|null|this|let|do|if|else|while|return"
SYMBOL_REGEX = "{|}|\(|\)|\[|\]|\.|,|;|\+|-|\*|\/|&|\||<|>|=|~|\^|#"
INT_CONST_REGEX = "\d+"
STRING_CONST_REGEX = "\".*\""
IDENTIFIER_REGEX = "\w+"

# Regex for all the categories:
PATTERN = "({}|{}|{}|{}|{})".format(
    STRING_CONST_REGEX, IDENTIFIER_REGEX, SYMBOL_REGEX, INT_CONST_REGEX,
    KEYWORD_REGEX)


class JackTokenizer:
    """Removes all comments from the input stream and breaks it
    into Jack language tokens, as specified by the Jack grammar.
    
    An Xxx .jack file is a stream of characters. If the file represents a
    valid program, it can be tokenized into a stream of valid tokens. The
    tokens may be separated by an arbitrary number of space characters, 
    newline characters, and comments, which are ignored. There are three 
    possible comment formats: /* comment until closing */ , /** API comment 
    until closing */ , and // comment until the line’s end.

    ‘xxx’: quotes are used for tokens that appear verbatim (‘terminals’);
    xxx: regular typeface is used for names of language constructs 
    (‘non-terminals’);
    (): parentheses are used for grouping of language constructs;
    x | y: indicates that either x or y can appear;
    x?: indicates that x appears 0 or 1 times;
    x*: indicates that x appears 0 or more times.

    ** Lexical elements **
    The Jack language includes five types of terminal elements (tokens).
    1. keyword: 'class' | 'constructor' | 'function' | 'method' | 'field' | 
    'static' | 'var' | 'int' | 'char' | 'boolean' | 'void' | 'true' | 'false' 
    | 'null' | 'this' | 'let' | 'do' | 'if' | 'else' | 'while' | 'return'
    2. symbol:  '{' | '}' | '(' | ')' | '[' | ']' | '.' | ',' | ';' | '+' | 
    '-' | '*' | '/' | '&' | '|' | '<' | '>' | '=' | '~' | '^' | '#'
    3. integerConstant: A decimal number in the range 0-32767.
    4. StringConstant: '"' A sequence of Unicode characters not including 
    double quote or newline '"'
    5. identifier: A sequence of letters, digits, and underscore ('_') not 
    starting with a digit.


    ** Program structure **
    A Jack program is a collection of classes, each appearing in a separate 
    file. The compilation unit is a class. A class is a sequence of tokens 
    structured according to the following context free syntax:
    
    class: 'class' className '{' classVarDec* subroutineDec* '}'
    classVarDec: ('static' | 'field') type varName (',' varName)* ';'
    type: 'int' | 'char' | 'boolean' | className
    subroutineDec: ('constructor' | 'function' | 'method') ('void' | type) 
    subroutineName '(' parameterList ')' subroutineBody
    parameterList: ((type varName) (',' type varName)*)?
    subroutineBody: '{' varDec* statements '}'
    varDec: 'var' type varName (',' varName)* ';'
    className: identifier
    subroutineName: identifier
    varName: identifier


    ** Statements **
    statements: statement*
    statement: letStatement | ifStatement | whileStatement | doStatement | 
    returnStatement
    letStatement: 'let' varName ('[' expression ']')? '=' expression ';'
    ifStatement: 'if' '(' expression ')' '{' statements '}' ('else' '{' 
    statements '}')?
    whileStatement: 'while' '(' 'expression' ')' '{' statements '}'
    doStatement: 'do' subroutineCall ';'
    returnStatement: 'return' expression? ';'


    ** Expressions **
    expression: term (op term)*
    term: integerConstant | stringConstant | keywordConstant | varName | 
    varName '['expression']' | subroutineCall | '(' expression ')' | unaryOp 
    term
    subroutineCall: subroutineName '(' expressionList ')' | (className | 
    varName) '.' subroutineName '(' expressionList ')'
    expressionList: (expression (',' expression)* )?
    op: '+' | '-' | '*' | '/' | '&' | '|' | '<' | '>' | '='
    unaryOp: '-' | '~' | '^' | '#'
    keywordConstant: 'true' | 'false' | 'null' | 'this'
    
    If you are wondering whether some Jack program is valid or not, you should
    use the built-in JackCompiler to compiler it. If the compilation fails, it
    is invalid. Otherwise, it is valid.
    """

    def __init__(self, input_stream: typing.TextIO) -> None:
        """Opens the input stream and gets ready to tokenize it.

        Args:
            input_stream (typing.TextIO): input stream.
        """
        input_lines = JackTokenizer._get_input_lines(input_stream)
        self.__tokens = list()
        for line in input_lines:
            self.__tokens += re.findall(PATTERN, line)
        self.__current_token = 0

    @staticmethod
    def _get_input_lines(input_stream: typing.TextIO) -> typing.List[str]:
        """Returns all the input lines from the given input stream."""
        input_lines = input_stream.read().splitlines()
        for i in range(len(input_lines)):
            JackTokenizer._clean_line(i, input_lines)
        return [line for line in input_lines if line]

    @staticmethod
    def _clean_line(i: int, input_lines: typing.List[str]) -> None:
        """Removes all the white spaces (before and after every command), tabs
        and comments."""
        input_lines[i] = input_lines[i].strip()
        input_lines[i] = input_lines[i].strip("\t")
        JackTokenizer._remove_single_line_comment(i, input_lines)
        JackTokenizer._remove_multiline_comments(i, input_lines)
        input_lines[i] = input_lines[i].strip()

    @staticmethod
    def _if_comment_in_string(line: str, start_comment_index: int) -> bool:
        """Returns True iff the current comment is in a string (iff its
        starting index is between a starting and ending indexes of some
        string)"""
        start_string_index = line.find("\"")
        while start_string_index != -1:
            end_string_index = line.find("\"", start_string_index + 1,
                                         len(line))
            if start_string_index < start_comment_index < end_string_index:
                return True
            start_string_index = line.find("\"", end_string_index + 1,
                                           len(line))
        return False

    @staticmethod
    def _remove_single_line_comment(i: int, input_lines: typing.List[str]) -> \
            None:
        """Removes all the single line comments (// ...) that are not inside of
        string literals."""
        if not JackTokenizer._if_comment_in_string(input_lines[i],
                                                   input_lines[i].find("//")):
            input_lines[i] = input_lines[i].split("//")[0]

    @staticmethod
    def _remove_multiline_comment_case_one_line(
            i: int, input_lines: typing.List[str], start_comment_index: int,
            end_comment_index: int) -> int:
        """Removes a multiline comment (/*(*) ... */) that is in one line."""
        input_lines[i] = input_lines[i][:start_comment_index] + \
            input_lines[i][end_comment_index + 2:]
        start_comment_index = input_lines[i].find("/*")
        return start_comment_index

    @staticmethod
    def _remove_multiline_comment_case_several_lines(
            i: int, input_lines: typing.List[str], start_comment_index: int) ->\
            typing.Tuple[int, int]:
        """Removes a multiline comment (/*(*) ... */) that is in several
        lines."""
        input_lines[i] = input_lines[i][:start_comment_index]
        i += 1
        end_comment_index = input_lines[i].find("*/")
        while end_comment_index == -1:
            input_lines[i] = ""
            i += 1
            end_comment_index = input_lines[i].find("*/")
        input_lines[i] = input_lines[i][end_comment_index + 2:]
        start_comment_index = input_lines[i].find("/*")
        return i, start_comment_index

    @staticmethod
    def _remove_multiline_comments(i: int, input_lines: typing.List[str]) -> \
            None:
        """Removes all the multiline comments (/*(*) ... */) that are not
        inside of string literals."""
        start_comment_index = input_lines[i].find("/*")
        while start_comment_index != -1:
            # If the comment is in a string, then don't delete it:
            if JackTokenizer._if_comment_in_string(input_lines[i],
                                                   start_comment_index):
                start_comment_index = input_lines[i].find(
                    "/*", start_comment_index + 1, len(input_lines[i]))
                continue
            end_comment_index = input_lines[i].find(
                "*/", start_comment_index + 1, len(input_lines[i]))
            if end_comment_index != -1:  # if the comment is in a single line.
                start_comment_index = \
                    JackTokenizer._remove_multiline_comment_case_one_line(
                        i, input_lines, start_comment_index, end_comment_index)
            else:  # if the comment is in multiple lines.
                i, start_comment_index = \
                    JackTokenizer._remove_multiline_comment_case_several_lines(
                        i, input_lines, start_comment_index)

    def has_more_tokens(self) -> bool:
        """Do we have more tokens in the input?

        Returns:
            bool: True if there are more tokens, False otherwise.
        """
        return self.__current_token <= (len(self.__tokens) - 1)

    def advance(self) -> None:
        """Gets the next token from the input and makes it the current token. 
        This method should be called if has_more_tokens() is true. 
        Initially there is no current token.
        """
        if self.has_more_tokens():
            self.__current_token += 1

    def token_type(self) -> str:
        """
        Returns:
            str: the type of the current token, can be
            "KEYWORD", "SYMBOL", "IDENTIFIER", "INT_CONST", "STRING_CONST"
        """
        token = self.__tokens[self.__current_token]
        if token in KEYWORDS:
            return "KEYWORD"
        elif token in SYMBOLS:
            return "SYMBOL"
        elif token.isdecimal():
            return "INT_CONST"
        elif token[0] == "\"" and token[-1] == "\"":
            return "STRING_CONST"
        else:
            return "IDENTIFIER"

    def keyword(self) -> str:
        """
        Returns:
            str: the keyword which is the current token.
            Should be called only when token_type() is "KEYWORD".
            Can return "CLASS", "METHOD", "FUNCTION", "CONSTRUCTOR", "INT", 
            "BOOLEAN", "CHAR", "VOID", "VAR", "STATIC", "FIELD", "LET", "DO", 
            "IF", "ELSE", "WHILE", "RETURN", "TRUE", "FALSE", "NULL", "THIS"
        """
        token = self.__tokens[self.__current_token]
        return token.upper()

    def symbol(self) -> str:
        """
        Returns:
            str: the character which is the current token.
            Should be called only when token_type() is "SYMBOL".
        """
        token = self.__tokens[self.__current_token]
        return token

    def identifier(self) -> str:
        """
        Returns:
            str: the identifier which is the current token.
            Should be called only when token_type() is "IDENTIFIER".
        """
        token = self.__tokens[self.__current_token]
        return token

    def int_val(self) -> int:
        """
        Returns:
            str: the integer value of the current token.
            Should be called only when token_type() is "INT_CONST".
        """
        token = self.__tokens[self.__current_token]
        return int(token)

    def string_val(self) -> str:
        """
        Returns:
            str: the string value of the current token, without the double 
            quotes. Should be called only when token_type() is "STRING_CONST".
        """
        token = self.__tokens[self.__current_token]
        return token[1: -1]

    def get_next_token(self) -> typing.Optional[typing.Tuple[str, str]]:
        """
        Returns:
            None if there is no next token, a tuple of the next token and its
            type otherwise.
        """
        if not self.has_more_tokens():
            return None
        self.__current_token += 1
        token = self.__tokens[self.__current_token]
        token_type = self.token_type()
        self.__current_token -= 1
        return token, token_type
