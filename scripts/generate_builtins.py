#!python3

# Generating a file with _all_ the terraform builtins is a lot of copy and paste!
# But we can just grab code for all of these from their website examples!

import os
import re
import tempfile

from git import Repo


def trimext(file: str) -> str:
    i = file.rindex(".")
    if i == -1:
        return file
    return file[0:i]

# Some functions don't have any examples in the Terraform docs. They _must_ have overrides here else we error on generation.
overrides = {
    "base64gzip": "base64gzip(\"test\")",
    "filebase64sha256": "filebase64sha256(\"hello.txt\")",
    "filebase64sha512": "filebase64sha512(\"hello.txt\")",
    "filemd5": "filemd5(\"hello.txt\")",
    "filesha1": "filesha1(\"hello.txt\")",
    "filesha256": "filesha256(\"hello.txt\")",
    "filesha512": "filesha512(\"hello.txt\")",
    "list": "list(1, 2, 3)",
    "map": "map(\"a\", \"b\", \"c\", \"d\")",
    "templatefile": [ # These are taken by hand from the docs because our parser can't handle the multiline example
        """templatefile("${path.module}/backends.tftpl", { port = 8080, ip_addrs = ["10.0.0.1", "10.0.0.2"] })""",
        """templatefile(
               "${path.module}/config.tftpl",
               {
                 config = {
                   "x"   = "y"
                   "foo" = "bar"
                   "key" = "value"
                 }
               }
              )"""
    ],
}

# There's a number of functions we only support in the new experimental converter
experimental = {
    "abs",
    "abspath",
    "base64decode",
    "base64encode",
    "base64gzip",
    "base64sha256",
    "base64sha512",
    "basename",
    "bcrypt",
    "ceil",
    "chomp",
    "cidrhost",
    "cidrnetmask",
    "cidrsubnet",
    "compact",
    "csvdecode",
    "dirname",
    "endswith",
    "filebase64sha512",
    "fileexists",
    "filemd5",
    "filesha1",
    "filesha256",
    "filesha512",
    "floor",
    "indent",
    "join",
    "log",
    "lower",
    "max",
    "md5",
    "min",
    "parseint",
    "pathexpand",
    "pow",
    "range",
    "replace",
    "rsadecrypt",
    "sensitive",
    "sha256",
    "sha512",
    "signum",
    "sort",
    "startswith",
    "strrev",
    "substr",
    "sum",
    "timeadd",
    "timecmp",
    "timestamp",
    "title",
    "transpose",
    "trim",
    "trimprefix",
    "trimspace",
    "trimsuffix",
    "upper",
    "urlencode",
    "uuid",
}

# There's a number of functions we _don't_ support yet, so we exclude emitting these to the file
unsupported = {
    "alltrue",
    "anytrue",
    "can",
    "chunklist",
    "cidrsubnets",
    "coalesce",
    "coalescelist",
    "concat",
    "contains",
    "distinct",
    "fileset",
    "flatten",
    "format",
    "formatdate",
    "formatlist",
    "index",
    "jsondecode",
    "keys",
    "list",
    "map",
    "matchkeys",
    "merge",
    "nonsensitive",
    "one",
    "regex",
    "regexall",
    "reverse",
    "setintersection",
    "setproduct",
    "setsubtract",
    "setunion",
    "slice",
    "templatefile",
    "textdecodebase64",
    "textencodebase64",
    "tobool",
    "tolist",
    "tomap",
    "tonumber",
    "toset",
    "tostring",
    "try",
    "type",
    "uuidv5",
    "values",
    "yamldecode",
    "yamlencode",
    "zipmap",
}

if __name__ == "__main__":
    with tempfile.TemporaryDirectory() as dir:
        repo = Repo.clone_from("https://github.com/hashicorp/terraform.git", dir)

        hcl = """# DO NOT EDIT BY HAND
# This file is auto generated by ./scripts/generate_builtins.py

locals {
    # A load of the examples in the docs use `path.module` which _should_ resolve to the file system path of
    # the current module, but tf2pulumi doesn't support that so we replace it with local.path_module.
    path_module = "some/path"

    # Some of the examples in the docs use `path.root` which _should_ resolve to the file system path of the
    # root module of the configuration, but tf2pulumi doesn't support that so we replace it with
    path_root = "root/path"
}
"""

        functions_path = os.path.join(dir, "website", "docs", "language", "functions")
        for file in sorted(os.listdir(functions_path)):
            if file == "index.mdx":
                continue # skip the index file

            with open(os.path.join(functions_path, file)) as f:
                mdx = f.read().splitlines()

            # Default to the file name minus extension, but look for "# `NAME` Function" in the code below
            function_name = trimext(os.path.basename(file))

            # Look for the first ``` after ## Examples
            in_code = False
            in_examples = False
            example_code = []
            for line in mdx:
                m = re.match("# `([a-z]+)` Function", line)
                if m:
                    function_name = m.group(1)

                if "## Examples" in line:
                    in_examples = True
                    continue

                if in_examples:
                    if line.startswith("```"):
                        in_code = not in_code
                        continue

                    if in_code:
                        if line.startswith("> "):
                            code = line[1:].strip().replace("path.module", "local.path_module").replace("path.root", "local.path_root")
                            example_code.append(code)

            if function_name in overrides:
                override = overrides[function_name]
                if isinstance(override, list):
                    example_code = override
                else:
                    example_code = [override]
            elif not example_code:
                raise Exception(f"No examples found for {function_name}")

            if function_name in unsupported:
                continue

            if function_name in experimental:
                # Write out an #if EXPERIMENTAL if it's "unsupported"
                hcl += "\n#if EXPERIMENTAL\n"

            # Only write out the example if we support it
            hcl += "\n# Examples for " + function_name + "\n"
            for index, example in enumerate(example_code):
                suffix = ""
                if len(example_code) > 1:
                    # If we have more than one example suffix with the index
                    suffix = str(index)

                hcl += "output \"func" + function_name.capitalize() + suffix + "\" {\n"
                hcl += "  value = " + example + "\n"
                hcl += "}\n"

            if function_name in experimental:
                hcl += "\n#endif\n"
            hcl += "\n"


        targetFile = os.path.join(os.path.dirname(__file__), "..", "pkg", "tf2pulumi", "convert", "testdata", "builtins", "main.tf")
        with open(targetFile, "w") as f:
            f.write(hcl)