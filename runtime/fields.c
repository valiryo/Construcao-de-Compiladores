#include "cobol_runtime.h"
#include <stdlib.h>
#include <string.h>
#include <ctype.h>
#include <limits.h>
#include <time.h>
const cb_desc cb_text_desc= {
    0,0,0,0,0,'.',""
};
static _Thread_local cb_runtime *active;
static _Thread_local int math_handled, math_failed;
void cb_math_begin(int handled) { math_handled=handled; math_failed=0; }
int cb_math_failed(void) { return math_failed; }
int cb_math_error(const char *code, const char *message) {
    if (!math_handled) cb_fail(code,message);
    math_failed=1;
    return 1;
}
void cb_math_end(void) { math_handled=math_failed=0; }
void cb_runtime_init(cb_runtime *rt) {
    memset(rt,0,sizeof *rt);
    rt->random=1;
    const char *encoding=getenv("COBOL_TERMINAL_ENCODING");
    rt->raw_terminal=encoding&&strcmp(encoding,"latin1")==0;
    active=rt;
}
void cb_origin(cb_runtime *rt,const char *file,int line,int column) {
    active=rt;
    rt->file=file;
    rt->line=line;
    rt->column=column;
}
_Noreturn void cb_fail(const char *code,const char *message) {
    if(active&&active->file)fprintf(stderr,"%s:%d:%d: ",active->file,active->line,active->column);
    fprintf(stderr,"%s: %s\n",code,message);
    exit(1);
}
void *cb_alloc(cb_runtime *rt,size_t n) {
    cb_mem *m=malloc(sizeof *m);
    if(!m)cb_fail("OUT_OF_MEMORY","Cannot allocate runtime memory.");
    m->data=calloc(n?n:1,1);
    if(!m->data)cb_fail("OUT_OF_MEMORY","Cannot allocate runtime buffer.");
    m->next=rt->memory;
    rt->memory=m;
    return m->data;
}
void cb_release(cb_runtime *rt,cb_mem *mark) {
    while(rt->memory!=mark) {
        if(!rt->memory)cb_fail("ARENA_SCOPE","Invalid memory scope.");
        cb_mem *m=rt->memory;
        rt->memory=m->next;
        free(m->data);
        free(m);
    }
}
void cb_runtime_destroy(cb_runtime *rt) {
    for(cb_file *f=rt->files;f;f=f->next) {
        if(f->fp) {
            if(fclose(f->fp))cb_fail("FILE_CLOSE","Error closing file at run-unit termination.");
            f->fp=NULL;
        }
    }
    cb_release(rt,NULL);
}
cb_slice cb_slice_literal(const char *s,size_t n) {
    return (cb_slice) {
        (unsigned char *)s,n
    };
}
cb_field cb_field_at(unsigned char *base,size_t capacity,size_t offset,size_t n,const cb_desc *desc) {
    if(!base)cb_fail("LINKAGE_UNBOUND","Access to unbound LINKAGE storage.");
    if(offset>capacity||n>capacity-offset)cb_fail("STORAGE_BOUNDS","Field access exceeds storage area.");
    return(cb_field) {
        base+offset,n,desc
    };
}
cb_field cb_refmod(cb_field f,long long start,long long length) {
    if(start<1||(unsigned long long)start>f.n||length<1||(unsigned long long)length>f.n-(size_t)start+1)cb_fail("REFMOD_BOUNDS","Reference modification out of bounds.");
    return(cb_field) {
        f.p+start-1,(size_t)length,&cb_text_desc
    };
}
long long cb_bound(long long n,long long minimum,long long maximum) {
    if(n<minimum||n>maximum)cb_fail("OCCURS_DEPENDING","Active OCCURS size outside declared bounds.");
    return n;
}
long long cb_index(cb_value value,long long bound) {
    long long n=cb_int(value);
    if(n<1||n>bound)cb_fail("SUBSCRIPT_BOUNDS","Table subscript out of bounds.");
    return n-1;
}
cb_value cb_field_value(cb_field f) {
    cb_value v= {
        0
    };
    v.f=f;
    return v;
}
cb_value cb_number(const char *s) {
    cb_value v= {
        0
    };
    v.kind=1;
    v.num=cb_decimal(s);
    v.text=cb_slice_literal(s,strlen(s));
    return v;
}
cb_value cb_numeric_value(cb_num n) {
    cb_value v= {
        0
    };
    v.kind=1;
    v.num=n;
    return v;
}
cb_value cb_text(const char *s,size_t n,int repeat) {
    cb_value v= {
        0
    };
    v.kind=2;
    v.text=cb_slice_literal(s,n);
    v.repeat=repeat;
    return v;
}
cb_value cb_fill(unsigned char byte) {
    cb_value v= {
        0
    };
    v.kind=3;
    v.repeat=1;
    v.f.n=byte;
    return v;
}
cb_slice cb_bytes(cb_runtime *rt,cb_value v) {
    if(v.kind==0) {
        if(v.f.desc->category==1&&cb_is_numeric(v)) {
            cb_desc d=*v.f.desc;
            d.usage=0;
            d.signedness=0;
            unsigned char *p=cb_alloc(rt,(size_t)d.digits);
            cb_field f= {
                p,(size_t)d.digits,&d
            };
            cb_store(f,cb_load(v.f),0,0);
            return(cb_slice) {
                p,(size_t)d.digits
            };
        }
        return(cb_slice) {
            v.f.p,v.f.n
        };
    }
    if(v.kind==3) {
        unsigned char *p=cb_alloc(rt,1);
        *p=(unsigned char)v.f.n;
        return(cb_slice) {
            p,1
        };
    }
    if(v.kind==2||v.text.p)return v.text;
    cb_num integer=cb_integer_num(v.num,0);
    if(cb_num_cmp(integer,v.num)!=0)cb_fail("NONINTEGER_TEXT","Noninteger expression requires a numeric receiver before text conversion.");
    cb_desc d= {
        1,CB_FIELD_DIGITS,0,0,0,'.',""
    };
    unsigned char *p=cb_alloc(rt,CB_FIELD_DIGITS+2);
    cb_field f= {
        p+1,CB_FIELD_DIGITS,&d
    };
    cb_store(f,v.num,0,1);
    size_t start=1;
    while(start<CB_FIELD_DIGITS&&p[start]=='0')++start;
    if(v.num.sign<0)p[--start]='-';
    return(cb_slice) {
        p+start,CB_FIELD_DIGITS+1-start
    };
}
cb_num cb_as_num(cb_value v) {
    if(v.kind==1)return v.num;
    if(v.kind==0&&v.f.desc->category==1)return cb_load(v.f);
    if(v.kind==3&&(unsigned char)v.f.n=='0')return cb_decimal("0");
    cb_slice s=v.kind==0?(cb_slice) {
        v.f.p,v.f.n
    }
    :v.text;
    if(s.n>CB_DIGITS)cb_fail("NUMERIC_CAPACITY","Numeric text too long.");
    char text[CB_DIGITS+1];
    memcpy(text,s.p,s.n);
    text[s.n]=0;
    return cb_decimal(text);
}
void cb_move(cb_runtime *rt,cb_value source,cb_field target) {
    if(target.desc->category==1||target.desc->category==3) {
        if(source.kind==3&&(unsigned char)source.f.n!='0') {
            memset(target.p,(unsigned char)source.f.n,target.n);
            return;
        }
        if(source.kind==0&&source.f.desc->category==2) {
            cb_slice s= {
                source.f.p,source.f.n
            };
            size_t n=s.n<target.n?s.n:target.n;
            memmove(target.p,s.p,n);
            if(n<target.n)memset(target.p+n,' ',target.n-n);
            return;
        }
        cb_store(target,cb_as_num(source),0,0);
        return;
    }
    cb_slice text;
    if(source.kind==0&&(source.f.desc->category==2||target.desc->category==2))text=(cb_slice) {
        source.f.p,source.f.n
    };
    else text=cb_bytes(rt,source);
    if(source.repeat) {
        if(!text.n)cb_fail("EMPTY_REPEAT","Cannot repeat empty value.");
        unsigned char *copy=cb_alloc(rt,text.n);
        memcpy(copy,text.p,text.n);
        for(size_t i=0;i<target.n;++i)target.p[i]=copy[i%text.n];
    }
    else {
        size_t n=text.n<target.n?text.n:target.n;
        memmove(target.p,text.p,n);
        if(n<target.n)memset(target.p+n,' ',target.n-n);
    }
}
static int numeric_kind(cb_value v) {
    return v.kind==1||(v.kind==0&&v.f.desc->category==1)||(v.kind==3&&(unsigned char)v.f.n=='0');
}
int cb_compare(cb_runtime *rt,cb_value a,cb_value b) {
    if(numeric_kind(a)&&numeric_kind(b)&&cb_is_numeric(a)&&cb_is_numeric(b))return cb_num_cmp(cb_as_num(a),cb_as_num(b));
    cb_slice x=cb_bytes(rt,a),y=cb_bytes(rt,b);
    size_t n=x.n>y.n?x.n:y.n;
    for(size_t i=0;i<n;++i) {
        unsigned char l=i<x.n?x.p[i]:a.repeat&&x.n?x.p[i%x.n]:' ',r=i<y.n?y.p[i]:b.repeat&&y.n?y.p[i%y.n]:' ';
        if(l!=r)return l>r?1:-1;
    }
    return 0;
}
int cb_class(cb_runtime *rt,cb_value v,const char *category) {
    if(strcmp(category,"NUMERIC")==0)return cb_is_numeric(v);
    if(strcmp(category,"POSITIVE")==0)return cb_as_num(v).sign>0;
    if(strcmp(category,"NEGATIVE")==0)return cb_as_num(v).sign<0;
    if(strcmp(category,"ZERO")==0)return cb_as_num(v).sign==0;
    cb_slice s=cb_bytes(rt,v);
    for(size_t i=0;i<s.n;++i) {
        unsigned char c=s.p[i];
        int lower=(c>='a'&&c<='z')||(c>=224&&c!=247),upper=(c>='A'&&c<='Z')||(c>=192&&c<=222&&c!=215);
        if(c==' ')continue;
        if(strcmp(category,"ALPHABETIC-LOWER")==0?!lower:strcmp(category,"ALPHABETIC-UPPER")==0?!upper:!(lower||upper))return 0;
    }
    return s.n!=0;
}
static void output(cb_runtime *rt,unsigned char c) {
    if(!rt->raw_terminal&&c>=128) {
        if(fputc(0xc0|(c>>6),stdout)==EOF||fputc(0x80|(c&63),stdout)==EOF)cb_fail("STDOUT_WRITE","Cannot write stdout.");
    }
    else if(fputc(c,stdout)==EOF)cb_fail("STDOUT_WRITE","Cannot write stdout.");
}
void cb_display(cb_runtime *rt,cb_value v) {
    if(v.kind==0&&v.f.desc->category==1&&cb_is_numeric(v)) {
        cb_slice s=cb_bytes(rt,v);
        const cb_desc *d=v.f.desc;
        if(d->signedness)output(rt,cb_load(v.f).sign<0?'-':'+');
        if(d->scale==d->digits)output(rt,(unsigned char)d->decimal);
        for(size_t i=0;i<s.n;++i) {
            output(rt,s.p[i]);
            if(d->scale&&i+1==s.n-(size_t)d->scale)output(rt,(unsigned char)d->decimal);
        }
        return;
    }
    cb_slice s=cb_bytes(rt,v);
    for(size_t i=0;i<s.n;++i)output(rt,s.p[i]);
}
void cb_display_end(int no_advancing) {
    if(!no_advancing&&fputc('\n',stdout)==EOF)cb_fail("STDOUT_WRITE","Cannot write stdout.");
    if(fflush(stdout))cb_fail("STDOUT_WRITE","Cannot flush stdout.");
}
static char *read_input(cb_runtime *rt) {
    size_t cap=128,n=0;
    char *p=malloc(cap);
    if(!p)cb_fail("OUT_OF_MEMORY","Cannot allocate input.");
    int c;
    while((c=fgetc(stdin))!=EOF&&c!='\n') {
        if(n+2>=cap) {
            cap*=2;
            if(cap>1048576)cb_fail("INPUT_TOO_LONG","Input line exceeds 1 MiB.");
            char *q=realloc(p,cap);
            if(!q)cb_fail("OUT_OF_MEMORY","Cannot grow input.");
            p=q;
        }
        p[n++]=(char)c;
    }
    if(c==EOF&&n==0) {
        free(p);
        cb_fail(ferror(stdin)?"STDIN_READ":"STDIN_EOF","No input available for ACCEPT.");
    }
    if(n&&p[n-1]=='\r')--n;
    p[n]=0;
    char *out=cb_alloc(rt,n+1);
    size_t j=0;
    for(size_t i=0;i<n;++i) {
        unsigned char byte=(unsigned char)p[i];
        if(!rt->raw_terminal&&byte>=128) {
            if((byte!=0xc2&&byte!=0xc3)||i+1>=n||((unsigned char)p[i+1]&0xc0)!=0x80)cb_fail("TERMINAL_ENCODING","Input is not UTF-8 representable in ISO-8859-1.");
            byte=(unsigned char)(((byte&31)<<6)|((unsigned char)p[++i]&63));
        }
        out[j++]=(char)byte;
    }
    out[j]=0;
    free(p);
    return out;
}
static int leap(int y) {
    return y%4==0&&(y%100!=0||y%400==0);
}
static int month_days(int y,int m) {
    static const int days[]= {
        0,31,28,31,30,31,30,31,31,30,31,30,31
    };
    return days[m]+(m==2&&leap(y));
}
static long long date_integer(int y,int m,int d) {
    if(y<1601||y>9999||m<1||m>12||d<1||d>month_days(y,m))cb_fail("DATE_DOMAIN","Invalid Gregorian date (1601..9999).");
    long long n=d;
    for(int i=1601;i<y;++i)n+=365+leap(i);
    for(int i=1;i<m;++i)n+=month_days(y,i);
    return n;
}
static struct tm clock_value(void) {
    struct tm t= {
        0
    };
    const char *fixed=getenv("COBOL_DATETIME");
    if(fixed) {
        int y,m,d,h=0,mi=0,s=0,used=0;
        if(sscanf(fixed,"%d-%d-%dT%d:%d:%d%n",&y,&m,&d,&h,&mi,&s,&used)!=6||fixed[used]||h<0||h>23||mi<0||mi>59||s<0||s>59)cb_fail("CLOCK_FORMAT","COBOL_DATETIME must be YYYY-MM-DDTHH:MM:SS.");
        long long n=date_integer(y,m,d);
        t.tm_year=y-1900;
        t.tm_mon=m-1;
        t.tm_mday=d;
        t.tm_hour=h;
        t.tm_min=mi;
        t.tm_sec=s;
        t.tm_wday=(int)(n%7);
        t.tm_yday=0;
        for(int i=1;i<m;++i)t.tm_yday+=month_days(y,i);
        t.tm_yday+=d-1;
        return t;
    }
    time_t now=time(NULL);
    struct tm *current=localtime(&now);
    if(!current)cb_fail("CLOCK_READ","Cannot read local clock.");
    return *current;
}
void cb_accept(cb_runtime *rt,cb_field f,const char *source,const char *format) {
    char date[40];
    char *text;
    if(source&&(!strcmp(source,"DATE")||!strcmp(source,"DAY")||!strcmp(source,"DAY-OF-WEEK")||!strcmp(source,"TIME"))) {
        struct tm t=clock_value();
        if(!strcmp(source,"DATE")) {
            if(format&&!strcmp(format,"YYYYMMDD"))snprintf(date,sizeof date,"%04d%02d%02d",t.tm_year+1900,t.tm_mon+1,t.tm_mday);
            else snprintf(date,sizeof date,"%02d%02d%02d",(t.tm_year+1900)%100,t.tm_mon+1,t.tm_mday);
        }
        else if(!strcmp(source,"DAY")) {
            if(format&&!strcmp(format,"YYYYDDD"))snprintf(date,sizeof date,"%04d%03d",t.tm_year+1900,t.tm_yday+1);
            else snprintf(date,sizeof date,"%02d%03d",(t.tm_year+1900)%100,t.tm_yday+1);
        }
        else if(!strcmp(source,"DAY-OF-WEEK"))snprintf(date,sizeof date,"%d",t.tm_wday?t.tm_wday:7);
        else snprintf(date,sizeof date,"%02d%02d%02d00",t.tm_hour,t.tm_min,t.tm_sec);
        text=date;
    }
    else if(!source||!strcmp(source,"CONSOLE"))text=read_input(rt);
    else cb_fail("ACCEPT_SOURCE","Unsupported ACCEPT source.");
    if(f.desc->category==1) {
        size_t n=strlen(text);
        char *numeric=cb_alloc(rt,n+1);
        memcpy(numeric,text,n+1);
        for(size_t i=0;i<n;++i)if(numeric[i]==f.desc->decimal)numeric[i]='.';
        int valid=0,point=0;
        size_t i=0;
        while(numeric[i]==' ')++i;
        if(numeric[i]=='+'||numeric[i]=='-')++i;
        for(;numeric[i];++i) {
            if(numeric[i]>='0'&&numeric[i]<='9')valid=1;
            else if(numeric[i]=='.'&&!point)point=1;
            else if(numeric[i]==' ') {
                while(numeric[i]==' ')++i;
                if(numeric[i])valid=0;
                break;
            }
            else {
                valid=0;
                break;
            }
        }
        if(valid)cb_store(f,cb_decimal(numeric),0,0);
        else {
            memset(f.p,' ',f.n);
            size_t size=n<f.n?n:f.n;
            memcpy(f.p,text,size);
        }
    }
    else cb_move(rt,cb_text(text,strlen(text),0),f);
}
cb_value cb_function(cb_runtime *rt,const char *name,cb_value *args,size_t count) {
    if(!strcmp(name,"REVERSE")||!strcmp(name,"UPPER-CASE")||!strcmp(name,"LOWER-CASE")) {
        cb_slice s=cb_bytes(rt,args[0]);
        unsigned char *out=cb_alloc(rt,s.n);
        for(size_t i=0;i<s.n;++i) {
            unsigned char c=s.p[i];
            if(!strcmp(name,"REVERSE"))out[s.n-i-1]=c;
            else {
                if(!strcmp(name,"UPPER-CASE")) {
                    if((c>='a'&&c<='z')||(c>=224&&c<=254&&c!=247))c-=32;
                }
                else if((c>='A'&&c<='Z')||(c>=192&&c<=222&&c!=215))c+=32;
                out[i]=c;
            }
        }
        return cb_text((const char *)out,s.n,0);
    }
    char number[64];
    long long n=0;
    if(!strcmp(name,"INTEGER"))return cb_numeric_value(cb_integer_num(cb_as_num(args[0]),1));
    if(!strcmp(name,"MOD")) {
        cb_num a=cb_as_num(args[0]),b=cb_as_num(args[1]);
        return cb_numeric_value(cb_sub(a,cb_mul(b,cb_integer_num(cb_div(a,b),1))));
    }
    if(!strcmp(name,"RANDOM")) {
        if(count)rt->random=(uint32_t)cb_int(args[0]);
        rt->random=rt->random*1664525u+1013904223u;
        snprintf(number,sizeof number,"%u",rt->random);
        return cb_numeric_value(cb_div(cb_decimal(number),cb_decimal("4294967296")));
    }
    if(!strcmp(name,"LENGTH"))n=(long long)cb_bytes(rt,args[0]).n;
    else if(!strcmp(name,"ORD")) {
        cb_slice s=cb_bytes(rt,args[0]);
        if(s.n!=1)cb_fail("ORD_LENGTH","ORD requires one byte.");
        n=s.p[0]+1;
    }
    else if(!strcmp(name,"INTEGER-OF-DATE")) {
        long long date=cb_int(args[0]);
        n=date_integer((int)(date/10000),(int)(date/100%100),(int)(date%100));
    }
    else if(!strcmp(name,"DATE-OF-INTEGER")) {
        n=cb_int(args[0]);
        if(n<1||n>3067671)cb_fail("DATE_DOMAIN","Date integer outside supported calendar.");
        int y=1601,m=1;
        while(n>365+leap(y)) {
            n-=365+leap(y);
            ++y;
        }
        while(n>month_days(y,m)) {
            n-=month_days(y,m);
            ++m;
        }
        n=y*10000+m*100+n;
    }
    else cb_fail("INTRINSIC","Unsupported intrinsic function.");
    snprintf(number,sizeof number,"%lld",n);
    return cb_number((char *)memcpy(cb_alloc(rt,strlen(number)+1),number,strlen(number)+1));
}
long long cb_inspect_count(cb_runtime *rt,cb_value subject,const char *mode,cb_value pattern) {
    cb_slice s=cb_bytes(rt,subject),p=cb_bytes(rt,pattern);
    if(!strcmp(mode,"CHARACTERS"))return(long long)s.n;
    if(!p.n)cb_fail("INSPECT_PATTERN","Empty INSPECT pattern.");
    long long n=0;
    if(!strcmp(mode,"TRAILING")) {
        size_t end=s.n;
        while(end>=p.n&&!memcmp(s.p+end-p.n,p.p,p.n)) {
            ++n;
            end-=p.n;
        }
        return n;
    }
    for(size_t i=0;i+p.n<=s.n;) {
        if(!memcmp(s.p+i,p.p,p.n)) {
            ++n;
            i+=p.n;
            if(!strcmp(mode,"FIRST"))break;
        }
        else {
            if(!strcmp(mode,"LEADING"))break;
            ++i;
        }
    }
    return n;
}
void cb_inspect_replace(cb_runtime *rt,cb_field subject,const char *mode,cb_value pattern,cb_value replacement) {
    cb_slice p=cb_bytes(rt,pattern),r=cb_bytes(rt,replacement);
    if(!p.n||p.n!=r.n)cb_fail("INSPECT_LENGTH","Replacement width differs from pattern.");
    size_t start=0,end=subject.n;
    if(!strcmp(mode,"TRAILING")) {
        start=end;
        while(start>=p.n&&!memcmp(subject.p+start-p.n,p.p,p.n))start-=p.n;
    }
    for(size_t i=start;i+p.n<=end;) {
        if(!memcmp(subject.p+i,p.p,p.n)) {
            memmove(subject.p+i,r.p,p.n);
            i+=p.n;
            if(!strcmp(mode,"FIRST"))break;
        }
        else {
            if(!strcmp(mode,"LEADING"))break;
            ++i;
        }
    }
}
void cb_inspect_convert(cb_runtime *rt,cb_field subject,cb_value from,cb_value to) {
    cb_slice a=cb_bytes(rt,from),b=cb_bytes(rt,to);
    if(a.n!=b.n)cb_fail("INSPECT_LENGTH","CONVERTING maps have different lengths.");
    for(size_t i=0;i<subject.n;++i)for(size_t j=0;j<a.n;++j)if(subject.p[i]==a.p[j]) {
        subject.p[i]=b.p[j];
        break;
    }
}
int cb_string_part(cb_runtime *rt,cb_field target,long long *pointer,cb_value value,cb_value delimiter,int size) {
    cb_slice s=cb_bytes(rt,value);
    size_t n=s.n;
    if(!size) {
        cb_slice d=cb_bytes(rt,delimiter);
        if(!d.n)cb_fail("STRING_DELIMITER","Empty delimiter.");
        for(size_t i=0;i+d.n<=n;++i)if(!memcmp(s.p+i,d.p,d.n)) {
            n=i;
            break;
        }
    }
    if(*pointer<1||(unsigned long long)*pointer>target.n+1)return 1;
    size_t available=target.n-(size_t)*pointer+1,copy=n<available?n:available;
    memmove(target.p+*pointer-1,s.p,copy);
    *pointer+=(long long)copy;
    return n>available;
}
long long cb_unstring_next(cb_runtime *rt,cb_value source,long long *pointer,cb_value *delimiters,int *alls,size_t count,cb_field target,cb_field delimiter_in,cb_field count_in) {
    cb_slice s=cb_bytes(rt,source);
    if(*pointer<1||(unsigned long long)*pointer>s.n)return 0;
    size_t begin=(size_t)*pointer-1,end=begin,delim=0;
    int which=-1;
    for(;end<s.n;++end) {
        for(size_t j=0;j<count;++j) {
            cb_slice d=cb_bytes(rt,delimiters[j]);
            if(!d.n)cb_fail("UNSTRING_DELIMITER","Empty delimiter.");
            if(end+d.n<=s.n&&!memcmp(s.p+end,d.p,d.n)) {
                which=(int)j;
                delim=d.n;
                break;
            }
        }
        if(which>=0)break;
    }
    cb_move(rt,cb_text((const char *)s.p+begin,end-begin,0),target);
    if(delimiter_in.p)cb_move(rt,delim?cb_text((const char *)s.p+end,delim,0):cb_fill(' '),delimiter_in);
    if(count_in.p) {
        char n[32];
        snprintf(n,sizeof n,"%zu",end-begin);
        cb_store(count_in,cb_decimal(n),0,0);
    }
    size_t next=end+delim;
    if(which>=0&&alls[which])while(next+delim<=s.n&&!memcmp(s.p+next,s.p+end,delim))next+=delim;
    *pointer=(long long)next+1;
    return 1;
}
void cb_push(cb_frame *f,int *depth,int ret,int limit) {
    if(*depth>=CB_STACK)cb_fail("PERFORM_STACK","PERFORM stack capacity exceeded.");
    f[(*depth)++]=(cb_frame) {
        ret,limit
    };
}
void cb_loop_push(cb_loop *loops,int *depth,int id,int exit_pc,int perform_depth,long long remaining) {
    if(*depth>=CB_STACK)cb_fail("LOOP_STACK","Loop stack capacity exceeded.");
    loops[(*depth)++]=(cb_loop) {
        id,exit_pc,perform_depth,remaining
    };
}
