#include <stdio.h>

int main()
{
    long orig;
    scanf("%6lx",&orig);
    int red, green, blue;
    red = orig >> 16;
    green = (orig >> 8) & 0xFF;
    blue = orig & 0xFF;
    int new = ((red * 7/255) << 5) + ((green * 7/255) << 2) + (blue * 3/255);
    printf("%d\n",new);

}
