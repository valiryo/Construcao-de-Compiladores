#include "cobol_runtime.h"
#include <errno.h>
#include <string.h>
static int status(cb_file *f,const char *code,const char *error) {
    if(f->status.p) {
        if(f->status.n!=2)cb_fail("FILE_STATUS_LAYOUT","FILE STATUS requires exactly two bytes.");
        memcpy(f->status.p,code,2);
        return 1;
    }
    if(error)cb_fail(error,"Sequential file operation failed (FILE STATUS unavailable).");
    return 0;
}
int cb_open(cb_runtime *rt,cb_file *f,cb_value path,int mode,int line,cb_field record,cb_field state) {
    f->status=state;
    if(!f->registered) {
        f->next=rt->files;
        rt->files=f;
        f->registered=1;
    }
    if(f->fp) {
        status(f,"41","FILE_ALREADY_OPEN");
        return 1;
    }
    cb_slice s=cb_bytes(rt,path);
    size_t n=s.n;
    while(n&&s.p[n-1]==' ')--n;
    if(!n||memchr(s.p,0,n))cb_fail("FILE_PATH","Invalid file path.");
    char *name=cb_alloc(rt,n+1);
    memcpy(name,s.p,n);
    name[n]=0;
    f->fp=fopen(name,mode==1?"rb":mode==2?"wb":"r+b");
    f->mode=mode;
    f->line=line;
    f->record=record;
    if(!f->fp) {
        status(f,errno==ENOENT?"35":"30","FILE_OPEN");
        return 1;
    }
    if(mode==3 && fseek(f->fp,0,SEEK_END)) {
        fclose(f->fp);
        f->fp=NULL;
        status(f,"30","FILE_SEEK");
        return 1;
    }
    status(f,"00",NULL);
    return 0;
}
int cb_read(cb_file *f) {
    if(!f->fp||!(f->mode==1||f->mode==4)) {
        status(f,"47","FILE_READ_MODE");
        return 2;
    }
    size_t n=0;
    int c=EOF,too_long=0;
    unsigned char *p=f->record.p;
    if(f->line) {
        int pending=-1;
        while((c=fgetc(f->fp))!=EOF&&c!='\n') {
            if(pending>=0) {
                if(n<f->record.n)p[n++]=(unsigned char)pending;
                else too_long=1;
            }
            pending=c;
        }
        if(pending>=0 && !(pending=='\r'&&c=='\n')) {
            if(n<f->record.n)p[n++]=(unsigned char)pending;
            else too_long=1;
        }
    }
    else n=fread(p,1,f->record.n,f->fp);
    if(ferror(f->fp)) {
        status(f,"30","FILE_READ");
        return 2;
    }
    if(!n&&c==EOF&&feof(f->fp)) {
        status(f,"10",NULL);
        return 1;
    }
    if(n<f->record.n)memset(p+n,' ',f->record.n-n);
    if(too_long||(!f->line&&n!=f->record.n)) {
        status(f,"04","FILE_RECORD_LENGTH");
        return 2;
    }
    status(f,"00",NULL);
    return 0;
}
void cb_write(cb_file *f) {
    if(!f->fp||!(f->mode==2||f->mode==3||f->mode==4)) {
        status(f,"48","FILE_WRITE_MODE");
        return;
    }
    if(fwrite(f->record.p,1,f->record.n,f->fp)!=f->record.n||(f->line&&fputc('\n',f->fp)==EOF)||fflush(f->fp)) {
        status(f,"30","FILE_WRITE");
        return;
    }
    status(f,"00",NULL);
}
void cb_close(cb_file *f) {
    if(!f->fp) {
        status(f,"42","FILE_NOT_OPEN");
        return;
    }
    int failed=fclose(f->fp);
    f->fp=NULL;
    if(failed) {
        status(f,"30","FILE_CLOSE");
        return;
    }
    status(f,"00",NULL);
}
