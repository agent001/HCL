# -*- coding: utf-8 -*-

from __future__ import print_function

import vm
import os
import re
import sys
import random
import compiler.frontend

SET = 'set'
MOV = 'mov'
INC = 'inc'
DEC = 'dec'
MUL = 'mul'
DIV = 'div'
ADD = 'add'
SUB = 'sub'
NOT = 'not'
OR = 'or'
AND = 'and'
XOR = 'xor'
MOD = 'mod'
CMP = 'cmp'
PUSH = 'push'
CALL = 'call'
FREE = 'free'
HALT = 'halt'
PRINT = 'print'

DO = 'do'
IF = 'if'
ASSIGNMENT = 'assignment'
READ = 'read'
CLC = 'clc'
GSS = 'gss'
EQU = 'equ'
NEQ = 'neq'
GE = 'sgt'
LE = 'slt'
GEQ = 'geq'
LEQ = 'leq'
ACT = 'act'

SPACE = 'space'
NEWLINE = 'nl'
SPACE_VAL = '100000'
NEWLINE_VAL = '001010'

FALSE = '0000'
TRUE = '0001'

INT = 'integer'
BOOL = 'boolean'
CHAR = 'char'

OP1 = 'oper1'
OP2 = 'oper2'
OPER = 'op'
NUM = 'num'
VAR = 'var'
SCOPE = 'scope'
INDEX = 'index'
FUNC = 'func'

type_equivalence = {'int':INT, BOOL:BOOL, CHAR:CHAR}

initialization = {}
allocation = {}
free_registers = {}

for _type in ['int', 'chr', 'bol']:
    for i in range(1, 6):
        free_registers['.r%d%s' % (i, _type)] = True
    free_registers['..ret%s' % (_type)] = True

def code_generation(data, tree):
    stat = 0
    lines = []
    path = data['path']
    folder = os.path.dirname(path)
    file_name = os.path.basename(path)
    output_file = file_name.replace('.hcl', '.vhcl')
    if output_file == file_name:
       output_file += '.vhcl'
    lines.append(';; %s : Autogenerated file by HCL Compiler v1.0\n' % (output_file))
    stat, lines = variable_declaration(data, lines)
    if stat == 0:
       lines.append('\n;; General program execution routine\n')
       stat, lines = program_generation(data, lines)
    return stat, lines

def variable_declaration(data, lines):
    stat = 0
    lines.append(';; Auxiliar character defintion')
    lines.append('%s %s %s  ;; Space character' % (SET, SPACE, CHAR))
    lines.append('%s %s %s  ;; New Line character' % (SET, NEWLINE, CHAR))
    lines.append('%s %s %s  ;; Space character initialization' % (MOV, SPACE, SPACE_VAL))
    lines.append('%s %s %s  ;; New Line character initialization\n' % (MOV, NEWLINE, NEWLINE_VAL))
    lines.append(';; General variable defintion')
    
    for scope in sorted(data['definitions'].keys()):
        scope_variables = data['definitions'][scope]
        for variable in scope_variables:
            var_info = scope_variables[variable]
            #Limitation: Number of indices allowed by the VM is restricted to 2
            if len(var_info['size']) > 2:
               stat = -13
               print("File: %s - Line: %d:%d\nVirtual Machine Limitation: Dimensions of array %s must not exceed two" % (data['path'], var_info['tok'].line, var_info['tok'].col, variable), file=sys.stderr)   
               break
            instr = '%s %s%d %s' % (SET, variable, scope, type_equivalence[var_info['type']])
            if len(var_info['size']) > 0:
               instr += '#'+'#'.join(map(str, var_info['size']))
               initialization['%s%d' % (variable, scope)] = True
            else:
               initialization['%s%d' % (variable, scope)] = False
            lines.append(instr)
    return stat, lines

def _ident(lvl):
    return '\t'*lvl

def recover_free_register():
    return random.choice(filter(lambda x: free_registers[x], free_registers))

def program_generation(data, lines, scope=0, ident=0):
    stat = 0
    for instruction in data['instructions'][scope]:
        instruction_type = [key for key in instruction if instruction[key] is not None][0]
        if instruction_type == READ:
           stat, lines = read_generation(instruction['read'], data, lines, ident)
    return stat, lines

def read_generation(read_info, data, lines, ident=0):
    stat = 0
    var_tok = read_info['var']
    scope = read_info['scope']
    read_func = read_info['read']
    size = data['definitions'][scope][var_tok.value]['size']
    lines.append(';; Reading variable %s (Scope %d) of size %s' % (var_tok.value, scope, 'x'.join(map(str,size))))
    if len(size) == 0:
       lines.append(_ident(ident)+'%s %s%d' % (read_func, var_tok.value, scope))
    elif len(size) == 1:
       lines.append(_ident(ident)+'%s %s %s' % (SET, '_sysidx1', INT))
       lines.append(_ident(ident)+'%s %s %s' % (MOV, '_sysidx1', FALSE))
       lines.append(_ident(ident)+'%s:' % (DO))
       ident += 1
       lines.append(_ident(ident)+'%s %s' % (GSS, '_sysguard1'))
       lines.append(_ident(ident)+'%s:' % (CLC))
       ident += 1
       bin_size = bin(size[0])[2:]
       lines.append(_ident(ident)+'%s %s %s' % (CMP, '_sysidx1', bin_size))
       lines.append(_ident(ident)+'%s:' % (LE))
       ident += 1
       lines.append(_ident(ident)+'%s %s %s' % (MOV, '_sysguard1', TRUE))
       ident -= 2
       lines.append(_ident(ident)+'%s %s:' % (ACT, '_sysguard1'))
       ident += 1
       lines.append(_ident(ident)+'%s %s%d[%s]' % (read_func, var_tok.value, scope, '_sysidx1'))
       lines.append(_ident(ident)+'%s %s' % (INC, '_sysidx1'))
       ident -= 2
       lines.append(_ident(ident)+'%s %s' % (FREE, '_sysidx1'))
    else:
       lines.append(_ident(ident)+'%s %s %s' % (SET, '_sysidx1', INT))
       lines.append(_ident(ident)+'%s %s %s' % (SET, '_sysidx2', INT))
       lines.append(_ident(ident)+'%s %s %s' % (MOV, '_sysidx1', FALSE))
       lines.append(_ident(ident)+'%s %s %s' % (MOV, '_sysidx2', FALSE))
       lines.append(_ident(ident)+'%s:' % (DO))
       ident += 1
       lines.append(_ident(ident)+'%s %s' % (GSS, '_sysguard1'))
       lines.append(_ident(ident)+'%s:' % (CLC))
       dim_1 = bin(size[0])[2:]
       ident += 1
       lines.append(_ident(ident)+'%s %s %s' % (CMP, '_sysidx1', dim_1))
       lines.append(_ident(ident)+'%s:' % (LE))
       ident += 1
       lines.append(_ident(ident)+'%s %s %s' % (MOV, '_sysguard1', TRUE))
       ident -= 2
       lines.append(_ident(ident)+'%s %s:' % (ACT, '_sysguard1'))
       ident += 1
       lines.append(_ident(ident)+'%s %s %s' % (MOV, '_sysidx2', FALSE))
       lines.append(_ident(ident)+'%s:' % (DO))
       ident += 1
       lines.append(_ident(ident)+'%s %s' % (GSS, '_sysguard2'))
       lines.append(_ident(ident)+'%s:' % (CLC))
       dim_2 = bin(size[1])[2:]
       ident += 1
       lines.append(_ident(ident)+'%s %s %s' % (CMP, '_sysidx2', dim_2))
       lines.append(_ident(ident)+'%s:' % (LE))
       ident += 1
       lines.append(_ident(ident)+'%s %s %s' % (MOV, '_sysguard2', TRUE))
       ident -= 2
       lines.append(_ident(ident)+'%s %s:' % (ACT, '_sysguard2'))
       ident += 1
       lines.append(_ident(ident)+'%s %s%d[%s][%s]' % (read_func, var_tok.value, scope, '_sysidx1', '_sysidx2'))
       lines.append(_ident(ident)+'%s %s' % (INC, '_sysidx2'))
       ident -= 2
       lines.append(_ident(ident)+'%s %s' % (INC, '_sysidx1'))
       ident -= 2
       lines.append(_ident(ident)+'%s %s' % (FREE, '_sysidx1'))
       lines.append(_ident(ident)+'%s %s' % (FREE, '_sysidx2'))
    initialization['%s%d' % (var_tok.value, scope)] = True
    return stat, lines


def process_expression(addr, data, lines, ident, index=False):
    stat = 0
    reg = ''
    addr_info = data['addresses'][addr]
    if addr_info[OPER] is None:
       #Case 1
       var_info = addr_info[OP1]
       if var_info[NUM] is not None:
          if index:
             reg = str(var_info[NUM].value)
          else:
             reg = bin(var_info[NUM].value)[2:]
       elif var_info[VAR] is not None:
          var_d = var_info[VAR]
          var_name = var_d[VAR]
          scope = var_d[SCOPE]
          reg = '%s%d' % (var_name.value, scope)
          if var_info[INDEX] is None:
             if not initialization[reg]:
                print("File: %s - Line: %d:%d\nWarning: Variable %s (Scope %d) has not been initialized" % (data['path'], var_name.line, var_name.col, var_name.value, scope), file=sys.stderr)
                lines.append(_ident(ident)+';;Warning - Variable %s%d without initialization, using default values' % (var_name.value, scope))
          else:
             index_key = var_info[INDEX]
             for ad in data['indices'][index_key]:
                 reg_i = process_expression(ad, data, lines, ident, index=True)
                 reg += '[%s]' % (reg_i)
       elif var_info[FUNC] is not None:         
          #TODO: Process functions and register allocation
          pass
