dist: clean
	scons

0:
	mkzero-gfxmonk -p src -p SConstruct net-sandbox.xml

clean:
	rm -rf .build/
