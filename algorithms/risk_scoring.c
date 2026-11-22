#include "aquatrace_algorithms.h"
#include <math.h>
#include <stdlib.h>
#include <string.h>

int aqt_risk_score(const double *values,const double *weights,size_t n,double *contributions,double *score,int *priority) 
{
    double sum=0,total=0;
    for(size_t i=0;i<n;i++)
    {
        if(!isfinite(values[i])||values[i]<0||values[i]>100||!isfinite(weights[i])||weights[i]<0)
            return 0;
        sum+=weights[i];
        contributions[i]=round(values[i]*weights[i]*10000.0)/10000.0;
        total+=values[i]*weights[i];
    }
    
    if(fabs(sum-1.0)>1e-9)return 0;

    *score=round(total*100.0)/100.0;
    
    *priority=*score>=80?3:*score>=60?2:*score>=40?1:0;return 1;
}

