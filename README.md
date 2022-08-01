This module uses shellcheck to lint bash embedded in groovy files.
It saves the content of the sh function to a tmp file, /tmp/lintme.sh
and then executes shellcheck against that.

Input parameters are either/or directories or files. If a dir is given,
it will recursively go to all subdirectories as well.
Multiple files/dirs can be given
