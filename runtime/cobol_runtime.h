#ifndef COBOL_RUNTIME_H
#define COBOL_RUNTIME_H
#include <stddef.h>
#include <stdio.h>
#include <stdint.h>

/* Project ABI: decimal digits, never host floating point. Capacity is checked. */
#define CB_DIGITS 512
#define CB_STACK 4096
#define CB_FIELD_DIGITS 128

typedef struct { int len; unsigned char v[CB_DIGITS]; } cb_big;
typedef struct { int sign; cb_big n, d; } cb_num;
typedef struct { unsigned char *p; size_t n; } cb_slice;
/* category: text=0 numeric=1 group=2 edited=3; usage: display=0 binary=1 packed=2 */
typedef struct { int category, digits, scale, signedness, usage; char decimal; const char *pic; } cb_desc;
typedef struct { unsigned char *p; size_t n; const cb_desc *desc; } cb_field;
typedef struct { int kind; cb_field f; cb_num num; cb_slice text; int repeat; } cb_value;
typedef struct cb_mem { struct cb_mem *next; void *data; } cb_mem;
typedef struct cb_file { FILE *fp; int mode, line; cb_field record, status; struct cb_file *next; int registered; } cb_file;
typedef struct { int ret, limit; } cb_frame;
typedef struct { int id, exit_pc, depth; long long remaining; } cb_loop;
typedef struct { cb_field field, target; long long line, column; } cb_screen_field;
typedef struct cb_runtime {
    unsigned char return_code[4], sort_return[4];
    int stop, raw_terminal, call_depth; uint32_t random;
    const char *file; int line, column;
    cb_mem *memory; cb_file *files;
    int terminal_active; long long terminal_line, terminal_column;
    cb_field cursor_field, crt_status_field;
    int terminal_stream; long long text_line, text_column;
} cb_runtime;

extern const cb_desc cb_text_desc;
void cb_runtime_init(cb_runtime *rt);
void cb_runtime_destroy(cb_runtime *rt);
void cb_origin(cb_runtime *rt, const char *file, int line, int column);
_Noreturn void cb_fail(const char *code, const char *message);
void *cb_alloc(cb_runtime *rt, size_t n);
void cb_release(cb_runtime *rt, cb_mem *mark);
cb_slice cb_slice_literal(const char *s, size_t n);
cb_field cb_field_at(unsigned char *base, size_t capacity, size_t offset, size_t n, const cb_desc *desc);
cb_field cb_refmod(cb_field f, long long start, long long length);
long long cb_index(cb_value value, long long bound);
long long cb_bound(long long value, long long minimum, long long maximum);

cb_num cb_decimal(const char *s);
cb_num cb_add(cb_num a, cb_num b);
cb_num cb_sub(cb_num a, cb_num b);
cb_num cb_mul(cb_num a, cb_num b);
cb_num cb_div(cb_num a, cb_num b);
cb_num cb_power(cb_num a, cb_num b);
cb_num cb_negate(cb_num a);
int cb_num_cmp(cb_num a, cb_num b);
cb_num cb_integer_num(cb_num a, int floor_mode);
long long cb_int(cb_value value);
cb_num cb_load(cb_field f);
/* store returns size error and leaves receiver unchanged when checked. */
int cb_store(cb_field f, cb_num value, int rounded, int checked);
int cb_floating_sign(const cb_desc *desc);
int cb_is_numeric(cb_value value);
cb_value cb_field_value(cb_field f);
cb_value cb_number(const char *s);
cb_value cb_numeric_value(cb_num n);
cb_value cb_text(const char *s, size_t n, int repeat);
cb_value cb_fill(unsigned char byte);
cb_slice cb_bytes(cb_runtime *rt, cb_value value);
cb_num cb_as_num(cb_value value);
void cb_move(cb_runtime *rt, cb_value source, cb_field target);
int cb_compare(cb_runtime *rt, cb_value a, cb_value b);
int cb_class(cb_runtime *rt, cb_value v, const char *category);
void cb_display(cb_runtime *rt, cb_value v);
void cb_display_end(int no_advancing);
void cb_terminal_at(cb_runtime *rt, long long line, long long column);
void cb_terminal_clear(cb_runtime *rt);
void cb_terminal_stream_begin(cb_runtime *rt);
void cb_terminal_bind(cb_runtime *rt, cb_field cursor, cb_field status);
void cb_screen_accept(cb_runtime *rt, cb_screen_field *fields, size_t count);
void cb_math_begin(int handled);
int cb_math_failed(void);
int cb_math_error(const char *code, const char *message);
void cb_math_end(void);
void cb_accept(cb_runtime *rt, cb_field f, const char *source, const char *format);
cb_value cb_function(cb_runtime *rt, const char *name, cb_value *args, size_t count);
long long cb_inspect_count(cb_runtime *rt, cb_value subject, const char *mode, cb_value pattern);
void cb_inspect_replace(cb_runtime *rt, cb_field subject, const char *mode, cb_value pattern, cb_value replacement);
void cb_inspect_convert(cb_runtime *rt, cb_field subject, cb_value from, cb_value to);
int cb_string_part(cb_runtime *rt, cb_field target, long long *pointer, cb_value value, cb_value delimiter, int size);
long long cb_unstring_next(cb_runtime *rt, cb_value source, long long *pointer, cb_value *delimiters, int *alls, size_t count, cb_field target, cb_field delimiter_in, cb_field count_in);

int cb_open(cb_runtime *rt, cb_file *file, cb_value path, int mode, int line, cb_field record, cb_field status);
int cb_read(cb_file *file); /* 0 record, 1 EOF, 2 I/O error */
void cb_write(cb_file *file);
void cb_close(cb_file *file);
void cb_push(cb_frame *frames, int *depth, int ret, int limit);
void cb_loop_push(cb_loop *loops, int *depth, int id, int exit_pc, int perform_depth, long long remaining);
#endif
