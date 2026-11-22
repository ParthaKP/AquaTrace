
#include "aquatrace_algorithms.h"
#include <math.h>
#include <stdlib.h>
#include <string.h>


// Recursive function for Depth First Search (DFS)
static int visit_recursive(
    const size_t *offsets,
    const int *neighbors,
    int node,
    int depth,
    int limit,
    unsigned char *seen,
    int *order,
    int *distances,
    int *used
)
{
    seen[node] = 1;
    order[(*used)++] = node;
    distances[node] = depth;

    // Stop traversal if the depth limit is reached
    if (limit >= 0 && depth >= limit)
        return 1;

    // Visit all unvisited neighboring nodes
    for (size_t e = offsets[node]; e < offsets[node + 1]; e++)
    {
        if (!seen[neighbors[e]])
        {
            if (!visit_recursive(
                    offsets,
                    neighbors,
                    neighbors[e],
                    depth + 1,
                    limit,
                    seen,
                    order,
                    distances,
                    used
                ))
                return 0;
        }
    }

    return 1;
}


// Perform graph traversal using BFS or DFS
int aqt_traverse(
    size_t n,
    const int *from,
    const int *to,
    size_t m,
    int start,
    int limit,
    int dfs,
    int *order,
    int *distances,
    int *order_count
)
{
    // Validate input parameters
    if (!order_count || !order || !distances ||
        start < 0 || (size_t)start >= n || (limit < -1))
        return 0;

    // Allocate memory for graph representation
    size_t *degree = (size_t *)calloc(n + 1, sizeof(size_t));
    size_t *offsets = (size_t *)calloc(n + 1, sizeof(size_t));
    size_t *cursor = (size_t *)calloc(n, sizeof(size_t));

    int *neighbors = (int *)malloc(m * sizeof(int));

    // Check memory allocation
    if (!degree || !offsets || !cursor || (m && !neighbors))
    {
        free(degree);
        free(offsets);
        free(cursor);
        free(neighbors);

        return 0;
    }

    // Calculate the degree of each vertex
    for (size_t e = 0; e < m; e++)
    {
        if (from[e] < 0 || to[e] < 0 ||
            (size_t)from[e] >= n || (size_t)to[e] >= n)
        {
            free(degree);
            free(offsets);
            free(cursor);
            free(neighbors);

            return 0;
        }

        degree[(size_t)from[e] + 1]++;
    }

    // Calculate adjacency list offsets
    for (size_t i = 1; i <= n; i++)
        offsets[i] = offsets[i - 1] + degree[i];

    // Initialize cursor positions
    memcpy(cursor, offsets, n * sizeof(size_t));

    // Build the adjacency list
    for (size_t e = 0; e < m; e++)
        neighbors[cursor[from[e]]++] = to[e];

    free(degree);
    free(cursor);


    // Allocate memory for traversal operations
    unsigned char *seen = (unsigned char *)calloc(
        n,
        sizeof(unsigned char)
    );

    int *queue = (int *)malloc(n * sizeof(int));
    int *depth = (int *)malloc(n * sizeof(int));

    int *stack = (int *)malloc((m + n + 1) * sizeof(int));

    // Check memory allocation
    if (!seen || !queue || !depth || !stack)
    {
        free(seen);
        free(queue);
        free(depth);
        free(stack);
        free(offsets);
        free(neighbors);

        return 0;
    }

    int used = 0;

    // Initialize all distances to -1
    for (size_t i = 0; i < n; i++)
        distances[i] = -1;


    // Recursive DFS traversal
    if (dfs == 1)
    {
        int ok = visit_recursive(
            offsets,
            neighbors,
            start,
            0,
            limit,
            seen,
            order,
            distances,
            &used
        );

        free(seen);
        free(queue);
        free(depth);
        free(stack);
        free(offsets);
        free(neighbors);

        *order_count = used;

        return ok;
    }


    // Initialize BFS queue or iterative DFS stack
    int head = 0;
    int tail = 0;

    if (dfs == 2)
    {
        stack[tail++] = start;
        distances[start] = 0;
    }
    else
    {
        queue[tail] = start;
        depth[tail++] = 0;

        seen[start] = 1;
        distances[start] = 0;
    }


    // Main traversal loop
    while (dfs == 2 ? tail > 0 : head < tail)
    {
        int node, d;

        // Iterative DFS
        if (dfs == 2)
        {
            node = stack[--tail];

            if (seen[node])
                continue;

            seen[node] = 1;
            d = distances[node];
        }

        // BFS
        else
        {
            node = queue[head];
            d = depth[head++];
        }

        // Store the visited node
        order[used++] = node;

        // Check depth limit
        if (limit >= 0 && d >= limit)
            continue;


        // Process neighbors using iterative DFS
        if (dfs == 2)
        {
            for (
                size_t e = offsets[node + 1];
                e > offsets[node];
                e--
            )
            {
                int v = neighbors[e - 1];

                if (!seen[v])
                {
                    if (distances[v] < 0)
                        distances[v] = d + 1;

                    stack[tail++] = v;
                }
            }
        }

        // Process neighbors using BFS
        else
        {
            for (
                size_t e = offsets[node];
                e < offsets[node + 1];
                e++
            )
            {
                int v = neighbors[e];

                if (!seen[v])
                {
                    seen[v] = 1;
                    distances[v] = d + 1;

                    queue[tail] = v;
                    depth[tail++] = d + 1;
                }
            }
        }
    }


    // Free allocated memory
    free(seen);
    free(queue);
    free(depth);
    free(stack);
    free(offsets);
    free(neighbors);

    // Store the total number of visited nodes
    *order_count = used;

    return 1;
}

