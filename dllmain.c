#include "dllmain.h"

int my_dll1()
{
	printf("dll is ok");
}

int my_dll2(char* chars1, int len_chars1, char* key,int len_key)
{
	int len = 0;
	char* key_i = key;
	//printf("%d	%d\n", len_chars1, len_key);
	while (len < len_chars1)
	{
		//printf("%d	%d	", *chars1, *key_i);
		*chars1 = ((~*chars1) & (*key_i)) | (*chars1 & (~*key_i));
		//printf("%c\n", *chars1);
		len++;//统计长度做校验
		key_i = key + (len % len_key);
		chars1++;//指针移动到字符串的下一位
	}
	//chars1 = chars1 - len;
	return len;
}

