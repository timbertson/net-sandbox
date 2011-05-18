/* gcc -o unshare-pid unshare-pid.c */
#include <stdlib.h>
#include <unistd.h>
#include <inttypes.h>
#include <sched.h>
#include <stdio.h>
#include <signal.h>
#include <asm/ioctls.h>
#include <err.h>
#include <assert.h>
#include <sys/wait.h>

int child(void *ptr)
{
		char **argv = ptr;
		execvp(*argv,argv);
		return -1;
}

int main(int argc, char ** argv)
{
		uint8_t stack[4096];
		int status;
		int flags = CLONE_NEWPID | SIGCLD;
		assert(argc > 1);
		if(geteuid() != 0) {
			err(1, "must be root! (or setuid root)\n");
		}
		int clone_result = clone(child, stack+sizeof(stack), flags, argv+1);
		if(clone_result == -1) {
			err(1, "Clone failed");
		}
		int wait_result = waitpid(clone_result, &status, 0);
		if(wait_result == -1) {
			err(1, "waitpid() failed");
		}
		return WEXITSTATUS(status);
}
