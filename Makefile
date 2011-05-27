dist: clean
	scons

0:
	mkzero-gfxmonk -p src -p SConstruct net-sandbox.xml

0compile: phony
	0local net-sandbox.xml
	[ -d net-sandbox-local ] || 0compile setup net-sandbox-local.xml
	cd net-sandbox-local && 0compile build
	@echo '####'
	@echo 0launch `find net-sandbox-local | fgrep /0install/net-sandbox-local.xml`

0compile-run: 0compile
	0launch `find net-sandbox-local | fgrep /0install/net-sandbox-local.xml`

clean:
	rm -rf .build/ net-sandbox-local*

.PHONY: phony
