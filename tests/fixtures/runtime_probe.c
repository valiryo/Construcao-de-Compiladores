#include "cobol_runtime.h"
#include <assert.h>
#include <string.h>

static cb_field field(unsigned char *p, size_t n, cb_desc *d) {
    return cb_field_at(p,n,0,n,d);
}
int main(int argc, char **argv) {
    cb_runtime rt;
    cb_runtime_init(&rt);
    cb_origin(&rt,"runtime-probe.cob",12,8);
    assert(argc==2);
    unsigned char data[256]={0};
    cb_desc dec={1,28,0,0,0,'.',""};
    cb_field f=field(data,28,&dec);
    if(!strcmp(argv[1],"big")) {
        cb_num a=cb_decimal("9999999999999999999999999999");
        cb_num b=cb_decimal("1");
        assert(cb_num_cmp(cb_sub(cb_add(a,b),b),a)==0);
        assert(cb_num_cmp(cb_mul(cb_div(a,cb_decimal("7")),cb_decimal("7")),a)==0);
        assert(!cb_store(f,a,0,1));
        assert(!memcmp(data,"9999999999999999999999999999",28));
        cb_num x=cb_mul(cb_div(cb_decimal("1"),cb_decimal("3")),cb_decimal("3"));
        assert(cb_num_cmp(x,cb_decimal("1"))==0);
    } else if(!strcmp(argv[1],"round")) {
        cb_desc d={1,5,2,1,0,'.',""};f=field(data,5,&d);
        cb_store(f,cb_decimal("-12.345"),1,0);
        assert(!memcmp(data,"0123N",5));
        assert(cb_num_cmp(cb_load(f),cb_decimal("-12.35"))==0);
        cb_store(f,cb_decimal("12.349"),0,0);
        assert(cb_num_cmp(cb_load(f),cb_decimal("12.34"))==0);
    } else if(!strcmp(argv[1],"binary")) {
        cb_desc d={1,4,0,1,1,'.',""};f=field(data,2,&d);
        cb_store(f,cb_decimal("-1234"),0,1);
        assert(data[0]==0x2e && data[1]==0xfb);
        assert(cb_num_cmp(cb_load(f),cb_decimal("-1234"))==0);
        d.digits=28;f=field(data,12,&d);
        cb_store(f,cb_decimal("-9999999999999999999999999999"),0,1);
        assert(cb_num_cmp(cb_load(f),cb_decimal("-9999999999999999999999999999"))==0);
    } else if(!strcmp(argv[1],"packed")) {
        cb_desc d={1,7,2,1,2,'.',""};f=field(data,4,&d);
        cb_store(f,cb_decimal("-12345.67"),0,1);
        const unsigned char expected[]={0x12,0x34,0x56,0x7d};
        assert(!memcmp(data,expected,4));
        assert(cb_num_cmp(cb_load(f),cb_decimal("-12345.67"))==0);
    } else if(!strcmp(argv[1],"edited")) {
        cb_desc d={3,11,2,0,0,',',"ZZZ.ZZZ.ZZZ,ZZ"};f=field(data,14,&d);
        cb_store(f,cb_decimal("1234.50"),0,0);
        assert(!memcmp(data,"      1.234,50",14));
    } else if(!strcmp(argv[1],"overflow")) {
        memset(data,'7',28);
        assert(cb_store(f,cb_decimal("10000000000000000000000000000"),0,1)==1);
        assert(!memcmp(data,"7777777777777777777777777777",28));
    } else if(!strcmp(argv[1],"strings")) {
        f=field(data,6,(cb_desc *)&cb_text_desc);
        cb_move(&rt,cb_text("abc",3,0),f);
        assert(!memcmp(data,"abc   ",6));
        cb_move(&rt,cb_text("xy",2,1),f);
        assert(!memcmp(data,"xyxyxy",6));
        cb_move(&rt,cb_field_value(cb_refmod(f,1,4)),cb_refmod(f,3,4));
        assert(!memcmp(data,"xyxyxy",6));
        assert(cb_compare(&rt,cb_text("abc",3,0),cb_text("abc   ",6,0))==0);
        assert(cb_compare(&rt,cb_fill('0'),cb_text("00000",5,0))==0);
    } else if(!strcmp(argv[1],"class")) {
        assert(cb_is_numeric(cb_text("123",3,0)));
        assert(!cb_is_numeric(cb_text("12 ",3,0)));
        assert(!cb_is_numeric(cb_text("1.2",3,0)));
        assert(!cb_is_numeric(cb_text("-12",3,0)));
        assert(cb_is_numeric(cb_fill('0')));
        assert(cb_class(&rt,cb_text("abc ",4,0),"ALPHABETIC"));
    } else if(!strcmp(argv[1],"refmod-error")) {
        f=field(data,6,(cb_desc *)&cb_text_desc);
        cb_refmod(f,5,3);
        assert(0);
    } else if(!strcmp(argv[1],"index-error")) {
        cb_index(cb_number("0"),3);
        assert(0);
    } else if(!strcmp(argv[1],"zero-error")) {
        cb_div(cb_decimal("1"),cb_decimal("0"));
        assert(0);
    } else if(!strcmp(argv[1],"intrinsics")) {
        cb_value x[]={cb_number("20240229")};
        cb_value n=cb_function(&rt,"INTEGER-OF-DATE",x,1);
        cb_value a[]={n};
        assert(cb_int(cb_function(&rt,"DATE-OF-INTEGER",a,1))==20240229);
        cb_value z[]={cb_number("-5"),cb_number("3")};
        assert(cb_int(cb_function(&rt,"MOD",z,2))==1);
        cb_value r[]={cb_text("abc  ",5,0)};
        cb_slice s=cb_bytes(&rt,cb_function(&rt,"REVERSE",r,1));
        assert(s.n==5&&!memcmp(s.p,"  cba",5));
    } else assert(0);
    cb_runtime_destroy(&rt);
    return 0;
}
