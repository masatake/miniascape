#
# Copyright (C) 2012 Satoru SATOH <ssato@redhat.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
import jinja2_cui.cui as JC
import logging
import os.path
import sys


M_CONF_DIR = "/etc/miniascape/default"
M_TMPL_DIR = "/usr/share/miniascape/templates/autoinstall.d"


def main(argv):
    p = JC.option_parser()
    (options, args) = p.parse_args(argv[1:])

    if not args:
        p.print_help()
        sys.exit(0)

    logging.getLogger().setLevel(DEBUG if options.debug else INFO)

    tmpl = args[0]
    ctx = JC.parse_and_load_contexts(
        options.contexts, options.encoding, options.werror
    )
    paths = JC.parse_template_paths(tmpl, options.template_paths)

    if options.vars:
        vars = list(find_vars(tmpl, paths))
        for v in vars:
            print v
        sys.exit(0)

    result = render(tmpl, ctx, paths)


# vim:sw=4:ts=4:et: