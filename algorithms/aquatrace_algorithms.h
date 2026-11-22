
#ifndef AQUATRACE_ALGORITHMS_H
#define AQUATRACE_ALGORITHMS_H

#include <stddef.h>


// Directed adjacency-list graph.
// Vertex indexes remain compact after deletion.

void *aqt_graph_create(void);

void aqt_graph_destroy(void *graph);

int aqt_graph_add_vertex(
    void *graph,
    const char *junction_id
);

int aqt_graph_remove_vertex(
    void *graph,
    const char *junction_id
);

int aqt_graph_has_vertex(
    void *graph,
    const char *junction_id
);

int aqt_graph_add_edge(
    void *graph,
    const char *source,
    const char *destination
);

int aqt_graph_remove_edge(
    void *graph,
    const char *source,
    const char *destination
);

int aqt_graph_has_edge(
    void *graph,
    const char *source,
    const char *destination
);

size_t aqt_graph_vertex_count(void *graph);

size_t aqt_graph_edge_count(void *graph);

const char *aqt_graph_vertex_id(
    void *graph,
    size_t index
);

size_t aqt_graph_neighbor_count(
    void *graph,
    const char *junction_id
);

const char *aqt_graph_neighbor_id(
    void *graph,
    const char *junction_id,
    size_t index
);


// Graph traversal functions
// Edge endpoints are zero-based. Mode: 0 = BFS, 1 = recursive DFS, 2 = iterative DFS.
// depth_limit < 0 means unlimited traversal. Results include distances from start.

int aqt_traverse(
    size_t vertex_count,
    const int *edge_from,
    const int *edge_to,
    size_t edge_count,
    int start,
    int depth_limit,
    int depth_first,
    int *order,
    int *distances,
    int *order_count
);


// Calculate impact score using population and infrastructure data

double aqt_impact_score(
    size_t count,
    const double *population,
    const double *infrastructure,
    double *population_sum,
    double *mean_infrastructure,
    double *count_score,
    double *population_score,
    int *impact_level
);


// Calculate risk score

int aqt_risk_score(
    const double *values,
    const double *weights,
    size_t count,
    double *contributions,
    double *score,
    int *priority
);


// Heap sorting function

void aqt_heap_order(
    const double *scores,
    const char *const *junction_ids,
    size_t count,
    size_t *order
);


// Persistent priority queue functions

void *aqt_heap_create(void);

void aqt_heap_destroy(void *heap);

int aqt_heap_push(
    void *heap,
    double score,
    const char *junction_id,
    size_t handle
);

int aqt_heap_pop(
    void *heap,
    size_t *handle
);

int aqt_heap_peek(
    void *heap,
    size_t *handle
);

size_t aqt_heap_size(void *heap);


// Build a heap from existing data

int aqt_heap_build(
    void *heap,
    const double *scores,
    const char *const *ids,
    const size_t *handles,
    size_t count
);


#endif
