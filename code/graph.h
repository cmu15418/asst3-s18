#include <stdio.h>
#include <stdlib.h>

#include "crun.h"

graph_t *new_graph(int nnode, int nedge) {
    bool ok = True;
    graph_t *g = malloc(sizeof(graph_t));
    if (g == NULL)
	return NULL;
    g->nnode = nnode;
    g->nedge = nedge;
    g->neighbor = calloc(nnode + nedge, sizeof(int));
    ok = ok && g->neighbor != NULL;
    g->neighbor_start = calloc(nnode + 1, sizeof(int));
    ok = ok && g->neighbor_start != NULL;
    if (!ok) {
	errmsg("Couldn't allocate graph data structures");
	return NULL;
    }
    return g;
}

/* Read in graph file and build graph data structure */
graph_t *read_graph(FILE *infile) {
    int nnode, nedge;
    int i, hid, tid;
    int nid, eid;

    // Read header information
    if (fscanf(infile, "%d %d", &nnode, &nedge) != 2) {
	errmsg("ERROR. Malformed graph file header (line 1)\n");
	return NULL;
    }
    graph_t g = new_graph(nnode, nedge);
    if (g == NULL)
	return g;

    nid = -1;
    // We're going to add self edges, so eid will keep track of all edges.
    eid = 0;  
    for (i = 0; i < nedge; i++) {
	if (fscanf(infile, "%d %d", &hid, &tid) != 2) {
	    fprintf(stderr, "Line #%u of graph file malformed\n", i+2);
	    return false;
	}
	if (hid < 0 || hid >= nnode) {
	    fprintf(stderr, "Invalid head index %d on line %d\n", hid, i+2);
	    return false;
	}
	if (tid < 0 || tid >= nnode) {
	    fprintf(stderr, "Invalid tail index %d on line %d\n", tid, i+2);
	    return false;
	}
	if (hid < nid) {
	    fprintf(stderr, "Head index %d on line %d out of order\n", hid, i+2);
	    return false;
	    
	}
	// Starting edges for new node(s)
	while (nid < hid) {
	    nid++;
	    g->neighbor_start[nid] = eid;
	    // Self edge
	    g->neighbor[eid++] = nid;
	}
	neighbor[eid++] = tid;
    }
    while (nid < nnode) {
	// Fill out any isolated nodes
	nid++;
	g->neighbor_start[nid] = eid;
	g->neighbor[eid++] = nid;
    }
    fprintf(stderr, "Loaded graph with %d nodes and %d edges\n", nnode, nedge);
#if DEBUG
    show_graph();
#endif
    return true;
}
