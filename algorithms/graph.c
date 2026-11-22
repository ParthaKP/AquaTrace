
#include "aquatrace_algorithms.h"
#include <math.h>
#include <stdlib.h>
#include <string.h>

// Structure representing a vertex in the graph
typedef struct
{
    char *id;
    int *neighbors;
    size_t count, capacity;
} graph_vertex;

// Structure representing the entire graph
typedef struct
{
    graph_vertex *vertices;
    size_t count, capacity, edges;
} aqt_graph;


// Find a vertex using its ID
static int graph_find(aqt_graph *g, const char *id)
{
    if (!g || !id)
        return -1;

    for (size_t i = 0; i < g->count; i++)
    {
        if (strcmp(g->vertices[i].id, id) == 0)
            return (int)i;
    }

    return -1;
}


// Create a new graph
void *aqt_graph_create(void)
{
    return calloc(1, sizeof(aqt_graph));
}


// Destroy the graph and free allocated memory
void aqt_graph_destroy(void *ptr)
{
    aqt_graph *g = (aqt_graph *)ptr;

    if (!g)
        return;

    for (size_t i = 0; i < g->count; i++)
    {
        free(g->vertices[i].id);
        free(g->vertices[i].neighbors);
    }

    free(g->vertices);
    free(g);
}


// Add a new vertex to the graph
int aqt_graph_add_vertex(void *ptr, const char *id)
{
    aqt_graph *g = (aqt_graph *)ptr;

    if (!g || !id || !*id || graph_find(g, id) >= 0)
        return 0;

    if (g->count == g->capacity)
    {
        size_t c = g->capacity ? g->capacity * 2 : 16;

        graph_vertex *p = (graph_vertex *)realloc(
            g->vertices,
            c * sizeof(*p)
        );

        if (!p)
            return 0;

        g->vertices = p;
        g->capacity = c;
    }

    size_t len = strlen(id) + 1;
    char *copy = (char *)malloc(len);

    if (!copy)
        return 0;

    memcpy(copy, id, len);

    g->vertices[g->count++] = (graph_vertex){
        copy, NULL, 0, 0
    };

    return 1;
}


// Remove a vertex and all its connected edges
int aqt_graph_remove_vertex(void *ptr, const char *id)
{
    aqt_graph *g = (aqt_graph *)ptr;
    int index = graph_find(g, id);

    if (index < 0)
        return 0;

    size_t k = (size_t)index;

    free(g->vertices[k].id);
    free(g->vertices[k].neighbors);

    g->edges -= g->vertices[k].count;

    g->vertices[k].neighbors = NULL;
    g->vertices[k].count = 0;

    for (size_t i = 0; i < g->count; i++)
    {
        graph_vertex *v = &g->vertices[i];

        for (size_t j = 0; j < v->count;)
        {
            if (v->neighbors[j] == index)
            {
                memmove(
                    &v->neighbors[j],
                    &v->neighbors[j + 1],
                    (v->count - j - 1) * sizeof(int)
                );

                v->count--;
                g->edges--;
            }
            else
            {
                if (v->neighbors[j] > (int)k)
                    v->neighbors[j]--;

                j++;
            }
        }
    }

    memmove(
        &g->vertices[k],
        &g->vertices[k + 1],
        (g->count - k - 1) * sizeof(graph_vertex)
    );

    g->count--;

    return 1;
}


// Check whether a vertex exists
int aqt_graph_has_vertex(void *ptr, const char *id)
{
    return graph_find((aqt_graph *)ptr, id) >= 0;
}


// Check whether an edge exists
int aqt_graph_has_edge(
    void *ptr,
    const char *source,
    const char *destination
)
{
    aqt_graph *g = (aqt_graph *)ptr;

    int u = graph_find(g, source);
    int v = graph_find(g, destination);

    if (u < 0 || v < 0)
        return 0;

    for (size_t i = 0; i < g->vertices[u].count; i++)
    {
        if (g->vertices[u].neighbors[i] == v)
            return 1;
    }

    return 0;
}


// Add an edge between two vertices
int aqt_graph_add_edge(
    void *ptr,
    const char *source,
    const char *destination
)
{
    aqt_graph *g = (aqt_graph *)ptr;

    int u = graph_find(g, source);
    int v = graph_find(g, destination);

    if (u < 0 || v < 0 || u == v ||
        aqt_graph_has_edge(g, source, destination))
        return 0;

    graph_vertex *x = &g->vertices[u];

    if (x->count == x->capacity)
    {
        size_t c = x->capacity ? x->capacity * 2 : 4;

        int *p = (int *)realloc(
            x->neighbors,
            c * sizeof(int)
        );

        if (!p)
            return 0;

        x->neighbors = p;
        x->capacity = c;
    }

    x->neighbors[x->count++] = v;
    g->edges++;

    return 1;
}


// Remove an edge between two vertices
int aqt_graph_remove_edge(
    void *ptr,
    const char *source,
    const char *destination
)
{
    aqt_graph *g = (aqt_graph *)ptr;

    int u = graph_find(g, source);
    int v = graph_find(g, destination);

    if (u < 0 || v < 0)
        return 0;

    graph_vertex *x = &g->vertices[u];

    for (size_t i = 0; i < x->count; i++)
    {
        if (x->neighbors[i] == v)
        {
            memmove(
                &x->neighbors[i],
                &x->neighbors[i + 1],
                (x->count - i - 1) * sizeof(int)
            );

            x->count--;
            g->edges--;

            return 1;
        }
    }

    return 0;
}


// Get the total number of vertices
size_t aqt_graph_vertex_count(void *ptr)
{
    aqt_graph *g = (aqt_graph *)ptr;

    return g ? g->count : 0;
}


// Get the total number of edges
size_t aqt_graph_edge_count(void *ptr)
{
    aqt_graph *g = (aqt_graph *)ptr;

    return g ? g->edges : 0;
}


// Get the vertex ID using its index
const char *aqt_graph_vertex_id(void *ptr, size_t index)
{
    aqt_graph *g = (aqt_graph *)ptr;

    return g && index < g->count
        ? g->vertices[index].id
        : NULL;
}


// Get the number of neighbors of a vertex
size_t aqt_graph_neighbor_count(void *ptr, const char *id)
{
    aqt_graph *g = (aqt_graph *)ptr;
    int u = graph_find(g, id);

    return u < 0 ? 0 : g->vertices[u].count;
}


// Get the ID of a neighbor using its index
const char *aqt_graph_neighbor_id(
    void *ptr,
    const char *id,
    size_t index
)
{
    aqt_graph *g = (aqt_graph *)ptr;
    int u = graph_find(g, id);

    if (u < 0 || index >= g->vertices[u].count)
        return NULL;

    return g->vertices[g->vertices[u].neighbors[index]].id;
}
