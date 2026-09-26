from mdaudiobook import latex


def test_layout_fragments_are_recognised():
    for tex in [r"\newpage", r"\nopagebreak[4]", r"\ifdim\dimen0>\dimen2 \ifdim\dimen2>0pt \vfil\fi",
                r"\noindent\begin{minipage}{\textwidth}", r"\end{minipage}", r"\vspace{2em}",
                r"\par\medskip\noindent\begin{minipage}{\textwidth}"]:
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
    assert latex.prepare_math(r"\begin{array}{c c|c@{\quad}c} a \end{array}") == r"\begin{array}{cc|cc} a \end{array}"
    assert latex.prepare_math(r"\text{synthetic \textit{a posteriori}}") == r"\text{synthetic a posteriori}"
    assert latex.prepare_math(r"\textbf{x} + 1") == r"\text{x} + 1"
