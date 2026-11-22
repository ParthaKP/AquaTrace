
#include "aquatrace_algorithms.h"
#include <math.h>
#include <stdlib.h>
#include <string.h>


// Calculate the impact score based on population and infrastructure
double aqt_impact_score(
    size_t n,
    const double *pop,
    const double *infra,
    double *pop_sum,
    double *mean_infra,
    double *count_score,
    double *population_score,
    int *impact_level
)
{
    double ps = 0;
    double is = 0;

    // Calculate total population and infrastructure score
    for (size_t i = 0; i < n; i++)
    {
        if (pop[i] > 0)
            ps += pop[i];

        if (infra[i] > 0)
            is += fmin(100.0, infra[i]);
    }

    // Calculate population sum and average infrastructure score
    *pop_sum = ps;
    *mean_infra = n ? is / (double)n : 0;

    // Calculate count score and population score
    *count_score = fmin(100.0, (double)n * 10.0);
    *population_score = fmin(100.0, ps / 100.0);

    // Calculate the final impact score
    double score = round(
        (
            0.4 * (*count_score) +
            0.3 * (*population_score) +
            0.3 * (*mean_infra)
        ) * 100.0
    ) / 100.0;

    // Determine the impact level
    *impact_level = score >= 70 ? 2 :
                    score >= 40 ? 1 : 0;

    return score;
}


