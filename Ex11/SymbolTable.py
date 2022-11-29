"""This file is part of nand2tetris, as taught in The Hebrew University,
and was written by Aviv Yaish according to the specifications given in  
https://www.nand2tetris.org (Shimon Schocken and Noam Nisan, 2017)
and as allowed by the Creative Common Attribution-NonCommercial-ShareAlike 3.0 
Unported License (https://creativecommons.org/licenses/by-nc-sa/3.0/).
"""
import typing


class SymbolTable:
    """A symbol table that associates names with information needed for Jack
    compilation: type, kind and running index. The symbol table has two nested
    scopes (class/subroutine).
    """

    def __init__(self) -> None:
        """Creates a new empty symbol table."""
        self.__class_table = dict()
        self.__subroutine_table = dict()
        self.__static_num = 0  # static type index.
        self.__field_num = 0  # this type index.
        self.__arg_num = 0  # argument type index.
        self.__var_num = 0  # local type index.

    def write_class_name(self, class_name: str) -> None:
        """Writes a class name."""
        self.__class_name = class_name

    def start_subroutine(self) -> None:
        """Starts a new subroutine scope (i.e., resets the subroutine's 
        symbol table).
        """
        self.__subroutine_table = dict()
        self.__arg_num = 0
        self.__var_num = 0

    def define(self, name: str, type_str: str, kind: str) -> None:
        """Defines a new identifier of a given name, type and kind and assigns 
        it a running index. "STATIC" and "FIELD" identifiers have a class
        scope,
        while "ARG" and "VAR" identifiers have a subroutine scope.

        Args:
            name (str): the name of the new identifier.
            type_str (str): the type of the new identifier.
            kind (str): the kind of the new identifier, can be:
            "STATIC", "FIELD", "ARG", "VAR".
        """
        if kind == "STATIC":
            self.__class_table[name] = (type_str, kind, self.__static_num)
            self.__static_num += 1
        elif kind == "FIELD":
            self.__class_table[name] = (type_str, kind, self.__field_num)
            self.__field_num += 1
        elif kind == "ARG":
            self.__subroutine_table[name] = (type_str, kind, self.__arg_num)
            self.__arg_num += 1
        else:  # the kind is 'VAR'.
            self.__subroutine_table[name] = (type_str, kind, self.__var_num)
            self.__var_num += 1

    def var_count(self, kind: str) -> int:
        """
        Args:
            kind (str): can be "STATIC", "FIELD", "ARG", "VAR".

        Returns:
            int: the number of variables of the given kind already defined in 
            the current scope.
        """
        if kind == "STATIC":
            return self.__static_num
        elif kind == "FIELD":
            return self.__field_num
        elif kind == "ARG":
            return self.__arg_num
        else:  # the kind is 'VAR'.
            return self.__var_num

    def kind_of(self, name: str) -> typing.Optional[str]:
        """
        Args:
            name (str): name of an identifier.

        Returns:
            str: the kind of the named identifier in the current scope, or None
            if the identifier is unknown in the current scope.
        """
        if name in self.__subroutine_table:
            type_str, kind, index = self.__subroutine_table[name]
            return kind
        elif name in self.__class_table:
            type_str, kind, index = self.__class_table[name]
            return kind
        return None

    def type_of(self, name: str) -> typing.Optional[str]:
        """
        Args:
            name (str):  name of an identifier.

        Returns:
            str: the type of the named identifier in the current scope, or None
            if the identifier is unknown in the current scope.
        """
        if name in self.__subroutine_table:
            type_str, kind, index = self.__subroutine_table[name]
            return type_str
        elif name in self.__class_table:
            type_str, kind, index = self.__class_table[name]
            return type_str
        return None

    def index_of(self, name: str) -> typing.Optional[int]:
        """
        Args:
            name (str):  name of an identifier.

        Returns:
            int: the index assigned to the named identifier, or None if the
            identifier is unknown in the current scope.
        """
        if name in self.__subroutine_table:
            type_str, kind, index = self.__subroutine_table[name]
            return index
        elif name in self.__class_table:
            type_str, kind, index = self.__class_table[name]
            return index
        return None

    def get_class_name(self) -> str:
        """Returns the current class name."""
        return self.__class_name
