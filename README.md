# Bazel Compilation Database

generate_compilation_database.py takes a bazel target (or target group like //...),
and outputs a clang compilation database at "compile_commands.json".

Uses aquery to get the commands used to build the targets.
