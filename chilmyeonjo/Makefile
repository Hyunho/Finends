SHELL := /bin/zsh

WEB_DIR := $(CURDIR)/web

.PHONY: web web-install web-test

web:
	cd "$(WEB_DIR)" && source ~/.zshrc && bundle check || bundle install
	cd "$(WEB_DIR)" && source ~/.zshrc && bin/rails server

web-install:
	cd "$(WEB_DIR)" && source ~/.zshrc && bundle install

web-test:
	cd "$(WEB_DIR)" && source ~/.zshrc && bin/rails test
