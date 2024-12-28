/*
 * viewer.c - Speech dispatcher module that communicates with the viewer
 *
 * Copyright (C) 2020-2022 Samuel Thibault <samuel.thibault@ens-lyon.org>
 * Copyright (C) 2024 Michael Schierl <schierlm@gmx.de>
 * All rights reserved.
 *
 * Redistribution and use in source and binary forms, with or without
 * modification, are permitted provided that the following conditions
 * are met:
 * 1. Redistributions of source code must retain the above copyright
 *    notice, this list of conditions and the following disclaimer.
 * 2. Redistributions in binary form must reproduce the above copyright
 *    notice, this list of conditions and the following disclaimer in the
 *    documentation and/or other materials provided with the distribution.
 *
 * THIS SOFTWARE IS PROVIDED BY Samuel Thibault AND CONTRIBUTORS ``AS IS'' AND
 * ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
 * IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
 * ARE DISCLAIMED.  IN NO EVENT SHALL THE REGENTS OR CONTRIBUTORS BE LIABLE
 * FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
 * DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS
 * OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION)
 * HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
 * LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY
 * OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF
 * SUCH DAMAGE.
 */

#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <string.h>
#include <sys/socket.h>
#include <sys/un.h>

#include "module_main.h"

static char send_buffer[102400];
static int data_socket = -1;

void send_message(const char* action, const char* message)
{
	ssize_t w;
	snprintf(send_buffer, sizeof(send_buffer), "%s %s", action, message);
	w = write(data_socket, send_buffer, strlen(send_buffer) + 1);
	if (w == -1) {
		perror("Write failure");
		fprintf(stderr, "Send message failed\n");
	}
}

int module_config(const char *configfile)
{
	return 0;
}

int module_init(char **msg)
{
	int ret;
	struct sockaddr_un addr = {};

	fprintf(stderr, "Initializing\n");

	data_socket = socket(AF_UNIX, SOCK_DGRAM, 0);
	if (data_socket == -1) {
		perror("Create failure");
		fprintf(stderr, "Create socket failed\n");
		return -1;
	}

    memset(&addr, 0, sizeof(addr));
	addr.sun_family = AF_UNIX;
	snprintf(addr.sun_path, sizeof(addr.sun_path), "/run/user/%d/speech-dispatcher/viewer.sock", getuid());
	ret = connect(data_socket, (const struct sockaddr *) &addr, sizeof(addr));
	if (ret == -1) {
		perror("Connect failure");
		fprintf(stderr, "Connect socket failed\n");
		data_socket = -1;
		return -1;
	}
	send_message("CONNECT", "");

	*msg = strdup("ok!");
	return 0;
}

SPDVoice **module_list_voices(void)
{
	/* Return list of voices */
	SPDVoice **ret = malloc(2*sizeof(*ret));

	ret[0] = malloc(sizeof(*(ret[0])));
	ret[0]->name = strdup("Viewer");
	ret[0]->language = NULL;
	ret[0]->variant = NULL;

	ret[1] = NULL;

	return ret;
}


int module_set(const char *var, const char *val)
{
	char buf[1024];
	snprintf(buf, sizeof(buf), "%s=%s", var, val);
	send_message("SET", buf);
	return 0;
}

int module_audio_set(const char *var, const char *val)
{
	char buf[1024];
	snprintf(buf, sizeof(buf), "%s=%s", var, val);
	send_message("SET_AUDIO", buf);
	return 0;
}

int module_audio_init(char **status)
{
	return 0;
}

int module_loglevel_set(const char *var, const char *val)
{
	return 0;
}

int module_debug(int enable, const char *file)
{
	return 0;
}

int module_loop(void)
{
	return module_process(STDIN_FILENO, 1);
}

void module_speak_sync(const char *data, size_t bytes, SPDMessageType msgtype)
{
	char* action = "SAY_UNKNOWN";
	switch(msgtype) {
		case SPD_MSGTYPE_TEXT:
			action="SAY";
			break;
        case SPD_MSGTYPE_SOUND_ICON:
			action="SOUND_ICON";
			break;
		case SPD_MSGTYPE_CHAR:
			action="SAY_CHAR";
			break;
		case SPD_MSGTYPE_KEY:
			action="SAY_KEY";
			break;
		case SPD_MSGTYPE_SPELL:
			action="SAY_SPELL";
			break;
	}
	module_speak_ok();
	module_report_event_begin();
	send_message(action, data);
	module_report_event_end();
}

size_t module_pause(void)
{
	send_message("PAUSE", "");
	return 0;
}

int module_stop(void)
{
	send_message("STOP", "");
	return 0;
}

int module_close(void)
{
	fprintf(stderr, "Closing\n");
	send_message("CLOSE", "");
	if (data_socket != -1) {
		close(data_socket);
	}
	fprintf(stderr, "Closed.\n");
	return 0;
}
