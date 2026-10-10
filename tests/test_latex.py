from mdaudiobook import latex


def test_layout_fragments_are_recognised():
    for tex in [r"\newpage", r"\nopagebreak[4]", r"\ifdim\dimen0>\dimen2 \ifdim\dimen2>0pt \vfil\fi",
                r"\noindent\begin{minipage}{\textwidth}", r"\end{minipage}", r"\vspace{2em}",
                r"\par\medskip\noindent\begin{minipage}{\textwidth}",
                r"\begingroup\postdisplaypenalty=10000 \csname @beginparpenalty\endcsname=10000"]:
        assert latex.is_layout(tex), tex


def test_content_is_not_layout():
    assert not latex.is_layout(r"\begin{center}\textit{hello}\end{center}")
    assert not latex.is_layout(r"\begin{tabular}{cc} a & b \end{tabular}")


def test_custom_columns_become_plain():
    tex = (r"\newcolumntype{R}[1]{>{\raggedright\arraybackslash\hspace{0pt}}p{#1}}"
           r"\begin{tabular}{R{2cm} R{3cm}|p{1cm}c@{\quad}l} x \end{tabular}")
    out = latex.prepare(tex)
    assert r"\begin{tabular}{lllll}" in out
    assert "newcolumntype" not in out


def test_captionof_table_becomes_a_table():
    tex = r"\begin{figure}[H]\begin{tabular}{cc}a&b\end{tabular}\captionof{table}{Two things.}\end{figure}"
    out = latex.prepare(tex)
    assert r"\begin{table}" in out and r"\caption{Two things.}" in out and "figure" not in out


def test_math_preparation():
    assert latex.prepare_math(r"\boldsymbol{e}^{i\pi}") == r"e^{i\pi}"
    assert latex.prepare_math(r"180^\circ") == "180°"
    assert latex.prepare_math(r"\begin{array}{c c|c@{\quad}c} a & b & c & d \\ e & f & g & h \end{array}") == \
        r"\begin{array}{cc|cc} a & b & c & d \\ e & f & g & h \end{array}"
    assert latex.prepare_math(r"\text{synthetic \textit{a posteriori}}") == r"\text{synthetic a posteriori}"
    assert latex.prepare_math(r"\textbf{x} + 1") == r"\text{x} + 1"


def test_an_equation_in_one_line_is_not_a_table():
    # Word numbers an equation by putting it in a one-row equation array
    assert latex.prepare_math("\\begin{array}{r}\nx^{2} + y^{2} = r,\n\\end{array} \\tag{1.3}").strip() == \
        r"{x^{2} + y^{2} = r,}"
    assert latex.prepare_math(r"\cosh^{2}\begin{array}{r} (u) - \sinh^{2}(u) = 1. \end{array}") == \
        r"\cosh^{2}{(u) - \sinh^{2}(u) = 1.}"
    assert latex.prepare_math(r"\begin{array}{r} \begin{array}{r} a = b \end{array} \end{array}") == r"{{a = b}}"
    assert latex.prepare_math(r"\begin{array}{r} a = b, \\ \end{array}") == r"{a = b,}"
    assert latex.prepare_math(r"\begin{aligned} x &= 1 \end{aligned}") == r"{x = 1}"
    assert latex.prepare_math(r"\begin{array}{r} \left\lbrack\begin{matrix} 1 & 0 \\ 0 & 1 \end{matrix}\right\rbrack = I "
                              r"\end{array}") == r"{\left\lbrack\begin{matrix} 1 & 0 \\ 0 & 1 \end{matrix}\right\rbrack = I}"


def test_tables_that_are_tables_stay():
    for tex in [r"\begin{array}{r} a = b, \\ c = d. \end{array}",          # two lines
                r"\begin{aligned} x &= a \\ &= b \end{aligned}",
                r"\left(\begin{array}{c} x \end{array}\right)",            # fenced: a matrix
                r"\left(\begin{array}{ccc} 1 & 2 & 3 \end{array}\right)",  # a row vector
                r"\begin{array}{ccc} 1 & 2 & 3 \end{array}",
                r"\begin{pmatrix} x \end{pmatrix}",
                r"\begin{cases} 1 & x > 0 \end{cases}",
                r"\begin{array}{|c|} \hline x \\ \hline \end{array}"]:
        assert latex.prepare_math(tex) == tex, tex


def test_a_continued_line_starts_with_the_word_plus():
    assert latex.prepare_math(r"\begin{array}{r} a = b + c \\ + d + e \end{array}") == \
        r"\begin{array}{r} a = b + c \\ \text{plus } d + e \end{array}"
    assert latex.prepare_math(r"\begin{aligned} a &= b \\ & + c \end{aligned}") == \
        r"\begin{aligned} a &= b \\ & \text{plus } c \end{aligned}"
    assert latex.prepare_math(r"\begin{array}{r} a = b \\ \ + c \end{array}") == \
        r"\begin{array}{r} a = b \\ \ \text{plus } c \end{array}"
    for tex in [r"\left(\begin{array}{r} a \\ + b \end{array}\right)",     # a vector's entry: a sign
                r"\begin{array}{cc} 1 & 0 \\ +1 & 2 \end{array}",          # a grid
                r"\begin{array}{r} + a \\ b \end{array}",                   # the first line
                r"\begin{pmatrix} a \\ + b \end{pmatrix}"]:
        assert latex.prepare_math(tex) == tex, tex


def test_sentence_punctuation_at_the_end_of_mathematics():
    tp = latex.trailing_punctuation
    assert tp("x = 1,") == ("x = 1", ",")
    assert tp("x = 1.") == ("x = 1", ".")
    assert tp("x = 1;") == ("x = 1", ";")
    assert tp(r"{\cos^{2}{(a) = \rho}},} ") == (r"{\cos^{2}{(a) = \rho}}}", ",")
    assert tp(r"\begin{array}{r} a = b, \\ c = d. \\ \end{array}") == \
        (r"\begin{array}{r} a = b, \\ c = d \\ \end{array}", ".")
    assert tp(r"x = 1, \quad") == ("x = 1", ",")
    assert tp(r"x \ldots.") == (r"x \ldots", ".")
    for tex in [r"f(x, y)", r"1, 2, ...", r"\left\{ x \right.", r"\left. x \right|", "0.5", ",", "{,}", r"\{1, 2\}"]:
        assert tp(tex) == (tex, ""), tex
