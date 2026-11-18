#include "cobol_runtime.h"
#include <string.h>
#include <limits.h>
static cb_big big_zero(void)  {
    cb_big a =  {
        1, {
            0
        }
    };
    return a;
}
static cb_big big_one(void)  {
    cb_big a =  {
        1, {
            1
        }
    };
    return a;
}
static void trim(cb_big *a)  {
    while(a->len>1 && a->v[a->len-1]==0) --a->len;
}
static int zero(cb_big a)  {
    return a.len==1 && !a.v[0];
}
static int cmp(cb_big a, cb_big b)  {
    if(a.len!=b.len) return a.len>b.len?1:-1;
    for(int i=a.len-1;i>=0;--i) if(a.v[i]!=b.v[i]) return a.v[i]>b.v[i]?1:-1;
    return 0;
}
static void capacity(int digits)  {
    if(digits>CB_DIGITS) cb_fail("DECIMAL_CAPACITY","Exact decimal intermediate exceeds 512 digits.");
}
static cb_big plus(cb_big a, cb_big b)  {
    cb_big r=big_zero();
    r.len=a.len>b.len?a.len:b.len;
    int carry=0;
    for(int i=0;i<r.len;++i)  {
        int d=(i<a.len?a.v[i]:0)+(i<b.len?b.v[i]:0)+carry;
        r.v[i]=(unsigned char)(d%10);
        carry=d/10;
    }
    if(carry)  {
        capacity(r.len+1);
        r.v[r.len++]=(unsigned char)carry;
    }
    return r;
}
static cb_big minus(cb_big a, cb_big b)  {
    int borrow=0;
    for(int i=0;i<a.len;++i)  {
        int d=a.v[i]-(i<b.len?b.v[i]:0)-borrow;
        borrow=d<0;
        if(borrow)d+=10;
        a.v[i]=(unsigned char)d;
    }
    trim(&a);
    return a;
}
static cb_big times(cb_big a, cb_big b)  {
    if(zero(a)||zero(b)) return big_zero();
    capacity(a.len+b.len);
    cb_big r=big_zero();
    r.len=a.len+b.len;
    for(int i=0;i<a.len;++i)  {
        int carry=0;
        for(int j=0;j<b.len;++j)  {
            int d=r.v[i+j]+a.v[i]*b.v[j]+carry;
            r.v[i+j]=(unsigned char)(d%10);
            carry=d/10;
        }
        for(int k=i+b.len;carry;++k)  {
            capacity(k+1);
            int d=r.v[k]+carry;
            r.v[k]=(unsigned char)(d%10);
            carry=d/10;
        }
    }
    trim(&r);
    return r;
}
static cb_big small(unsigned int n)  {
    cb_big r=big_zero();
    r.len=0;
    do  {
        r.v[r.len++]=(unsigned char)(n%10);
        n/=10;
    }
    while(n);
    return r;
}
static cb_big shift(cb_big a,int n)  {
    if(zero(a)||n==0)return a;
    capacity(a.len+n);
    memmove(a.v+n,a.v,(size_t)a.len);
    memset(a.v,0,(size_t)n);
    a.len+=n;
    return a;
}
static cb_big quotient(cb_big a, cb_big b, cb_big *remainder)  {
    if(zero(b))cb_fail("DIVISION_BY_ZERO","Division by zero.");
    cb_big q=big_zero(),r=big_zero();
    q.len=a.len;
    for(int i=a.len-1;i>=0;--i)  {
        r=shift(r,1);
        r.v[0]=a.v[i];
        trim(&r);
        unsigned char digit=0;
        while(cmp(r,b)>=0) {
            r=minus(r,b);
            ++digit;
        }
        q.v[i]=digit;
    }
    trim(&q);
    *remainder=r;
    return q;
}
static cb_num normalized(cb_num a)  {
    if(zero(a.n)) {
        a.sign=0;
        a.d=big_one();
        return a;
    }
    /* Common powers of ten are cheap and prevent scale growth in loops. */
    while(a.n.v[0]==0 && a.d.v[0]==0)  {
        memmove(a.n.v,a.n.v+1,(size_t)--a.n.len);
        a.n.v[a.n.len]=0;
        memmove(a.d.v,a.d.v+1,(size_t)--a.d.len);
        a.d.v[a.d.len]=0;
    }
    return a;
}
cb_num cb_decimal(const char *s)  {
    cb_num r= {
        1, {
            1, {
                0
            }
        }, {
            1, {
                1
            }
        }
    };
    size_t n=strlen(s),start=0,end=n;
    int scale=0,point=0,seen=0;
    while(start<end && s[start]==' ')++start;
    while(end>start && s[end-1]==' ')--end;
    if(start<end && (s[start]=='-'||s[start]=='+')) {
        r.sign=s[start]=='-'?-1:1;
        ++start;
    }
    for(size_t i=start;i<end;++i)  {
        unsigned char c=(unsigned char)s[i];
        if(c=='.'&&!point) {
            point=1;
            continue;
        }
        if(c<'0'||c>'9')cb_fail("INVALID_NUMERIC","Invalid numeric representation.");
        r.n=shift(r.n,1);
        r.n.v[0]=(unsigned char)(c-'0');
        seen=1;
        if(point)++scale;
    }
    if(!seen)cb_fail("INVALID_NUMERIC","Empty numeric representation.");
    r.d=shift(big_one(),scale);
    return normalized(r);
}
cb_num cb_negate(cb_num a) {
    a.sign=-a.sign;
    return a;
}
cb_num cb_add(cb_num a,cb_num b)  {
    cb_num r;
    r.d=times(a.d,b.d);
    cb_big x=times(a.n,b.d),y=times(b.n,a.d);
    if(a.sign==b.sign) {
        r.sign=a.sign;
        r.n=plus(x,y);
    }
    else  {
        int c=cmp(x,y);
        r.sign=c>=0?a.sign:b.sign;
        r.n=c>=0?minus(x,y):minus(y,x);
    }
    return normalized(r);
}
cb_num cb_sub(cb_num a,cb_num b) {
    return cb_add(a,cb_negate(b));
}
cb_num cb_mul(cb_num a,cb_num b) {
    cb_num r= {
        a.sign*b.sign,times(a.n,b.n),times(a.d,b.d)
    };
    return normalized(r);
}
cb_num cb_div(cb_num a,cb_num b) {
    if(!b.sign) {
        cb_math_error("DIVISION_BY_ZERO","Division by zero.");
        return cb_decimal("0");
    }
    cb_num r= {
        a.sign*b.sign,times(a.n,b.d),times(a.d,b.n)
    };
    return normalized(r);
}
int cb_num_cmp(cb_num a,cb_num b) {
    if(a.sign!=b.sign)return a.sign>b.sign?1:-1;
    return a.sign*cmp(times(a.n,b.d),times(b.n,a.d));
}
static long long big_int(cb_big a)  {
    unsigned long long result=0;
    for(int i=a.len-1;i>=0;--i) {
        if(result>((unsigned long long)LLONG_MAX-a.v[i])/10)cb_fail("INTEGER_RANGE","Integer exceeds control/index range.");
        result=result*10+a.v[i];
    }
    return (long long)result;
}
long long cb_int(cb_value value)  {
    cb_num a=cb_as_num(value);
    cb_big rem,q=quotient(a.n,a.d,&rem);
    if(!zero(rem))cb_fail("INTEGER_REQUIRED","Control value must be an exact integer.");
    return a.sign*big_int(q);
}
cb_num cb_integer_num(cb_num a,int floor_mode) {
    cb_big rem;
    cb_num r= {
        a.sign,quotient(a.n,a.d,&rem),big_one()
    };
    if(a.sign<0&&floor_mode&&!zero(rem))r.n=plus(r.n,big_one());
    return normalized(r);
}
cb_num cb_power(cb_num a,cb_num b)  {
    long long exponent=cb_int(cb_numeric_value(b));
    if(exponent>4096||exponent< -4096)cb_fail("POWER_RANGE","Power exponent outside -4096..4096.");
    cb_num r=cb_decimal("1");
    int inverse=exponent<0;
    if(inverse)exponent=-exponent;
    while(exponent) {
        if(exponent&1)r=cb_mul(r,a);
        exponent/=2;
        if(exponent)a=cb_mul(a,a);
    }
    return inverse?cb_div(cb_decimal("1"),r):r;
}
static cb_big scaled(cb_num value,int scale,int rounded) {
    cb_big rem,q=quotient(shift(value.n,scale),value.d,&rem);
    if(rounded&&cmp(plus(rem,rem),value.d)>=0)q=plus(q,big_one());
    return q;
}
static int decode_sign(unsigned char *c) {
    const char *positive="{ABCDEFGHI",*negative="}JKLMNOPQR";
    for(int i=0;i<10;++i) {
        if(*c==(unsigned char)positive[i]) {
            *c=(unsigned char)('0'+i);
            return 1;
        }
        if(*c==(unsigned char)negative[i]) {
            *c=(unsigned char)('0'+i);
            return -1;
        }
    }
    return 0;
}
int cb_is_numeric(cb_value v) {
    if(v.kind==3) return (unsigned char)v.f.n=='0';
    if(v.kind==1)return 1;
    if(v.kind==0&&v.f.desc->category==1&&v.f.desc->usage==1)return 1;
    if(v.kind==0&&v.f.desc->category==1&&v.f.desc->usage==2) {
        for(size_t i=0;i<v.f.n;++i) {
            unsigned char a=v.f.p[i]>>4,b=v.f.p[i]&15;
            if(a>9)return 0;
            if(i+1==v.f.n) {
                if(b!=12&&b!=13&&b!=15)return 0;
            }
            else if(b>9)return 0;
        }
        return 1;
    }
    cb_slice s=v.kind==0?(cb_slice) {
        v.f.p,v.f.n
    }
    :v.text;
    if(!s.n)return 0;
    for(size_t i=0;i<s.n;++i) {
        unsigned char c=s.p[i];
        if(v.kind==0&&v.f.desc->signedness&&i+1==s.n)decode_sign(&c);
        if(c<'0'||c>'9')return 0;
    }
    return 1;
}
cb_num cb_load(cb_field f)  {
    const cb_desc *d=f.desc;
    cb_num r= {
        1, {
            1, {
                0
            }
        }, {
            1, {
                1
            }
        }
    };
    if(d->category!=1)cb_fail("NUMERIC_DESCRIPTOR","A numeric descriptor is required.");
    if(!cb_is_numeric(cb_field_value(f)))cb_fail("INVALID_NUMERIC","Field contains invalid numeric bytes.");
    if(d->usage==1) {
        int negative=d->signedness&&f.n&&(f.p[f.n-1]&128);
        unsigned int carry=negative?1:0;
        unsigned char bytes[128];
        if(f.n>sizeof bytes)cb_fail("BINARY_CAPACITY","Binary field too wide.");
        for(size_t i=0;i<f.n;++i) {
            unsigned int x=(negative?(unsigned char)~f.p[i]:f.p[i])+carry;
            bytes[i]=(unsigned char)x;
            carry=x>>8;
        }
        for(size_t i=f.n;i>0;--i)r.n=plus(times(r.n,small(256)),small(bytes[i-1]));
        if(negative)r.sign=-1;
    }
    else if(d->usage==2) {
        for(size_t i=0;i<f.n;++i) {
            r.n=plus(shift(r.n,1),small(f.p[i]>>4));
            if(i+1<f.n)r.n=plus(shift(r.n,1),small(f.p[i]&15));
            else if((f.p[i]&15)==13)r.sign=-1;
        }
    }
    else {
        for(size_t i=0;i<f.n;++i) {
            unsigned char c=f.p[i];
            if(d->signedness&&i+1==f.n) {
                int sign=decode_sign(&c);
                if(sign)r.sign=sign;
            }
            r.n=shift(r.n,1);
            r.n.v[0]=(unsigned char)(c-'0');
        }
    }
    r.d=shift(big_one(),d->scale);
    return normalized(r);
}
int cb_floating_sign(const cb_desc *desc) {
    int plus=0,minus=0;
    for(const char *p=desc->pic;*p;++p) { plus+=*p=='+'; minus+=*p=='-'; }
    return plus>1?'+':minus>1?'-':0;
}
int cb_store(cb_field f,cb_num value,int rounded,int checked)  {
    if(checked && cb_math_failed()) return 1;
    const cb_desc *d=f.desc;
    cb_big q=scaled(value,d->scale,rounded);
    if(checked&&q.len>d->digits)return 1;
    if(d->category!=1&&d->category!=3)cb_fail("NUMERIC_DESCRIPTOR","Numeric receiver required.");
    if(d->digits>CB_FIELD_DIGITS)cb_fail("FIELD_PRECISION","Numeric receiver exceeds 128 digits.");
    if(q.len>d->digits) {
        q.len=d->digits;
        trim(&q);
    }
    if(d->category==3) {
        if(!value.sign && !strchr(d->pic,'9')) {
            memset(f.p,' ',f.n);
            return 0;
        }
        int digit=d->digits-1,nonzero=0;
        int floating=cb_floating_sign(d),seen=0,placed=0;
        size_t sign_slot=0;
        size_t out=0;
        int after=0;
        for(const char *p=d->pic;*p;++p) {
            char c=*p;
            if(c=='S'||c=='V') {
                if(c=='V')after=1;
                continue;
            }
            if(c==floating&&!seen++) {
                sign_slot=out; f.p[out++]=' '; continue;
            }
            if(c=='9'||c=='Z'||c=='*'||c==floating) {
                int v=digit>=0&&digit<q.len?q.v[digit]:0;
                --digit;
                if(c=='9'||v||after)nonzero=1;
                if(c!='9'&&!nonzero) { sign_slot=out; f.p[out++]=(unsigned char)(c=='*'?'*':' '); }
                else {
                    if(floating&&!placed) { f.p[sign_slot]=(unsigned char)(value.sign<0?'-':floating=='+'?'+':' '); placed=1; }
                    f.p[out++]=(unsigned char)('0'+v);
                }
            }
            else if(c==d->decimal) {
                if(floating&&!placed) { f.p[sign_slot]=(unsigned char)(value.sign<0?'-':floating=='+'?'+':' '); placed=1; }
                f.p[out++]=(unsigned char)c;
                after=1;
                nonzero=1;
            }
            else if(c=='+'||c=='-')f.p[out++]=(unsigned char)(value.sign<0?'-':c=='+'?'+':' ');
            else if(c=='B')f.p[out++]=' ';
            else if(c=='0')f.p[out++]='0';
            else {
                if(floating&&!nonzero&&(c=='.'||c==','))sign_slot=out;
                f.p[out++]=(unsigned char)(!nonzero&&(c=='.'||c==','||c=='/')?' ':c);
            }
        }
        if(out!=f.n)cb_fail("PICTURE_LENGTH","Edited picture/descriptor size mismatch.");
    }
    else if(d->usage==1) {
        for(size_t i=0;i<f.n;++i) {
            cb_big rem;
            q=quotient(q,small(256),&rem);
            f.p[i]=(unsigned char)big_int(rem);
        }
        if(value.sign<0&&d->signedness) {
            unsigned int carry=1;
            for(size_t i=0;i<f.n;++i) {
                unsigned int x=(unsigned char)~f.p[i]+carry;
                f.p[i]=(unsigned char)x;
                carry=x>>8;
            }
        }
    }
    else if(d->usage==2) {
        memset(f.p,0,f.n);
        size_t nibble=f.n*2-1;
        f.p[f.n-1]=(unsigned char)(value.sign<0&&d->signedness?13:12);
        for(int i=0;i<d->digits;++i) {
            --nibble;
            unsigned char digit=(unsigned char)(i<q.len?q.v[i]:0);
            if(nibble&1)f.p[nibble/2]|=digit;
            else f.p[nibble/2]|=(unsigned char)(digit<<4);
        }
    }
    else {
        for(size_t i=0;i<f.n;++i) {
            size_t digit=f.n-i-1;
            f.p[i]=(unsigned char)('0'+(digit<(size_t)q.len?q.v[digit]:0));
        }
        if(d->signedness&&f.n) {
            int digit=f.p[f.n-1]-'0';
            f.p[f.n-1]=(unsigned char)(value.sign<0?"}JKLMNOPQR"[digit]:"{ABCDEFGHI"[digit]);
        }
    }
    return 0;
}
