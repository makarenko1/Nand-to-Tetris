// This file is part of nand2tetris, as taught in The Hebrew University,
// and was written by Aviv Yaish, and is published under the Creative 
// Common Attribution-NonCommercial-ShareAlike 3.0 Unported License 
// https://creativecommons.org/licenses/by-nc-sa/3.0/

// An implementation of a sorting algorithm. 
// An array is given in R14 and R15, where R14 contains the start address of
// the array, and R15 contains the length of the array.
// You are not allowed to change R14, R15.
// The program should sort the array in-place and in descending order - 
// the largest number at the head of the array.
// You can assume that each array value x is between -16384 < x < 16384.
// You can assume that the address in R14 is at least >= 2048, and that 
// R14 + R15 <= 16383. 
// No other assumptions can be made about the length of the array.
// You can implement any sorting algorithm as long as its runtime complexity is 
// at most C*O(N^2), like bubble-sort.

// Define a variable finalAddress to be the first address after the last
// element in the array:
    @R14
    D=M
    @R15
    D=D+M
    @finalAddress
    M=D

// Define a counter for the outer loop. Initialize in to -1:
    @i
    M=-1

(OUTERLOOP)
    @i
    M=M+1

// The outer loop ends when i == finalAddress:
    @R15
    D=M
    @i
    D=D-M
    @END
    D;JEQ

// Define a counter for the inner loop. Initialize it to 0:
    @j
    M=0

// Define a variable currentAddress to be the address of the current element
// in the array. Each iteration it is incremented by 1. Initialize it to the
// address of the first element in the array:
    @R14
    D=M
    @currentAddress
    M=D

// Define a variable nextAddress to be the address of the element right after
// the current element. Initialize it to the address of the second element:
    D=D+1
    @nextAddress
    M=D

// Define a swap indicator. Initialize it to 0:
    @swapped
    M=0

(INNERLOOP)
    @j
    M=M+1

// The inner loop ends when j == finalAddress:
    @R15
    D=M
    @j
    D=D-M
    @OUTERLOOP
    D;JEQ

    @currentAddress
    A=M
    D=M
    @firstArg
    M=D

    @nextAddress
    A=M
    D=M
    @secondArg
    M=D

// If the element in the current address is greater or equal to the element in
// the next address, then the order of the elements is correct, and so we
// continue:
    @firstArg
    D=M
    @secondArg
    D=D-M
    @CONTINUE
    D;JGE

// Else, perform a swap of these two elements:
    @secondArg
    D=M
    @currentAddress
    A=M
    M=D

    @firstArg
    D=M
    @nextAddress
    A=M
    M=D

    @swapped
    M=1

(CONTINUE)
    @currentAddress
    M=M+1
    @nextAddress
    M=M+1

    @INNERLOOP
    0;JMP

// If there hasn't been performed any swap during the run of the inner loop,
// then the array is sorted. And so, we exit the program:
    @swapped
    D=M
    @END
    D;JEQ

    @OUTERLOOP
    0;JMP

(END)
    @END
    0;JMP
