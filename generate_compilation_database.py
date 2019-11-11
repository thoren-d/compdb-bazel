import analysis_pb2 as analysis
import os
import json
import subprocess
import sys

def filter_argument(argument):
    if argument.startswith('/I'):
        return '-I' + argument[2:]
    if argument.startswith('/D'):
        return '-D' + argument[2:]
    if argument.startswith('/std:'):
        return '-std=' + argument[5:]
    if argument == '/c' or argument == '-c':
        return '-c'
    if argument.startswith('/clang:'):
        return argument[7:]
    if argument.startswith('-I'):
        return argument
    if argument.startswith('-D'):
        return argument
    if argument.startswith('-W'):
        return argument

def parse_arguments(arguments):
    results = []

    for argument in arguments:
        if not results:
            results.append(argument) # compiler is first arg
            continue
        if argument.endswith('.cc') or argument.endswith('.cpp'):
            cc_file = argument
            results.append(argument)
            continue

        filtered_arg = filter_argument(argument)
        if filtered_arg:
            results.append(filtered_arg)

    return {
        'file': cc_file,
        'arguments': results
    }

def get_commands(action_graph, execution_root):
    results = []
    for action in action_graph.actions:
        command_info = parse_arguments(action.arguments)
        command_info['directory'] = execution_root
        results.append(command_info)
        if os.path.exists(command_info['directory'] + '/' + command_info['file'].replace('.cc', '.h')):
            header_command = command_info.copy()
            header_command['file'] = command_info['file'].replace('.cc', '.h')
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
