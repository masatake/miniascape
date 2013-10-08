#
# Copyright (C) 2012, 2013 Satoru SATOH <ssato@redhat.com>
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
from miniascape.globals import LOGGER as logging, set_loglevel

import miniascape.config as C
import miniascape.globals as G
import miniascape.options as O
import miniascape.template as T
import miniascape.utils as U

import anyconfig as A
import optparse
import os.path
import os
import sys


def _netoutdir(topdir, host_subdir=G.M_HOST_OUT_SUBDIR,
               net_subdir=G.M_NETS_OUT_SUBDIR):
    """
    :param topdir: Working top dir
    """
    return os.path.join(topdir, host_subdir, net_subdir)


def hosts_w_unique_macs(nc):
    """
    :return: list of hosts having nics w unique mac addresses assigned.
    """
    return [
        h for h in nc.get("hosts", []) if "mac" in h and h["mac"] != "RANDOM"
    ]


def _find_template(tmpldirs, template):
    for tdir in tmpldirs:
        tmpl = os.path.join(tdir, template)
        if os.path.exists(tmpl):
            return tmpl

    logging.warn("Could not find template %s in paths: %s" %
                 (template, str(tmpldirs)))
    return template  # Could not find in tmpldirs


def gen_vnet_files(cf, tmpldirs, workdir, force):
    nets = cf.load_nets_confs()
    outdir = _netoutdir(workdir)
    tpaths = [os.path.join(d, "host") for d in tmpldirs]

    if not os.path.exists(outdir):
        os.makedirs(outdir)

    for name in nets:
        netconf = os.path.join(outdir, "%s.yml" % name)
        if os.path.exists(netconf) and not force:
            logging.warn("Net conf already exists: " + netconf)
            return

        logging.debug("Dump conf for the net: " + name)
        A.dump(nets[name], netconf)

        netxml = os.path.join(outdir, "%s.xml" % name)
        if os.path.exists(netxml) and not force:
            logging.warn("Net xml already exists: " + netxml)
            return

        nc = A.load(netconf)
        nc["hosts"] = hosts_w_unique_macs(nc)

        logging.debug("Generating network xml: " + netxml)
        T.renderto(tpaths, nc, _find_template(tmpldirs, "host/network.xml"),
                   netxml)

    T.renderto(tpaths, {"networks": [n for n in nets]},
               _find_template(tmpldirs, "host/network_register.sh"),
               os.path.join(outdir, "network_register.sh"))


def gen_host_files(cf, tmpldirs, workdir, force):
    conf = cf.load_host_confs()
    gen_vnet_files(cf, tmpldirs, workdir, force)

    for k, v in conf.get("host_templates", {}).iteritems():
        src = v.get("src", None)
        dst = v.get("dst", src)

        if src is None:
            continue

        if os.path.sep in src:
            srcdirs = [os.path.join(d, os.path.dirname(src)) for d in tmpldirs]
        else:
            srcdirs = tmpldirs

        # strip dir part as it will be searched from srcdir.
        src = os.path.basename(src)
        dst = os.path.join(workdir, dst)

        logging.info("Generating %s from %s [%s]" % (dst, src, k))
        T.renderto(srcdirs + [workdir], conf, src, dst)


def option_parser():
    defaults = dict(force=False, yes=False, dryrun=False, **O.M_DEFAULTS)
    p = O.option_parser(defaults, "%prog [OPTION ...]")

    p.add_option("-f", "--force", action="store_true",
                 help="Force outputs even if these exist")
    p.add_option("", "--dryrun", action="store_true", help="Dry run mode")
    return p


def main(argv):
    p = option_parser()
    (options, args) = p.parse_args(argv[1:])

    set_loglevel(options.verbose)
    options = O.tweak_tmpldir(options)

    cf = C.ConfFiles(options.confdir)

    houtdir = os.path.join(options.workdir, G.M_HOST_CONF_SUBDIR)
    if os.path.exists(houtdir) and not options.force:
        yesno = raw_input(
            "Are you sure to generate networks in %s ? [y/n]: " %
            options.workdir
        )
        if not yesno.strip().lower().startswith('y'):
            print >> "Cancel creation of networks..."
            sys.exit(0)

        options.force = True

    gen_host_files(cf, options.tmpldir, options.workdir, options.force)


if __name__ == '__main__':
    main(sys.argv)

# vim:sw=4:ts=4:et:
