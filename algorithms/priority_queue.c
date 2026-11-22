
#include "aquatrace_algorithms.h"
#include <math.h>
#include <stdlib.h>
#include <string.h>


// Structure representing an item in the temporary heap
typedef struct
{
    size_t index;
    double score;
    const char *id;
} heap_item;


// Compare two heap items
static int before(heap_item a, heap_item b)
{
    if (a.score != b.score)
        return a.score > b.score;

    return strcmp(a.id, b.id) < 0;
}


// Swap two heap items
static void swap(heap_item *a, heap_item *b)
{
    heap_item t = *a;
    *a = *b;
    *b = t;
}


// Arrange elements in descending score order using a heap
void aqt_heap_order(
    const double *scores,
    const char *const *ids,
    size_t n,
    size_t *order
)
{
    heap_item *h = (heap_item *)malloc(n * sizeof(heap_item));

    if (!h)
        return;

    // Initialize heap items
    for (size_t i = 0; i < n; i++)
    {
        h[i].index = i;
        h[i].score = scores[i];
        h[i].id = ids[i];
    }

    // Build the heap
    for (size_t i = n / 2; i > 0; i--)
    {
        size_t p = i - 1;

        for (;;)
        {
            size_t l = p * 2 + 1;
            size_t r = l + 1;
            size_t b = p;

            if (l < n && before(h[l], h[b]))
                b = l;

            if (r < n && before(h[r], h[b]))
                b = r;

            if (b == p)
                break;

            swap(&h[p], &h[b]);
            p = b;
        }
    }

    // Extract elements in priority order
    for (size_t k = 0; k < n; k++)
    {
        order[k] = h[0].index;

        h[0] = h[n - k - 1];

        size_t len = n - k - 1;
        size_t p = 0;

        for (;;)
        {
            size_t l = p * 2 + 1;
            size_t r = l + 1;
            size_t b = p;

            if (l < len && before(h[l], h[b]))
                b = l;

            if (r < len && before(h[r], h[b]))
                b = r;

            if (b == p)
                break;

            swap(&h[p], &h[b]);
            p = b;
        }
    }

    free(h);
}


// Structure representing an item in the persistent heap
typedef struct
{
    double score;
    char *id;
    size_t handle;
} persistent_item;


// Structure representing the persistent heap
typedef struct
{
    persistent_item *items;
    size_t size, capacity;
} persistent_heap;


// Compare two persistent heap items
static int item_before(persistent_item a, persistent_item b)
{
    if (a.score != b.score)
        return a.score > b.score;

    return strcmp(a.id, b.id) < 0;
}


// Swap two persistent heap items
static void swap_persistent(persistent_item *a, persistent_item *b)
{
    persistent_item t = *a;
    *a = *b;
    *b = t;
}


// Move an element upward to maintain heap property
static void sift_up(persistent_heap *h, size_t i)
{
    while (i)
    {
        size_t p = (i - 1) / 2;

        if (!item_before(h->items[i], h->items[p]))
            break;

        swap_persistent(&h->items[i], &h->items[p]);
        i = p;
    }
}


// Move an element downward to maintain heap property
static void sift_down(persistent_heap *h, size_t i)
{
    for (;;)
    {
        size_t l = i * 2 + 1;
        size_t r = l + 1;
        size_t b = i;

        if (l < h->size && item_before(h->items[l], h->items[b]))
            b = l;

        if (r < h->size && item_before(h->items[r], h->items[b]))
            b = r;

        if (b == i)
            break;

        swap_persistent(&h->items[i], &h->items[b]);
        i = b;
    }
}


// Create a new persistent heap
void *aqt_heap_create(void)
{
    return calloc(1, sizeof(persistent_heap));
}


// Destroy the heap and free allocated memory
void aqt_heap_destroy(void *ptr)
{
    persistent_heap *h = (persistent_heap *)ptr;

    if (!h)
        return;

    for (size_t i = 0; i < h->size; i++)
        free(h->items[i].id);

    free(h->items);
    free(h);
}


// Insert a new item into the persistent heap
int aqt_heap_push(
    void *ptr,
    double score,
    const char *id,
    size_t handle
)
{
    persistent_heap *h = (persistent_heap *)ptr;

    if (!h || !id || !isfinite(score))
        return 0;

    // Increase capacity if required
    if (h->size == h->capacity)
    {
        size_t c = h->capacity ? h->capacity * 2 : 16;

        persistent_item *p = (persistent_item *)realloc(
            h->items,
            c * sizeof(*p)
        );

        if (!p)
            return 0;

        h->items = p;
        h->capacity = c;
    }

    // Copy the ID into dynamically allocated memory
    size_t n = strlen(id) + 1;
    char *copy = (char *)malloc(n);

    if (!copy)
        return 0;

    memcpy(copy, id, n);

    // Insert the item and restore heap property
    h->items[h->size] = (persistent_item){
        score, copy, handle
    };

    sift_up(h, h->size++);

    return 1;
}


// Remove and return the highest-priority item
int aqt_heap_pop(void *ptr, size_t *handle)
{
    persistent_heap *h = (persistent_heap *)ptr;

    if (!h || !h->size)
        return 0;

    *handle = h->items[0].handle;

    free(h->items[0].id);

    h->size--;

    if (h->size)
    {
        h->items[0] = h->items[h->size];
        sift_down(h, 0);
    }

    return 1;
}


// Get the handle of the highest-priority item without removing it
int aqt_heap_peek(void *ptr, size_t *handle)
{
    persistent_heap *h = (persistent_heap *)ptr;

    if (!h || !h->size)
        return 0;

    *handle = h->items[0].handle;

    return 1;
}


// Get the current number of elements in the heap
size_t aqt_heap_size(void *ptr)
{
    persistent_heap *h = (persistent_heap *)ptr;

    return h ? h->size : 0;
}
