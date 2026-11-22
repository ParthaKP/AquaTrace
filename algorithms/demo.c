/* Deterministic stand-alone acceptance demo for AquaTrace's C DSA. */
#include "aquatrace_algorithms.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define CHECK(condition, message) do { \
    if (!(condition)) { fprintf(stderr, "FAIL: %s\n", message); return 1; } \
} while (0)

static int find_vertex(void *graph,const char *id) {
    for(size_t i=0;i<aqt_graph_vertex_count(graph);i++)
        if(strcmp(aqt_graph_vertex_id(graph,i),id)==0) return (int)i;
    return -1;
}

static int run_traversal(void *graph,const char *start,int mode,int limit,
                         char **names,int *count) {
    size_t n=aqt_graph_vertex_count(graph),m=aqt_graph_edge_count(graph),at=0;
    int *from=(int*)malloc(m*sizeof(int)),*to=(int*)malloc(m*sizeof(int));
    int *order=(int*)malloc(n*sizeof(int)),*dist=(int*)malloc(n*sizeof(int));
    if(!from||!to||!order||!dist){free(from);free(to);free(order);free(dist);return 0;}
    for(size_t u=0;u<n;u++) {
        const char *source=aqt_graph_vertex_id(graph,u);
        size_t degree=aqt_graph_neighbor_count(graph,source);
        for(size_t j=0;j<degree;j++) {
            const char *destination=aqt_graph_neighbor_id(graph,source,j);
            int v=find_vertex(graph,destination);
            if(v<0){free(from);free(to);free(order);free(dist);return 0;}
            from[at]=(int)u;to[at++]=v;
        }
    }
    int start_index=find_vertex(graph,start),used=0;
    int ok=aqt_traverse(n,from,to,m,start_index,limit,mode,order,dist,&used);
    for(int i=0;ok&&i<used;i++) names[i]=(char*)aqt_graph_vertex_id(graph,(size_t)order[i]);
    *count=used;
    free(from);free(to);free(order);free(dist);
    return ok;
}

static int matches(char **actual,int count,const char **expected,int expected_count) {
    if(count!=expected_count)return 0;
    for(int i=0;i<count;i++)if(strcmp(actual[i],expected[i])!=0)return 0;
    return 1;
}

static void print_order(const char *label,char **items,int count) {
    printf("%s",label);
    for(int i=0;i<count;i++)printf("%s%s",i?" -> ":"",items[i]);
    putchar('\n');
}

int main(void) {
    void *graph=aqt_graph_create();
    CHECK(graph,"allocate graph");
    const char *vertices[]={"J1","J2","J3","J4","J5"};
    for(size_t i=0;i<5;i++)CHECK(aqt_graph_add_vertex(graph,vertices[i]),"add graph vertex");
    CHECK(!aqt_graph_add_vertex(graph,"J1"),"reject duplicate vertex");
    const char *edge_from[]={"J1","J1","J2","J3","J4"};
    const char *edge_to[]={"J2","J3","J4","J4","J1"};
    for(size_t i=0;i<5;i++)CHECK(aqt_graph_add_edge(graph,edge_from[i],edge_to[i]),"add graph edge");
    CHECK(!aqt_graph_add_edge(graph,"J1","J2"),"reject duplicate edge");
    CHECK(!aqt_graph_add_edge(graph,"J5","J5"),"reject self-loop");
    CHECK(!aqt_graph_add_edge(graph,"J99","J1"),"reject missing endpoint");
    CHECK(aqt_graph_add_vertex(graph,"J6"),"add temporary vertex for removal check");
    CHECK(aqt_graph_add_edge(graph,"J5","J6"),"add incoming test edge");
    CHECK(aqt_graph_add_edge(graph,"J6","J5"),"add outgoing test edge");
    CHECK(aqt_graph_remove_vertex(graph,"J6"),"remove vertex with incoming and outgoing edges");
    CHECK(aqt_graph_vertex_count(graph)==5&&aqt_graph_edge_count(graph)==5,"graph counts");
    printf("Graph: %zu junctions, %zu directed connections (J5 disconnected)\n",
        aqt_graph_vertex_count(graph),aqt_graph_edge_count(graph));

    char *order[5];int count=0;
    const char *bfs_expected[]={"J1","J2","J3","J4"};
    CHECK(run_traversal(graph,"J1",0,-1,order,&count),"run BFS");
    CHECK(matches(order,count,bfs_expected,4),"BFS expected order and cycle protection");
    print_order("BFS from J1:       ",order,count);
    const char *shallow_expected[]={"J1","J2","J3"};
    CHECK(run_traversal(graph,"J1",0,1,order,&count),"run depth-limited BFS");
    CHECK(matches(order,count,shallow_expected,3),"BFS maximum depth");
    const char *dfs_expected[]={"J1","J2","J4","J3"};
    CHECK(run_traversal(graph,"J1",1,-1,order,&count),"run recursive DFS");
    CHECK(matches(order,count,dfs_expected,4),"recursive DFS expected order");
    print_order("Recursive DFS:     ",order,count);
    CHECK(run_traversal(graph,"J1",2,-1,order,&count),"run iterative DFS");
    CHECK(matches(order,count,dfs_expected,4),"iterative DFS expected order");
    print_order("Iterative DFS:     ",order,count);
    CHECK(aqt_graph_neighbor_count(graph,"J5")==0,"disconnected vertex remains unreachable");

    double population[]={2000,4000,1000},infrastructure[]={80,90,30};
    double population_sum,mean_infrastructure,count_score,population_score;int impact_level=0;
    double impact=aqt_impact_score(3,population,infrastructure,&population_sum,
        &mean_infrastructure,&count_score,&population_score,&impact_level);
    CHECK(impact==53.0&&impact_level==1,"impact score and MEDIUM classification");
    puts("Potentially affected: J2, J3, J4 (3 unique downstream junctions)");
    printf("Impact score:        %.2f (MEDIUM)\n",impact);

    double values[]={90,53,80,70,90,85};
    double weights[]={.25,.25,.15,.15,.10,.10};
    double contributions[6],risk=0;int priority=0;
    CHECK(aqt_risk_score(values,weights,6,contributions,&risk,&priority),"calculate risk score");
    CHECK(risk==75.75&&priority==2,"risk score and HIGH classification");
    printf("Risk score:          %.2f (HIGH)\n",risk);

    void *heap=aqt_heap_create();CHECK(heap,"allocate priority queue");
    CHECK(aqt_heap_push(heap,75.75,"J3",1),"insert J3");
    CHECK(aqt_heap_push(heap,53.0,"J4",2),"insert J4");
    CHECK(aqt_heap_push(heap,75.75,"J2",0),"insert J2");
    size_t handle=0;
    CHECK(aqt_heap_pop(heap,&handle)&&handle==0,"heap max with deterministic tie break");
    printf("Heap order:          J2 (75.75)");
    CHECK(aqt_heap_pop(heap,&handle)&&handle==1,"second heap item");
    printf(" -> J3 (75.75)");
    CHECK(aqt_heap_pop(heap,&handle)&&handle==2,"third heap item");
    printf(" -> J4 (53.00)\n");
    CHECK(!aqt_heap_pop(heap,&handle),"empty heap behavior");
    aqt_heap_destroy(heap);aqt_graph_destroy(graph);
    puts("PASS: all C DSA checks matched their expected results.");
    return 0;
}
