#! /bin/bash
set -ex

# see also: http://red.ht/2fXMOtA
#
# Prerequisites:
# - RH Login account to download RHEL, RHUI and RH Gluster FS ISO images into RHUA
# 
# Setup yum repos:
#
# 1. RHEL: a or b
#    a. Setup another www server and make it providing loop back mounted RHEL ISO repo
#    b. Put RHEL ISO somewhere on RHUA and make it accessible from RHUA, CDS and LB nodes
#       e.g. install httpd during kickstart installation, start httpd (systemclt start httpd),
#       mkdir -p /var/www/html/pub/rhel/7/3/ && mount -o ro,loop /path/to/rhel-7.3.iso /var/www/...,
#       arrange yum repo file for RHEL repo.      
#
# 2. RHUI:
#    0) Download ISO image from RH site:
#       https://access.redhat.com/downloads/content/147/ver=3/rhel---7/3.0/x86_64/product-software/
#    1) mount -o ro,loop <RHUI_3_beta_1.iso> /mnt
#    2) cd /mnt && ./setup_package_repos
#    3) mkdir -p /var/www/html/pub/rhui/3/beta_1 && mount -o bind /opt/rhui/ /var/www/...
#    4) arrange yum repo file for RHUI repo
#
# 3. RH Gluster FS
#    0) Download ISO image from RH site:
#       https://access.redhat.com/downloads/content/186/ver=3.1/rhel---7/3.1/x86_64/product-software
#    1) mkdir -p /var/www/html/pub/rhgs/3.1/ && mount -o ro,loop <RHGS iso> /var/www/...
#    2) arrange yum repo file for RH GlusterFS repo
#
# Install RHUI (rhui-installer) RPMs on RHUA:
#
#
# Setup password-less connection to CDS and LB from RHUA:
#
#

ISO_DIR=/root/setup/

RHEL_ISO=rhel-server-7.3-x86_64-dvd.iso
RHUI_ISO=$(cd ${ISO_DIR} && ls -1 RHUI-3*.iso | head -n 1)
RHGS_ISO=$(cd ${ISO_DIR} && ls -1 rhgs-3.1*.iso | head -n 1)

MNT_DIR=/var/www/html
RHEL_SUBDIR=pub/rhel/7/3/
RHUI_SUBDIR=pub/rhui/3/beta1/
RHGS_SUBDIR=pub/rhgs/3.1/

rpm -q httpd && (systemctl is-active httpd || systemctl start httpd)

cd ${MNT_DIR}
mkdir -p ${RHEL_SUBDIR:?} ${RHUI_SUBDIR:?} ${RHGS_SUBDIR:?}
mount -o ro,loop ${ISO_DIR}/${RHEL_ISO:?}  ${RHEL_SUBDIR}
mount -o ro,loop ${ISO_DIR}/${RHUI_ISO:?}  ${RHUI_SUBDIR}
mount -o ro,loop ${ISO_DIR}/${RHGS_ISO:?}  ${RHGS_SUBDIR}

cat << EOF > /etc/yum.repos.d/rhel-7.3-iso.repo
[rhel-7.3]
name=RHEL 7.3
baseurl=http://$(hostname -f)/${RHEL_SUBDIR}/
enabled=1
gpgcheck=1
EOF

cat << EOF > /etc/yum.repos.d/rhui-3-beta1-iso.repo
[rhui-3-beta-1]
name=RHUI 3 beta 1
baseurl=http://$(hostname -f)/${RHUI_SUBDIR}/
enabled=1
# FIXME:
gpgcheck=0
EOF

cat << EOF > /etc/yum.repos.d/rhgs-3.1-iso.repo
[rhgs-3.1]
name=RH Gluset FS 3.x
baseurl=http://$(hostname -f)/${RHGS_SUBDIR}/
enabled=1
EOF

yum install -y rhui-installer

ssh-keygen -t rsa -P '' -f ~/.ssh/id_rsa
remote_nodes="{{ rhui.lb.servers|join(' ') }} {{ rhui.cdses|join(' ') }}"
for node in ${remote_nodes}
do
    ssh-copy-id ${node} && scp /etc/yum.repos/*.repo ${node}:/etc/yum.repos.d/
done

# vim:sw=4:ts=4:et:
