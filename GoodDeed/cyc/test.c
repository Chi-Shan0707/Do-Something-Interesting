#include<stdio.h>
int main()
{
    int x=3;
    do{ 
        printf("%d",x-=2);
    }while(!(--x));
    return 0;
}