import sys
import os
import re

program_filepath = sys.argv[1]

print("[CMD] Parsing")

program_lines = []

with open(program_filepath, "r") as pf:
    program_lines = [
        line.strip()
        for line in pf.readlines()
    ]

# [CMD] Parsing Starts
program = []
variables = {}
error_found = False  # Flag variable to track if an error is found

for line in program_lines:
    parts = re.findall(r'(\w+|\d+|;)', line)
    opcode = parts[0]

    if opcode == "":
        continue
    if parts[-1] != ";":
        print(f"{line} <-- missing semicolon (;)")
        error_found = True
        break  # Exit the loop if error found
    if opcode == "EXIT_CODE":
        operand = parts[1]
        if not operand.isdigit() and operand not in variables:
            print(f"{line} <-- invalid operand for EXIT_CODE. Must be an integer or declared variable.")
            error_found = True
            break
        program.append((opcode, operand))
    elif opcode == "VAR":
        var_name = parts[1]
        if var_name in variables:
            print(f"{line} <-- variable {var_name} already declared.")
            error_found = True
            break
        variables[var_name] = None
        program.append((opcode, var_name))
    elif opcode == "ASSIGN":
        var_name, val = parts[1], parts[2]
        if var_name not in variables:
            print(f"{line} <-- variable {var_name} not declared.")
            error_found = True
            break
        if not val.isdigit():
            print(f"{line} <-- invalid value {val} for ASSIGN. Must be an integer.")
            error_found = True
            break
        program.append((opcode, var_name, int(val)))
    elif opcode == "PRINT":
        var_name = parts[1]
        if var_name not in variables:
            print(f"{line} <-- variable {var_name} not declared.")
            error_found = True
            break
        program.append((opcode, var_name))
    elif opcode in {"ADD", "SUB", "MUL", "DIV"}:
        var1, var2, var3 = parts[1], parts[2], parts[3]
        if var1 not in variables or var2 not in variables or var3 not in variables:
            print(f"{line} <-- all operands for {opcode} must be declared variables.")
            error_found = True
            break
        program.append((opcode, var1, var2, var3))

if not error_found:
    print("DONE PARSING")  # DEBUG
    print(program)  # DEBUG

    '''
        COMPILATION TO ASSEMBLY
    '''

    asm_filepath = f"{program_filepath[:-4]}asm"
    output = open(asm_filepath, "w")

    output.write("""// ENTRY POINT
.global _start
.section .text
_start:
""")

    var_register_map = {}
    next_register = 1  # start from x1 because x0 is used for system calls

    def get_register(var_name):
        global next_register
        if var_name not in var_register_map:
            var_register_map[var_name] = f"x{next_register}"
            next_register += 1
        return var_register_map[var_name]

    for instruction in program:
        opcode = instruction[0]
        if opcode == "VAR":
            var_name = instruction[1]
            # Initialize variable in a register
            reg = get_register(var_name)
            output.write(f"\t/* VAR: {var_name} initialized to 0 */\n")
            output.write(f"\tmov {reg}, #0\n")
        elif opcode == "ASSIGN":
            var_name, val = instruction[1], instruction[2]
            reg = get_register(var_name)
            output.write(f"\t/* ASSIGN: {var_name} = {val} */\n")
            output.write(f"\tmov {reg}, #{val}\n")
        elif opcode == "EXIT_CODE":
            operand = instruction[1]
            if operand in variables:
                reg = get_register(operand)
                output.write(f"\t/* EXIT_CODE: {operand} */\n")
                output.write(f"\tmov x0, {reg}\n")
            else:
                output.write(f"\t/* EXIT_CODE: {operand} */\n")
                output.write(f"\tmov x0, #{operand}\n")
            output.write("\tmov x8, #93\n")  # syscall number for exit
            output.write("\tsvc #0\n")       # make syscall
        elif opcode == "PRINT":
            var_name = instruction[1]
            reg = get_register(var_name)
            output.write(f"\t/* PRINT: {var_name} */\n")
            output.write(f"\tbl print_int\n")  # Branch to print_int function
            output.write(f"\tmov x0, {reg}\n") # Move variable value to x0
        elif opcode in {"ADD", "SUB", "MUL", "DIV"}:
            var1, var2, var3 = instruction[1], instruction[2], instruction[3]
            reg1, reg2, reg3 = get_register(var1), get_register(var2), get_register(var3)
            if opcode == "ADD":
                output.write(f"\t/* ADD: {var1} + {var2} = {var3} */\n")
                output.write(f"\tadd {reg3}, {reg1}, {reg2}\n")
            elif opcode == "SUB":
                output.write(f"\t/* SUB: {var1} - {var2} = {var3} */\n")
                output.write(f"\tsub {reg3}, {reg1}, {reg2}\n")
            elif opcode == "MUL":
                output.write(f"\t/* MUL: {var1} * {var2} = {var3} */\n")
                output.write(f"\tmul {reg3}, {reg1}, {reg2}\n")
            elif opcode == "DIV":
                output.write(f"\t/* DIV: {var1} / {var2} = {var3} */\n")
                output.write(f"\tsdiv {reg3}, {reg1}, {reg2}\n")

    output.write("""

print_int:
    mov x2, #0        // reset digit counter
    mov x1, x0        // copy value to x1
    ldr x3, =buffer+19// point to the end of the buffer
    add x3, x3, x2    // add the digit counter
    add x3, x3, #1    // move to next position in buffer
    mov w4, #0x0A     // newline character
    strb w4, [x3]     // store newline at end of buffer
    sub x3, x3, #1    // point to where next digit goes
    cmp x1, #0        // check if value is 0
    b.eq .print_zero  // if zero, jump to print_zero
.print_loop:
    udiv x4, x1, #10  // x4 = x1 / 10
    msub x5, x4, x4, #10 // x5 = x1 - x4*10 (remainder)
    add x5, x5, #48   // convert to ASCII
    strb w5, [x3]     // store ASCII character in buffer
    sub x3, x3, #1    // move to next position
    mov x1, x4        // update x1 with quotient
    cmp x1, #0        // check if quotient is zero
    b.ne .print_loop  // if not, repeat loop
    add x3, x3, #1    // point to the first digit
    mov x1, x3        // set buffer pointer for write syscall
    mov x2, x4        // set buffer size
    mov x0, #1        // file descriptor (stdout)
    mov x8, #64       // syscall number (write)
    svc #0            // make syscall
    ret               // return from function
.print_zero:
    mov w5, #48       // ASCII '0'
    strb w5, [x3]     // store '0' in buffer
    add x3, x3, #1    // move to next position
    mov x1, x3        // set buffer pointer for write syscall
    mov x2, #1        // buffer size is 1
    mov x0, #1        // file descriptor (stdout)
    mov x8, #64       // syscall number (write)
    svc #0            // make syscall
    ret               // return from function

.section .bss
buffer: .skip 20      // allocate 20 bytes for buffer
""")

    output.close()

    print("DONE COMPILING")  # DEBUG
    print(f"OUTPUT ASSEMBLY: {asm_filepath}")
    
    '''
        Assemble
    '''
    
    os.system(f"as {asm_filepath} -o {asm_filepath[:-4]}.o")
    print("DONE ASSEMBLING")  # DEBUG

    '''
        Linking
    '''
    os.system(f"ld {asm_filepath[:-4]}.o -o {asm_filepath[:-4]}.elf")
    print("DONE LINKING")  # DEBUG
else:
    print("Error found during parsing. Compilation aborted.")
