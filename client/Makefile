# On OSX the PATH variable isn't exported unless "SHELL" is also set, see: http://stackoverflow.com/a/25506676
SHELL = /bin/bash
NODE_BINDIR = ./node_modules/.bin
export PATH := $(NODE_BINDIR):$(PATH)

# Available locales for the app.
LOCALES = de_DE
LOCALE_FILES ?= $(patsubst %,./translations/%.po,$(LOCALES))

# Makefile Targets
.PHONY: translations

translations:
# Extract gettext strings from templates and source using gettext-extract
# (instead of using the equally named gettext-extract from easygettext
	./node_modules/gettext-extract/bin/gettext-extract
# Generate .po files for each available language.
	@for lang in $(LOCALES); do \
		export PO_FILE=./translations/$$lang.po; \
		echo "msgmerge --update $$PO_FILE $@"; \
		mkdir -p $$(dirname $$PO_FILE); \
		[ -f $$PO_FILE ] && msgmerge --lang=$$lang --update $$PO_FILE ./translations/template.pot || msginit --no-translator --locale=$$lang --input=./translations/template.pot --output-file=$$PO_FILE; \
		msgattrib --no-wrap --no-obsolete -o $$PO_FILE $$PO_FILE; \
	done;
	gettext-compile --output src/translations.json $(LOCALE_FILES)

