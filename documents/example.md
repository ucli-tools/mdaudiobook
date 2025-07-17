---
# =============================================================================
# COMMON METADATA (used by both mdtexpdf and mdaudiobook)
# =============================================================================
title: "Real and Complex Mathematical Analysis"
author: "Arithmoi Foundation"
date: "May 23, 2025"
description: "A comprehensive guide to real and complex mathematical analysis, covering foundations, sequences, series, continuity, differentiation, integration, and complex function theory."

# =============================================================================
# PDF-SPECIFIC METADATA (mdtexpdf only)
# =============================================================================
# Document structure
format: "book"
section: "foundations"

# Section numbering
no_numbers: true

# Headers and footers
header_footer_policy: "all"
footer: "© 2025 Arithmoi Foundation | arithmoi.org. All rights reserved."
pageof: true
date_footer: "DD/MM/YY"
---

# Real and Complex Mathematical Analysis

# Part 1: Real Analysis

## Chapter 1: Foundations of Real Numbers

### 1.1 The Real Number System

The **real numbers**, denoted by $\mathbb{R}$ (pronounced "R, the set of real numbers"), are a fundamental building block of mathematical analysis. Real numbers include:

- The rational numbers $\mathbb{Q}$ (pronounced "Q, the set of rationals"): numbers that can be written as fractions, $\frac{p}{q}$, where $p$ and $q$ are integers and $q \neq 0$.
- The irrational numbers: numbers that cannot be written as fractions, such as $\sqrt{2}$ and $\pi$ (pronounced "pi").

**Properties of $\mathbb{R}$:**

- **Field properties**: Real numbers can be added, subtracted, multiplied, and divided (except by zero), and these operations satisfy the usual field axioms.
- **Order properties**: The real numbers have a total order; for any $a, b \in \mathbb{R}$, we can say $a < b$, $a = b$, or $a > b$.
- **Completeness**: Every non-empty set of real numbers that is bounded above has a least upper bound (supremum).

### 1.2 The Completeness Axiom

The **completeness axiom** is a defining property of the real numbers. It is what distinguishes $\mathbb{R}$ from $\mathbb{Q}$.

**Completeness Axiom Statement:**

For every non-empty subset $S \subseteq \mathbb{R}$ that is bounded above, there exists a least upper bound (supremum) $s_0 \in \mathbb{R}$ such that:

$$
\forall x \in S, \quad x \leq s_0
$$

and

$$
\forall \epsilon > 0, \quad \exists x_0 \in S \text{ such that } s_0 - \epsilon < x_0 \leq s_0
$$

Here, $\epsilon$ (pronounced "epsilon") is any positive real number, representing an arbitrarily small quantity.

- **Supremum** (least upper bound): The smallest real number that is greater than or equal to every element of $S$.

### 1.3 Order Properties of $\mathbb{R}$

The real numbers are an **ordered field**, which means:

- For any $a, b, c \in \mathbb{R}$:
  - If $a < b$, then $a + c < b + c$
  - If $a < b$ and $c > 0$, then $ac < bc$
  - For any $a \in \mathbb{R}$, exactly one of $a = 0$, $a > 0$, or $a < 0$ is true (trichotomy law)

These properties allow us to compare and manipulate inequalities involving real numbers.

### 1.4 The Archimedean Property and Density of $\mathbb{Q}$

#### Archimedean Property

The **Archimedean property** states that:

For any real number $x$, there exists a natural number $n \in \mathbb{N}$ such that 

$$
n > x
$$

where $\mathbb{N}$ (pronounced "N, the set of natural numbers") is the set $\{1, 2, 3, \dots\}$.

#### Density of $\mathbb{Q}$

The **rational numbers** are **dense** in $\mathbb{R}$. This means:

Between any two real numbers $a$ and $b$ with $a < b$, there exists a rational number $q$ such that

$$
a < q < b
$$

This property is essential for constructing sequences and for approximation arguments in analysis.

### 1.5 Supremum and Infimum (Least Upper and Greatest Lower Bounds)

Given a subset $S \subseteq \mathbb{R}$:

- An **upper bound** for $S$ is any $u \in \mathbb{R}$ such that $x \leq u$ for all $x \in S$.
- The **supremum** (least upper bound), denoted $\sup S$, is the smallest upper bound of $S$.

Similarly:

- A **lower bound** for $S$ is any $l \in \mathbb{R}$ such that $x \geq l$ for all $x \in S$.
- The **infimum** (greatest lower bound), denoted $\inf S$, is the largest lower bound of $S$.

**Formal Definitions:**

Let $S$ be a non-empty subset of $\mathbb{R}$.

- $u$ is an **upper bound** of $S$ if $\forall x \in S, \ x \leq u$.
- $s_0$ is the **supremum** of $S$ if:
  - $s_0$ is an upper bound of $S$
  - For any $\epsilon > 0$, there exists $x_0 \in S$ such that $s_0 - \epsilon < x_0$

The **infimum** is defined analogously.

### 1.6 The Extended Real Number System

The **extended real number system** augments $\mathbb{R}$ with two symbols, $+\infty$ and $-\infty$ (pronounced "plus infinity" and "minus infinity"), to handle limits and unbounded sets.

- The set is denoted $\overline{\mathbb{R}} = \mathbb{R} \cup \{+\infty, -\infty\}$
- For any real $x$:
  - $x < +\infty$
  - $x > -\infty$

**Applications:**

- Useful when working with limits, especially in improper integrals and measures.



#### Exercises

1. Prove that between any two distinct real numbers, there is an irrational number.
2. Show that the set $S = \{x \in \mathbb{Q} : x^2 < 2\}$ is bounded above in $\mathbb{Q}$, but its supremum does not belong to $\mathbb{Q}$.
3. Give an example of a non-empty set $S \subseteq \mathbb{R}$ that is bounded below but does not attain its infimum.
