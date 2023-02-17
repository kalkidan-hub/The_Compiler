import re



text_segment = ".text\n"
data_segment = ".data\n"


# declaring possible patterns,
pattern_start,pattern2,pattern_end = r"^[a-zA-z0-9?]", r"^#",r"[a-zA-z0-9?]$"
pattern_var = r"^[a-zA-Z]+[0-9]?"
pattern_component = r"[a-zA-Z0-9?]+|[0-9]+"

operations = ['+','-','/','*','**','%','//']
# operation_map = {
#     "+" : "add",
#     "-" : "sub",
#     "*" : "mul",
#     "/" : "div",
#     "//" : "mflo",
#     "%" : "rem"
# } 
VAR_REG = ["$t0"] # initializing register and for the pupose of dynamic allocation
cn = 0   # to count register

def sortPrecedence(Plist:list):
        diction = {'+':6,'-':5,'/':4,'*':1,'**':0,'%':3,'//':2}
        toSort = []
        Slist = []
        for i in Plist:
            toSort += [diction[i[0]]]
        toSort.sort()
        flipped_dict = {value: key for key, value in diction.items()}

        for j in toSort:
            for k in Plist :
                if k[0] == flipped_dict[j]:
                    Slist += [k]
            
        return Slist
def adjustReg(cn):
    global VAR_REG
    cn += 1 
    VAR_REG += [f'$t{cn}']
    return VAR_REG




def doMath(code):
    global data_segment, text_segment, cn, VAR_REG, operations, pattern2,pattern_check, pattern_component, pattern_end, pattern_start, pattern_var
    input_lines = code.split("\n")
    
    
    for line in input_lines:
        line = line.strip()
        if re.search(pattern2,line):
            continue
        start_right = re.findall(pattern_start,line)
        end_right = re.findall(pattern_end,line)
        if start_right and end_right:
            assign = False
            Terminal = line
            if '=' in line:
                splitted = line.split('=')
                
                nonTerminal, Terminal = splitted[0], splitted[1]
                # we expect the nonTerminal to be variable and a valid expression, so let's check it out
                if not re.search(pattern_var,nonTerminal):
                    return "invalid expression"
                data_segment += f"{nonTerminal}: .word 0\n"  # adding the variable into the data segment
                assign = True
                


            
            # Now we're left with the Terminal part, the expression to be evaluated
            #check it's validity and produce precedence map, we gonna do it a two-dimentional array           
            precedence = []
            ct = 0
            for i in operations:
                if i in Terminal:
                    pattern_check = rf'(\w|\d|\s){i}(\w|\d|\s)'
                    check = re.search(pattern_check,Terminal)
                    if check:
                        ct += 1
                        precedence += [[f'{i}',ct]]

                    if not check or (i == '*' or i == '/'):
                        pattern_check = rf'(\w|\d|\s){i+i}(\w|\d|\s)'
                        check = re.search(pattern_check,Terminal)
                        if not check:
                            return "Invalid syntax"
                        ct += 1
                        precedence += [[f'{i}{i}',ct]]         
                    

            components = re.findall(pattern_component,Terminal)
            precedence = sortPrecedence(precedence)


            #at this point we got the components and the precedence array, therfore do a thing to change it into assembly program
            # sort the precedence

            for op in precedence:
                operand1, operand2 = components[op[1]-1], components[op[1]]
                ## polishing our register by loading the existing variables and the already occupied register
                valid = False
                if operand1 in data_segment or operand2 in data_segment:
                    valid = True
                    if operand1 in data_segment:
                        text_segment += f"lw $t{cn},{operand1}\n"
                        components[op[1]-1] = f'$t{cn}'
                        adjustReg(cn)
                    elif operand2 in data_segment:
                        text_segment += f"lw $t{cn},{operand2}\n"
                        components[op[1]] = f'$t{cn}'
                        adjustReg(cn)
                elif operand1 in VAR_REG or operand2 in VAR_REG:
                    valid = True
                elif str(operand1).isdigit() or str(operand2).isdigit():
                    valid = True
                    if operand1.isdigit:
                        text_segment += f"li $t{cn},{operand1}\n"
                        components[op[1]-1] = f'$t{cn}'
                        adjustReg(cn)
                    elif operand2.isdigit:
                        text_segment += f"li $t{cn},{operand2}\n"
                        components[op[1]] = f'$t{cn}'
                        adjustReg(cn)
                    ## now we are with a list of components of registers 
            if valid:
                for op in precedence: 
                    if op[0] == '**':
                        text_segment += ""  # to be applied using the looping struncture
                        components = [i if i !=components[op[1]] else components[op[1]-1] for i in components]


                    elif op[0] == '*':
                        text_segment += f"mul {components[op[1]-1]}, {components[op[1]-1]}, {components[op[1]]}\n"
                        components = [i if i !=components[op[1]] else components[op[1]-1] for i in components]


                    elif op[0] == '+':
                        text_segment += f"add {components[op[1]-1]}, {components[op[1]]}\n"
                        components = [i if i !=components[op[1]] else components[op[1]-1] for i in components]



                    elif op[0] == '-':
                        text_segment += f"sub {components[op[1]-1]}, {components[op[1]]}\n"
                        components = [i if i !=components[op[1]] else components[op[1]-1] for i in components]



                    elif op[0] == '//':
                        text_segment += f"div {components[op[1]-1]}, {components[op[1]]} \n mflo {components[op[1]-1]}\n"
                        components = [i if i !=components[op[1]] else components[op[1]-1] for i in components]



                    elif op[0] == '/':
                        text_segment += f"div {components[op[1]-1]}, {components[op[1]]}\n"
                        components = [i if i !=components[op[1]] else components[op[1]-1] for i in components]



                    elif op[0] == '%':
                        text_segment += f"rem {components[op[1]-1]}, {components[op[1]]}\n"
                        components = [i if i !=components[op[1]] else components[op[1]-1] for i in components]

            ## at this point all entries of the component has the same value the final value and the final register,
            res = components[0]

            if assign:
                data = data_segment.rstrip()
                data = data.split("\n")
                lastval = data[-1]
                var = lastval[:lastval.index(':')].rstrip()
                adjustReg(cn)

                text_segment += f"la {VAR_REG[-1]}, {var} \n sw {res},({VAR_REG[-1]})\n"
            text_segment += f"li $v0,1 \n move $a0,{res} \n syscall\n"
        
        else:
            return "Invalid Syntax"

        return data_segment + text_segment
    
print(doMath("complex_math = 6 + 7"))

def read_and_compile(file_path):
    with open(file_path, 'r') as file:
        code = file.read()
        mips_code = doMath(code)
    with open("output1.asm", "w") as file:
        print(mips_code)

file_path = "hello.py"
read_and_compile(file_path)