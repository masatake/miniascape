#
# Copyright (C) 2013 Satoru SATOH <ssato@redhat.com>
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
import miniascape.config as C
import miniascape.globals as G
import miniascape.guest as MG
import miniascape.options as O
import miniascape.template as T
import miniascape.utils as U

import anyconfig as AC
import logging
import optparse
import os.path
import os
import sys
import yaml

from itertools import groupby
from operator import itemgetter


def _outdir(topdir):
    """
    :param topdir: Working top dir
    :param name: Site's name

    :return: Output top dir, e.g. $workdir/conf.d
    """
    return os.path.join(topdir, "conf.d")


def gen_conf_files(conf, tmpldirs, workdir):
    """
    :param conf: Object holding config parameters
    :param tmpldirs: Template path list
    :param workdir: Working top dir, e.g. miniascape-workdir-201303121
    """
    tpaths = [os.path.join(d, "config") for d in tmpldirs]
    outdir = _outdir(workdir)

    if not os.path.exists(outdir):
        os.makedirs(outdir)

    logging.info("Generating site config files into %s" % outdir)

    for tmpl, subdir in (("common.j2", "common"), ("host.j2", "host.d")):
        T.renderto(tpaths, conf, tmpl,
                   os.path.join(outdir, subdir, "00_base.yml"))

    for net in conf.get("networks"):
        netoutdir = os.path.join(outdir, "networks.d", net["name"])
        if not os.path.exists(netoutdir):
            os.makedirs(netoutdir)

        T.renderto(tpaths, net, "network.j2",
                   os.path.join(netoutdir, "00_base.yml"))

    guests_key = "guests"
    for ggroup in conf.get("guests"):
        ggoutdir = os.path.join(outdir, "guests.d", ggroup["name"])
        if not os.path.exists(ggoutdir):
            os.makedirs(ggoutdir)

        ggroup_conf = dict()
        for k, v in ggroup.iteritems():
            if k != guests_key:
                ggroup_conf[k] = v

        AC.dump(ggroup_conf, os.path.join(ggoutdir, "00_base.yml"))

        for guest in ggroup["guests"]:
            name = guest.get("name", guest.get("hostname", guest.get("fqdn")))
            goutdir = os.path.join(ggoutdir, name)
            if not os.path.exists(goutdir):
                os.makedirs(goutdir)

            AC.dump(guest, os.path.join(goutdir, "00_base.yml"))


def option_parser():
    defaults = dict(force=False, yes=False, **O.M_DEFAULTS)
    defaults["confdir"] = None

    p = O.option_parser(defaults, "%prog [OPTION ...]")

    p.add_option("-f", "--force", action="store_true",
                 help="Force outputs even if these exist")
    return p


def main(argv):
    p = option_parser()
    (options, args) = p.parse_args(argv[1:])

    U.init_log(options.verbose)
    options = O.tweak_tmpldir(options)

    if not options.confdir:
        options.confdir = raw_input("Specify config src dir: ")

    if os.path.exists(options.workdir) and not options.force:
        yesno = raw_input(
            "Are you sure to re-generate configs in %s ? [y/n]: " %
            options.workdir
        )
        if not yesno.strip().lower().startswith('y'):
            print >> "Cancel re-generation of configs..."
            sys.exit(0)

    conf = AC.load(options.confdir)
    assert conf is not None, "No config loaded from: " + options.confdir

    gen_conf_files(conf, options.tmpldir, options.workdir)


if __name__ == '__main__':
    main(sys.argv)

# vim:sw=4:ts=4:et: