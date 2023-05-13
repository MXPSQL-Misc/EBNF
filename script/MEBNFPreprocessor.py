#!/usr/bin/env python3
# MXPSQL-EBNF preprocessor
# Incomplete, but can deal with directives

import os, sys, argparse, io, shlex, typing

__all__ = ["MEBNFError", "MEBNFBadDirectiveError", "MEBNFBadSyntaxError", "preprocess"]

class MEBNFError(ValueError):
    pass

class MEBNFBadDirectiveError(MEBNFError):
    pass

class MEBNFBadSyntaxError(MEBNFError, SyntaxError):
    pass


# Internals

# API
def preprocess(mebnf : str, namespace : typing.Optional[str] = None, *, recursive : bool =False, descriptive : bool =True, strict : bool =False) -> str:
    """
    The MXPSQL-EBNF preprocessor function.

    It only converts MXPSQL-EBNF to normal (sometimes invalid) EBNF.
    """
    mebnf_workspace = io.StringIO()

    processed_files = set()  # Set to store the names of processed files

    def do_work(input_mebnf, current_file):
        # Check if the current file has already been processed
        cf = ""
        if (current_file is not None):
            cf = os.path.realpath(current_file)
            if cf in processed_files:
                return f"(* ALREADY INCLUDED: {current_file} *)"

        # Add the current file to the set of processed files
        processed_files.add(cf)

        for _linenumber, line in enumerate(input_mebnf.splitlines()):
            # comment processor 1
            if line.startswith("#"):
                comment = f"(* {line[1:]} *)"
                mebnf_workspace.write(comment + "\n")
                continue

            # directive processor
            if len(line) > 0 and line[0] == "@":
                line = line[1:]
                tok = shlex.split(line)
                toks = len(tok)
                if toks < 1:
                    raise MEBNFBadSyntaxError("Bad MXPSQL-EBNF directive.")

                directive = tok[0]
                if directive == "include":
                    if toks < 2:
                        raise MEBNFBadDirectiveError("Missing arguments for include directive")

                    include_file = tok[1]
                    if include_file in processed_files:
                        continue  # Skip processing if the included file has already been processed

                    include = ""
                    if descriptive:
                        include += f"(* INCLUDE FROM: {include_file} *)\n"
                    with open(include_file, "rb") as fs:
                        include += fs.read().decode("ascii")

                    if recursive:
                        include = do_work(include, include_file)

                    mebnf_workspace.write(str(include) + "\n")
                else:
                    if strict:
                        raise MEBNFBadDirectiveError(f"Unrecognized directive: {tok[0]}")
            else:
                mebnf_workspace.write(str(line) + "\n")

    do_work(mebnf, namespace)  # Start with the main file

    return mebnf_workspace.getvalue()

def main(argv : list[str]):
    parser = argparse.ArgumentParser(
        prog=__file__,
        description="MXPSQL-EBNF preprocessor that outputs an EBNF file"
    )
    parser.add_argument("-f", "--input-file", dest="ifi", type=str, help="file to process")
    parser.add_argument("-o", "--output-file", dest="ofi", type=str, help="output filename")
    parser.add_argument("-w", "--overwrite", dest="ovw", action="store_true", help="overwrite a file?")

    args = parser.parse_args(argv)

    mebnf = ""
    if args.ifi:
        with open(args.ifi, "rb") as f:
            mebnf = f.read().decode("ascii")
    else:
        print("Input yout script into stdin...", file=sys.stderr)
        mebnf = sys.stdin.read()

    mebnf_out = preprocess(mebnf, args.ifi, recursive=True)
    
    if args.ofi:
        if args.ovw and os.path.isfile(args.ofi):
            raise ValueError("Refuse to overwrite a file")

        with open(args.ofi, "wb") as f:
            f.write(bytes(mebnf_out, "ascii"))
    else:
        print(mebnf_out, file=sys.stdout)

    return 0

if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
