/*
!gcc -o main -Wall % && ./main
*/
#include <stdio.h>
#include <sys/wait.h>
#include <sys/types.h>
#include <stdlib.h>
#include <sched.h>
#include <err.h>
#include <unistd.h>
#include <assert.h>
#include <sys/types.h>

// py: http://starship.python.net/crew/arcege/extwriting/pyext.html

int childProcess(void* cmd) {
	unshare(CLONE_NEWNS);
	return system((char*)cmd);
}

int main(int argc, char** argv) {
	if(argc < 1) {
		printf("usage: net_namespace command_string\n");
		exit(1);
	}
	char *cmd = argv[1];

	void **child_stack = (void **) malloc(65536);
	assert(child_stack != 0);

	if(geteuid() != 0) {
		err(1, "net_namespace: must be root! (or setuid root)\n");
	}

	// new network & filesystem namespace
	int flags = CLONE_NEWNET | CLONE_NEWNS;

	pid_t result = clone(childProcess, child_stack, flags, cmd, NULL);
	//TODO: PyOS_AfterFork
	// Also: http://docs.python.org/extending/extending.html#calling-python-functions-from-c
	// http://code.google.com/p/python-unshare/source/browse/unshare.c

	if (result == -1) {
		err(1, "net_namespace: clone() failed");
	}
	else {
		int status;
		printf("net_namespace: clone returned new PID %d...\n", result);
		if(waitpid(result, &status, __WCLONE) == -1) {
			err(1, "net_namespace: waitpid failed!");
		} else {
			exit(status);
		}
	}
}
