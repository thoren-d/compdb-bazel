import analysis_pb2 as analysis
import os
import json
import subprocess
import sys

def make_absolute(path, execution_root):
    if path.startswith('external'):
        return os.path.abspath(os.path.join(execution_root, path))
    else:
        return path

def filter_argument(argument, execution_root):
    if argument.startswith('/I'):
        return filter_argument('-I' + argument[2:], execution_root)
    if argument.startswith('/D'):
        return filter_argument('-D' + argument[2:], execution_root)
    if argument.startswith('/std:'):
        return ['-std=' + argument[5:]]
    if argument == '/c' or argument == '-c':
        return ['-c']
    if argument.startswith('/clang:'):
        return [argument[7:]]
    if argument.startswith('-I'):
        return ['-I', make_absolute(argument[2:], execution_root)]
    if argument.startswith('-D'):
        return ['-D', argument[2:]]
    if argument.startswith('-W'):
        return [argument]

    return []

def parse_arguments(arguments, execution_root):
    results = []

    for argument in arguments:
        if not results:
            results.append(argument.replace('clang-cl', 'clang')) # compiler is first arg
            results.append('-xc++')
            continue
        if argument.endswith('.cc') or argument.endswith('.cpp'):
            cc_file = make_absolute(argument, execution_root)
            results.append(argument)
            continue

        results += filter_argument(argument, execution_root)

    return {
        'file': cc_file,
        'arguments': results
    }

def get_header_command(command_info):
    cc_file = command_info['file']
    if cc_file.endswith('.cc'):
        header_file = cc_file.replace('.cc', '.h')
    elif cc_file.endswith('.cpp'):
        header_file = cc_file.replace('.hpp')
    if not os.path.exists(header_file):
        return None

    header_command = command_info.copy()
    header_command['file'] = header_file
    header_command['arguments'] = command_info['arguments'].copy()
    try:
        file_arg = header_command['arguments'].index(command_info['file'])
        header_command['arguments'][file_arg] = header_command['file']
    except ValueError:
        return None
    return header_command


def get_commands(action_graph, execution_root):
    results = []
    for action in action_graph.actions:
        command_info = parse_arguments(action.arguments, execution_root)
        command_info['directory'] = os.path.abspath(os.curdir)
        results.append(command_info)
        
        header_command = get_header_command(command_info)
        if header_command:
            results.append(header_command)

    return results

def main():
    target = sys.argv[1]

    execution_root = str(subprocess.check_output(['bazel', 'info', 'execution_root'], encoding='utf-8')).strip()
    command = ['bazel', 'aquery', '--output=proto', '--compiler=clang-cl', 'mnemonic("CppCompile", deps(%s))' % target]
    result = subprocess.check_output(command)
    action_graph = analysis.ActionGraphContainer()
    action_graph.ParseFromString(result)

    with open('compile_commands.json', mode='w') as output_file:
        json.dump(get_commands(action_graph, execution_root), output_file)

if __name__ == '__main__':
    main()
