#include <stdio.h> 
#include <stdlib.h> 
#include <errno.h> 
#include <string.h> 
#include <sys/types.h> 
#include <netinet/in.h> 
#include <sys/socket.h> 
#include <netdb.h>
#include <sys/wait.h> 
#include <signal.h>

#define MYPORT 19876    /* the port users will be connecting to */
#define MAXSIZE 4096

int getCmdResult( char *cmd, char *buf );

int main(int argc, char *argv[])
{
  char result[MAXSIZE];
	char *program = argv[0];
	int port = 0;
	int sockfd, new_fd;  /* listen on sock_fd, new connection on new_fd */
	struct sockaddr_in my_addr;    /* my address information */
	struct sockaddr_in their_addr; /* connector's address information */
	struct hostent* hoststruct;
	size_t sin_size;
	extern int optind;
	extern char *optarg;
	int c;
	int popt = 0;
	int on = 1;
	int len;
	int status;

	signal(SIGHUP, SIG_IGN);
	signal(SIGCHLD, SIG_IGN);

	while( (c=getopt(argc, argv, "p:")) != EOF ) {
		switch( c ) {
			case 'p' :
				popt = 1;
				port = atoi(optarg);
				if( port == 0 ) {
					fprintf(stderr, "\nusage: %s [\"command1\", ..] ([-p port](default:19876)\n\n", program );
					exit(-1);
				}
				break;
			default :
				fprintf(stderr, "\nusage: %s [\"command1\", ..] ([-p port](default:19876)\n\n", program );
				exit(-1);
		}
	}

	if( argc == 1 || optind > 5)  {
		fprintf(stderr, "\nusage: %s [\"command1\", ..] ([-p port](default:19876)\n\n", program );
		exit(-1);
	}

	if( (sockfd = socket(AF_INET, SOCK_STREAM, 0)) < 0 )
		exit(1);

	if( setsockopt(sockfd, SOL_SOCKET, SO_REUSEADDR, &on, sizeof(on)) < 0) {
		(void)close(sockfd);
		exit(-1 * errno);
	}

	my_addr.sin_family = AF_INET;         /* host byte order */
	my_addr.sin_port = htons(MYPORT);     /* short, network byte order */
	if( popt )
		my_addr.sin_port = htons(port);     /* short, network byte order */
	my_addr.sin_addr.s_addr = INADDR_ANY; /* auto-fill with my IP */
	bzero(&(my_addr.sin_zero), 8);        /* zero the rest of the struct */

	if( bind(sockfd, (struct sockaddr *)&my_addr, sizeof(struct sockaddr)) < 0 )
		exit(1);

	if( listen(sockfd, 10) < 0 ) exit(1);

	while (1 ) {
		sin_size = sizeof(struct sockaddr_in);

		new_fd = accept(sockfd, (struct sockaddr *)&their_addr, &sin_size);
		memset( result, 0, sizeof(result) );
		if( !fork() ) { /* this is the child process */
			for( ;optind<argc;++optind ) {
				getCmdResult( argv[optind], result );
				if( send(new_fd, result, strlen(result), 0 ) < 0 ) exit(-1);
			}

			close(new_fd);
			exit(0);
		}
		close(new_fd);  /* parent doesn't need this */
	}
}

int getCmdResult( char *cmd, char *buf )
{
	int c;
	int i=0;
	FILE * fp;

	if( (fp=popen(cmd, "r")) == NULL ) return -1;

	while( (c = fgetc(fp)) != EOF ) {
		if( i >= MAXSIZE ) {
			strcpy(buf, "result exceeded(4096bytes)");
			return 0;
		}
		buf[i] = c;
		i++;
	}
	if( !i ) return -1;
	buf[++i] = 0;
	pclose(fp);

	return 0;
}
