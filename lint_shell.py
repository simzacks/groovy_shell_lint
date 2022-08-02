"""
This module uses shellcheck to lint bash embedded in groovy files.
It saves the content of the sh function to a tmp file, /tmp/lintme.sh
and then executes shellcheck against that.

Input parameters are either/or directories or files. If a dir is given,
it will recursively go to all subdirectories as well.
Multiple files/dirs can be given
"""

import re
import os
import subprocess
import sys

TMPFILE = "/tmp/lintme.sh"
IGNORE = "SC2154,SC1091,SC1090"
LINTER = ["shellcheck", '-s', 'bash', '-e', IGNORE,  TMPFILE]

def lint_sh_content(f_data, filename):
    start_sh = 0
    # the below pattern will look for the whole word sh, but not if it has a
    # dot before it (for example a filename
    p_sh = re.compile(r'(?<!\.)\bsh\b')
    # the below pattern will look for the first instance of either 3 quotes in
    # a row or one quote, both double or single quotes. In python regex, the
    # order the pattern is provided impacts what it finds, so if the one
    # quote was listed before the 3 quotes, it would always find the one and
    # never the 3.
    p_startq = re.compile(r"\"\"\"|\"|\'\'\'|\'")
    while True:
        sh = p_sh.search(f_data, start_sh)
        if not sh:
            break
        start_sh = sh.end()
        start_quote = p_startq.search(f_data, sh.end())
        if not start_quote:
            print("sh with no quotes!")
        else:
            # the below pattern looks for the same quotation set that was found
            # in the start of the content, however, only if there is no
            # backslash before it.
            p_endq = re.compile(r'(?<!\\){}'.format(start_quote.group(0)))
            endquote = p_endq.search(f_data, start_quote.end())
            if not endquote:
                print("sh with no end quotes")
                break
            content = f_data[start_quote.end():endquote.start()]
            vars = re.findall(r'\${(.*?)}', content)
            for var in vars:
                # ${...} is for groovy var substitution, but the shell checker
                # doesn't see them, so I remove the subsitituion chars and
                # make it look like it was already substitued
                content = content.replace("${{{}}}".format(var),
                                          "${}".format(var))
            # the escape was so that the actual char would get into the shell.
            content = content.replace("\\", "")
            with open(TMPFILE, "w") as w:
                w.write(content)
            res = subprocess.run(LINTER, stdout=subprocess.PIPE)
            # capture stdout in order to replace the tmp file name and line
            # number with the actual filename and line number.
            if res.stdout:
                if b"In %b" % TMPFILE.encode() in res.stdout:
                    line = f_data.count("\n", 0, start_sh)
                    final_msg = b""
                    brk = b"\nIn %b line " % TMPFILE.encode()
                    hdr = b"\nIn %b line " % filename.encode()
                    lst_probs = res.stdout.split(brk)
                    for l in lst_probs:
                        num_match = re.match(b"\d+", l)
                        if num_match:
                            fake_num = num_match.group(0)
                            real_num = str(int(fake_num) + line).encode()
                            final_msg += b"%b%b" % (hdr, l.replace(fake_num,
                                                    real_num, 1))
                print(final_msg.decode())


def lintfile(current_file):
    with open(current_file) as f:
        fdata = f.read()
        lint_sh_content(fdata, current_file)


def lintdir(thedir):
    for root, dirs, files in os.walk(thedir):
        for item in files:
            current_file = "{}/{}".format(root, item)
            if current_file.endswith(".groovy"):
                lintfile(current_file)


if __name__ == "__main__":
    if len(sys.argv) > 1:
        for i in range(len(sys.argv)-1):
            item = sys.argv[i+1]
            if os.path.isdir(item):
                lintdir(item)
            elif os.path.isfile(item):
                lintfile(item)
            else:
                raise Exception("{} is not a file or diir".format(item))
    else:
        raise Exception("Usage: lint_shell.py [DIR | FILE] ...")
