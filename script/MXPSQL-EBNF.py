#!/usr/bin/env python3
# MXPSQL-EBNF preprocessor
# Incomplete, but can deal with directives

import os, sys, argparse, io, shlex

def preprocess(mebnf : str, strict=False):
    mebnf_workspace = io.StringIO()

    for linenumber, line in enumerate(mebnf.splitlines()):
        # directive processor
        if len(line) > 0 and line[0] == "@":
            line = line[1:]
            tok = shlex.split(line)
            toks = len(tok)
            if toks < 1:
                raise ValueError("Bad MXPSQL-EBNF directive.")

            directive = tok[0]
            if directive == "include":
                if toks < 2:
                    raise ValueError("Missing arguments for include directive")

                include = ""
                with open(tok[1], "rb") as fs:
                    include = fs.read().decode("ascii")

                mebnf_workspace.write(include)
            else:
                if strict:
                    raise ValueError(f"Unrecognized directive: {tok[0]}")
        else:
            mebnf_workspace.write(line)

    return mebnf_workspace.getvalue()

def main(argv : list[str]):
    parser = argparse.ArgumentParser(
        prog=__file__,
        description="MXPSQL-EBNF preprocessor that outputs an EBNF file"
    )
    parser.add_argument("-if", "--input-file", dest="ifi", type=str, help="file to process")
    parser.add_argument("-of", "--output-file", dest="ofi", type=str, help="output filename")
    parser.add_argument("-ov", "--overwrite", dest="ov", action="store_true", help="overwrite a file?")

    args = parser.parse_args(argv)

    mebnf = ""
    if args.ifi:
        with open(args.ifi, "rb") as f:
            mebnf = f.read().decode("ascii")
    else:
        mebnf = sys.stdin.read()

    mebnf_out = preprocess(mebnf)
    if args.ofi:
        with open(args.ofi, "rb") as f:
            f.write(mebnf_out)
    else:
        print(mebnf_out, file=sys.stdout)

    return 0

if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
