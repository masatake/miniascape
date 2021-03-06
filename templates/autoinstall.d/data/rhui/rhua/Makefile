# Makefile to fetch RHUI DVD iso image, install RHUI and generate certs.
# Requirements: openssl, curl or wget
# Author: Satoru SATOH <ssato@redhat.com>
# License: MIT
#
WORKDIR ?= /root/setup
CERTSDIR = $(WORKDIR)/certs
QPID_SSL_VALID ?= 120

# @see http://red.ht/RAKEyc :
RHUI_CERT ?= $(WORKDIR)/$(notdir {{ rhui_entitlement_certs[0] }})
RHUI_ISO ?= RHEL-6-RHUI-2-LATEST-Server-x86_64-DVD.iso
RHUI_URL ?= https://cdn.redhat.com/content/dist/rhel/rhui/server/6/6Server/x86_64/rhui/2/iso/$(RHUI_ISO)

FETCH_PROG ?= curl

ifeq ($(FETCH_PROG),curl)
# TODO: curl doesn't look work well:
fetch_RHUI_ISO = curl -v --cacert /etc/rhsm/ca/redhat-uep.pem --cert $(RHUI_CERT) -O
{% if proxy is defined and proxy.fqdn is defined -%}
fetch_RHUI_ISO += --proxy https://{{ proxy.fqdn }}:{{ proxy.port|default("443") }}
{%     if proxy.user is defined -%}
fetch_RHUI_ISO += --proxy-user {{ proxy.user }}:{{ proxy.password }}
{%-    endif %}
{%- endif %}
else
{% if proxy is defined and proxy.fqdn is defined -%}
fetch_RHUI_ISO = env https_proxy=https://{{ proxy.fqdn }}:{{ proxy.port|default("443") }} wget --certificate $(RHUI_CERT)
{%     if proxy.user is defined -%}
fetch_RHUI_ISO += --proxy-user={{ proxy.user }} --proxy-password={{ proxy.password }}
{%-    endif %}
{% else -%}
fetch_RHUI_ISO = wget --ca-certificate /etc/rhsm/ca/redhat-uep.pem --certificate $(RHUI_CERT) --secure-protocol=SSLv3
{%- endif %}
endif

CDS_CLUSTER ?= {{ cds.clusters }}

SUBSCRIPTION_MANAGER_OPTIONS ?=
SUBSCRIPTION_MANAGER_LOGIN_OPTIONS	?= {{ "--username=%s" % rhn.username if rhn.username }} {{ "--password=%s" % rhn.password if rhn.password }}


all:
	@echo "Usage: make [VAR_OVERRIDES ...]"
	@echo ""
	@echo "ex. make RHUI_URL=http://example.com/rhui.iso fetch_RHUI_ISO='curl ' fetch"
	@echo "ex. make install"
	@echo ""
	@echo "  Targets for RHUA: register check fetch install certs genconf genkey"
	@echo ""

# common:
register:
	subscription-manager unregister || :
	subscription-manager clean || :
	subscription-manager register --type=rhui $(SUBSCRIPTION_MANAGER_OPTIONS) $(SUBSCRIPTION_MANAGER_LOGIN_OPTIONS)
	subscription-manager repos --disable '*'
	subscription-manager repos --enable rhel-6-server-rhui-rpms --enable rhel-x86_64-6-rhui-2-rpms
	@echo "Now you ready to generate RHUI entitlement cert on: https://access.redhat.com/management/consumers/ "

check: $(WORKDIR)/check.stamp
$(WORKDIR)/check.stamp:
	date
	fqdn=`hostname -f`; test "x$$fqdn" = 'x{{ fqdn }}'
	rpm -q ntp && service ntpd status && which ntptime && ntptime || :
	test -f check.sh && bash -x ./check.sh || :
	touch $@

fetch: $(RHUI_ISO)
$(RHUI_ISO):
	$(fetch_RHUI_ISO) $(RHUI_URL)

install: $(WORKDIR)/install.stamp
$(WORKDIR)/install.stamp: $(RHUI_ISO)
	mount -o ro,loop $(RHUI_ISO) /mnt
	cd /mnt && ./install_RHUA.sh && cd - && umount /mnt
	touch $@

certs: $(CERTSDIR)/certs.stamp
$(CERTSDIR)/certs.stamp:
	test -f $@ || make -C $(CERTSDIR)

# TODO:
#$(CERTSDIR)/certs.stamp:
#	/usr/share/rh-rhua/rhui_certs/create_rhui_ssl_certs.sh \
#		--country {{ rhui.ssl.country|default('JP') }} \
#		--state {{ rhui.ssl.state|default('Tokyo') }} \
#		$(shell hostname) {{ cdsservers|join(' ', attribute='fqdn') }}

genconf: $(WORKDIR)/genconf.stamp
$(WORKDIR)/genconf.stamp: $(CERTSDIR)/certs.stamp $(WORKDIR)/answers.txt
	rhui-installer $(WORKDIR)/answers.txt 2>&1 | tee $(WORKDIR)/rhui-install.log

genkey: $(WORKDIR)/genkey.stamp
$(WORKDIR)/genkey.stamp: $(WORKDIR)/gen_rpm_gpgkey.sh
	bash -x $< 2>&1 | tee $<.log
	install -m 644 $(WORKDIR)/RPM-GPG-KEY-rhui-custom /etc/pki/rpm-gpg/

.PHONY: register check fetch install certs genconf genkey

