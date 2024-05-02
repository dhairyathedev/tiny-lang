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

# print(program_lines) # Print the program lines individually
# [CMD] Parsing Starts
program = []
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
        val = int(parts[1])
        program.append((opcode, val))

if not error_found:
    print("DONE PARSING")
    print(program)

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

    # TODO: WRITE ASSEMBLY (ARM64) for RETURN opcode. Use #93 (x8 register) and mov x0, parts[1]
    for opcode, *operands in program:
        print(opcode, operands)
        if opcode == "EXIT_CODE":
            return_val = operands[0]
            output.write(f"\tmov x0, #{return_val}\n")
            output.write("\tmov x8, #93\n")  # syscall number for exit
            output.write("\tsvc #0\n")       # make syscall
  
    output.close()
    
    print("DONE COMPILING")
    print(f"OUTPUT ASSEMBLY: {asm_filepath}")
    
    '''
        Assemble
    '''
    
    os.system(f"as {asm_filepath} -o {asm_filepath[:-4]}.o")
    print("DONE ASSEMBLING")

    '''
        Linking
    '''
    os.system(f"ld {asm_filepath[:-4]}.o -o {asm_filepath[:-4]}.elf")
    print("DONE LINKING")
else:
    print("Error found during parsing. Compilation aborted.")



