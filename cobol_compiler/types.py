"""Tipos lógicos e ABI de armazenamento do projeto (sem valores de runtime)."""

from dataclasses import dataclass
import re


@dataclass(frozen=True, slots=True)
class CobolType:
    category: str
    length: int | None = None
    precision: int | None = None
    scale: int | None = None
    signed: bool = False
    edited: bool = False
    usage: str = "DISPLAY"
    picture: str | None = None
    expanded_picture: str | None = None
    decimal_point: str = "."
    representation: str = "bytes"

    @property
    def numeric(self):
        return self.category in {"numeric", "index"}

    @property
    def textual(self):
        return self.category in {"alphanumeric", "alphabetic", "numeric-edited", "group"}

    @property
    def integral(self):
        return self.numeric and self.scale == 0


ERROR = CobolType("error")
BOOLEAN = CobolType("boolean")
INDEX = CobolType("index", 8, 18, 0, True, usage="INDEX", representation="binary-le")


class PictureError(ValueError):
    pass


def parse_picture(mask, usage="DISPLAY", *, decimal_comma=False, allow_floating=False):
    """Interpreta PIC; limita expansão para não alocar a partir de fonte hostil."""
    usage = {"COMPUTATIONAL": "COMP", "BINARY": "COMP", "COMP-4": "COMP",
             "PACKED-DECIMAL": "COMP-3"}.get(usage, usage)
    parts = []
    pos = 0
    for match in re.finditer(r"([AX9SVZ+\-.,0B/*$])(?:\(([0-9]+)\))?", mask.upper()):
        if match.start() != pos:
            raise PictureError("Símbolo ou repetição inválida em PIC.")
        count = int(match[2] or 1)
        if not 1 <= count <= 100000 or sum(map(len, parts)) + count > 100000:
            raise PictureError("PIC excede o limite de 100000 posições do front-end.")
        parts.append(match[1] * count)
        pos = match.end()
    if pos != len(mask) or not parts:
        raise PictureError("Máscara PIC vazia ou inválida.")
    pic = "".join(parts)
    decimal = "," if decimal_comma else "."
    separator = "." if decimal_comma else ","
    if "X" in pic or "A" in pic:
        if set(pic) <= {"A"}:
            category = "alphabetic"
        elif set(pic) <= {"X", "A", "9"} and "X" in pic:
            category = "alphanumeric"
        else:
            raise PictureError("PIC alfanumérico combina símbolos incompatíveis.")
        if usage != "DISPLAY":
            raise PictureError("PIC textual requer USAGE DISPLAY.")
        return CobolType(category, len(pic), picture=mask, expanded_picture=pic, decimal_point=decimal)
    repeated = next((c for c in '+-' if pic.count(c)>1), None)
    if repeated:
        prefix=pic[:pic.rfind(repeated)+1]
        if (not allow_floating or set(pic)&set('Z*$') or set(prefix)-{repeated,separator}
                or any(c in pic for c in '+-' if c!=repeated)):
            raise PictureError('Edição flutuante exige sequência inicial de um único sinal, sem Z, * ou moeda.')
    digits = sum(pic.count(c) for c in "9Z*") + (pic.count(repeated)-1 if repeated else 0)
    if not digits:
        raise PictureError("PIC numérico sem posição de dígito.")
    if pic.count("S") > 1 or ("S" in pic and not pic.startswith("S")) or pic.count("V") > 1:
        raise PictureError("S deve ser único e inicial; V deve ser único.")
    if pic.count(decimal) > 1 or ("V" in pic and decimal in pic):
        raise PictureError("Mais de um ponto decimal em PIC.")
    edited = bool(set(pic) - {"S", "9", "V"})
    if (pic.count("+") + pic.count("-") > 1 and not repeated) or pic.count("$") > 1:
        raise PictureError("Edição flutuante com sinais/moedas repetidos fora do subconjunto.")
    if "S" in pic and edited:
        raise PictureError("S não pode combinar com edição numérica.")
    point = pic.find("V") if "V" in pic else pic.find(decimal)
    scale = sum(c in "9Z*" for c in pic[point+1:]) if point >= 0 else 0
    if point >= 0 and separator in pic[point+1:]:
        raise PictureError("Separador de milhares após o decimal.")
    length = len(pic) - pic.count("S") - pic.count("V")
    representation = "display-overpunch" if "S" in pic else "display-digits"
    if usage in {"COMP", "COMP-5"}:
        if edited:
            raise PictureError("COMP não admite PIC editado.")
        # Larguras fixas, independente do sizeof(long) do host. Acima de 18,
        # largura mínima capaz de representar todos os dígitos, com bit de sinal.
        length = 2 if digits <= 4 else 4 if digits <= 9 else 8 if digits <= 18 else ((10**digits-1).bit_length()+1+7)//8
        representation = "binary-le"
    elif usage == "COMP-3":
        if edited:
            raise PictureError("COMP-3 não admite PIC editado.")
        length = (digits + 2)//2
        representation = "packed-decimal"
    elif usage != "DISPLAY":
        raise PictureError(f"USAGE {usage} não suportado com PIC neste subconjunto.")
    return CobolType("numeric-edited" if edited else "numeric", length, digits, scale,
                     any(c in pic for c in "S+-"), edited, usage, mask, pic, decimal, representation)


def numeric_type(precision=None, scale=0, signed=True):
    return CobolType("numeric", precision=precision, scale=scale, signed=signed,
                     representation="exact-decimal" if scale is not None else "exact-rational")


def arithmetic_type(operator, left, right):
    if operator in {"/", "**"} or None in (left.precision, right.precision, left.scale, right.scale):
        return numeric_type(scale=None)
    if operator == "*":
        return numeric_type(left.precision+right.precision, left.scale+right.scale)
    scale = max(left.scale, right.scale)
    return numeric_type(max(left.precision-left.scale, right.precision-right.scale)+scale+1, scale)
