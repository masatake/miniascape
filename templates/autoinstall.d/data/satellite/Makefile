# Makefile to install RHN Satellite
# Author: Satoru SATOH <ssato@redhat.com>
# License: MIT
#
WORKDIR ?= /root/setup

# Make a symlink to the actual ISO images in advance.
SATELLITE_ISO ?= $(WORKDIR)/satellite.iso
ANSTXT ?= $(WORKDIR)/answers.txt

EXTRA_INSTALLER_OPTS ?= --disconnected


all: check install genkey

check: $(WORKDIR)/check.stamp
$(WORKDIR)/check.stamp:
	date
	fqdn=`hostname -f`; test "x$$fqdn" = 'x{{ fqdn }}'
	touch $@

install: $(WORKDIR)/install.stamp
$(WORKDIR)/install.stamp: $(SATELLITE_ISO)
	rpm --import /etc/pki/rpm-gpg/RPM-GPG-KEY-redhat-release
	mount -o ro,loop $(SATELLITE_ISO) /mnt
	cd /mnt && ./install.pl --answer-file=$(ANSTXT) $(EXTRA_INSTALLER_OPTS) && cd - && umount /mnt
	touch $@

genkey: $(WORKDIR)/genkey.stamp
$(WORKDIR)/genkey.stamp: $(WORKDIR)/gen_rpm_gpgkey.sh
	bash -x $< 2>&1 | tee $<.log

#	install -m 644 $(WORKDIR)/RPM-GPG-KEY-satellite-custom /etc/pki/rpm-gpg/

.PHONY: check install
