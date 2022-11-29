// This file is part of www.nand2tetris.org
// and the book "The Elements of Computing Systems"
// by Nisan and Schocken, MIT Press.
// File name: projects/04/Fill.asm

// Runs an infinite loop that listens to the keyboard input.
// When a key is pressed (any key), the program blackens the screen,
// i.e. writes "black" in every pixel;
// the screen should remain fully black as long as the key is pressed. 
// When no key is pressed, the program clears the screen, i.e. writes
// "white" in every pixel;
// the screen should remain fully clear as long as no key is pressed.

// Define a variable screenFlag. If flag is 0, then the screen is white. If
// 1, then it is black. The default value is 0:
@screenFlag
M=0

(LOOP)
// If the screen is black and a key is pressed, or if the screen is white and
// no key is pressed, then go to the next iteration:
    @KBD
    D=M
    @keyboardFlag  // Set the keyboardFlag to 0 if no key is pressed
    M=D
    @COMPAREFLAGS
    D;JEQ
    M=1  // Else, set the keyboardFlag to 1.

(COMPAREFLAGS)  // If the two flags are equal, no need to change the screen
    @screenFlag
    D=M
    @keyboardFlag
    D=D-M
    @LOOP
    D;JEQ

// Define a variable addr, initialize it to the last pixel of the screen:
    @SCREEN
    D=A
    @addr
    M=D
    @8191
    D=A
    @addr
    M=D+M

// Internal loop, updates the color of each pixel in the screen:
(UPDATESCREENLOOP)
    @addr
    D=M
    @STOPUPDATESCREEN
    D;JLT

// If the screenFlag is 0, then we will turn the screen black:
    @screenFlag
    D=M
    @MAKEBLACK
    D;JEQ

// Else:
    @addr
    A=M
    M=0
    @CONTINUE
    0;JMP

(MAKEBLACK)
    @addr
    A=M
    M=-1

(CONTINUE)
    @addr
    M=M-1
    @UPDATESCREENLOOP
    0;JMP

// After every screen update we set the screenFlag to be equal to the
// keyboardFlag (the states of the screen and the keyboard synced):
(STOPUPDATESCREEN)
    @keyboardFlag
    D=M
    @screenFlag
    M=D

    @LOOP
    0;JMP
