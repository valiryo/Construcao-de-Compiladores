/* Resolution and marshalling at the boundary of the project and native ABIs. */
#define _POSIX_C_SOURCE 200809L
#include "cobol_runtime.h"
#include <dlfcn.h>
#include <errno.h>
#include <limits.h>
#include <stdlib.h>
#include <string.h>
#include <sys/stat.h>
#include <unistd.h>

typedef struct cb_library {
    struct cb_library *next;
    char *path;
    void *handle;
    int own;
    const cb_module *module;
} cb_library;

static cb_call_result error(const char *code) {
    return (cb_call_result){.error=code};
}

static cb_library *load(cb_runtime *rt, const char *path, int own) {
    for(cb_library *lib=rt->libraries;lib;lib=lib->next)
        if(lib->own==own&&!strcmp(lib->path,path))return lib;
    void *handle=dlopen(path,RTLD_NOW|RTLD_LOCAL);
    if(!handle)return NULL;
    cb_library *lib=calloc(1,sizeof *lib);
    if(!lib)cb_fail("OUT_OF_MEMORY","Cannot allocate library record.");
    lib->path=strdup(path);
    if(!lib->path)cb_fail("OUT_OF_MEMORY","Cannot allocate library path.");
    lib->handle=handle;
    lib->own=own;
    if(own) {
        const cb_module *module=dlsym(handle,"cobol_project_module_v1");
        if(module&&module->version==CB_MODULE_ABI&&module->runtime_size==sizeof(cb_runtime))
            lib->module=module;
    }
    lib->next=rt->libraries;
    rt->libraries=lib;
    return lib;
}

void cb_libraries_close(cb_runtime *rt) {
    while(rt->libraries) {
        cb_library *lib=rt->libraries;
        rt->libraries=lib->next;
        dlclose(lib->handle);
        free(lib->path);
        free(lib);
    }
}

static const cb_program *find(const cb_program *programs,size_t count,const char *name) {
    for(size_t i=0;i<count;++i)
        if(!strcmp(programs[i].name,name))return &programs[i];
    return NULL;
}

static int same_layout(const cb_formal *formal,const cb_call_arg *actual) {
    const cb_desc *expected=&formal->desc,*received=actual->field.desc;
    if(!received||actual->field.n!=formal->size||expected->category!=received->category)return 0;
    if(expected->category==2)return actual->shape&&formal->shape&&!strcmp(actual->shape,formal->shape);
    if(expected->category==3)return expected->decimal==received->decimal&&!strcmp(expected->pic,received->pic);
    return expected->digits==received->digits&&expected->scale==received->scale&&
        expected->signedness==received->signedness&&expected->usage==received->usage;
}

static cb_call_result invoke_cobol(cb_runtime *rt,const cb_program *p,cb_call_arg *args,size_t n,int wants_pointer) {
    if(wants_pointer)return error("CALL_RETURN_TYPE");
    if(p->count!=n)return error("CALL_ARITY");
    cb_field *fields=n?cb_alloc(rt,n*sizeof *fields):NULL;
    for(size_t i=0;i<n;++i) {
        const cb_formal *formal=&p->formals[i];
        cb_call_arg *actual=&args[i];
        if(formal->mode!=actual->mode&&!(formal->mode==CB_REFERENCE&&actual->mode==CB_CONTENT))
            return error("CALL_MODE_MISMATCH");
        if(formal->desc.category==1&&actual->number&&(actual->mode==CB_VALUE||actual->numeric_literal)) {
            fields[i]=(cb_field){cb_alloc(rt,formal->size),formal->size,&formal->desc};
            if(cb_store(fields[i],cb_as_num(*actual->number),0,1))return error("CALL_LAYOUT_MISMATCH");
            continue;
        }
        if(!same_layout(formal,actual))return error("CALL_LAYOUT_MISMATCH");
        fields[i]=actual->field;
    }
    int status=p->entry(rt,fields,n);
    return (cb_call_result){.status=status};
}

/* Search explicit directories only. A COBOL name never selects an arbitrary path. */
static cb_call_result search(cb_runtime *rt,const char *path,const char *name,cb_call_arg *args,size_t n,int pointer) {
    if(!path)return error("CALL_NOT_FOUND");
    while(*path) {
        size_t length=strcspn(path,":");
        if(length&&length<PATH_MAX) {
            char candidate[PATH_MAX];
            int size=snprintf(candidate,sizeof candidate,"%.*s/%s.so",(int)length,path,name);
            if(size<0||(size_t)size>=sizeof candidate)return error("CALL_MODULE_PATH");
            struct stat st;
            if(!stat(candidate,&st)) {
                if(!S_ISREG(st.st_mode))return error("CALL_MODULE_LOAD");
                cb_library *lib=load(rt,candidate,1);
                if(!lib)return error("CALL_MODULE_LOAD");
                if(!lib->module)return error("CALL_MODULE_ABI");
                const cb_program *p=find(lib->module->programs,lib->module->count,name);
                if(!p)return error("CALL_MODULE_ENTRY");
                return invoke_cobol(rt,p,args,n,pointer);
            }
            if(errno!=ENOENT&&errno!=ENOTDIR)return error("CALL_MODULE_LOAD");
        }
        path+=length;
        if(*path)++path;
    }
    return error("CALL_NOT_FOUND");
}

cb_call_result cb_call(cb_runtime *rt,cb_slice target,cb_call_arg *args,size_t n,int returning,
    const cb_program *local,size_t local_count,const cb_native *native,size_t native_count,const char *dirs,
    const char *const *libraries,size_t library_count) {
    char name[256], upper[256];
    while(target.n&&target.p[target.n-1]==' ')--target.n;
    if(!target.n||target.n>=sizeof name||memchr(target.p,0,target.n))return error("CALL_INVALID_NAME");
    for(size_t i=0;i<target.n;++i) {
        unsigned char c=target.p[i];
        name[i]=(char)c;
        upper[i]=(char)(c>='a'&&c<='z'?c-'a'+'A':c);
    }
    name[target.n]=upper[target.n]=0;
    int pointer=returning==CB_RESULT_POINTER;
    const cb_program *p=find(local,local_count,upper);
    if(!p)p=find(rt->linked_programs,rt->linked_count,upper);
    for(cb_library *lib=rt->libraries;!p&&lib;lib=lib->next)
        if(lib->module)p=find(lib->module->programs,lib->module->count,upper);
    if(p)return invoke_cobol(rt,p,args,n,pointer);
    for(size_t i=0;i<native_count;++i) {
        const cb_native *f=&native[i];
        if(strcmp(name,f->name))continue;
        if(returning>=0&&returning!=f->result_kind)return error("CALL_RETURN_TYPE");
        void *handle=RTLD_DEFAULT;
        if(f->library) {
            cb_library *lib=load(rt,f->library,0);
            if(!lib)return error("CALL_LIBRARY_LOAD");
            handle=lib->handle;
        }
        void *address=dlsym(handle,f->name);
        if(!address)return error("CALL_SYMBOL_NOT_FOUND");
        if(f->terminal==1&&n==0) {
            if(!isatty(STDIN_FILENO)||!isatty(STDOUT_FILENO))return error("CALL_NATIVE_TERMINAL");
            void *shutdown=dlsym(handle,"endwin");
            if(!shutdown)return error("CALL_SYMBOL_NOT_FOUND");
            _Static_assert(sizeof rt->terminal_shutdown==sizeof shutdown,"Unsupported POSIX symbol ABI");
            memcpy(&rt->terminal_shutdown,&shutdown,sizeof shutdown);
        }
        cb_call_result native_result=f->invoke(rt,address,args,n);
        native_result.kind=f->result_kind;
        if(f->terminal==2&&!native_result.error&&!native_result.status)rt->terminal_shutdown=NULL;
        return native_result;
    }
    for(size_t i=0;i<target.n;++i) {
        char c=upper[i];
        if(!((c>='A'&&c<='Z')||(c>='0'&&c<='9')||c=='-'||c=='_'))
            return error("CALL_NOT_FOUND");
    }
    cb_call_result result=search(rt,dirs,upper,args,n,pointer);
    if(result.error&&!strcmp(result.error,"CALL_NOT_FOUND")&&rt->module_dirs&&
       (!dirs||strcmp(dirs,rt->module_dirs)))
        result=search(rt,rt->module_dirs,upper,args,n,pointer);
    if(result.error&&!strcmp(result.error,"CALL_NOT_FOUND"))
        result=search(rt,getenv("COBOL_MODULE_PATH"),upper,args,n,pointer);
    if(result.error&&!strcmp(result.error,"CALL_NOT_FOUND")) {
        if(dlsym(RTLD_DEFAULT,name))return error("CALL_SIGNATURE_REQUIRED");
        for(size_t i=0;i<library_count;++i) {
            cb_library *lib=load(rt,libraries[i],0);
            if(!lib)return error("CALL_LIBRARY_LOAD");
            if(dlsym(lib->handle,name))return error("CALL_SIGNATURE_REQUIRED");
        }
    }
    return result;
}

_Noreturn void cb_call_fail(cb_runtime *rt,cb_slice name,const char *code) {
    char message[320];
    (void)rt;
    size_t length=name.n<255?name.n:255;
    while(length&&name.p[length-1]==' ')--length;
    snprintf(message,sizeof message,"CALL '%.*s': target unavailable or incompatible.",(int)length,name.p);
    cb_fail(code,message);
}

void cb_pointer_store(cb_field field,void *p) {
    if(field.n!=sizeof p||field.desc->category!=4)cb_fail("CALL_RETURN_TYPE","Expected USAGE POINTER field.");
    memcpy(field.p,&p,sizeof p);
}

void *cb_pointer_load(cb_field field) {
    void *p;
    if(field.n!=sizeof p||field.desc->category!=4)cb_fail("CALL_NATIVE_ARGUMENT","Expected USAGE POINTER field.");
    memcpy(&p,field.p,sizeof p);
    return p;
}

int cb_native_int(cb_call_arg *arg,int *out) {
    if(arg->mode!=CB_VALUE||!arg->number)return 0;
    cb_num number=cb_as_num(*arg->number);
    if(cb_num_cmp(number,cb_decimal("-2147483648"))<0||
       cb_num_cmp(number,cb_decimal("2147483647"))>0||
       cb_num_cmp(number,cb_integer_num(number,0)))return 0;
    *out=(int)cb_int(*arg->number);
    return 1;
}

const char *cb_native_string(cb_runtime *rt,cb_call_arg *arg) {
    if(arg->mode==CB_VALUE||!arg->field.desc||arg->field.desc->category!=0)return NULL;
    cb_field src=arg->field;
    char *copy=cb_alloc(rt,src.n+1);
    memcpy(copy,src.p,src.n);
    return copy;
}

/* Simple checked format subset. No writes via %n, positional directives or * widths. */
int cb_native_format(const char *p,const char *types,int scan) {
    for(;*p;++p) {
        if(*p!='%')continue;
        ++p;
        if(*p=='%')continue;
        if(!*p||!*types)return 0;
        if(scan) {
            if(*p!='d'||*types!='i')return 0;
        } else if(!((*p=='d'&&*types=='i')||(*p=='s'&&*types=='s')))return 0;
        ++types;
    }
    return !*types;
}
