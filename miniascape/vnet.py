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
from miniascape.globals import M_ENCODING, M_CONF_DIR, M_TMPL_DIR, \
    M_WORK_TOPDIR

import miniascape.template as T
import miniascape.utils as U
import jinja2_cui.render as R

import glob
import logging
import optparse
import os.path
import os
import subprocess
import sys
import yaml

from itertools import groupby
from logging import DEBUG, INFO
from operator import itemgetter


def load_network_configs(netconfs):
    """Load network configuration files.
    """
    return R.parse_and_load_contexts(netconfs, M_ENCODING, False)


def aggregate_guest_networks(filepaths):
    """
    Aggregate guest's network interface info from each guest configurations and
    return list of host list grouped by each networks.
    """
    guests = [R.load_context(f) for f in filepaths]
    hostsets = [
        list(g) for k, g in groupby(
            U.concat(g["interfaces"] for g in guests), itemgetter("network")
        )
    ]
    return hostsets


def load_configs(confdir):
    gconfs = glob.glob(os.path.join(confdir, "guests.d/*.yml"))
    nconfs = glob.glob(os.path.join(confdir, "networks.d/*.yml"))

    hostsets = aggregate_guest_networks(gconfs)
    nets = R.MyDict.createFromDict()

    for nc in nconfs:
        netctx = load_network_configs([nc])
        name = netctx["name"]

        hss = [hs for hs in hostsets if hs and hs[0]["network"] == name]
        if hss:
            netctx["hosts"] = hss[0]

        nets[name] = netctx

    return nets


def gen_vnet_files(tmpldir, confdir, workdir, force):
    nets = load_configs(confdir)
    outdir = os.path.join(workdir, "libvirt/networks.d")

    if not os.path.exists(outdir):
        os.makedirs(outdir)

    for name in nets:
        netconf = os.path.join(outdir, "%s.yml" % name)
        if os.path.exists(netconf) and not force:
            logging.warn("Net conf already exists: " + netconf)
            return

        yaml.dump(nets[name], open(netconf, 'w'))

        netxml = os.path.join(outdir, "%s.xml" % name)
        if os.path.exists(netxml) and not force:
            logging.warn("Net xml already exists: " + netxml)
            return

        cmd = T.mk_tmpl_cmd(
            [os.path.join(tmpldir, "libvirt")], [netconf], netxml,
            os.path.join(tmpldir, "libvirt/network.xml"),
        )

        logging.debug("Generating network xml: " + cmd)
        subprocess.check_output(cmd, shell=True)


def option_parser(defaults=None):
    if defaults is None:
        defaults = dict(
            tmpldir=M_TMPL_DIR,
            confdir=M_CONF_DIR,
            workdir=M_WORK_TOPDIR,
            force=False,
            debug=False,
        )

    p = optparse.OptionParser("%prog [OPTION ...]")
    p.set_defaults(**defaults)

    p.add_option("-t", "--tmpldir", help="Template top dir [%default]")
    p.add_option("-c", "--confdir",
        help="Configuration files top dir [%default]"
    )
    p.add_option("-w", "--workdir", help="Working top dir [%default]")
    p.add_option("-f", "--force", action="store_true",
        help="Force outputs even if these exist"
    )

    p.add_option("-D", "--debug", action="store_true", help="Debug mode")

    return p


def main(argv):
    p = option_parser()
    (options, args) = p.parse_args(argv[1:])

    logging.getLogger().setLevel(DEBUG if options.debug else INFO)

    gen_vnet_files(
        options.tmpldir, options.confdir, options.workdir, options.force
    )


if __name__ == '__main__':
    main(sys.argv)

# vim:sw=4:ts=4:et: