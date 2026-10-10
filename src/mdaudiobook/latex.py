"""Raw LaTeX in a Markdown book: what pandoc can read, and what is only layout.

Books written for mdtexpdf carry figures, tables and page-layout commands as
raw LaTeX blocks. pandoc's LaTeX reader turns figures and tables into
structure the script can read aloud; these helpers prepare the fragments for
it and recognise the ones that carry nothing to say.
"""
import re

# TeX primitives and commands that only steer the page: nothing to read
LAYOUT_TEX = re.compile(
    r"(\s|\\csname\s*[@A-Za-z]+\s*\\endcsname"
    r"|\\(dimen\d*|ifdim|fi|else|penalty-?\d*|break|newline|begingroup|endgroup|baselineskip|pagegoal|"
    r"pagetotal|advance|relax|hfill|vfil|vfill|linebreak|allowbreak|newpage|clearpage|cleardoublepage|pagebreak|"
    r"noindent|FloatBarrier|medskip|bigskip|smallskip|par|centering|nopagebreak|postdisplaypenalty|vspace\*?|"
    r"hspace\*?|enlargethispage\*?|needspace|thispagestyle|mbox|pagestyle|raggedbottom|flushbottom)"
    r"|\{[^{}]*\}|\[[^]]*\]|[-=<>0-9.a-z*]+)*")

# A wrapper opened in one raw block and closed in another, with ordinary
# Markdown between them: the fragments are layout, the text between is read
WRAPPER_TEX = re.compile(
    r"\s*(\\(par|medskip|bigskip|smallskip|noindent|centering)\s*)*\\(begin|end)\{(minipage|center|samepage|"
    r"flushleft|flushright|adjustwidth|parbox|figure|table|landscape)\}(\{[^}]*\}|\[[^]]*\])*\s*")

DRAWING = re.compile(r"\\begin\{(tikzpicture|pgfpicture|axis|circuitikz)\}|\\includegraphics|\\draw\b")

# A line the book gives as the spoken reading of the equation above it
CENTRED_ITALIC = re.compile(r"^\s*\\begin\{center\}\s*\\textit\{.*\}\s*\\end\{center\}\s*$", re.S)


def is_layout(tex):
    return bool(LAYOUT_TEX.fullmatch(tex.strip()) or WRAPPER_TEX.fullmatch(tex))


def _balanced(s, i):
    """Index just past the {...} group starting at s[i] == '{'."""
    depth = 0
    for j in range(i, len(s)):
        if s[j] == "{":
            depth += 1
        elif s[j] == "}":
            depth -= 1
            if depth == 0:
                return j + 1
    return len(s)


def _column_count(spec):
    spec = re.sub(r"@\{(?:[^{}]|\{[^{}]*\})*\}|!\{(?:[^{}]|\{[^{}]*\})*\}|>\{(?:[^{}]|\{[^{}]*\})*\}|<\{(?:[^{}]|\{[^{}]*\})*\}",
                  "", spec)
    n = 0
    i = 0
    while i < len(spec):
        ch = spec[i]
        if ch == "*" and i + 1 < len(spec) and spec[i + 1] == "{":
            end = _balanced(spec, i + 1)
            count = int(spec[i + 2:end - 1] or 1)
            j = end
            body_end = _balanced(spec, j) if j < len(spec) and spec[j] == "{" else j
            n += count * _column_count(spec[j + 1:body_end - 1])
            i = body_end
            continue
        if ch in "lcrXLCRSJ" or ch.isupper():
            n += 1
            if i + 1 < len(spec) and spec[i + 1] == "{":
                i = _balanced(spec, i + 1)
                continue
        elif ch in "pmb" and i + 1 < len(spec) and spec[i + 1] == "{":
            n += 1
            i = _balanced(spec, i + 1)
            continue
        i += 1
    return n


def prepare(tex):
    """Rewrite a raw LaTeX fragment into what pandoc's LaTeX reader parses.

    Custom column types, spacing and size commands are dropped, every tabular
    gets a plain column specification, and a table captioned with
    \\captionof{table} inside a figure becomes a table with a caption.
    """
    # Page-only wrappers can open in a different Markdown raw block. Drop
    # both ends so a closing wrapper cannot hide the neighbouring prose.
    tex = re.sub(r"\\(?:begin|end)\{samepage\}", "", tex)
    tex = re.sub(r"\\newcolumntype\{.\}(\[\d\])?\{(?:[^{}]|\{(?:[^{}]|\{[^{}]*\})*\})*\}", "", tex)
    tex = re.sub(r"\\renewcommand\{\\arraystretch\}\{[^}]*\}", "", tex)
    tex = re.sub(r"\\noalign\{(?:[^{}]|\{[^{}]*\})*\}", "", tex)
    tex = re.sub(r"\\(tiny|scriptsize|footnotesize|small|normalsize|large|Large|LARGE|huge|Huge|centering)\b", "", tex)
    tex = re.sub(r"\\(vspace|hspace)\*?\{[^}]*\}", "", tex)

    out, pos = [], 0
    for m in re.finditer(r"\\begin\{(tabular\*?|tabularx|longtable)\}", tex):
        if m.start() < pos:
            continue
        i = m.end()
        if m.group(1) in ("tabular*", "tabularx") and i < len(tex) and tex[i] == "{":
            i = _balanced(tex, i)          # width argument
        while i < len(tex) and tex[i] in " \n":
            i += 1
        if i < len(tex) and tex[i] == "[":
            i = tex.index("]", i) + 1
        if i >= len(tex) or tex[i] != "{":
            continue
        end = _balanced(tex, i)
        cols = max(_column_count(tex[i + 1:end - 1]), 1)
        out.append(tex[pos:m.start()] + "\\begin{tabular}{" + "l" * cols + "}")
        pos = end
    tex = "".join(out) + tex[pos:]
    tex = re.sub(r"\\end\{(tabularx|longtable|tabular\*)\}", r"\\end{tabular}", tex)

    if "\\captionof{table}" in tex:
        tex = tex.replace("\\captionof{table}", "\\caption")
        tex = re.sub(r"\\begin\{figure\}(\[[^]]*\])?", r"\\begin{table}", tex)
        tex = tex.replace("\\end{figure}", "\\end{table}")
    tex = tex.replace("\\captionof{figure}", "\\caption")
    return tex


def prepare_math(tex):
    """Rewrite TeX into what pandoc's MathML writer renders.

    Typography that is not spoken goes (bold symbols are the same symbols),
    a degree sign becomes a unit, array column specifications lose the
    spacing directives (@{...}) the MathML converter rejects, and an equation
    set out in one line is no longer a table.
    """
    tex = tex.replace("\n", " ").strip()
    tex = re.sub(r"\\boldsymbol\{((?:[^{}]|\{[^{}]*\})*)\}", r"\1", tex)
    tex = re.sub(r"\\bm\{((?:[^{}]|\{[^{}]*\})*)\}", r"\1", tex)
    tex = re.sub(r"\^\{?\\circ\}?", "°", tex)
    tex = re.sub(r"\\(label|tag)\{[^}]*\}", "", tex)

    def spec(m):
        s = re.sub(r"@\{(?:[^{}]|\{[^{}]*\})*\}", "", m.group(2))
        return m.group(1) + "{" + re.sub(r"\s+", "", s) + "}"
    tex = re.sub(r"(\\begin\{array\})\{((?:[^{}]|\{(?:[^{}]|\{[^{}]*\})*\})*)\}", spec, tex)
    return _flatten_text(_one_line_tables(tex))


# Environments that set an equation out in lines. Word numbers an equation by
# putting it in a one-row equation array, which a conversion hands over as
# \begin{array}{r} ... \end{array}; read as a table it is "1 lines Line 1: ..."
_LINE_ENVS = {"array", "aligned", "alignedat", "gathered", "split", "align", "align*", "alignat", "alignat*",
              "gather", "gather*"}
# What opens a matrix or a vector: a fenced array stays a table
_FENCE = re.compile(r"(\\left\s*(\\[A-Za-z]+|\\.|.)|[(\[|]|\\[{|]|\\(lbrack|lparen|langle|lvert|lVert|vert|Vert|"
                    r"lfloor|lceil))\s*$")
_BEGIN_END = re.compile(r"\\(begin|end)\{([^{}]*)\}")


def _rows(body):
    """A table's rows that are not empty, each a list of its cells: split at
    the table's own row and cell marks, not at those of a table inside it."""
    rows, cells, depth, i, start = [], [], 0, 0, 0
    while i < len(body):
        ch = body[i]
        if depth == 0 and (ch == "&" or body.startswith("\\\\", i)):
            cells.append(body[start:i])
            if ch == "&":
                i += 1
            else:
                rows.append(cells)
                cells = []
                i += 2
                m = re.match(r"\s*\[[^]]*\]", body[i:])       # \\[2pt]
                i += m.end() if m else 0
            start = i
            continue
        if ch == "\\":
            m = re.match(r"\\(begin|end)\{[^{}]*\}", body[i:])
            if m:
                depth += 1 if m.group(1) == "begin" else -1
                i += m.end()
            else:
                i += 2
            continue
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
        i += 1
    rows.append(cells + [body[start:]])
    return [r for r in rows if "".join(r).strip()]


def _one_line_tables(tex):
    """An equation set out in one line is just that line: a one-row table of
    lines becomes a group, so it is spoken as its content. Tables of two or
    more lines, matrices, cases and fenced arrays are kept."""
    out, i = [], 0
    while True:
        m = _BEGIN_END.search(tex, i)
        if not m:
            break
        if m.group(1) == "end":                     # unbalanced: left as it is
            out.append(tex[i:m.end()])
            i = m.end()
            continue
        depth = 0
        for end in _BEGIN_END.finditer(tex, m.start()):
            depth += 1 if end.group(1) == "begin" else -1
            if depth == 0:
                break
        else:
            break
        env, k = m.group(2), m.end()
        if env in ("array", "alignedat", "alignat", "alignat*"):    # column specification
            a = re.match(r"\s*(\[[^]]*\]\s*)?\{", tex[k:end.start()])
            if a:
                k = _balanced(tex, k + a.end() - 1)
        body = _one_line_tables(tex[k:end.start()])
        rows = _rows(body)
        before = "".join(out) + tex[i:m.start()]
        # an array's columns are columns (a row vector), and a fenced array is
        # a matrix; the & of the aligning environments only line rows up
        if (env in _LINE_ENVS and len(rows) <= 1 and "\\hline" not in body
                and not (env == "array" and (rows and len(rows[0]) > 1 or _FENCE.search(before)))):
            line = " ".join(c.strip() for c in rows[0]) if rows else ""
            out.append(tex[i:m.start()] + "{" + line.strip() + "}")
        else:
            out.append(tex[i:k] + body + end.group(0))
        i = end.end()
    return "".join(out) + tex[i:]


_FONT = re.compile(r"\\(textit|textbf|textrm|textsf|texttt|textup|textsl|emph)\{")


def _flatten_text(tex):
    """Font commands inside \\text{...} are dropped (the converter rejects
    nested text); outside it, a font command's content becomes \\text{...}."""
    out, i = [], 0
    while True:
        m = re.search(r"\\text\{", tex[i:])
        if not m:
            break
        start = i + m.end() - 1
        end = _balanced(tex, start)
        inner = tex[start + 1:end - 1]
        while True:
            f = _FONT.search(inner)
            if not f:
                break
            b = _balanced(inner, f.end() - 1)
            inner = inner[:f.start()] + inner[f.end():b - 1] + inner[b:]
        out.append(tex[i:i + m.start()] + "\\text{" + inner + "}")
        i = end
    tex = "".join(out) + tex[i:]
    return _FONT.sub(lambda m: "\\text{", tex)
