// This file is part of www.nand2tetris.org
// and the book "The Elements of Computing Systems"
// by Nisan and Schocken, MIT Press.
// File name: projects/04/Mult.asm

// Multiplies R0 and R1 and stores the result in R2.
// (R0, R1, R2 refer to RAM[0], RAM[1], and RAM[2], respectively.)
//
// This program only needs to handle arguments that satisfy
// R0 >= 0, R1 >= 0, and R0*R1 < 32768.

// Define a variable mult, initialize it to 0. We will add to it R0 times R1:
    @mult
    M=0

// Define a loop counter i, initialize to 0:
    @i
    M=0

(LOOP)
// If (i == R0) goto STOP:
    @i
    D=M
    @R0
    D=D-M
    @STOP
    D;JEQ

// mult = mult + R1:
    @R1
    D=M
    @mult
    M=D+M

// i++:
    @i
    M=M+1

    @LOOP
    0;JMP

// Transfer the value in mult to R2:
(STOP)
    @mult
    D=M
    @R2
    M=D

// The end of the program:
(END)
    @END
    0;JMP
