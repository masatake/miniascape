TOPDIR = .
SITE ?=

miniascape_OPTIONS = -t $(TOPDIR)/templates


all: build

build:
	miniascape b $(miniascape_OPTIONS) -C $(TOPDIR)/$(SITE) -w $(TOPDIR)/out

setup:
	for d in $(wildcard $(TOPDIR)/out/guests.d/*); do test -d $$d && make -C $$d setup || :; done 

.PHONY: build setup