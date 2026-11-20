"""Interface executável do compilador COBOL → C11 → GCC."""

from cobol_compiler.__main__ import main

if __name__=='__main__':
    raise SystemExit(main(compile_default=True))
