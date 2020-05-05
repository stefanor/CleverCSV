# -*- coding: utf-8 -*-

import code

from cleo import Command

from clevercsv import __version__
from clevercsv.utils import get_encoding
from clevercsv.wrappers import detect_dialect

from ._utils import parse_int


class CodeCommand(Command):
    """
    Generate Python code for importing the CSV file

    code
        { path : The path to the CSV file }
        { --e|encoding= : Set the encoding of the CSV file. }
        { --i|interact : Drop into a Pyohon interactive shell. }
        { --n|num-chars= : Limit the number of characters to read for
        detection. This will speed up detection but may reduce accuracy. }
        { --p|pandas : Write code that imports to a Pandas DataFrame }
    """

    help = """\
The <info>code</info> command generates Python code for importing the specified 
CSV file. This is especially useful if you don't want to repeatedly detect the 
dialect of the same file. Simply run:

clevercsv code yourfile.csv

and copy the generated code to a Python script.
"""

    def handle(self):
        filename = self.argument("path")
        encoding = self.option("encoding") or get_encoding(filename)
        num_chars = parse_int(self.option("num-chars"), "num-chars")
        dialect = detect_dialect(
            filename,
            num_chars=num_chars,
            encoding=encoding,
            verbose=self.option("verbose"),
        )
        if dialect is None:
            return self.line("Dialect detection failed.")

        d = '"\\t"' if dialect.delimiter == "\t" else f'"{dialect.delimiter}"'
        q = '"%s"' % (dialect.quotechar.replace('"', '\\"'))
        e = repr(f"{dialect.escapechar}").replace("'", '"')
        base = [
            "",
            f"# Code generated with CleverCSV version {__version__}",
            "",
            "import clevercsv",
        ]
        if self.option("pandas"):
            thecode = base + [
                "",
                f'df = clevercsv.csv2df("{filename}", delimiter={d}, quotechar={q}, escapechar={e})',
                "",
            ]
        else:
            enc = "None" if encoding is None else f'"{encoding}"'
            thecode = base + [
                "",
                f'with open("{filename}", "r", newline="", encoding={enc}) as fp:',
                "    reader = clevercsv.reader(fp, "
                + f"delimiter={d}, quotechar={q}, escapechar={e})",
                "    rows = list(reader)",
                "",
            ]

        if not self.option("interact"):
            self.line("\n".join(thecode))
            return

        console = code.InteractiveConsole()
        for line in thecode:
            retcode = console.push(line)
        if retcode:
            self.line(
                "An error occurred starting the interactive console. "
                "Printing commands instead:\n"
            )
            self.line("\n".join(thecode))
            return
        self.line("Dropping you into an interactive shell.\n")
        banner = "CleverCSV has loaded the data into the variable: "
        banner += "df" if self.option("pandas") else "rows"
        console.interact(banner=banner)
