// this entire program is very unsafe. there is no error checking. careful what you input.

#include <stdio.h>
#include <string.h>
#include <time.h>
#include <stdlib.h>

#define MAX_QUEST 100

char* sum_hex(char s[], char ans[], long limit, int n)
{
    s[0] = '\0';

    long r[n];
    long sum = 0;
    char temp[MAX_QUEST];
    for(int i = 0; i < n; i++)
    {
        r[i] = rand() % limit;
        sum += r[i];
        sprintf(temp, "%lx %s ", r[i], i == n-1? "=" : "+");
        strcat(s,temp);
    }

    sprintf(ans, "%lx", sum);
    return ans;
}

char* sum_dec(char s[], char ans[], long limit, int n)
{
    s[0] = '\0';

    long r[n];
    long sum = 0;
    char temp[MAX_QUEST];
    for(int i = 0; i < n; i++)
    {
        r[i] = rand() % limit;
        sum += r[i];
        sprintf(temp, "%lu %s ", r[i], i == n-1? "=" : "+");
        strcat(s,temp);
    }

    sprintf(ans, "%ld", sum);
    return ans;
}

char* mult_dec(char s[], char ans[], long limit, int n)
{
    s[0] = '\0';

    long r[n];
    long prod = 1;
    char temp[MAX_QUEST];
    for(int i = 0; i < n; i++)
    {
        r[i] = rand() % limit;
        prod *= r[i];
        sprintf(temp, "%lu %s ", r[i], i == n-1? "=" : "*");
        strcat(s,temp);
    }

    sprintf(ans, "%ld", prod);
    return ans;
}

char* dif_dec(char s[], char ans[], int limit)
{
    long r1 = rand() % limit;
    long r2 = rand() % limit;
    sprintf(s, "%ld - %ld = ", r1, r2);

    sprintf(ans, "%ld", r1-r2);
    return ans;
}

int main()
{
    srand(time(NULL));
    char s[MAX_QUEST];
    char ans[MAX_QUEST];
    char resp[MAX_QUEST];
    for(int i = 0; i < 100; i++)
    {
        sum_hex(s, ans, 15, 2);
        do
        {
            printf("%s", s);
            fgets(resp, MAX_QUEST, stdin);

            char *pos;
            if((pos=strchr(resp, '\n')) != NULL)
                *pos='\0';
        } while(strcmp(resp,ans) != 0);
    }
}
