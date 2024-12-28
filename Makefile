SD_SOURCE ?= ../speech-dispatcher

all: sd_viewer

sd_viewer: viewer.c ${SD_SOURCE}/src/modules/module_main.c ${SD_SOURCE}/src/modules/module_readline.c ${SD_SOURCE}/src/modules/module_process.c
	gcc -Wall -o $@ $^ -I ${SD_SOURCE}/include -I ${SD_SOURCE}/src/common -I ${SD_SOURCE}/src/modules

.PHONY: clean
clean:
	rm sd_viewer

.PHONY: install
install:
	install sd_viewer /usr/lib/speech-dispatcher-modules/sd_viewer

.PHONY: uninstall
uninstall:
	rm -f /usr/lib/speech-dispatcher-modules/sd_viewer

