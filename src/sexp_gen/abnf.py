"""
Helper module for generating strategies for the ABNF rules defined in RFC 9804.

Through this module we can effectively implement the ABNF rules as strategies,
which are then used in the testing framework.

This ensures that any valid S-expression can be generated and tested against the
rules defined in the ABNF grammar.

This file is structured in the same order as ./docs/rfc9804/sexp_abnf, where
each rule is implemented as a strategy.
"""

from hypothesis import strategies as st

# sp             =  %x20   ; space
sp = st.just(" ")

# htab           =  %x09   ; horizontal tab
htab = st.just("\t")

# cr             =  %x0D   ; carriage return
cr = st.just("\r")

# lf             =  %x0A   ; line feed
lf = st.just("\n")

# digit          =  %x30-39 ; 0-9
digit = st.from_regex(r"[0-9]", fullmatch=True)

# alpha          =  %x41-5A / %x61-7A ; ; A-Z / a-z
alpha = st.from_regex(r"[a-zA-Z]", fullmatch=True)

# hexdig         =  digit / %x41-46 / %x61-66 ; 0-9 / A-F / a-f
hexdig = st.from_regex(r"[0-9a-fA-F]", fullmatch=True)

# octet          =  %x00-FF ; any octet
octet = st.binary(min_size=1, max_size=1)

# dquote         =  %x22   ; double quote
dquote = st.just('"')

# vtab           =  %x0B   ; vertical tab
vtab = st.just("\v")

# ff             =  %x0C   ; form feed
ff = st.just("\f")

# whitespace     =  sp / htab / vtab / cr / lf / ff
whitespace = st.from_regex(r"[\s]", fullmatch=True)

# decimal        =  %x30 / (%x31-39 *digit)
decimal = st.integers(min_value=0).map(str)

# verbatim       =  decimal ":" *octet
verbatim = st.binary().map(lambda b: f"{len(b)}:{b.decode('latin-1')}")

# printable      =  %x20-21 / %x23-5B / %x5D-7E
printable = st.one_of(
    st.characters(min_codepoint=0x20, max_codepoint=0x21),
    st.characters(min_codepoint=0x23, max_codepoint=0x5B),
    st.characters(min_codepoint=0x5D, max_codepoint=0x7E),
)

# backslash      =  %x5C
backslash = st.just("\\")

# question-mark  =  %x3F   ; question mark
question_mark = st.just("?")

# a              =  %x61   ; lowercase a
a = st.just("a")

# b              =  %x62   ; lowercase b
b = st.just("b")

# f              =  %x66   ; lowercase f
f = st.just("f")

# n              =  %x6E   ; lowercase n
n = st.just("n")

# r              =  %x72   ; lowercase r
r = st.just("r")

# t              =  %x74   ; lowercase t
t = st.just("t")

# v              =  %x76   ; lowercase v
v = st.just("v")

# quote          =  %x27   ; single quote
quote = st.just("'")

# zero-to-seven  =  %x30-37 ; 0-7
zero_to_seven = st.from_regex(r"[0-7]", fullmatch=True)

# x              =  %x78   ; lowercase x
x = st.just("x")

# escaped        =  backslash (question-mark / a / b / f / n / r / t / v / dquote / quote / backslash / 3(zero-to-seven) / (x 2hexdig) / cr / lf / (cr lf) / (lf cr))
escaped = st.one_of(
    st.builds(
        lambda b, c: f"{b}{c}",
        b=backslash,
        c=st.one_of(
            question_mark,
            a,
            b,
            f,
            n,
            r,
            t,
            v,
            dquote,
            quote,
            backslash,
            cr,
            lf,
        ),
    ),
    st.builds(
        lambda b, d: f"{b}{''.join(d)}",
        b=backslash,
        d=st.lists(zero_to_seven, min_size=3, max_size=3),
    ),
    st.builds(
        lambda b, c, d: f"{b}{c}{''.join(d)}",
        b=backslash,
        c=x,
        d=st.lists(hexdig, min_size=2, max_size=2),
    ),
    st.builds(lambda b, c1, c2: f"{b}{c1}{c2}", b=backslash, c1=cr, c2=lf),
    st.builds(lambda b, c1, c2: f"{b}{c1}{c2}", b=backslash, c1=lf, c2=cr),
)

# quoted-string  =  [decimal] dquote *(printable / escaped) dquote
quoted_string = st.builds(
    lambda d, c, q1, q2: f"{d or ''}{q1}{''.join(c)}{q2}",
    d=st.one_of(st.none(), decimal),
    c=st.lists(st.one_of(printable, escaped)),
    q1=dquote,
    q2=dquote,
)

# simple-punc    =  "-" / "." / "/" / "_" / ":" / "*" / "+" / "="
simple_punc = st.sampled_from("-./_:*+=")

# token          =  (alpha / simple-punc) *(alpha / digit / simple-punc)
token = st.from_regex(r"([a-zA-Z-./_:*+=])([a-zA-Z0-9-./_:*+=]*)", fullmatch=True)

# hexadecimals   =  2(hexdig *whitespace)
hexadecimals = st.builds(
    lambda h1, w1, h2, w2: f"{h1}{''.join(w1)}{h2}{''.join(w2)}",
    h1=hexdig,
    w1=st.lists(whitespace),
    h2=hexdig,
    w2=st.lists(whitespace),
)

# hexadecimal    =  [decimal] "#" *whitespace *hexadecimals "#"
hexadecimal = st.builds(
    lambda d, w1, h, w2: f"{d or ''}#{''.join(w1)}{''.join(h)}#{''.join(w2)}",
    d=st.one_of(st.none(), decimal),
    w1=st.lists(whitespace),
    h=st.lists(hexadecimals),
    w2=st.lists(whitespace),
)

# base-64-char   =  alpha / digit / "+" / "/"
base_64_char = st.from_regex(r"[a-zA-Z0-9+/]", fullmatch=True)

# base-64-chars  =  4(base-64-char *whitespace)
base_64_chars = st.builds(
    lambda c, w: "".join(f"{ci}{''.join(wi)}" for ci, wi in zip(c, w)),
    c=st.lists(base_64_char, min_size=4, max_size=4),
    w=st.lists(st.lists(whitespace), min_size=4, max_size=4),
)

# base-64-end    =  base-64-chars / 3(base-64-char *whitespace) ["=" *whitespace] / 2(base-64-char *whitespace) *2("=" *whitespace)
base_64_end = st.one_of(
    base_64_chars,
    st.builds(
        lambda c, w, eq, we: "{}{}{}".format(
            "".join(f"{ci}{''.join(wi)}" for ci, wi in zip(c, w)),
            eq or "",
            "".join(we or []),
        ),
        c=st.lists(base_64_char, min_size=3, max_size=3),
        w=st.lists(st.lists(whitespace), min_size=3, max_size=3),
        eq=st.one_of(st.none(), st.just("=")),
        we=st.one_of(st.none(), st.lists(whitespace)),
    ),
    st.builds(
        lambda c, w, eq, we: "{}{}".format(
            "".join(f"{ci}{''.join(wi)}" for ci, wi in zip(c, w)),
            "".join(f"{eqi}{''.join(wei)}" for eqi, wei in zip(eq, we)),
        ),
        c=st.lists(base_64_char, min_size=2, max_size=2),
        w=st.lists(st.lists(whitespace), min_size=2, max_size=2),
        eq=st.lists(st.just("="), min_size=0, max_size=2),
        we=st.lists(st.lists(whitespace), min_size=0, max_size=2),
    ),
)

# base-64        =  [decimal] "|" *whitespace *base-64-chars [base-64-end] "|"
base_64 = st.builds(
    lambda content, with_prefix: (f"{len(content)}" if with_prefix else "")
    + f"|{content}|",
    content=st.builds(
        lambda w1, c, e: f"{''.join(w1)}{''.join(c)}{e or ''}",
        w1=st.lists(whitespace),
        c=st.lists(base_64_chars),
        e=st.one_of(st.none(), base_64_end),
    ),
    with_prefix=st.booleans(),
)

# simple-string  =  verbatim / quoted-string / token / hexadecimal / base-64
simple_string = st.one_of(verbatim, quoted_string, token, hexadecimal, base_64)

# display        =  "[" *whitespace simple-string *whitespace "]" *whitespace
display = st.builds(
    lambda w1, s, w2, w3: f"[{''.join(w1)}{s}{''.join(w2)}]{''.join(w3)}",
    w1=st.lists(whitespace),
    s=simple_string,
    w2=st.lists(whitespace),
    w3=st.lists(whitespace),
)

# string         =  [display] simple-string
string = st.builds(
    lambda d, s: f"{d or ''}{s}",
    d=st.one_of(st.none(), display),
    s=simple_string,
)

# value          =  string / ("(" *(value / whitespace) ")")
value = st.deferred(
    lambda: st.one_of(
        string,
        st.builds(
            lambda items: f"({''.join(items)})",
            st.lists(st.one_of(value, whitespace)),
        ),
    )
)

# sexp           =  *whitespace value *whitespace
sexp = st.builds(
    lambda w1, v, w2: f"{''.join(w1)}{v}{''.join(w2)}",
    w1=st.lists(whitespace),
    v=value,
    w2=st.lists(whitespace),
)
