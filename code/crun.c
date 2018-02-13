/* C implementation of graphrats simulator */

#include <string.h>
#include <getopt.h>

#include "crun.h"

static void usage(char *name) {
    char *use_string = "-g GFILE -r RFILE [-n STEPS] [-s SEED] [-u (r|b|s)] [-q] [-i INT] [-t THD]";
    outmsg("Usage: %s %s\n", name, use_string);
    outmsg("   -h        Print this message\n");
    outmsg("   -g GFILE  Graph file\n");
    outmsg("   -r RFILE  Initial rat position file\n");
    outmsg("   -n STEPS  Number of simulation steps\n");
    outmsg("   -s SEED   Initial RNG seed\n");
    outmsg("   -u UPDT   Update mode:\n");
    outmsg("             s: Synchronous.  Compute all new states and then update all\n");
    outmsg("             r: Rat order.    Compute update each rat state in sequence\n");
    outmsg("             b: Batched.      Repeatedly compute states for small batches of rats and then update\n");
    outmsg("   -q        Operate in quiet mode.  Do not generate simulation results\n");
    outmsg("   -i INT    Display update interval\n");
    outmsg("   -t THD    Set number of threads\n");
    done();
    exit(0);
}

int main(int argc, char *argv[]) {
    FILE *gfile = NULL;
    FILE *rfile = NULL;
    int steps = 1;
    int dinterval = 1;
    random_t global_seed = DEFAULTSEED;
    update_t update_mode = UPDATE_BATCH;
    int c;
    graph_t *g = NULL;
    state_t *s = NULL;
    bool display = true;
    int thread_count = 1;

    char *optstring = "hg:r:R:n:s:u:i:qt:b:";
    while ((c = getopt(argc, argv, optstring)) != -1) {
	switch(c) {
	case 'h':
	    usage(argv[0]);
	    break;
	case 'g':
	    gfile = fopen(optarg, "r");
	    if (gfile == NULL) {
		outmsg("Couldn't open graph file %s\n", optarg);
		done();
		exit(1);
	    }
	    break;
	case 'r':
	    rfile = fopen(optarg, "r");
	    if (rfile == NULL) {
		outmsg("Couldn't open rat position file %s\n", optarg);
		done();
		exit(1);
	    }
	    break;
	case 'n':
	    steps = atoi(optarg);
	    break;
	case 's':
	    global_seed = strtoul(optarg, NULL, 0);
	    break;
	case 'u':
	    if (optarg[0] == 'r')
		update_mode = UPDATE_RAT;
	    else if (optarg[0] == 'b')
		update_mode = UPDATE_BATCH;
	    else if (optarg[0] == 's')
		update_mode = UPDATE_SYNCHRONOUS;
	    else {
		outmsg("Invalid update mode '%c'\n", optarg[0]);
		usage(argv[0]);
		done();
		exit(1);
	    }
	    break;
	case 'q':
	    display = false;
	    break;
	case 'i':
	    dinterval = atoi(optarg);
	    break;
	case 't':
	    thread_count = atoi(optarg);
	    break;
	default:
	    outmsg("Unknown option '%c'\n", c);
	    usage(argv[0]);
	    done();
	    exit(1);
	}
    }
    if (gfile == NULL) {
	outmsg("Need graph file\n");
	usage(argv[0]);
    }
    if (rfile == NULL) {
	outmsg("Need initial rat position file\n");
	usage(argv[0]);
    }

    outmsg("Running with %d threads\n", thread_count);

    g = read_graph(gfile);
    if (g == NULL) {
	done();
	exit(1);
    }
    s = read_rats(g, rfile, global_seed);
    if (s == NULL) {
	done();
	exit(1);
    }

    s->nthread = thread_count;
    double start = currentSeconds();
    simulate(s, steps, update_mode, dinterval, display);
    double delta = currentSeconds() - start;
    outmsg("%d steps, %d rats, %.3f seconds\n", steps, s->nrat, delta);

    return 0;
}

