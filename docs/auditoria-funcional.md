# Auditoria funcional — Etapa 5

Gerado por `python -m tools.auditar_funcional --write`. Fontes originais preservados;
snapshot `1ffb3bf279bbb1e596b1091f1dda1cf7ddf51295`. GnuCOBOL é apenas oráculo independente.

## Métricas

- suite_tests: **476**.
- discovered_compiled_programs: **60**.
- previously_pending_programs: **49**.
- selected_programs: **60**.
- compiled_programs: **60**.
- executed_programs: **60**.
- validated_programs: **60**.
- additional_executed_programs: **53**.
- newly_validated_programs: **49**.
- executed_scenarios: **140**.
- validated_scenarios: **140**.
- identical_comparisons: **136**.
- divergences: **3**.
- expected_abi_differences: **3**.
- unexpected_divergences: **0**.
- without_fixtures: **0**.
- blocked_dependencies: **0**.
- dependency_blocks_outside_compiled_cohort: **6**.
- compiler_failures_fixed: **2**.
- official_programs_validated: **7**.
- official_scenarios: **25**.
- official_identical_comparisons: **24**.

A contagem direta das definições confirma **25 cenários oficiais**. Não há divergência com os 25 relatados.
Cada programa é recompilado em diretório independente com fontes/COPY copiados e hashes registrados.
C e artefato devem estar ausentes antes e ser criados pela compilação atual; GCC é invocado de novo.
Cada cenário começa em diretório vazio, com apenas suas fixtures. Persistência é preparada explicitamente,
sem herdar arquivos de outro cenário. As entradas e todos os bytes de stdout, stderr e arquivos
estão no JSON (base64, tamanho e SHA-256), junto aos comandos e evidências de construção.

## Sete oficiais

| Programa | Compilação | Execução | Cenários | GnuCOBOL | Resultado | Pendências |
|---|---|---|---:|---|---|---|
| [examples/oficiais/BUSCA01A.cbl](../examples/oficiais/BUSCA01A.cbl) (BUSCA01A, executable) | GCC OK | executado | 4 | 4 iguais / 0 ABI previstas / 0 inesperadas | validated |  |
| [examples/oficiais/CAD0002A.cbl](../examples/oficiais/CAD0002A.cbl) (CAD0002A, module) | GCC OK | executado | 2 | 2 iguais / 0 ABI previstas / 0 inesperadas | validated |  |
| [examples/oficiais/CAD0004A.cbl](../examples/oficiais/CAD0004A.cbl) (CAD0004A, executable) | GCC OK | executado | 2 | 2 iguais / 0 ABI previstas / 0 inesperadas | validated |  |
| [examples/corrigidos/CAD0005A.cbl](../examples/corrigidos/CAD0005A.cbl) (CAD0005A, executable) | GCC OK | executado | 7 | 7 iguais / 0 ABI previstas / 0 inesperadas | validated |  |
| [examples/oficiais/CAIXAREG.cbl](../examples/oficiais/CAIXAREG.cbl) (CAIXAREG, executable) | GCC OK | executado | 2 | 2 iguais / 0 ABI previstas / 0 inesperadas | validated |  |
| [examples/oficiais/CALCMD01.cbl](../examples/oficiais/CALCMD01.cbl) (CALCMD01, executable) | GCC OK | executado | 3 | 2 iguais / 0 ABI previstas / 0 inesperadas | validated |  |
| [examples/oficiais/PROG024A.cbl](../examples/oficiais/PROG024A.cbl) (PROG024A, executable) | GCC OK | executado | 5 | 5 iguais / 0 ABI previstas / 0 inesperadas | validated |  |
## Demais programas compilados

| Programa | Compilação | Execução | Cenários | GnuCOBOL | Resultado | Pendências |
|---|---|---|---:|---|---|---|
| [examples/complementares/GRAV001A.cbl](../examples/complementares/GRAV001A.cbl) (GRAV001A, module) | GCC OK | executado | 2 | 2 iguais / 0 ABI previstas / 0 inesperadas | validated |  |
| [examples/complementares/PROG008A.cbl](../examples/complementares/PROG008A.cbl) (LEARQDAT, executable) | GCC OK | executado | 2 | 2 iguais / 0 ABI previstas / 0 inesperadas | validated |  |
| [examples/complementares/LER0001A.cbl](../examples/complementares/LER0001A.cbl) (LER0001A, module) | GCC OK | executado | 2 | 2 iguais / 0 ABI previstas / 0 inesperadas | validated |  |
| [examples/complementares/LER0002A.cbl](../examples/complementares/LER0002A.cbl) (LER0002A, executable) | GCC OK | executado | 2 | 2 iguais / 0 ABI previstas / 0 inesperadas | validated |  |
| [examples/complementares/LOGIN01A.cbl](../examples/complementares/LOGIN01A.cbl) (LOGIN01A, executable) | GCC OK | executado | 3 | 3 iguais / 0 ABI previstas / 0 inesperadas | validated |  |
| [examples/complementares/meu_programa.cob](../examples/complementares/meu_programa.cob) (MEU-PROGRAMA, executable) | GCC OK | executado | 1 | 1 iguais / 0 ABI previstas / 0 inesperadas | validated |  |
| [examples/complementares/MINICALC.cbl](../examples/complementares/MINICALC.cbl) (MINICALC, executable) | GCC OK | executado | 3 | 3 iguais / 0 ABI previstas / 0 inesperadas | validated |  |
| [examples/complementares/PROG001A.cbl](../examples/complementares/PROG001A.cbl) (PROG001A, executable) | GCC OK | executado | 2 | 2 iguais / 0 ABI previstas / 0 inesperadas | validated |  |
| [examples/complementares/PROG003A.cbl](../examples/complementares/PROG003A.cbl) (PROG003A, executable) | GCC OK | executado | 1 | 1 iguais / 0 ABI previstas / 0 inesperadas | validated |  |
| [examples/complementares/PROG004A.cbl](../examples/complementares/PROG004A.cbl) (PROG004A, executable) | GCC OK | executado | 2 | 2 iguais / 0 ABI previstas / 0 inesperadas | validated |  |
| [examples/complementares/PROG005A.cbl](../examples/complementares/PROG005A.cbl) (PROG005A, executable) | GCC OK | executado | 2 | 1 iguais / 1 ABI previstas / 0 inesperadas | validated |  |
| [examples/complementares/PROG007A.cbl](../examples/complementares/PROG007A.cbl) (PROG007A, executable) | GCC OK | executado | 2 | 2 iguais / 0 ABI previstas / 0 inesperadas | validated |  |
| [examples/complementares/PROG009A.cbl](../examples/complementares/PROG009A.cbl) (PROG009A, executable) | GCC OK | executado | 2 | 2 iguais / 0 ABI previstas / 0 inesperadas | validated |  |
| [examples/complementares/PROG011A.cbl](../examples/complementares/PROG011A.cbl) (PROG011A, executable) | GCC OK | executado | 1 | 1 iguais / 0 ABI previstas / 0 inesperadas | validated |  |
| [examples/complementares/PROG012A.cbl](../examples/complementares/PROG012A.cbl) (PROG012A, executable) | GCC OK | executado | 1 | 1 iguais / 0 ABI previstas / 0 inesperadas | validated |  |
| [examples/complementares/PROG014A.cbl](../examples/complementares/PROG014A.cbl) (PROG014A, executable) | GCC OK | executado | 1 | 1 iguais / 0 ABI previstas / 0 inesperadas | validated |  |
| [examples/complementares/PROG015A.cbl](../examples/complementares/PROG015A.cbl) (PROG015A, executable) | GCC OK | executado | 1 | 1 iguais / 0 ABI previstas / 0 inesperadas | validated |  |
| [examples/complementares/PROG016A.cbl](../examples/complementares/PROG016A.cbl) (PROG016A, executable) | GCC OK | executado | 2 | 2 iguais / 0 ABI previstas / 0 inesperadas | validated |  |
| [examples/complementares/PROG017A.cbl](../examples/complementares/PROG017A.cbl) (PROG017A, executable) | GCC OK | executado | 3 | 3 iguais / 0 ABI previstas / 0 inesperadas | validated |  |
| [examples/complementares/PROG019A.cbl](../examples/complementares/PROG019A.cbl) (PROG019A, executable) | GCC OK | executado | 2 | 2 iguais / 0 ABI previstas / 0 inesperadas | validated |  |
| [examples/complementares/PROG020A.cbl](../examples/complementares/PROG020A.cbl) (PROG020A, executable) | GCC OK | executado | 2 | 2 iguais / 0 ABI previstas / 0 inesperadas | validated |  |
| [examples/complementares/PROG021A.cbl](../examples/complementares/PROG021A.cbl) (PROG021A, executable) | GCC OK | executado | 3 | 2 iguais / 1 ABI previstas / 0 inesperadas | validated |  |
| [examples/complementares/PROG022A.cbl](../examples/complementares/PROG022A.cbl) (PROG022A, executable) | GCC OK | executado | 2 | 2 iguais / 0 ABI previstas / 0 inesperadas | validated |  |
| [examples/complementares/PROG023A.cbl](../examples/complementares/PROG023A.cbl) (PROG023A, executable) | GCC OK | executado | 3 | 3 iguais / 0 ABI previstas / 0 inesperadas | validated |  |
| [examples/complementares/PROG023B.cbl](../examples/complementares/PROG023B.cbl) (PROG023B, executable) | GCC OK | executado | 3 | 3 iguais / 0 ABI previstas / 0 inesperadas | validated |  |
| [examples/complementares/PROG023D.cbl](../examples/complementares/PROG023D.cbl) (PROG023D, executable) | GCC OK | executado | 4 | 4 iguais / 0 ABI previstas / 0 inesperadas | validated |  |
| [examples/complementares/PROG023E.cbl](../examples/complementares/PROG023E.cbl) (PROG023E, executable) | GCC OK | executado | 5 | 5 iguais / 0 ABI previstas / 0 inesperadas | validated |  |
| [examples/complementares/PROG025A.cbl](../examples/complementares/PROG025A.cbl) (PROG025A, executable) | GCC OK | executado | 2 | 2 iguais / 0 ABI previstas / 0 inesperadas | validated |  |
| [examples/complementares/PROG027A.cbl](../examples/complementares/PROG027A.cbl) (PROG027A, executable) | GCC OK | executado | 2 | 2 iguais / 0 ABI previstas / 0 inesperadas | validated |  |
| [examples/complementares/PROG028A.cbl](../examples/complementares/PROG028A.cbl) (PROG028A, executable) | GCC OK | executado | 4 | 4 iguais / 0 ABI previstas / 0 inesperadas | validated |  |
| [examples/complementares/PROG029A.cbl](../examples/complementares/PROG029A.cbl) (PROG029A, executable) | GCC OK | executado | 2 | 2 iguais / 0 ABI previstas / 0 inesperadas | validated |  |
| [examples/complementares/PROG033A.cbl](../examples/complementares/PROG033A.cbl) (PROG033A, executable) | GCC OK | executado | 3 | 3 iguais / 0 ABI previstas / 0 inesperadas | validated |  |
| [examples/complementares/PROG034A.cbl](../examples/complementares/PROG034A.cbl) (PROG034A, executable) | GCC OK | executado | 2 | 2 iguais / 0 ABI previstas / 0 inesperadas | validated |  |
| [examples/complementares/PROG035A.cbl](../examples/complementares/PROG035A.cbl) (PROG035A, executable) | GCC OK | executado | 2 | 2 iguais / 0 ABI previstas / 0 inesperadas | validated |  |
| [examples/complementares/PROG036A.cbl](../examples/complementares/PROG036A.cbl) (PROG036A, executable) | GCC OK | executado | 3 | 3 iguais / 0 ABI previstas / 0 inesperadas | validated |  |
| [examples/complementares/PROG037A.cbl](../examples/complementares/PROG037A.cbl) (PROG037A, executable) | GCC OK | executado | 2 | 2 iguais / 0 ABI previstas / 0 inesperadas | validated |  |
| [examples/complementares/PROG038A.cbl](../examples/complementares/PROG038A.cbl) (PROG038A, executable) | GCC OK | executado | 2 | 2 iguais / 0 ABI previstas / 0 inesperadas | validated |  |
| [examples/complementares/PROG039A.cbl](../examples/complementares/PROG039A.cbl) (PROG039A, executable) | GCC OK | executado | 1 | 1 iguais / 0 ABI previstas / 0 inesperadas | validated |  |
| [examples/complementares/PROG040A.cbl](../examples/complementares/PROG040A.cbl) (PROG040A, executable) | GCC OK | executado | 2 | 2 iguais / 0 ABI previstas / 0 inesperadas | validated |  |
| [examples/complementares/PROG041A.cbl](../examples/complementares/PROG041A.cbl) (PROG041A, executable) | GCC OK | executado | 2 | 2 iguais / 0 ABI previstas / 0 inesperadas | validated |  |
| [examples/complementares/PROG042B.cbl](../examples/complementares/PROG042B.cbl) (PROG042B, module) | GCC OK | executado | 2 | 2 iguais / 0 ABI previstas / 0 inesperadas | validated |  |
| [examples/complementares/PROG043A.cbl](../examples/complementares/PROG043A.cbl) (PROG043A, executable) | GCC OK | executado | 2 | 2 iguais / 0 ABI previstas / 0 inesperadas | validated |  |
| [examples/complementares/PROG044A.cbl](../examples/complementares/PROG044A.cbl) (PROG044A, executable) | GCC OK | executado | 2 | 2 iguais / 0 ABI previstas / 0 inesperadas | validated |  |
| [examples/complementares/PROG045A.cbl](../examples/complementares/PROG045A.cbl) (PROG045A, executable) | GCC OK | executado | 2 | 2 iguais / 0 ABI previstas / 0 inesperadas | validated |  |
| [examples/dependencias/PROGDATA.cbl](../examples/dependencias/PROGDATA.cbl) (PROGDATA, module) | GCC OK | executado | 1 | 1 iguais / 0 ABI previstas / 0 inesperadas | validated |  |
| [examples/complementares/PROGTEST4.cbl](../examples/complementares/PROGTEST4.cbl) (PROGTEST4, executable) | GCC OK | executado | 1 | 0 iguais / 1 ABI previstas / 0 inesperadas | validated |  |
| [examples/complementares/PROGTIME.cbl](../examples/complementares/PROGTIME.cbl) (PROGTIME, module) | GCC OK | executado | 3 | 3 iguais / 0 ABI previstas / 0 inesperadas | validated |  |
| [examples/complementares/REL0001A.cbl](../examples/complementares/REL0001A.cbl) (REL0001A, module) | GCC OK | executado | 2 | 2 iguais / 0 ABI previstas / 0 inesperadas | validated |  |
| [examples/complementares/REL0002A.cbl](../examples/complementares/REL0002A.cbl) (REL0002A, executable) | GCC OK | executado | 2 | 2 iguais / 0 ABI previstas / 0 inesperadas | validated |  |
| [examples/complementares/SORT002A.cbl](../examples/complementares/SORT002A.cbl) (SORT002A, executable) | GCC OK | executado | 3 | 3 iguais / 0 ABI previstas / 0 inesperadas | validated |  |
| [examples/complementares/VALCNPJ.cbl](../examples/complementares/VALCNPJ.cbl) (VALCNPJ, executable) | GCC OK | executado | 2 | 2 iguais / 0 ABI previstas / 0 inesperadas | validated |  |
| [examples/complementares/VALCPF01.cbl](../examples/complementares/VALCPF01.cbl) (VALCPF01, executable) | GCC OK | executado | 2 | 2 iguais / 0 ABI previstas / 0 inesperadas | validated |  |
| [examples/complementares/VALIDA1A.cbl](../examples/complementares/VALIDA1A.cbl) (VALIDA1A, executable) | GCC OK | executado | 3 | 3 iguais / 0 ABI previstas / 0 inesperadas | validated |  |

## Cenários individuais

| Cenário | Programa | Retorno | Expectativa própria | Oráculo |
|---|---|---:|---|---|
| busca-first | BUSCA01A | 0 | OK | igual |
| busca-last | BUSCA01A | 0 | OK | igual |
| busca-absent | BUSCA01A | 0 | OK | igual |
| busca-empty | BUSCA01A | 0 | OK | igual |
| cad2-fim | CAD0002A | 0 | OK | igual |
| cad2-validation-and-shared-record | CAD0002A | 0 | OK | igual |
| cad4-one | CAD0004A | 0 | OK | igual |
| cad4-two | CAD0004A | 0 | OK | igual |
| agenda-empty | CAD0005A | 0 | OK | igual |
| agenda-add | CAD0005A | 0 | OK | igual |
| agenda-reopen-add | CAD0005A | 0 | OK | igual |
| agenda-list | CAD0005A | 0 | OK | igual |
| agenda-duplicate | CAD0005A | 0 | OK | igual |
| agenda-fim | CAD0005A | 0 | OK | igual |
| agenda-invalid-option | CAD0005A | 0 | OK | igual |
| caixa-no-discount | CAIXAREG | 0 | OK | igual |
| caixa-retries-and-discount | CAIXAREG | 0 | OK | igual |
| calcmd-basic | CALCMD01 | 0 | OK | igual |
| calcmd-retry-and-fraction | CALCMD01 | 0 | OK | igual |
| calcmd-zero-divisor | CALCMD01 | 1 | OK | não comparado |
| grav001a-empty | GRAV001A | 0 | OK | igual |
| grav001a-two | GRAV001A | 0 | OK | igual |
| learqdat-records | LEARQDAT | 0 | OK | igual |
| learqdat-empty | LEARQDAT | 0 | OK | igual |
| ler0001a-empty | LER0001A | 0 | OK | igual |
| ler0001a-two | LER0001A | 0 | OK | igual |
| ler0002a-records | LER0002A | 0 | OK | igual |
| ler0002a-empty | LER0002A | 0 | OK | igual |
| login01a-valid | LOGIN01A | 0 | OK | igual |
| login01a-invalid | LOGIN01A | 0 | OK | igual |
| login01a-missing | LOGIN01A | 0 | OK | igual |
| meu-programa-message | MEU-PROGRAMA | 0 | OK | igual |
| minicalc-addition | MINICALC | 0 | OK | igual |
| minicalc-negative-division | MINICALC | 0 | OK | igual |
| minicalc-zero | MINICALC | 0 | OK | igual |
| prog001a-clock | PROG001A | 0 | OK | igual |
| prog001a-leap-clock | PROG001A | 0 | OK | igual |
| prog003a-arithmetic | PROG003A | 0 | OK | igual |
| prog004a-register | PROG004A | 0 | OK | igual |
| prog004a-empty | PROG004A | 0 | OK | igual |
| prog005a-record | PROG005A | 0 | OK | igual |
| prog005a-empty | PROG005A | 0 | OK | ABI prevista |
| prog007a-normal | PROG007A | 0 | OK | igual |
| prog007a-limit | PROG007A | 0 | OK | igual |
| prog009a-one | PROG009A | 0 | OK | igual |
| prog009a-two | PROG009A | 0 | OK | igual |
| prog011a-initialize | PROG011A | 0 | OK | igual |
| extra-refmod-count | PROG012A | 0 | OK | igual |
| prog014a-reverse-tally | PROG014A | 0 | OK | igual |
| prog015a-inspect | PROG015A | 0 | OK | igual |
| prog016a-clock | PROG016A | 0 | OK | igual |
| prog016a-afternoon | PROG016A | 0 | OK | igual |
| prog017a-approved | PROG017A | 0 | OK | igual |
| prog017a-cancelled | PROG017A | 0 | OK | igual |
| prog017a-invalid | PROG017A | 0 | OK | igual |
| prog019a-found | PROG019A | 0 | OK | igual |
| prog019a-absent | PROG019A | 0 | OK | igual |
| extra-search-found | PROG020A | 0 | OK | igual |
| extra-search-absent | PROG020A | 0 | OK | igual |
| prog021a-valid | PROG021A | 0 | OK | igual |
| prog021a-invalid | PROG021A | 0 | OK | ABI prevista |
| prog021a-missing | PROG021A | 0 | OK | igual |
| prog022a-normal | PROG022A | 0 | OK | igual |
| prog022a-retry | PROG022A | 0 | OK | igual |
| prog023a-empty | PROG023A | 0 | OK | igual |
| prog023a-list-existing | PROG023A | 0 | OK | igual |
| prog023a-add-and-move | PROG023A | 0 | OK | igual |
| prog023b-empty | PROG023B | 0 | OK | igual |
| prog023b-list-existing | PROG023B | 0 | OK | igual |
| prog023b-delete | PROG023B | 0 | OK | igual |
| prog023d-empty | PROG023D | 0 | OK | igual |
| prog023d-list-existing | PROG023D | 0 | OK | igual |
| prog023d-register-log | PROG023D | 0 | OK | igual |
| prog023d-deactivate-log | PROG023D | 0 | OK | igual |
| prog023e-empty | PROG023E | 0 | OK | igual |
| prog023e-list-existing | PROG023E | 0 | OK | igual |
| prog023e-register-log | PROG023E | 0 | OK | igual |
| prog023e-minimum-stock | PROG023E | 0 | OK | igual |
| prog023e-below-minimum | PROG023E | 0 | OK | igual |
| biblioteca-empty | PROG024A | 0 | OK | igual |
| biblioteca-add-loan-return-query | PROG024A | 0 | OK | igual |
| biblioteca-reopen-list | PROG024A | 0 | OK | igual |
| biblioteca-absent | PROG024A | 0 | OK | igual |
| biblioteca-loan-unavailable | PROG024A | 0 | OK | igual |
| prog025a-on-time | PROG025A | 0 | OK | igual |
| prog025a-late | PROG025A | 0 | OK | igual |
| prog027a-empty | PROG027A | 0 | OK | igual |
| prog027a-tax | PROG027A | 0 | OK | igual |
| prog028a-entry | PROG028A | 0 | OK | igual |
| prog028a-reject-first-exit | PROG028A | 0 | OK | igual |
| prog028a-exit-after-entry | PROG028A | 0 | OK | igual |
| prog028a-reject-duplicate | PROG028A | 0 | OK | igual |
| prog029a-convert | PROG029A | 0 | OK | igual |
| prog029a-zero | PROG029A | 0 | OK | igual |
| prog033a-exit | PROG033A | 0 | OK | igual |
| prog033a-list-empty | PROG033A | 0 | OK | igual |
| prog033a-register | PROG033A | 0 | OK | igual |
| prog034a-append | PROG034A | 0 | OK | igual |
| prog034a-empty-input | PROG034A | 0 | OK | igual |
| prog035a-records | PROG035A | 0 | OK | igual |
| prog035a-empty | PROG035A | 0 | OK | igual |
| prog036a-sort-1 | PROG036A | 0 | OK | igual |
| prog036a-sort-2 | PROG036A | 0 | OK | igual |
| prog036a-sort-3 | PROG036A | 0 | OK | igual |
| prog037a-change | PROG037A | 0 | OK | igual |
| prog037a-preserve | PROG037A | 0 | OK | igual |
| prog038a-found | PROG038A | 0 | OK | igual |
| prog038a-absent | PROG038A | 0 | OK | igual |
| extra-sequential-delete | PROG039A | 0 | OK | igual |
| prog040a-append | PROG040A | 0 | OK | igual |
| prog040a-retry | PROG040A | 0 | OK | igual |
| prog041a-records | PROG041A | 0 | OK | igual |
| prog041a-empty | PROG041A | 0 | OK | igual |
| prog042b-empty | PROG042B | 0 | OK | igual |
| prog042b-next | PROG042B | 0 | OK | igual |
| prog043a-found | PROG043A | 0 | OK | igual |
| prog043a-absent | PROG043A | 0 | OK | igual |
| prog044a-records | PROG044A | 0 | OK | igual |
| prog044a-empty | PROG044A | 0 | OK | igual |
| prog045a-found | PROG045A | 0 | OK | igual |
| prog045a-absent | PROG045A | 0 | OK | igual |
| progdata-clock | PROGDATA | 0 | OK | igual |
| progtest4-search | PROGTEST4 | 0 | OK | ABI prevista |
| progtime-noon | PROGTIME | 0 | OK | igual |
| progtime-afternoon | PROGTIME | 0 | OK | igual |
| progtime-night-source-condition | PROGTIME | 0 | OK | igual |
| rel0001a-empty | REL0001A | 0 | OK | igual |
| rel0001a-pagination | REL0001A | 0 | OK | igual |
| rel0002a-empty | REL0002A | 0 | OK | igual |
| rel0002a-total | REL0002A | 0 | OK | igual |
| sort002a-sort-N | SORT002A | 0 | OK | igual |
| sort002a-sort-I | SORT002A | 0 | OK | igual |
| sort002a-sort-S | SORT002A | 0 | OK | igual |
| valcnpj-digits | VALCNPJ | 0 | OK | igual |
| valcnpj-exit | VALCNPJ | 0 | OK | igual |
| valcpf01-formatted | VALCPF01 | 0 | OK | igual |
| valcpf01-bad-format | VALCPF01 | 0 | OK | igual |
| valida1a-cpf | VALIDA1A | 0 | OK | igual |
| valida1a-cnpj | VALIDA1A | 0 | OK | igual |
| valida1a-bad-branch | VALIDA1A | 0 | OK | igual |

## Inventário de execução

### BUSCA01A

- Classe: `executable_with_fixtures`; parâmetros: `[]`.
- COPY: nenhum; fontes CALL: nenhuma.
- ACCEPT: `[{"target": "WRK-CPF-PROCURADO", "source": null, "line": 51, "picture": "9(11)", "bytes": 11}]`; relógio: não utilizado.
- Arquivos: `[{"select": "ARQUIVO-ENTRADA", "path": "CADASTRO2.dat", "organization": "LINE SEQUENTIAL", "record_lengths": [43], "open_modes": ["INPUT"]}]`.
- Construções: Accept, Arithmetic:ADD, Close, Display, Exit, If, Move, Open, Perform, Read, StopRun.
- Riscos: ACCEPT exige stdin completo; EOF pode manter menus/repetições ativos. Repetições/desvios exigem entradas de término; timeout e limite de CPU são obrigatórios. OPEN pode criar/truncar/gravar arquivos; executar somente com caminhos relativos e fixtures isoladas.
- Execução: stdin finito, fixtures declaradas, relógio fixo, CPU 5s, timeout 8s e arquivos até 16 MiB; sem chamadas de rede no runtime.

### CAD0002A

- Classe: `module_needs_caller`; parâmetros: `[{"name": "COPY002A-REGISTRO", "bytes": 10552}]`.
- COPY: examples/dependencias/COPY002A.cpy; fontes CALL: nenhuma.
- ACCEPT: `[{"target": "WRK-TELEFONE", "source": null, "line": 149, "picture": "9(09)", "bytes": 9}, {"target": "WRK-RUA", "source": null, "line": 152, "picture": "X(50)", "bytes": 50}, {"target": "WRK-CIDADE", "source": null, "line": 155, "picture": "X(30)", "bytes": 30}, {"target": "WRK-ESTADO", "source": null, "line": 158, "picture": "X(02)", "bytes": 2}, {"target": "WRK-CEP", "source": null, "line": 161, "picture": "9(08)", "bytes": 8}, {"target": "WRK-NOME", "source": null, "line": 208, "picture": "X(30)", "bytes": 30}, {"target": "WRK-IDADE", "source": null, "line": 235, "picture": "9(02)", "bytes": 2}, {"target": "WRK-DATA-NASC-AUX", "source": null, "line": 259, "picture": null, "bytes": 10}, {"target": "WRK-CARGO", "source": null, "line": 334, "picture": "X(20)", "bytes": 20}, {"target": "WRK-EMAIL", "source": null, "line": 360, "picture": "X(50)", "bytes": 50}]`; relógio: não utilizado.
- Arquivos: `[]`.
- Construções: Accept, Arithmetic:ADD, Arithmetic:SUBTRACT, Display, Evaluate, Exit, GoTo, Goback, If, Initialize, Inspect, Move, Perform.
- Riscos: ACCEPT exige stdin completo; EOF pode manter menus/repetições ativos. Repetições/desvios exigem entradas de término; timeout e limite de CPU são obrigatórios. LINKAGE pertence ao chamador; requer harness real e conferência dos parâmetros após retorno.
- Execução: stdin finito, fixtures declaradas, relógio fixo, CPU 5s, timeout 8s e arquivos até 16 MiB; sem chamadas de rede no runtime.

### CAD0004A

- Classe: `executable_with_fixtures`; parâmetros: `[]`.
- COPY: nenhum; fontes CALL: nenhuma.
- ACCEPT: `[{"target": "WRK-NOME", "source": null, "line": 46, "picture": "X(30)", "bytes": 30}, {"target": "WRK-IDADE", "source": null, "line": 49, "picture": "9(03)", "bytes": 3}, {"target": "WRK-CPF", "source": null, "line": 52, "picture": "X(14)", "bytes": 14}, {"target": "WRK-CONTINUAR", "source": null, "line": 62, "picture": "X(1)", "bytes": 1}]`; relógio: não utilizado.
- Arquivos: `[{"select": "ARQUIVO-CADASTRO", "path": "CADASTRO.dat", "organization": "LINE SEQUENTIAL", "record_lengths": [47], "open_modes": ["OUTPUT"]}]`.
- Construções: Accept, Close, Display, Move, Open, Perform, StopRun, Write.
- Riscos: ACCEPT exige stdin completo; EOF pode manter menus/repetições ativos. Repetições/desvios exigem entradas de término; timeout e limite de CPU são obrigatórios. OPEN pode criar/truncar/gravar arquivos; executar somente com caminhos relativos e fixtures isoladas.
- Execução: stdin finito, fixtures declaradas, relógio fixo, CPU 5s, timeout 8s e arquivos até 16 MiB; sem chamadas de rede no runtime.

### CAD0005A

- Classe: `executable_with_fixtures`; parâmetros: `[]`.
- COPY: nenhum; fontes CALL: nenhuma.
- ACCEPT: `[{"target": "WRK-OPCAO", "source": null, "line": 90, "picture": "9(01)", "bytes": 1}, {"target": "WRK-REG-NOME", "source": null, "line": 117, "picture": "X(30)", "bytes": 30}, {"target": "WRK-REG-TELEFONE", "source": null, "line": 123, "picture": "X(15)", "bytes": 15}]`; relógio: não utilizado.
- Arquivos: `[{"select": "ARQUIVO-ENT", "path": "CADAGENDA.dat", "organization": "LINE SEQUENTIAL", "record_lengths": [45], "open_modes": ["INPUT", "OUTPUT", "INPUT"]}]`.
- Construções: Accept, Arithmetic:ADD, Close, Continue, Display, Evaluate, Exit, If, Move, Open, Perform, Read, StopRun, Write.
- Riscos: ACCEPT exige stdin completo; EOF pode manter menus/repetições ativos. Repetições/desvios exigem entradas de término; timeout e limite de CPU são obrigatórios. OPEN pode criar/truncar/gravar arquivos; executar somente com caminhos relativos e fixtures isoladas.
- Execução: stdin finito, fixtures declaradas, relógio fixo, CPU 5s, timeout 8s e arquivos até 16 MiB; sem chamadas de rede no runtime.

### CAIXAREG

- Classe: `standalone`; parâmetros: `[]`.
- COPY: nenhum; fontes CALL: nenhuma.
- ACCEPT: `[{"target": "WRK-VALOR-ITEM1", "source": null, "line": 77, "picture": "9(05)V99", "bytes": 7}, {"target": "WRK-VALOR-ITEM2", "source": null, "line": 100, "picture": "9(05)V99", "bytes": 7}, {"target": "WRK-VALOR-ITEM3", "source": null, "line": 122, "picture": "9(05)V99", "bytes": 7}, {"target": "WRK-VALIDA-DESC", "source": null, "line": 162, "picture": "X(01)", "bytes": 1}, {"target": "WRK-DESCONTO", "source": null, "line": 186, "picture": "9(05)V99", "bytes": 7}]`; relógio: não utilizado.
- Arquivos: `[]`.
- Construções: Accept, Arithmetic:ADD, Arithmetic:COMPUTE, Display, Exit, If, Move, Perform, StopRun.
- Riscos: ACCEPT exige stdin completo; EOF pode manter menus/repetições ativos. Repetições/desvios exigem entradas de término; timeout e limite de CPU são obrigatórios.
- Execução: stdin finito, fixtures declaradas, relógio fixo, CPU 5s, timeout 8s e arquivos até 16 MiB; sem chamadas de rede no runtime.

### CALCMD01

- Classe: `standalone`; parâmetros: `[]`.
- COPY: nenhum; fontes CALL: nenhuma.
- ACCEPT: `[{"target": "WRK-VALOR01", "source": null, "line": 58, "picture": "9(06)V99", "bytes": 8}, {"target": "WRK-VALOR02", "source": null, "line": 79, "picture": "9(06)V99", "bytes": 8}, {"target": "WRK-VALOR03", "source": null, "line": 100, "picture": "9(06)V99", "bytes": 8}, {"target": "WRK-DIVISOR", "source": null, "line": 125, "picture": "9(02)", "bytes": 2}]`; relógio: não utilizado.
- Arquivos: `[]`.
- Construções: Accept, Arithmetic:COMPUTE, Display, Exit, If, Move, Perform, StopRun.
- Riscos: ACCEPT exige stdin completo; EOF pode manter menus/repetições ativos. Repetições/desvios exigem entradas de término; timeout e limite de CPU são obrigatórios.
- Execução: stdin finito, fixtures declaradas, relógio fixo, CPU 5s, timeout 8s e arquivos até 16 MiB; sem chamadas de rede no runtime.

### GRAV001A

- Classe: `module_needs_caller`; parâmetros: `[{"name": "COPY002A-REGISTRO", "bytes": 10552}]`.
- COPY: examples/dependencias/COPY002A.cpy; fontes CALL: nenhuma.
- ACCEPT: `[]`; relógio: não utilizado.
- Arquivos: `[{"select": "ARQUIVO-OUT", "path": "SEQSAI02.dat", "organization": "LINE SEQUENTIAL", "record_lengths": [211], "open_modes": ["OUTPUT"]}]`.
- Construções: Close, Display, Exit, Goback, Move, Open, Perform, Write.
- Riscos: Repetições/desvios exigem entradas de término; timeout e limite de CPU são obrigatórios. OPEN pode criar/truncar/gravar arquivos; executar somente com caminhos relativos e fixtures isoladas. LINKAGE pertence ao chamador; requer harness real e conferência dos parâmetros após retorno.
- Execução: stdin finito, fixtures declaradas, relógio fixo, CPU 5s, timeout 8s e arquivos até 16 MiB; sem chamadas de rede no runtime.

### LEARQDAT

- Classe: `executable_with_fixtures`; parâmetros: `[]`.
- COPY: nenhum; fontes CALL: nenhuma.
- ACCEPT: `[]`; relógio: não utilizado.
- Arquivos: `[{"select": "ARQUIVO-ENTRADA", "path": "SEQENT01.dat", "organization": "LINE SEQUENTIAL", "record_lengths": [27], "open_modes": ["INPUT"]}]`.
- Construções: Close, Display, If, Move, Open, Perform, Read, StopRun.
- Riscos: Repetições/desvios exigem entradas de término; timeout e limite de CPU são obrigatórios. OPEN pode criar/truncar/gravar arquivos; executar somente com caminhos relativos e fixtures isoladas.
- Execução: stdin finito, fixtures declaradas, relógio fixo, CPU 5s, timeout 8s e arquivos até 16 MiB; sem chamadas de rede no runtime.

### LER0001A

- Classe: `module_needs_caller`; parâmetros: `[{"name": "COPY002A-REGISTRO", "bytes": 10552}]`.
- COPY: examples/dependencias/COPY002A.cpy; fontes CALL: nenhuma.
- ACCEPT: `[]`; relógio: não utilizado.
- Arquivos: `[{"select": "ARQUIVO-ENTRADA", "path": "SEQENT01.dat", "organization": "LINE SEQUENTIAL", "record_lengths": [211], "open_modes": ["INPUT"]}]`.
- Construções: Arithmetic:ADD, Close, Display, Exit, Goback, If, Move, Open, Perform, Read.
- Riscos: Repetições/desvios exigem entradas de término; timeout e limite de CPU são obrigatórios. OPEN pode criar/truncar/gravar arquivos; executar somente com caminhos relativos e fixtures isoladas. LINKAGE pertence ao chamador; requer harness real e conferência dos parâmetros após retorno.
- Execução: stdin finito, fixtures declaradas, relógio fixo, CPU 5s, timeout 8s e arquivos até 16 MiB; sem chamadas de rede no runtime.

### LER0002A

- Classe: `executable_with_fixtures`; parâmetros: `[]`.
- COPY: nenhum; fontes CALL: nenhuma.
- ACCEPT: `[]`; relógio: não utilizado.
- Arquivos: `[{"select": "ARQUIVO-ENTRADA", "path": "CADASTRO2.dat", "organization": "LINE SEQUENTIAL", "record_lengths": [43], "open_modes": ["INPUT"]}]`.
- Construções: Close, Display, Move, Open, Perform, Read, StopRun.
- Riscos: Repetições/desvios exigem entradas de término; timeout e limite de CPU são obrigatórios. OPEN pode criar/truncar/gravar arquivos; executar somente com caminhos relativos e fixtures isoladas.
- Execução: stdin finito, fixtures declaradas, relógio fixo, CPU 5s, timeout 8s e arquivos até 16 MiB; sem chamadas de rede no runtime.

### LOGIN01A

- Classe: `executable_with_fixtures`; parâmetros: `[]`.
- COPY: nenhum; fontes CALL: nenhuma.
- ACCEPT: `[{"target": "USER-INFORMADO", "source": null, "line": 95, "picture": "X(20)", "bytes": 20}, {"target": "SENHA-INFORMADA", "source": null, "line": 97, "picture": "X(10)", "bytes": 10}]`; relógio: não utilizado.
- Arquivos: `[{"select": "ARQ-USUARIOS", "path": "USUARIO.dat", "organization": "LINE SEQUENTIAL", "record_lengths": [30], "open_modes": ["INPUT"]}]`.
- Construções: Accept, Arithmetic:ADD, Close, Display, Exit, If, Move, Open, Perform, Read, StopRun.
- Riscos: ACCEPT exige stdin completo; EOF pode manter menus/repetições ativos. Repetições/desvios exigem entradas de término; timeout e limite de CPU são obrigatórios. OPEN pode criar/truncar/gravar arquivos; executar somente com caminhos relativos e fixtures isoladas.
- Execução: stdin finito, fixtures declaradas, relógio fixo, CPU 5s, timeout 8s e arquivos até 16 MiB; sem chamadas de rede no runtime.

### MEU-PROGRAMA

- Classe: `standalone`; parâmetros: `[]`.
- COPY: nenhum; fontes CALL: nenhuma.
- ACCEPT: `[]`; relógio: não utilizado.
- Arquivos: `[]`.
- Construções: Display, StopRun.
- Riscos: Sem entrada interativa ou recurso externo; limites de execução mantidos.
- Execução: stdin finito, fixtures declaradas, relógio fixo, CPU 5s, timeout 8s e arquivos até 16 MiB; sem chamadas de rede no runtime.

### MINICALC

- Classe: `standalone`; parâmetros: `[]`.
- COPY: nenhum; fontes CALL: nenhuma.
- ACCEPT: `[{"target": "WRK-RAW1", "source": null, "line": 60, "picture": "X(30)", "bytes": 30}, {"target": "WRK-OPERACAO", "source": null, "line": 67, "picture": "X(01)", "bytes": 1}, {"target": "WRK-RAW2", "source": null, "line": 80, "picture": "X(30)", "bytes": 30}, {"target": "WRK-KEEP", "source": null, "line": 188, "picture": "X(01)", "bytes": 1}]`; relógio: não utilizado.
- Arquivos: `[]`.
- Construções: Accept, Arithmetic:COMPUTE, Continue, Display, Evaluate, Exit, If, Inspect, Move, Perform, StopRun.
- Riscos: ACCEPT exige stdin completo; EOF pode manter menus/repetições ativos. Repetições/desvios exigem entradas de término; timeout e limite de CPU são obrigatórios.
- Execução: stdin finito, fixtures declaradas, relógio fixo, CPU 5s, timeout 8s e arquivos até 16 MiB; sem chamadas de rede no runtime.

### PROG001A

- Classe: `standalone`; parâmetros: `[]`.
- COPY: nenhum; fontes CALL: nenhuma.
- ACCEPT: `[{"target": "WRK-DATA", "source": "DATE", "line": 54, "picture": "X(08)", "bytes": 8}, {"target": "WRK-TIME", "source": "TIME", "line": 56, "picture": "X(12)", "bytes": 12}]`; relógio: controlado.
- Arquivos: `[]`.
- Construções: Accept, Display, Move, Perform, StopRun.
- Riscos: Repetições/desvios exigem entradas de término; timeout e limite de CPU são obrigatórios.
- Execução: stdin finito, fixtures declaradas, relógio fixo, CPU 5s, timeout 8s e arquivos até 16 MiB; sem chamadas de rede no runtime.

### PROG003A

- Classe: `standalone`; parâmetros: `[]`.
- COPY: nenhum; fontes CALL: nenhuma.
- ACCEPT: `[]`; relógio: não utilizado.
- Arquivos: `[]`.
- Construções: Arithmetic:ADD, Arithmetic:COMPUTE, Arithmetic:DIVIDE, Arithmetic:MULTIPLY, Arithmetic:SUBTRACT, Display, Move, StopRun.
- Riscos: Sem entrada interativa ou recurso externo; limites de execução mantidos.
- Execução: stdin finito, fixtures declaradas, relógio fixo, CPU 5s, timeout 8s e arquivos até 16 MiB; sem chamadas de rede no runtime.

### PROG004A

- Classe: `standalone`; parâmetros: `[]`.
- COPY: nenhum; fontes CALL: nenhuma.
- ACCEPT: `[{"target": "TEMP-NOME", "source": null, "line": 32, "picture": "X(30)", "bytes": 30}, {"target": "TEMP-IDADE", "source": null, "line": 39, "picture": "9(02)", "bytes": 2}, {"target": "TEMP-CARGO", "source": null, "line": 42, "picture": "X(20)", "bytes": 20}]`; relógio: não utilizado.
- Arquivos: `[]`.
- Construções: Accept, Arithmetic:ADD, Display, Exit, If, Move, Perform, StopRun.
- Riscos: ACCEPT exige stdin completo; EOF pode manter menus/repetições ativos. Repetições/desvios exigem entradas de término; timeout e limite de CPU são obrigatórios.
- Execução: stdin finito, fixtures declaradas, relógio fixo, CPU 5s, timeout 8s e arquivos até 16 MiB; sem chamadas de rede no runtime.

### PROG005A

- Classe: `executable_with_fixtures`; parâmetros: `[]`.
- COPY: nenhum; fontes CALL: nenhuma.
- ACCEPT: `[]`; relógio: não utilizado.
- Arquivos: `[{"select": "ARQUIVO-ENTRADA", "path": "SEQENT02.dat", "organization": "LINE SEQUENTIAL", "record_lengths": [59], "open_modes": ["INPUT"]}]`.
- Construções: Close, Display, Exit, If, Initialize, Move, Open, Perform, Read, StopRun.
- Riscos: Repetições/desvios exigem entradas de término; timeout e limite de CPU são obrigatórios. OPEN pode criar/truncar/gravar arquivos; executar somente com caminhos relativos e fixtures isoladas.
- Execução: stdin finito, fixtures declaradas, relógio fixo, CPU 5s, timeout 8s e arquivos até 16 MiB; sem chamadas de rede no runtime.

### PROG007A

- Classe: `standalone`; parâmetros: `[]`.
- COPY: nenhum; fontes CALL: nenhuma.
- ACCEPT: `[{"target": "WS-NOME", "source": null, "line": 14, "picture": "X(20)", "bytes": 20}, {"target": "WS-IDADE", "source": null, "line": 16, "picture": "99", "bytes": 2}]`; relógio: não utilizado.
- Arquivos: `[]`.
- Construções: Accept, Display, StopRun.
- Riscos: ACCEPT exige stdin completo; EOF pode manter menus/repetições ativos.
- Execução: stdin finito, fixtures declaradas, relógio fixo, CPU 5s, timeout 8s e arquivos até 16 MiB; sem chamadas de rede no runtime.

### PROG009A

- Classe: `executable_with_fixtures`; parâmetros: `[]`.
- COPY: nenhum; fontes CALL: nenhuma.
- ACCEPT: `[{"target": "COD", "source": null, "line": 40, "picture": "9(02)", "bytes": 2}, {"target": "NOME", "source": null, "line": 42, "picture": "X(20)", "bytes": 20}, {"target": "IDADE", "source": null, "line": 44, "picture": "9(02)", "bytes": 2}, {"target": "OPCAO", "source": null, "line": 49, "picture": "X", "bytes": 1}]`; relógio: não utilizado.
- Arquivos: `[{"select": "ARQUIVO-OUT", "path": "SEQSAI01.dat", "organization": "LINE SEQUENTIAL", "record_lengths": [24], "open_modes": ["OUTPUT"]}]`.
- Construções: Accept, Close, Display, Exit, Open, Perform, StopRun, Write.
- Riscos: ACCEPT exige stdin completo; EOF pode manter menus/repetições ativos. Repetições/desvios exigem entradas de término; timeout e limite de CPU são obrigatórios. OPEN pode criar/truncar/gravar arquivos; executar somente com caminhos relativos e fixtures isoladas.
- Execução: stdin finito, fixtures declaradas, relógio fixo, CPU 5s, timeout 8s e arquivos até 16 MiB; sem chamadas de rede no runtime.

### PROG011A

- Classe: `standalone`; parâmetros: `[]`.
- COPY: nenhum; fontes CALL: nenhuma.
- ACCEPT: `[]`; relógio: não utilizado.
- Arquivos: `[]`.
- Construções: Display, Initialize, StopRun.
- Riscos: Sem entrada interativa ou recurso externo; limites de execução mantidos.
- Execução: stdin finito, fixtures declaradas, relógio fixo, CPU 5s, timeout 8s e arquivos até 16 MiB; sem chamadas de rede no runtime.

### PROG012A

- Classe: `standalone`; parâmetros: `[]`.
- COPY: nenhum; fontes CALL: nenhuma.
- ACCEPT: `[]`; relógio: não utilizado.
- Arquivos: `[]`.
- Construções: Arithmetic:ADD, Display, If, Move, Perform, StopRun.
- Riscos: Repetições/desvios exigem entradas de término; timeout e limite de CPU são obrigatórios.
- Execução: stdin finito, fixtures declaradas, relógio fixo, CPU 5s, timeout 8s e arquivos até 16 MiB; sem chamadas de rede no runtime.

### PROG014A

- Classe: `standalone`; parâmetros: `[]`.
- COPY: nenhum; fontes CALL: nenhuma.
- ACCEPT: `[]`; relógio: não utilizado.
- Arquivos: `[]`.
- Construções: Arithmetic:SUBTRACT, Display, Inspect, Move, StopRun.
- Riscos: Sem entrada interativa ou recurso externo; limites de execução mantidos.
- Execução: stdin finito, fixtures declaradas, relógio fixo, CPU 5s, timeout 8s e arquivos até 16 MiB; sem chamadas de rede no runtime.

### PROG015A

- Classe: `standalone`; parâmetros: `[]`.
- COPY: nenhum; fontes CALL: nenhuma.
- ACCEPT: `[]`; relógio: não utilizado.
- Arquivos: `[]`.
- Construções: Arithmetic:SUBTRACT, Display, Inspect, Move, StopRun.
- Riscos: Sem entrada interativa ou recurso externo; limites de execução mantidos.
- Execução: stdin finito, fixtures declaradas, relógio fixo, CPU 5s, timeout 8s e arquivos até 16 MiB; sem chamadas de rede no runtime.

### PROG016A

- Classe: `executable_with_fixtures`; parâmetros: `[]`.
- COPY: examples/dependencias/COD001A.cpy; fontes CALL: examples/complementares/PROGTIME.cbl, examples/dependencias/PROGDATA.cbl.
- ACCEPT: `[]`; relógio: controlado.
- Arquivos: `[]`.
- Construções: Call, Display, Move, StopRun.
- Riscos: Sem entrada interativa ou recurso externo; limites de execução mantidos.
- Execução: stdin finito, fixtures declaradas, relógio fixo, CPU 5s, timeout 8s e arquivos até 16 MiB; sem chamadas de rede no runtime.

### PROG017A

- Classe: `standalone`; parâmetros: `[]`.
- COPY: nenhum; fontes CALL: nenhuma.
- ACCEPT: `[{"target": "WRK-VALOR", "source": null, "line": 24, "picture": "9(01)", "bytes": 1}]`; relógio: não utilizado.
- Arquivos: `[]`.
- Construções: Accept, Display, Evaluate, If, Move, Perform, Set, StopRun.
- Riscos: ACCEPT exige stdin completo; EOF pode manter menus/repetições ativos. Repetições/desvios exigem entradas de término; timeout e limite de CPU são obrigatórios.
- Execução: stdin finito, fixtures declaradas, relógio fixo, CPU 5s, timeout 8s e arquivos até 16 MiB; sem chamadas de rede no runtime.

### PROG019A

- Classe: `standalone`; parâmetros: `[]`.
- COPY: nenhum; fontes CALL: nenhuma.
- ACCEPT: `[{"target": "WRK-PROCURADO", "source": null, "line": 33, "picture": "9(3)", "bytes": 3}]`; relógio: não utilizado.
- Arquivos: `[]`.
- Construções: Accept, Display, If, Move, Search, Set, StopRun.
- Riscos: ACCEPT exige stdin completo; EOF pode manter menus/repetições ativos.
- Execução: stdin finito, fixtures declaradas, relógio fixo, CPU 5s, timeout 8s e arquivos até 16 MiB; sem chamadas de rede no runtime.

### PROG020A

- Classe: `standalone`; parâmetros: `[]`.
- COPY: nenhum; fontes CALL: nenhuma.
- ACCEPT: `[{"target": "WRK-PROCURADO", "source": null, "line": 34, "picture": "9(3)", "bytes": 3}]`; relógio: não utilizado.
- Arquivos: `[]`.
- Construções: Accept, Display, If, Move, Search, StopRun.
- Riscos: ACCEPT exige stdin completo; EOF pode manter menus/repetições ativos.
- Execução: stdin finito, fixtures declaradas, relógio fixo, CPU 5s, timeout 8s e arquivos até 16 MiB; sem chamadas de rede no runtime.

### PROG021A

- Classe: `executable_with_fixtures`; parâmetros: `[]`.
- COPY: nenhum; fontes CALL: nenhuma.
- ACCEPT: `[{"target": "USER-INFORMADO", "source": null, "line": 36, "picture": "X(20)", "bytes": 20}, {"target": "SENHA-INFORMADA", "source": null, "line": 38, "picture": "X(10)", "bytes": 10}]`; relógio: não utilizado.
- Arquivos: `[{"select": "ARQ-USUARIOS", "path": "USUARIO.dat", "organization": "LINE SEQUENTIAL", "record_lengths": [30], "open_modes": ["INPUT"]}]`.
- Construções: Accept, Close, Display, If, Move, Open, Perform, Read, StopRun.
- Riscos: ACCEPT exige stdin completo; EOF pode manter menus/repetições ativos. Repetições/desvios exigem entradas de término; timeout e limite de CPU são obrigatórios. OPEN pode criar/truncar/gravar arquivos; executar somente com caminhos relativos e fixtures isoladas.
- Execução: stdin finito, fixtures declaradas, relógio fixo, CPU 5s, timeout 8s e arquivos até 16 MiB; sem chamadas de rede no runtime.

### PROG022A

- Classe: `standalone`; parâmetros: `[]`.
- COPY: nenhum; fontes CALL: nenhuma.
- ACCEPT: `[{"target": "WRK-NOME", "source": null, "line": 64, "picture": "X(30)", "bytes": 30}, {"target": "WRK-IDADE", "source": null, "line": 107, "picture": "9(02)", "bytes": 2}]`; relógio: não utilizado.
- Arquivos: `[]`.
- Construções: Accept, Arithmetic:COMPUTE, Display, Exit, If, Inspect, Move, Perform, StopRun.
- Riscos: ACCEPT exige stdin completo; EOF pode manter menus/repetições ativos. Repetições/desvios exigem entradas de término; timeout e limite de CPU são obrigatórios.
- Execução: stdin finito, fixtures declaradas, relógio fixo, CPU 5s, timeout 8s e arquivos até 16 MiB; sem chamadas de rede no runtime.

### PROG023A

- Classe: `executable_with_fixtures`; parâmetros: `[]`.
- COPY: nenhum; fontes CALL: nenhuma.
- ACCEPT: `[{"target": "WRK-OPCAO", "source": null, "line": 149, "picture": "9(01)", "bytes": 1}, {"target": "WRK-COD-PRODUTO", "source": null, "line": 199, "picture": "9(05)", "bytes": 5}, {"target": "WRK-NOME-PRODUTO", "source": null, "line": 229, "picture": "X(20)", "bytes": 20}, {"target": "WRK-QTDE-PRODUTO", "source": null, "line": 250, "picture": "9(05)", "bytes": 5}]`; relógio: não utilizado.
- Arquivos: `[{"select": "ARQUIVO-ENT", "path": "ESTOQUE.dat", "organization": "LINE SEQUENTIAL", "record_lengths": [30], "open_modes": ["INPUT", "OUTPUT"]}]`.
- Construções: Accept, Arithmetic:ADD, Arithmetic:SUBTRACT, Close, Continue, Display, Evaluate, Exit, If, Move, Open, Perform, Read, StopRun, Write.
- Riscos: ACCEPT exige stdin completo; EOF pode manter menus/repetições ativos. Repetições/desvios exigem entradas de término; timeout e limite de CPU são obrigatórios. OPEN pode criar/truncar/gravar arquivos; executar somente com caminhos relativos e fixtures isoladas.
- Execução: stdin finito, fixtures declaradas, relógio fixo, CPU 5s, timeout 8s e arquivos até 16 MiB; sem chamadas de rede no runtime.

### PROG023B

- Classe: `executable_with_fixtures`; parâmetros: `[]`.
- COPY: nenhum; fontes CALL: nenhuma.
- ACCEPT: `[{"target": "WRK-OPCAO", "source": null, "line": 160, "picture": "9(01)", "bytes": 1}, {"target": "WRK-COD-PRODUTO", "source": null, "line": 215, "picture": "9(05)", "bytes": 5}, {"target": "WRK-NOME-PRODUTO", "source": null, "line": 245, "picture": "X(20)", "bytes": 20}, {"target": "WRK-QTDE-PRODUTO", "source": null, "line": 265, "picture": "9(05)", "bytes": 5}, {"target": "WRK-VALOR-PRODUTO", "source": null, "line": 293, "picture": "9(15)V99", "bytes": 17}, {"target": "WRK-EXCLUIR", "source": null, "line": 458, "picture": "X(01)", "bytes": 1}]`; relógio: não utilizado.
- Arquivos: `[{"select": "ARQUIVO-ENT", "path": "ESTOQUE.dat", "organization": "LINE SEQUENTIAL", "record_lengths": [47], "open_modes": ["INPUT", "OUTPUT"]}]`.
- Construções: Accept, Arithmetic:ADD, Arithmetic:SUBTRACT, Close, Continue, Display, Evaluate, Exit, If, Move, Open, Perform, Read, StopRun, Write.
- Riscos: ACCEPT exige stdin completo; EOF pode manter menus/repetições ativos. Repetições/desvios exigem entradas de término; timeout e limite de CPU são obrigatórios. OPEN pode criar/truncar/gravar arquivos; executar somente com caminhos relativos e fixtures isoladas.
- Execução: stdin finito, fixtures declaradas, relógio fixo, CPU 5s, timeout 8s e arquivos até 16 MiB; sem chamadas de rede no runtime.
- Observação do fonte: A exclusão física não consulta a confirmação WRK-EXCLUIR dentro da rotina de exclusão.

### PROG023D

- Classe: `executable_with_fixtures`; parâmetros: `[]`.
- COPY: examples/dependencias/COD001A.cpy; fontes CALL: examples/complementares/PROGTIME.cbl, examples/dependencias/PROGDATA.cbl.
- ACCEPT: `[{"target": "WRK-OPCAO", "source": null, "line": 207, "picture": "9(01)", "bytes": 1}, {"target": "WRK-COD-PRODUTO", "source": null, "line": 264, "picture": "9(05)", "bytes": 5}, {"target": "WRK-NOME-PRODUTO", "source": null, "line": 294, "picture": "X(20)", "bytes": 20}, {"target": "WRK-QTDE-PRODUTO", "source": null, "line": 314, "picture": "9(05)", "bytes": 5}, {"target": "WRK-VALOR-PRODUTO", "source": null, "line": 342, "picture": "9(15)V99", "bytes": 17}, {"target": "WRK-PROD-STATUS", "source": null, "line": 376, "picture": "X(01)", "bytes": 1}, {"target": "WRK-EXCLUIR", "source": null, "line": 577, "picture": "X(01)", "bytes": 1}, {"target": "WRK-EXCLUIR", "source": null, "line": 586, "picture": "X(01)", "bytes": 1}]`; relógio: controlado.
- Arquivos: `[{"select": "ARQUIVO-ENT", "path": "ESTOQUE.dat", "organization": "LINE SEQUENTIAL", "record_lengths": [48], "open_modes": ["INPUT", "OUTPUT"]}, {"select": "ARQUIVO-SAI", "path": "ARQLOG1.dat", "organization": "LINE SEQUENTIAL", "record_lengths": [102], "open_modes": ["EXTEND"]}]`.
- Construções: Accept, Arithmetic:ADD, Arithmetic:SUBTRACT, Call, Close, Continue, Display, Evaluate, Exit, If, Move, Open, Perform, Read, StopRun, Write.
- Riscos: ACCEPT exige stdin completo; EOF pode manter menus/repetições ativos. Repetições/desvios exigem entradas de término; timeout e limite de CPU são obrigatórios. OPEN pode criar/truncar/gravar arquivos; executar somente com caminhos relativos e fixtures isoladas.
- Execução: stdin finito, fixtures declaradas, relógio fixo, CPU 5s, timeout 8s e arquivos até 16 MiB; sem chamadas de rede no runtime.

### PROG023E

- Classe: `executable_with_fixtures`; parâmetros: `[]`.
- COPY: examples/dependencias/COD001A.cpy; fontes CALL: examples/complementares/PROGTIME.cbl, examples/dependencias/PROGDATA.cbl.
- ACCEPT: `[{"target": "WRK-OPCAO", "source": null, "line": 221, "picture": "9(01)", "bytes": 1}, {"target": "WRK-COD-PRODUTO", "source": null, "line": 283, "picture": "9(05)", "bytes": 5}, {"target": "WRK-NOME-PRODUTO", "source": null, "line": 313, "picture": "X(20)", "bytes": 20}, {"target": "WRK-QTDE-PRODUTO", "source": null, "line": 333, "picture": "9(05)", "bytes": 5}, {"target": "WRK-VALOR-PRODUTO", "source": null, "line": 361, "picture": "9(15)V99", "bytes": 17}, {"target": "WRK-QTDE-MIN", "source": null, "line": 381, "picture": "9(05)", "bytes": 5}, {"target": "WRK-PROD-STATUS", "source": null, "line": 416, "picture": "X(01)", "bytes": 1}, {"target": "WRK-EXCLUIR", "source": null, "line": 642, "picture": "X(01)", "bytes": 1}, {"target": "WRK-EXCLUIR", "source": null, "line": 651, "picture": "X(01)", "bytes": 1}]`; relógio: controlado.
- Arquivos: `[{"select": "ARQUIVO-ENT", "path": "ESTOQUE.dat", "organization": "LINE SEQUENTIAL", "record_lengths": [58], "open_modes": ["INPUT", "OUTPUT"]}, {"select": "ARQUIVO-SAI", "path": "ARQLOG1.dat", "organization": "LINE SEQUENTIAL", "record_lengths": [102], "open_modes": ["EXTEND"]}]`.
- Construções: Accept, Arithmetic:ADD, Arithmetic:SUBTRACT, Call, Close, Continue, Display, Evaluate, Exit, If, Move, Open, Perform, Read, StopRun, Write.
- Riscos: ACCEPT exige stdin completo; EOF pode manter menus/repetições ativos. Repetições/desvios exigem entradas de término; timeout e limite de CPU são obrigatórios. OPEN pode criar/truncar/gravar arquivos; executar somente com caminhos relativos e fixtures isoladas.
- Execução: stdin finito, fixtures declaradas, relógio fixo, CPU 5s, timeout 8s e arquivos até 16 MiB; sem chamadas de rede no runtime.
- Observação do fonte: A gravação do log na saída está no ELSE do teste de estoque igual ao mínimo (linhas 521–542). Na igualdade há alerta e persistência, sem log; abaixo do mínimo há log.

### PROG024A

- Classe: `executable_with_fixtures`; parâmetros: `[]`.
- COPY: examples/dependencias/COD001A.cpy; fontes CALL: examples/dependencias/PROGDATA.cbl.
- ACCEPT: `[{"target": "WRK-OPCAO", "source": null, "line": 199, "picture": "9(01)", "bytes": 1}, {"target": "WRK-COD-LIVRO", "source": null, "line": 253, "picture": "9(05)", "bytes": 5}, {"target": "WRK-NOME-LIVRO", "source": null, "line": 283, "picture": "X(40)", "bytes": 40}, {"target": "WRK-AUTOR-LIVRO", "source": null, "line": 303, "picture": "X(20)", "bytes": 20}]`; relógio: controlado.
- Arquivos: `[{"select": "ARQUIVO-ENT", "path": "BIBLIOTECA.dat", "organization": "LINE SEQUENTIAL", "record_lengths": [76], "open_modes": ["INPUT", "OUTPUT"]}, {"select": "ARQUIVO-SAI", "path": "BIBLIOTECA.txt", "organization": "LINE SEQUENTIAL", "record_lengths": [113], "open_modes": ["EXTEND"]}]`.
- Construções: Accept, Arithmetic:ADD, Arithmetic:SUBTRACT, Call, Close, Continue, Display, Evaluate, Exit, If, Move, Open, Perform, Read, StopRun, Write.
- Riscos: ACCEPT exige stdin completo; EOF pode manter menus/repetições ativos. Repetições/desvios exigem entradas de término; timeout e limite de CPU são obrigatórios. OPEN pode criar/truncar/gravar arquivos; executar somente com caminhos relativos e fixtures isoladas.
- Execução: stdin finito, fixtures declaradas, relógio fixo, CPU 5s, timeout 8s e arquivos até 16 MiB; sem chamadas de rede no runtime.

### PROG025A

- Classe: `executable_with_fixtures`; parâmetros: `[]`.
- COPY: examples/dependencias/COD001A.cpy; fontes CALL: examples/dependencias/PROGDATA.cbl.
- ACCEPT: `[]`; relógio: controlado.
- Arquivos: `[{"select": "ARQUIVO-ENT", "path": "TITULOS.dat", "organization": "LINE SEQUENTIAL", "record_lengths": [256], "open_modes": ["INPUT"]}, {"select": "ARQUIVO-PARM", "path": "PARAMETROS.dat", "organization": "LINE SEQUENTIAL", "record_lengths": [64], "open_modes": ["INPUT"]}, {"select": "ARQUIVO-SAI", "path": "BOLETOS.dat", "organization": "LINE SEQUENTIAL", "record_lengths": [80], "open_modes": ["OUTPUT"]}]`.
- Construções: Arithmetic:ADD, Arithmetic:COMPUTE, Call, Close, Display, Exit, If, Move, Open, Perform, Read, StopRun, Unstring, Write.
- Riscos: Repetições/desvios exigem entradas de término; timeout e limite de CPU são obrigatórios. OPEN pode criar/truncar/gravar arquivos; executar somente com caminhos relativos e fixtures isoladas.
- Execução: stdin finito, fixtures declaradas, relógio fixo, CPU 5s, timeout 8s e arquivos até 16 MiB; sem chamadas de rede no runtime.

### PROG027A

- Classe: `executable_with_fixtures`; parâmetros: `[]`.
- COPY: examples/dependencias/COD001A.cpy; fontes CALL: examples/dependencias/PROGDATA.cbl.
- ACCEPT: `[]`; relógio: controlado.
- Arquivos: `[{"select": "ARQUIVO-ENT", "path": "PRODUTOS.dat", "organization": "LINE SEQUENTIAL", "record_lengths": [43], "open_modes": ["INPUT"]}, {"select": "ARQUIVO-SAI", "path": "NOTAFISCAL.dat", "organization": "LINE SEQUENTIAL", "record_lengths": [80], "open_modes": ["OUTPUT"]}]`.
- Construções: Arithmetic:ADD, Arithmetic:COMPUTE, Call, Close, Display, Exit, If, Move, Open, Perform, Read, StopRun, Write.
- Riscos: Repetições/desvios exigem entradas de término; timeout e limite de CPU são obrigatórios. OPEN pode criar/truncar/gravar arquivos; executar somente com caminhos relativos e fixtures isoladas.
- Execução: stdin finito, fixtures declaradas, relógio fixo, CPU 5s, timeout 8s e arquivos até 16 MiB; sem chamadas de rede no runtime.

### PROG028A

- Classe: `executable_with_fixtures`; parâmetros: `[]`.
- COPY: examples/dependencias/COD001A.cpy; fontes CALL: examples/complementares/PROGTIME.cbl, examples/dependencias/PROGDATA.cbl.
- ACCEPT: `[{"target": "WRK-COD-FUNCIONARIO", "source": null, "line": 253, "picture": "9(05)", "bytes": 5}, {"target": "WRK-COD-TIPO", "source": null, "line": 305, "picture": "X(01)", "bytes": 1}]`; relógio: controlado.
- Arquivos: `[{"select": "ARQUIVO-ENT", "path": "FUNCIONARIO.dat", "organization": "LINE SEQUENTIAL", "record_lengths": [35], "open_modes": ["INPUT"]}, {"select": "ARQUIVO-SAI", "path": "PONTO.dat", "organization": "LINE SEQUENTIAL", "record_lengths": [54], "open_modes": ["EXTEND", "INPUT"]}]`.
- Construções: Accept, Arithmetic:ADD, Arithmetic:SUBTRACT, Call, Close, Continue, Display, Exit, If, Move, Open, Perform, Read, StopRun, Write.
- Riscos: ACCEPT exige stdin completo; EOF pode manter menus/repetições ativos. Repetições/desvios exigem entradas de término; timeout e limite de CPU são obrigatórios. OPEN pode criar/truncar/gravar arquivos; executar somente com caminhos relativos e fixtures isoladas.
- Execução: stdin finito, fixtures declaradas, relógio fixo, CPU 5s, timeout 8s e arquivos até 16 MiB; sem chamadas de rede no runtime.

### PROG029A

- Classe: `standalone`; parâmetros: `[]`.
- COPY: nenhum; fontes CALL: nenhuma.
- ACCEPT: `[{"target": "WRK-VALOR-REAL", "source": null, "line": 84, "picture": "9(7)V9(02)", "bytes": 9}]`; relógio: não utilizado.
- Arquivos: `[]`.
- Construções: Accept, Arithmetic:COMPUTE, Display, Exit, If, Move, Perform, StopRun.
- Riscos: ACCEPT exige stdin completo; EOF pode manter menus/repetições ativos. Repetições/desvios exigem entradas de término; timeout e limite de CPU são obrigatórios.
- Execução: stdin finito, fixtures declaradas, relógio fixo, CPU 5s, timeout 8s e arquivos até 16 MiB; sem chamadas de rede no runtime.

### PROG033A

- Classe: `executable_with_fixtures`; parâmetros: `[]`.
- COPY: nenhum; fontes CALL: examples/complementares/PROG034A.cbl, examples/complementares/PROG035A.cbl.
- ACCEPT: `[{"target": "WRK-OPCAO-MENU", "source": null, "line": 57, "picture": "9(002)", "bytes": 2}]`; relógio: não utilizado.
- Arquivos: `[]`.
- Construções: Accept, Call, Display, Evaluate, Exit, Initialize, Perform, StopRun.
- Riscos: ACCEPT exige stdin completo; EOF pode manter menus/repetições ativos. Repetições/desvios exigem entradas de término; timeout e limite de CPU são obrigatórios.
- Execução: stdin finito, fixtures declaradas, relógio fixo, CPU 5s, timeout 8s e arquivos até 16 MiB; sem chamadas de rede no runtime.

### PROG034A

- Classe: `executable_with_fixtures`; parâmetros: `[]`.
- COPY: nenhum; fontes CALL: nenhuma.
- ACCEPT: `[]`; relógio: não utilizado.
- Arquivos: `[{"select": "ARQUIVO-ENT", "path": "CADENT001.dat", "organization": "LINE SEQUENTIAL", "record_lengths": [38], "open_modes": ["INPUT"]}, {"select": "ARQUIVO-SAI", "path": "CADASTRO1.dat", "organization": "LINE SEQUENTIAL", "record_lengths": [38], "open_modes": ["EXTEND"]}]`.
- Construções: Arithmetic:ADD, Close, Display, Exit, If, Move, Open, Perform, Read, StopRun, Write.
- Riscos: Repetições/desvios exigem entradas de término; timeout e limite de CPU são obrigatórios. OPEN pode criar/truncar/gravar arquivos; executar somente com caminhos relativos e fixtures isoladas.
- Execução: stdin finito, fixtures declaradas, relógio fixo, CPU 5s, timeout 8s e arquivos até 16 MiB; sem chamadas de rede no runtime.
- Observação do fonte: O fonte lê somente o primeiro registro e escreve mesmo quando a entrada está vazia.

### PROG035A

- Classe: `executable_with_fixtures`; parâmetros: `[]`.
- COPY: nenhum; fontes CALL: nenhuma.
- ACCEPT: `[]`; relógio: não utilizado.
- Arquivos: `[{"select": "ARQUIVO-ENT", "path": "CADASTRO1.dat", "organization": "LINE SEQUENTIAL", "record_lengths": [38], "open_modes": ["INPUT"]}]`.
- Construções: Arithmetic:ADD, Close, Display, Exit, If, Move, Open, Perform, Read, StopRun.
- Riscos: Repetições/desvios exigem entradas de término; timeout e limite de CPU são obrigatórios. OPEN pode criar/truncar/gravar arquivos; executar somente com caminhos relativos e fixtures isoladas.
- Execução: stdin finito, fixtures declaradas, relógio fixo, CPU 5s, timeout 8s e arquivos até 16 MiB; sem chamadas de rede no runtime.
- Observação do fonte: O fonte conta/lê registros, mas não os exibe. Verificam-se caminhos vazio/preenchido.

### PROG036A

- Classe: `executable_with_fixtures`; parâmetros: `[]`.
- COPY: nenhum; fontes CALL: nenhuma.
- ACCEPT: `[]`; relógio: não utilizado.
- Arquivos: `[{"select": "ARQUIVO-ENT1", "path": "CLASSENT.dat", "organization": "LINE SEQUENTIAL", "record_lengths": [1], "open_modes": ["INPUT"]}, {"select": "ARQUIVO-ENT2", "path": "CADASTRO1.dat", "organization": "LINE SEQUENTIAL", "record_lengths": [38], "open_modes": ["INPUT", "OUTPUT"]}]`.
- Construções: Arithmetic:ADD, Close, Display, Evaluate, Exit, If, Move, Open, Perform, Read, StopRun, Write.
- Riscos: Repetições/desvios exigem entradas de término; timeout e limite de CPU são obrigatórios. OPEN pode criar/truncar/gravar arquivos; executar somente com caminhos relativos e fixtures isoladas.
- Execução: stdin finito, fixtures declaradas, relógio fixo, CPU 5s, timeout 8s e arquivos até 16 MiB; sem chamadas de rede no runtime.

### PROG037A

- Classe: `executable_with_fixtures`; parâmetros: `[]`.
- COPY: nenhum; fontes CALL: nenhuma.
- ACCEPT: `[]`; relógio: não utilizado.
- Arquivos: `[{"select": "ARQUIVO-ENT1", "path": "ALTENT01.dat", "organization": "LINE SEQUENTIAL", "record_lengths": [38], "open_modes": ["INPUT"]}, {"select": "ARQUIVO-ENT2", "path": "CADASTRO1.dat", "organization": "LINE SEQUENTIAL", "record_lengths": [38], "open_modes": ["INPUT", "OUTPUT"]}]`.
- Construções: Arithmetic:ADD, Arithmetic:SUBTRACT, Close, Continue, Display, Exit, If, Move, Open, Perform, Read, StopRun, Write.
- Riscos: Repetições/desvios exigem entradas de término; timeout e limite de CPU são obrigatórios. OPEN pode criar/truncar/gravar arquivos; executar somente com caminhos relativos e fixtures isoladas.
- Execução: stdin finito, fixtures declaradas, relógio fixo, CPU 5s, timeout 8s e arquivos até 16 MiB; sem chamadas de rede no runtime.

### PROG038A

- Classe: `executable_with_fixtures`; parâmetros: `[]`.
- COPY: nenhum; fontes CALL: nenhuma.
- ACCEPT: `[]`; relógio: não utilizado.
- Arquivos: `[{"select": "ARQUIVO-ENT1", "path": "ALTCONS01.dat", "organization": "LINE SEQUENTIAL", "record_lengths": [5], "open_modes": ["INPUT"]}, {"select": "ARQUIVO-ENT2", "path": "CADASTRO1.dat", "organization": "LINE SEQUENTIAL", "record_lengths": [38], "open_modes": ["INPUT"]}, {"select": "ARQUIVO-SAI", "path": "ALTRET01.dat", "organization": "LINE SEQUENTIAL", "record_lengths": [38], "open_modes": ["OUTPUT"]}]`.
- Construções: Arithmetic:ADD, Arithmetic:SUBTRACT, Close, Display, Exit, If, Move, Open, Perform, Read, StopRun, Write.
- Riscos: Repetições/desvios exigem entradas de término; timeout e limite de CPU são obrigatórios. OPEN pode criar/truncar/gravar arquivos; executar somente com caminhos relativos e fixtures isoladas.
- Execução: stdin finito, fixtures declaradas, relógio fixo, CPU 5s, timeout 8s e arquivos até 16 MiB; sem chamadas de rede no runtime.

### PROG039A

- Classe: `executable_with_fixtures`; parâmetros: `[]`.
- COPY: nenhum; fontes CALL: nenhuma.
- ACCEPT: `[{"target": "WRK-ID-CLIENTE", "source": null, "line": 104, "picture": "9(05)", "bytes": 5}]`; relógio: não utilizado.
- Arquivos: `[{"select": "ARQUIVO-ENT", "path": "CADASTRO1.dat", "organization": "LINE SEQUENTIAL", "record_lengths": [38], "open_modes": ["INPUT", "OUTPUT"]}]`.
- Construções: Accept, Arithmetic:ADD, Close, Display, Exit, If, Move, Open, Perform, Read, StopRun, Write.
- Riscos: ACCEPT exige stdin completo; EOF pode manter menus/repetições ativos. Repetições/desvios exigem entradas de término; timeout e limite de CPU são obrigatórios. OPEN pode criar/truncar/gravar arquivos; executar somente com caminhos relativos e fixtures isoladas.
- Execução: stdin finito, fixtures declaradas, relógio fixo, CPU 5s, timeout 8s e arquivos até 16 MiB; sem chamadas de rede no runtime.

### PROG040A

- Classe: `executable_with_fixtures`; parâmetros: `[]`.
- COPY: nenhum; fontes CALL: nenhuma.
- ACCEPT: `[{"target": "WRK-VALOR", "source": null, "line": 67, "picture": "9(05)V99", "bytes": 7}, {"target": "WRK-ID-PRODUTO", "source": null, "line": 101, "picture": "9(05)", "bytes": 5}, {"target": "WRK-NOME-PRODUTO", "source": null, "line": 120, "picture": "X(30)", "bytes": 30}]`; relógio: não utilizado.
- Arquivos: `[{"select": "ARQUIVO-SAI", "path": "CADASTRO2.dat", "organization": "LINE SEQUENTIAL", "record_lengths": [42], "open_modes": ["EXTEND"]}]`.
- Construções: Accept, Close, Display, Exit, GoTo, If, Move, Open, Perform, StopRun, Write.
- Riscos: ACCEPT exige stdin completo; EOF pode manter menus/repetições ativos. Repetições/desvios exigem entradas de término; timeout e limite de CPU são obrigatórios. OPEN pode criar/truncar/gravar arquivos; executar somente com caminhos relativos e fixtures isoladas.
- Execução: stdin finito, fixtures declaradas, relógio fixo, CPU 5s, timeout 8s e arquivos até 16 MiB; sem chamadas de rede no runtime.

### PROG041A

- Classe: `executable_with_fixtures`; parâmetros: `[]`.
- COPY: nenhum; fontes CALL: nenhuma.
- ACCEPT: `[]`; relógio: não utilizado.
- Arquivos: `[{"select": "ARQUIVO-SAI", "path": "CADASTRO2.dat", "organization": "LINE SEQUENTIAL", "record_lengths": [42], "open_modes": ["INPUT"]}]`.
- Construções: Arithmetic:ADD, Close, Display, Exit, If, Move, Open, Perform, Read, StopRun.
- Riscos: Repetições/desvios exigem entradas de término; timeout e limite de CPU são obrigatórios. OPEN pode criar/truncar/gravar arquivos; executar somente com caminhos relativos e fixtures isoladas.
- Execução: stdin finito, fixtures declaradas, relógio fixo, CPU 5s, timeout 8s e arquivos até 16 MiB; sem chamadas de rede no runtime.

### PROG042B

- Classe: `module_needs_caller`; parâmetros: `[{"name": "WRK-ID-PEDIDO", "bytes": 5}]`.
- COPY: nenhum; fontes CALL: nenhuma.
- ACCEPT: `[]`; relógio: não utilizado.
- Arquivos: `[{"select": "ARQUIVO-ENT", "path": "CADASTRO3.dat", "organization": "LINE SEQUENTIAL", "record_lengths": [92], "open_modes": ["INPUT"]}]`.
- Construções: Arithmetic:ADD, Close, Display, Exit, Goback, If, Move, Open, Perform, Read.
- Riscos: Repetições/desvios exigem entradas de término; timeout e limite de CPU são obrigatórios. OPEN pode criar/truncar/gravar arquivos; executar somente com caminhos relativos e fixtures isoladas. LINKAGE pertence ao chamador; requer harness real e conferência dos parâmetros após retorno.
- Execução: stdin finito, fixtures declaradas, relógio fixo, CPU 5s, timeout 8s e arquivos até 16 MiB; sem chamadas de rede no runtime.

### PROG043A

- Classe: `executable_with_fixtures`; parâmetros: `[]`.
- COPY: nenhum; fontes CALL: nenhuma.
- ACCEPT: `[]`; relógio: não utilizado.
- Arquivos: `[{"select": "ARQUIVO-ENT1", "path": "PRODCONS01.dat", "organization": "LINE SEQUENTIAL", "record_lengths": [5], "open_modes": ["INPUT"]}, {"select": "ARQUIVO-ENT2", "path": "CADASTRO2.dat", "organization": "LINE SEQUENTIAL", "record_lengths": [42], "open_modes": ["INPUT"]}, {"select": "ARQUIVO-SAI", "path": "PRODRET01.dat", "organization": "LINE SEQUENTIAL", "record_lengths": [42], "open_modes": ["OUTPUT"]}]`.
- Construções: Arithmetic:ADD, Arithmetic:SUBTRACT, Close, Display, Exit, If, Move, Open, Perform, Read, StopRun, Write.
- Riscos: Repetições/desvios exigem entradas de término; timeout e limite de CPU são obrigatórios. OPEN pode criar/truncar/gravar arquivos; executar somente com caminhos relativos e fixtures isoladas.
- Execução: stdin finito, fixtures declaradas, relógio fixo, CPU 5s, timeout 8s e arquivos até 16 MiB; sem chamadas de rede no runtime.

### PROG044A

- Classe: `executable_with_fixtures`; parâmetros: `[]`.
- COPY: nenhum; fontes CALL: nenhuma.
- ACCEPT: `[]`; relógio: não utilizado.
- Arquivos: `[{"select": "ARQUIVO-ENT", "path": "CADASTRO3.dat", "organization": "LINE SEQUENTIAL", "record_lengths": [92], "open_modes": ["INPUT"]}]`.
- Construções: Arithmetic:ADD, Close, Display, Exit, If, Move, Open, Perform, Read, StopRun.
- Riscos: Repetições/desvios exigem entradas de término; timeout e limite de CPU são obrigatórios. OPEN pode criar/truncar/gravar arquivos; executar somente com caminhos relativos e fixtures isoladas.
- Execução: stdin finito, fixtures declaradas, relógio fixo, CPU 5s, timeout 8s e arquivos até 16 MiB; sem chamadas de rede no runtime.

### PROG045A

- Classe: `executable_with_fixtures`; parâmetros: `[]`.
- COPY: nenhum; fontes CALL: nenhuma.
- ACCEPT: `[]`; relógio: não utilizado.
- Arquivos: `[{"select": "ARQUIVO-ENT1", "path": "PEDDET01.dat", "organization": "LINE SEQUENTIAL", "record_lengths": [5], "open_modes": ["INPUT"]}, {"select": "ARQUIVO-ENT2", "path": "CADASTRO3.dat", "organization": "LINE SEQUENTIAL", "record_lengths": [92], "open_modes": ["INPUT"]}, {"select": "ARQUIVO-SAI", "path": "CADASTRO4.dat", "organization": "LINE SEQUENTIAL", "record_lengths": [92], "open_modes": ["OUTPUT"]}]`.
- Construções: Arithmetic:ADD, Arithmetic:SUBTRACT, Close, Display, Exit, If, Move, Open, Perform, Read, StopRun, Write.
- Riscos: Repetições/desvios exigem entradas de término; timeout e limite de CPU são obrigatórios. OPEN pode criar/truncar/gravar arquivos; executar somente com caminhos relativos e fixtures isoladas.
- Execução: stdin finito, fixtures declaradas, relógio fixo, CPU 5s, timeout 8s e arquivos até 16 MiB; sem chamadas de rede no runtime.

### PROGDATA

- Classe: `module_needs_caller`; parâmetros: `[{"name": "COD001A-REGISTRO", "bytes": 81}]`.
- COPY: examples/dependencias/COD001A.cpy; fontes CALL: nenhuma.
- ACCEPT: `[{"target": "COD001A-DATA", "source": "DATE", "line": 49, "picture": null, "bytes": 8}, {"target": "COD001A-DIA-SEMANA", "source": "DAY-OF-WEEK", "line": 50, "picture": "9(002)", "bytes": 2}, {"target": "WRK-DIAS-ANO-YYYYDDD", "source": "DAY", "line": 133, "picture": null, "bytes": 7}]`; relógio: controlado.
- Arquivos: `[]`.
- Construções: Accept, Evaluate, Exit, Goback, Move, Perform.
- Riscos: Repetições/desvios exigem entradas de término; timeout e limite de CPU são obrigatórios. LINKAGE pertence ao chamador; requer harness real e conferência dos parâmetros após retorno.
- Execução: stdin finito, fixtures declaradas, relógio fixo, CPU 5s, timeout 8s e arquivos até 16 MiB; sem chamadas de rede no runtime.

### PROGTEST4

- Classe: `standalone`; parâmetros: `[]`.
- COPY: nenhum; fontes CALL: nenhuma.
- ACCEPT: `[]`; relógio: não utilizado.
- Arquivos: `[]`.
- Construções: Display, If, Move, Search, Set, StopRun.
- Riscos: Sem entrada interativa ou recurso externo; limites de execução mantidos.
- Execução: stdin finito, fixtures declaradas, relógio fixo, CPU 5s, timeout 8s e arquivos até 16 MiB; sem chamadas de rede no runtime.

### PROGTIME

- Classe: `module_needs_caller`; parâmetros: `[{"name": "COD001A-REGISTRO", "bytes": 81}]`.
- COPY: examples/dependencias/COD001A.cpy; fontes CALL: nenhuma.
- ACCEPT: `[{"target": "COD001A-TIME", "source": "TIME", "line": 41, "picture": null, "bytes": 8}]`; relógio: controlado.
- Arquivos: `[]`.
- Construções: Accept, Exit, Goback, If, Move, Perform.
- Riscos: Repetições/desvios exigem entradas de término; timeout e limite de CPU são obrigatórios. LINKAGE pertence ao chamador; requer harness real e conferência dos parâmetros após retorno.
- Execução: stdin finito, fixtures declaradas, relógio fixo, CPU 5s, timeout 8s e arquivos até 16 MiB; sem chamadas de rede no runtime.
- Observação do fonte: A condição >=19 AND <=00 é impossível: às 20h o próprio fonte retorna MADRUGADA.

### REL0001A

- Classe: `module_needs_caller`; parâmetros: `[{"name": "COPY002A-REGISTRO", "bytes": 10552}]`.
- COPY: examples/dependencias/COD001A.cpy, examples/dependencias/COPY002A.cpy; fontes CALL: examples/complementares/PROGTIME.cbl, examples/dependencias/PROGDATA.cbl.
- ACCEPT: `[]`; relógio: controlado.
- Arquivos: `[{"select": "REL0001A-OUT", "path": "REL0001A.txt", "organization": "LINE SEQUENTIAL", "record_lengths": [100], "open_modes": ["OUTPUT"]}]`.
- Construções: Arithmetic:ADD, Call, Close, Display, Exit, Goback, If, Move, Open, Perform, Write.
- Riscos: Repetições/desvios exigem entradas de término; timeout e limite de CPU são obrigatórios. OPEN pode criar/truncar/gravar arquivos; executar somente com caminhos relativos e fixtures isoladas. LINKAGE pertence ao chamador; requer harness real e conferência dos parâmetros após retorno.
- Execução: stdin finito, fixtures declaradas, relógio fixo, CPU 5s, timeout 8s e arquivos até 16 MiB; sem chamadas de rede no runtime.
- Observação do fonte: DET2 é escrito antes de atualizar TELEFONE: primeiro telefone zero, seguintes usam o anterior.

### REL0002A

- Classe: `executable_with_fixtures`; parâmetros: `[]`.
- COPY: examples/dependencias/COD001A.cpy; fontes CALL: examples/complementares/PROGTIME.cbl, examples/dependencias/PROGDATA.cbl.
- ACCEPT: `[]`; relógio: controlado.
- Arquivos: `[{"select": "ARQUIVO-ENTRADA", "path": "CADASTRO3.dat", "organization": "LINE SEQUENTIAL", "record_lengths": [39], "open_modes": ["INPUT"]}, {"select": "REL0002A-SAIDA", "path": "REL0002A.txt", "organization": "LINE SEQUENTIAL", "record_lengths": [100], "open_modes": ["OUTPUT"]}]`.
- Construções: Arithmetic:ADD, Call, Close, Display, Exit, If, Move, Open, Perform, Read, StopRun, Write.
- Riscos: Repetições/desvios exigem entradas de término; timeout e limite de CPU são obrigatórios. OPEN pode criar/truncar/gravar arquivos; executar somente com caminhos relativos e fixtures isoladas.
- Execução: stdin finito, fixtures declaradas, relógio fixo, CPU 5s, timeout 8s e arquivos até 16 MiB; sem chamadas de rede no runtime.

### SORT002A

- Classe: `executable_with_fixtures`; parâmetros: `[]`.
- COPY: nenhum; fontes CALL: nenhuma.
- ACCEPT: `[{"target": "WRK-CTPO-CASS", "source": null, "line": 65, "picture": "X(01)", "bytes": 1}]`; relógio: não utilizado.
- Arquivos: `[{"select": "ARQUIVO-ENTRADA", "path": "CADASTRO3.dat", "organization": "LINE SEQUENTIAL", "record_lengths": [39], "open_modes": ["INPUT"]}]`.
- Construções: Accept, Arithmetic:ADD, Close, Display, Evaluate, Exit, If, Move, Open, Perform, Read, StopRun.
- Riscos: ACCEPT exige stdin completo; EOF pode manter menus/repetições ativos. Repetições/desvios exigem entradas de término; timeout e limite de CPU são obrigatórios. OPEN pode criar/truncar/gravar arquivos; executar somente com caminhos relativos e fixtures isoladas.
- Execução: stdin finito, fixtures declaradas, relógio fixo, CPU 5s, timeout 8s e arquivos até 16 MiB; sem chamadas de rede no runtime.

### VALCNPJ

- Classe: `standalone`; parâmetros: `[]`.
- COPY: nenhum; fontes CALL: nenhuma.
- ACCEPT: `[{"target": "WS-ENTRADA", "source": null, "line": 70, "picture": "X(40)", "bytes": 40}]`; relógio: não utilizado.
- Arquivos: `[]`.
- Construções: Accept, Arithmetic:ADD, Arithmetic:COMPUTE, Display, Exit, GoTo, If, Move, Perform, StopRun.
- Riscos: ACCEPT exige stdin completo; EOF pode manter menus/repetições ativos. Repetições/desvios exigem entradas de término; timeout e limite de CPU são obrigatórios.
- Execução: stdin finito, fixtures declaradas, relógio fixo, CPU 5s, timeout 8s e arquivos até 16 MiB; sem chamadas de rede no runtime.
- Observação do fonte: WS-LEN conta todas as 40 posições de WS-RAW; a checagem de 14 nunca passa. Fonte preservado.

### VALCPF01

- Classe: `standalone`; parâmetros: `[]`.
- COPY: nenhum; fontes CALL: nenhuma.
- ACCEPT: `[{"target": "WRK-CPF-ENTRADA", "source": null, "line": 62, "picture": "X(14)", "bytes": 14}]`; relógio: não utilizado.
- Arquivos: `[]`.
- Construções: Accept, Continue, Display, Exit, If, Initialize, Inspect, Perform, StopRun, Unstring.
- Riscos: ACCEPT exige stdin completo; EOF pode manter menus/repetições ativos. Repetições/desvios exigem entradas de término; timeout e limite de CPU são obrigatórios.
- Execução: stdin finito, fixtures declaradas, relógio fixo, CPU 5s, timeout 8s e arquivos até 16 MiB; sem chamadas de rede no runtime.

### VALIDA1A

- Classe: `standalone`; parâmetros: `[]`.
- COPY: nenhum; fontes CALL: nenhuma.
- ACCEPT: `[{"target": "WRK-CPF-CNPJ-ENTRADA", "source": null, "line": 88, "picture": "X(14)", "bytes": 14}]`; relógio: não utilizado.
- Arquivos: `[]`.
- Construções: Accept, Arithmetic:SUBTRACT, Continue, Display, Exit, If, Inspect, Move, Perform, StopRun.
- Riscos: ACCEPT exige stdin completo; EOF pode manter menus/repetições ativos. Repetições/desvios exigem entradas de término; timeout e limite de CPU são obrigatórios.
- Execução: stdin finito, fixtures declaradas, relógio fixo, CPU 5s, timeout 8s e arquivos até 16 MiB; sem chamadas de rede no runtime.

## Divergências e correções

- prog005a-empty: `[{"part": "stdout", "first_byte": 10, "ours": "b'WRK-NOME:                \\nWRK-NOME:                \\nFIM DO PROGRAMA\\n'", "reference": "b'WRK-NOME: \\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\nWRK-NOME:                \\nFIM DO PROGRAMA\\n'"}]`
  Justificativa e expectativa independente: O fonte exibe o buffer FD depois de READ AT END em arquivo vazio. A ABI do projeto inicializa texto com espaços; GnuCOBOL 3.2 mantém NUL no FD ainda não lido. Ambos os stdout são verificados integralmente.
- prog021a-invalid: `[{"part": "stdout", "first_byte": 82, "ours": "b'v\\xc3\\xa1lidos.                       \\n'", "reference": "b'v\\xc3\\xa1lidos.                     \\n'"}]`
  Justificativa e expectativa independente: Acentos no VALUE PIC X(50): o projeto armazena ISO-8859-1 e converte para UTF-8 no terminal; GnuCOBOL armazena os bytes UTF-8 do literal. Verificação integral dos dois paddings, sem normalização.
- progtest4-search: `[{"part": "stdout", "first_byte": 40, "ours": "b'CONTRADO: JO\\xc3\\x83O SILVA          \\n'", "reference": "b'CONTRADO: JO\\xc3\\x83O SILVA         \\n'"}]`
  Justificativa e expectativa independente: PIC X(20) com JOÃO SILVA: ISO-8859-1 interno no projeto versus bytes UTF-8 no GnuCOBOL. Uma posição de padding difere; expectativas binárias independentes para os dois lados.
- {"id": "decimal-text-conversion", "component": "runtime/fields.c", "problem": "MOVE/UNSTRING alfanumérico com vírgula decimal falhava em INVALID_NUMERIC.", "fix": "Aplicar o separador decimal do descritor receptor na conversão textual.", "affected": ["MINICALC", "PROG025A"], "regression": ["test_move_text_uses_receiver_decimal_convention", "test_unstring_decimal_text_into_numeric_receivers"]}
- {"id": "continued-literal-padding", "component": "cobol_lexer/fixed_format.py; preprocessor.py", "problem": "Espaços até a coluna 72 eram descartados em literais abertos continuados.", "fix": "Frontend habilita preservação de padding; API histórica do lexer mantém seu padrão.", "affected": ["PROG044A"], "regression": ["test_frontend_preserves_literal_spaces_through_column72", "test_legacy_lexer_continuation_api_remains_compatible"]}

O GnuCOBOL é configurado com `-fnot-reserved=ID -freserved=VALUES:VALUE`,
compatibilizando o vocabulário do projeto sem editar os fontes: ID é um nome de campo
e VALUES é aceito como sinônimo de VALUE. Os comandos completos ficam no JSON.
O relógio de referência usa `COB_CURRENT_DATE=2026111712345600`: os dois últimos
dígitos fixam os centésimos, que permaneciam reais com a configuração de 14 dígitos.
Os três casos de ABI têm expectativas binárias completas para ambos os lados;
as diferenças permanecem nos logs e não são contadas como comparações idênticas.
O cenário de divisor zero conserva a expectativa de erro do projeto e não usa o oráculo.

## Reprodução

```bash
python -m tools.auditar_funcional --write
python -m tools.auditar_funcional --officials
python -m tools.auditar_funcional --program PROG036A
python -m tools.auditar_funcional --failed-from docs/auditoria-funcional.json
python -m tools.auditar_funcional --seed 2026
python -m unittest discover -s tests -v
```

GCC/C11 e Python 3.11+ são necessários; GnuCOBOL é opcional (`--no-oracle`).
Filtros não sobrescrevem o relatório integral: `--write` com seleção grava em build/.
O corpus fora da coorte compilada permanece separado no JSON, sem alegação de execução.
