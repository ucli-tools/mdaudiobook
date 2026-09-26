---
title: "A Small Book of Circles"
subtitle: "An Example for mdaudiobook"
author: "Jane Doe"
date: "2026"
audiobook:
  voice: am_michael
  lexicon: example_lexicon.yaml
  equation_readings: after
---

# Part One: Circles

## Chapter 1: The Unit Circle

A circle of radius one, drawn around the origin, holds every point $(x, y)$ with $x^2 + y^2 = 1$. The Greek word for a circle's measure, μέτρον, gave us "metre", e.g. in geometry.[^1] Euler found the circle inside the exponential function.

[^1]: The word is also the root of "symmetry".

$$e^{i\theta} = \cos\theta + i\sin\theta$$

```{=latex}
\begin{center}\textit{\(e\) to the \(i\) theta equals cosine theta plus \(i\) sine theta.}\end{center}
```

$$\sum_{n=1}^{\infty} \frac{1}{n^2} = \frac{\pi^2}{6}$$

```{=latex}
\begin{figure}[H]
\centering
\begin{tikzpicture}[scale=2]
  \draw (0,0) circle (1);
  \fill (1,0) circle (1pt) node[right] {$1$};
\end{tikzpicture}
\caption[The unit circle]{The unit circle. Every point on it is one unit from the centre.}
\end{figure}
```

```{=latex}
\newpage
```

### Angles

An angle of $180^\circ$ is half a turn, as the table shows.

```{=latex}
\begin{table}[H]
\centering
\newcolumntype{R}[1]{>{\raggedright\arraybackslash\hspace{0pt}}p{#1}}
\begin{tabular}{R{2cm} R{3cm}}
\hline
\textbf{Angle} & \textbf{Fraction of a turn} \\
\hline
\noalign{\vskip 3pt}
90 degrees & a quarter \\
180 degrees & a half \\
\hline
\end{tabular}
\caption{Angles as fractions of a turn.}
\end{table}
```

## Chapter 2: Counting

Ancient scribes wrote numbers with marks. A wedge [𒁹]{speak=""} stood for one, as the chart shows.

::: {.print-only speak="Written in wedges, one to three are one, two and three vertical wedges."}
```{=latex}
\begin{center}
\begin{tabular}{cc}
1 & 𒁹 \\
2 & 𒁹𒁹 \\
3 & 𒁹𒁹𒁹 \\
\end{tabular}
\end{center}
```
:::

| Number | Name |
|--------|------|
| 1      | one  |
| 2      | two  |

```{=latex}
\begin{center}
\begin{tikzpicture}
  \draw (0,0) -- (1,1);
\end{tikzpicture}
\end{center}
```

```python
print("not read aloud")
```

The circle, said Hegel, returns into itself.
