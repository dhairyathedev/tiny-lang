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
    # program.append(opcode)
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

    for instruction in program:
        opcode = instruction[0]
        if opcode == "VAR":
            var_name = instruction[1]
            # Initialize variable in a register
            reg = f"x{next_register}"
            var_register_map[var_name] = reg
            next_register += 1
            output.write(f"\t/* VAR: {var_name} initialized to 0 */\n")
            output.write(f"\tmov {reg}, #0\n")
        elif opcode == "ASSIGN":
            var_name, val = instruction[1], instruction[2]
            reg = var_register_map[var_name]
            output.write(f"\t/* ASSIGN: {var_name} = {val} */\n")
            output.write(f"\tmov {reg}, #{val}\n")
        elif opcode == "EXIT_CODE":
            operand = instruction[1]
            if operand in variables:
                reg = var_register_map[operand]
                output.write(f"\t/* EXIT_CODE: {operand} */\n")
                output.write(f"\tmov x0, {reg}\n")
            else:
                output.write(f"\t/* EXIT_CODE: {operand} */\n")
                output.write(f"\tmov x0, #{operand}\n")
            output.write("\tmov x8, #93\n")  # syscall number for exit
            output.write("\tsvc #0\n")       # make syscall
        elif opcode in {"ADD", "SUB", "MUL", "DIV"}:
            var1, var2, var3 = instruction[1], instruction[2], instruction[3]
            reg1, reg2, reg3 = var_register_map[var1], var_register_map[var2], var_register_map[var3]
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
