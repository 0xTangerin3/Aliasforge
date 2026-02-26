#!/usr/bin/env python3
"""
AliasForge
Generates username combinations based on naming style (Chinese / Western).
Based on OSINT / username enumeration techniques.

Design decisions:
  - ALL output is lowercase only
  - Only "." is used as a separator  (Gmail-safe; "_" and "-" excluded)
  - Chinese: full given name (taiman) used as a unit — never split into syllables
  - Reversed names excluded
  - Length window: 6–16 characters (outside range filtered out)
  - Month-only date suffixes excluded (e.g. tommy10); mmdd (1015) and yy/yyyy are fine
"""

import argparse

MIN_LEN = 6
MAX_LEN_CN = 16   # Chinese usernames — shorter names, tighter cap
MAX_LEN_EN = 18   # Western usernames — longer names need more room


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def ini(s: str) -> str:
    return s[0].lower() if s else ""

def low(s: str) -> str:
    return s.lower()

def trim(lst: list, maxlen: int = MAX_LEN_CN) -> list:
    """Dedupe, enforce length window, preserve order."""
    seen, result = set(), []
    for x in lst:
        x = x.strip()
        if x and MIN_LEN <= len(x) <= maxlen and x not in seen:
            seen.add(x)
            result.append(x)
    return result

def parse_dates(year: str = "", dob: str = "") -> tuple:
    """
    Returns (yr4, yr2, dy2, md).
    Month-only token deliberately excluded.
    e.g. dob="2001/10/15" -> yr4="2001" yr2="01" dy2="15" md="1015"
    """
    yr4 = yr2 = dy2 = md = ""
    if year:
        yr4 = year.strip()[-4:]
        yr2 = yr4[-2:]
    if dob:
        parts = dob.strip().replace("-", "/").split("/")
        if len(parts) == 3:
            if not yr4:
                yr4 = parts[0]
                yr2 = yr4[-2:]
            mo  = parts[1].zfill(2)
            dy  = parts[2].zfill(2)
            dy2 = dy[-2:]
            md  = mo + dy
    return yr4, yr2, dy2, md


# ─────────────────────────────────────────────────────────────────────────────
# Chinese name generator
# ─────────────────────────────────────────────────────────────────────────────

def generate_chinese(
    last:   str,          # surname / family name  -> chan
    first:  str,          # given name(s)          -> "tai man"
    alias:  str = "",     # english / alias name   -> tommy
    alias2: str = "",
    year:   str = "",
    dob:    str = "",
    full:   bool = False,
) -> list:
    """
    Chinese naming logic  (lowercase · dot-only · 6-16 chars)
    ----------------------------------------------------------
    Structure: [Surname] [Given1] [Given2]  e.g. chan tai man  (+alias tommy)

    Tokens:
      s        = chan        surname
      g        = taiman      full given name (g1+g2 concatenated, NEVER split)
      si       = c           surname initial
      gi       = tm          given initials  (t+m)
      init_sg  = ctm         surname initial + given initials
      a        = tommy       english alias
      ai       = t           alias initial

    Three first-class body tokens — each gets full date/initial/surname treatment:
      a   = tommy   (alias / English name)
      g   = taiman  (full given name, g1+g2 joined)
      g2  = man     (3rd word / 2nd given syllable — many users anchor on this alone)

    Priority tiers:
      TIER 1  alias alone + date/initial combos
                tommy2001  tommy01  tommy1015  tommy15  tommy1501
                tommyc  tc  tctm  t.chan
      TIER 2  alias + given  +  alias + given + date
                tommytaiman  tommy.taiman  tommytaiman01  tommytaiman1015
      TIER 3  alias + init_sg  (very common!)
                tommyctm  tommy.ctm  tommyctm01  tommyctm1015
      TIER 4  alias + surname
                tommychan  tommy.chan  tommychan01
      TIER 5  g2 (3rd word) alone + date/initial  — same depth as alias
                man2001  man01  man1015  man15  man1501
                manc  man.c  c.man
      TIER 6  g2 + given / g2 + init_sg / g2 + surname
                mantaiman  man.taiman  manctm  man.ctm  manchan  man.chan
                manctm01  man.chan1015  man.ctm15
      TIER 7  given + surname-initial  +  given + si + date
                taimanc  taiman.c  taimanc01  taimanc1015  taimanc15
      TIER 8  given + date
                taiman2001  taiman01  taiman1015  taiman15
      TIER 9  surname + given-initials only  (NO bare s+date)
                chantm  ctm  chantm01  ctm1015
      TIER 10 full surname combos  (light in DEFAULT)
                chantaiman  taimanchan
    """
    s  = low(last.strip())
    a  = low(alias.strip())  if alias  else ""
    a2 = low(alias2.strip()) if alias2 else ""

    gparts = low(first.strip()).split()
    g1 = gparts[0] if len(gparts) >= 1 else ""   # tai
    g2 = gparts[1] if len(gparts) >= 2 else ""   # man  ← first-class body token
    g  = g1 + g2                                  # taiman

    si  = ini(s)                    # c
    g1i = ini(g1)                   # t
    g2i = ini(g2) if g2 else ""     # m
    gi  = g1i + g2i                 # tm
    ai  = ini(a) if a else ""       # t

    init_sg  = si + gi              # ctm
    init_as  = ai + si if ai else ""     # tc
    init_asg = ai + init_sg if ai else ""  # tctm

    yr4, yr2, dy2, md = parse_dates(year, dob)
    # date suffix list — no month-only
    dates = [x for x in [yr4, yr2, md, dy2] if x]

    combos = []

    # ══════════════════════════════════════════════════════════════════════════
    # TIER 1 – alias alone + quick initial combos
    # ══════════════════════════════════════════════════════════════════════════
    if a:
        # alias + date (all variants)
        for d in dates:
            combos += [a + d]                       # tommy2001 / tommy01 / tommy1015 / tommy15

        # day+year flip  e.g. tommy1501
        if dy2 and yr2:
            combos += [a + dy2 + yr2]               # tommy1501

        # alias + surname-initial
        combos += [
            a + si,                                  # tommyc
            a + "." + si,                            # tommy.c
            si + "." + a,                            # c.tommy
        ]

        # alias initials combos
        combos += [
            init_as,                                 # tc
            init_asg,                                # tctm
            ai + "." + s,                            # t.chan
        ]

    # ══════════════════════════════════════════════════════════════════════════
    # TIER 2 – alias + full given  +  alias + given + date
    # ══════════════════════════════════════════════════════════════════════════
    if a:
        combos += [
            a + g,                                   # tommytaiman
            a + "." + g,                             # tommy.taiman
            g + "." + a,                             # taiman.tommy
        ]
        for d in dates:
            combos += [
                a + g + d,                           # tommytaiman2001 / ...01 / ...1015 / ...15
                a + "." + g + d,                     # tommy.taiman01
            ]

    # ══════════════════════════════════════════════════════════════════════════
    # TIER 3 – alias + init_sg  (tommyctm pattern — very common!)
    # ══════════════════════════════════════════════════════════════════════════
    if a:
        combos += [
            a + init_sg,                             # tommyctm  ← explicitly requested
            a + "." + init_sg,                       # tommy.ctm
            init_sg + "." + a,                       # ctm.tommy
        ]
        for d in dates:
            combos += [
                a + init_sg + d,                     # tommyctm2001 / ...01 / ...1015 / ...15
                a + "." + init_sg + d,               # tommy.ctm01
            ]

    # ══════════════════════════════════════════════════════════════════════════
    # TIER 4 – alias + surname
    # ══════════════════════════════════════════════════════════════════════════
    if a:
        combos += [
            a + s,                                   # tommychan
            a + "." + s,                             # tommy.chan
            s + "." + a,                             # chan.tommy
        ]
        for d in dates:
            combos += [
                a + s + d,                           # tommychan2001 / ...01 / ...1015 / ...15
                a + "." + s + d,                     # tommy.chan01
            ]

    # ══════════════════════════════════════════════════════════════════════════
    # TIER 5 – g2 (3rd word) alone + date/initial  — same depth as alias
    # ══════════════════════════════════════════════════════════════════════════
    if g2:
        for d in dates:
            combos += [g2 + d]                       # man2001  man01  man1015  man15
        if dy2 and yr2:
            combos += [g2 + dy2 + yr2]               # man1501
        combos += [
            g2 + si,                                 # manc
            g2 + "." + si,                           # man.c
            si + "." + g2,                           # c.man
        ]
        for d in dates:
            combos += [
                g2 + si + d,                         # manc2001  manc01  manc1015  manc15
                g2 + "." + si + d,                   # man.c01  man.c1015
            ]

    # ══════════════════════════════════════════════════════════════════════════
    # TIER 6 – g2 + given / g2 + init_sg / g2 + surname
    # ══════════════════════════════════════════════════════════════════════════
    if g2:
        # g2 + full given
        combos += [
            g2 + g,                                  # mantaiman
            g2 + "." + g,                            # man.taiman
        ]
        for d in dates:
            combos += [g2 + g + d, g2 + "." + g + d]   # mantaiman01  man.taiman1015

        # g2 + init_sg
        combos += [
            g2 + init_sg,                            # manctm
            g2 + "." + init_sg,                      # man.ctm
            init_sg + "." + g2,                      # ctm.man
        ]
        for d in dates:
            combos += [
                g2 + init_sg + d,                    # manctm01  manctm1015  manctm15
                g2 + "." + init_sg + d,              # man.ctm01  man.ctm1015
            ]

        # g2 + surname
        combos += [
            g2 + s,                                  # manchan
            g2 + "." + s,                            # man.chan
            s + "." + g2,                            # chan.man
        ]
        for d in dates:
            combos += [
                g2 + s + d,                          # manchan01  manchan1015  manchan15
                g2 + "." + s + d,                    # man.chan01  man.chan1015
            ]

    # ══════════════════════════════════════════════════════════════════════════
    # TIER 7 – given + surname-initial  +  given + si + date
    # ══════════════════════════════════════════════════════════════════════════
    combos += [
        g + si,                                      # taimanc
        g + "." + si,                                # taiman.c
        si + "." + g,                                # c.taiman
    ]
    for d in dates:
        combos += [
            g + si + d,                              # taimanc2001  taimanc01  taimanc1015
            g + "." + si + d,                        # taiman.c01
        ]

    # ══════════════════════════════════════════════════════════════════════════
    # TIER 8 – given + date
    # ══════════════════════════════════════════════════════════════════════════
    for d in dates:
        combos += [g + d]                            # taiman2001  taiman01  taiman1015  taiman15

    # ══════════════════════════════════════════════════════════════════════════
    # TIER 9 – surname + given-initials only  (NO bare s+date)
    # ══════════════════════════════════════════════════════════════════════════
    combos += [
        s + gi,                                      # chantm
        init_sg,                                     # ctm
        s + "." + gi,                                # chan.tm
    ]
    for d in dates:
        combos += [
            s + gi + d,                              # chantm2001  chantm01  chantm1015
            init_sg + d,                             # ctm2001  ctm01  ctm1015  ctm15
        ]

    # ══════════════════════════════════════════════════════════════════════════
    # TIER 10 – full surname combos (light in DEFAULT)
    # ══════════════════════════════════════════════════════════════════════════
    combos += [
        s + g,                                       # chantaiman
        g + s,                                       # taimanchan
    ]

    # ── ALIAS2 ────────────────────────────────────────────────────────────────
    if a2:
        combos += [a2 + g, a2 + s, g + "." + a2, a + "." + a2 if a else ""]
        for d in dates:
            combos += [a2 + d, a2 + g + d]

    # ==========================================================================
    # FULL mode – deeper date × token matrix, more dot variants
    # ==========================================================================
    if full:
        # alias × all combos × all dates
        if a:
            for d in dates:
                combos += [
                    a + g + si + d,                  # tommytaimanc01
                    a + "." + g + "." + si + d,      # tommy.taiman.c01  (long, filtered)
                    ai + g + d,                      # ttaiman01
                    ai + "." + g + d,                # t.taiman01
                    ai + init_sg + d,                # tctm01
                ]
            combos += [
                ai + g,                              # ttaiman
                ai + "." + g,                        # t.taiman
                ai + init_sg,                        # tctm
                a + "." + s + "." + g,               # tommy.chan.taiman
                a + gi,                              # tommytm  (alias + given-initials)
                a + "." + gi,                        # tommy.tm
            ]

        # given × date dot variants
        for d in dates:
            combos += [
                g + "." + d,                         # taiman.2001
                g + "." + si + "." + d,              # taiman.c.01  (likely too long)
            ]

        # surname dot combos (NO bare s+date)
        combos += [
            s + "." + g,                             # chan.taiman
            g + "." + s,                             # taiman.chan
            s + "." + init_sg,                       # chan.ctm
            init_sg + "." + s,                       # ctm.chan
        ]

        # g2 extended in full mode
        if g2:
            for d in dates:
                combos += [
                    g2 + g + si + d,                 # mantaimanc01
                    ai + g2 + d if a else "",         # tman01
                    g2 + "." + g + "." + si,         # man.taiman.c
                ]
            combos += [
                g2 + "." + g + si,                   # man.taimanc
                g2 + gi,                             # mantm  (g2 + given-initials)
                g2 + "." + gi,                       # man.tm
                ai + g2 if a else "",                # tman  (alias-initial + g2)
                ai + "." + g2 if a else "",          # t.man
            ]
            if a:
                combos += [
                    a + g2,                          # tommyman
                    a + "." + g2,                    # tommy.man
                ]
                for d in dates:
                    combos += [
                        a + g2 + d,                  # tommyman01  tommyman1015
                        a + "." + g2 + d,            # tommy.man01
                        a + g2 + si + d,             # tommymanc01
                    ]

        # alias2 extended
        if a2:
            for d in dates:
                combos += [a2 + d, a2 + "." + d, a2 + g + d]
            combos += [a2 + "." + g, a2 + "." + s, a2 + init_sg]

    return trim(combos, MAX_LEN_CN)


# ─────────────────────────────────────────────────────────────────────────────
# Western name generator
# ─────────────────────────────────────────────────────────────────────────────

def generate_western(
    first:  str,
    last:   str,
    middle: str = "",
    alias:  str = "",
    alias2: str = "",
    year:   str = "",
    dob:    str = "",
    full:   bool = False,
) -> list:
    """
    Western naming logic  (lowercase · dot-only · 6-16 chars)
    ----------------------------------------------------------
    --first  charlie   (f)    fi = c
    --middle monroe    (m)    mi = m
    --last   brown     (l)    li = b
    --alias  (optional)       ai = alias-initial

    Initials: cmb  (charlie monroe brown)
    Short combos: charlieb  charlie.b  cbrown  c.brown  etc.
    Month-only date suffix excluded.
    """
    f  = low(first.strip())
    l  = low(last.strip())
    m  = low(middle.strip())  if middle else ""
    a  = low(alias.strip())   if alias  else ""
    a2 = low(alias2.strip())  if alias2 else ""

    fi  = ini(f)
    li  = ini(l)
    mi  = ini(m) if m else ""
    ai  = ini(a) if a else ""

    init_fl  = fi + li
    init_fml = fi + mi + li if mi else fi + li   # cmb

    ml = m + l if m else ""                       # monroebrown

    yr4, yr2, dy2, md = parse_dates(year, dob)
    dates = [x for x in [yr4, yr2, md, dy2] if x]

    combos = []

    # ── PLAIN NAME ─────────────────────────────────────────────────────────────
    combos += [f + l, l + f]                         # charliebrown  browncharlie
    if m:
        combos += [f + mi + l, ml]                   # charliembrown  monroebrown

    # ── SHORT COMBOS ───────────────────────────────────────────────────────────
    combos += [
        f  + li,                                     # charlieb
        fi + l,                                      # cbrown
        f  + "." + li,                               # charlie.b
        fi + "." + l,                                # c.brown
        li + "." + f,                                # b.charlie
    ]
    if m:
        combos += [
            f  + mi,                                 # charliem
            f  + "." + mi,                           # charlie.m
            fi + "." + m,                            # c.monroe
            fi + mi + "." + l,                       # cm.brown
            f  + mi + "." + li,                      # charliem.b
        ]

    # ── ALIAS COMBOS ───────────────────────────────────────────────────────────
    if a:
        combos += [
            a + f,   f + a,                          # alias+first  first+alias
            a + l,   l + a,                          # alias+last   last+alias
            a + fi,  ai + f,                         # alias+fi     ai+first
            a + li,  ai + l,                         # alias+li     ai+last
            a  + "." + fi,  ai + "." + f,            # alias.fi     ai.first
            a  + "." + li,  ai + "." + l,            # alias.li     ai.last
            li + "." + a,   fi + "." + a,            # li.alias     fi.alias
        ]
        if m:
            combos += [a + init_fml]                 # alias+cmb

    # ── ALIAS + DATE ───────────────────────────────────────────────────────────
    if a:
        for d in dates:
            combos += [a + d]
        if dy2 and yr2:
            combos += [a + dy2 + yr2]

    # ── INITIALS ───────────────────────────────────────────────────────────────
    combos += [
        init_fml,                                    # cmb
        init_fml + "." + l,                          # cmb.brown
        f + "." + init_fml,                          # charlie.cmb
    ]
    for d in dates:
        combos += [init_fml + d, init_fl + d]        # cmb0322  cb0322  cmb1990  cb1990 ...
    if a:
        ai_fml = ai + init_fml
        combos += [ai_fml]                           # acmb

    # ── ALIAS + INITIALS (fl / fml) + DATE ─────────────────────────────────────
    # alias+fl  e.g.  tommycb  tommy.cb  tommycb1990  tommy.cb90
    # alias+fml e.g.  tommycmb already in init_fml block above via a+init_fml+d
    if a:
        combos += [
            a + init_fl,                             # tommycb   (alias + first+last initials)
            a + "." + init_fl,                       # tommy.cb
            init_fl + "." + a,                       # cb.tommy
        ]
        for d in dates:
            combos += [
                a + init_fl + d,                     # tommycb1990  tommycb90  tommycb0322  tommycb22
                a + "." + init_fl + d,               # tommy.cb1990  tommy.cb90  tommy.cb0322
            ]

    # ── ALIAS + LAST + DATE  (all date variants) ────────────────────────────────
    # alias+last already exists as a plain combo; add date variants here
    if a:
        for d in dates:
            combos += [
                a + l + d,                           # tommybrown1990  tommybrown90  ...
                a + "." + l + d,                     # tommy.brown1990  tommy.brown90  ...
            ]

    # ── DATE + NAME ────────────────────────────────────────────────────────────
    for d in dates:
        combos += [f + d, l + d]                     # charlie1990  brown1990 ...
    if a:
        for d in dates:
            combos += [
                a + f + d,                           # charliefirst+date (if alias differs)
                a + "." + f + d,                     # alias.first+date
                a + init_fml + d,                    # alias+fml+date
            ]
    if md:
        if m: combos += [ml + md, ml + dy2]

    # ── SEPARATOR VARIANTS (dot only) ──────────────────────────────────────────
    combos += [
        f + "." + l,                                 # charlie.brown
        l + "." + f,                                 # brown.charlie
    ]
    if m:
        combos += [
            f + "." + mi + "." + l,                  # charlie.m.brown
            fi + "." + mi + "." + l,                 # c.m.brown
        ]

    if a:
        combos += [
            a + "." + f,   f + "." + a,              # alias.first  first.alias
            a + "." + l,   l + "." + a,              # alias.last   last.alias
            a + "." + init_fml,                      # alias.cmb
            init_fml + "." + a,                      # cmb.alias
        ]
        for d in dates:
            combos += [a + "." + init_fml + d]       # alias.cmb0322
        if m:
            combos += [a + f + mi + li, a + fi + li + f]

    # ── FIRST + ALIAS combos ────────────────────────────────────────────────────
    if a:
        combos += [
            f + a + l,                               # charlietommybrown
            f + "." + a + "." + l,                   # charlie.tommy.brown
            f + a + li,                              # charlietommyb
            f + "." + a + li,                        # charlie.tommyb
        ]
        # first + alias + date
        for d in dates:
            combos += [
                f + a + d,                           # charlietommy1990  ...90  ...0322  ...22
                f + "." + a + d,                     # charlie.tommy1990  charlie.tommy90  ...
                f + a + li + d,                      # charlietommyb1990  ...
            ]
        # first + alias-initial
        combos += [
            f + ai,                                  # charliet
            f + "." + ai,                            # charlie.t
        ]
        for d in dates:
            combos += [
                f + ai + d,                          # charliet1990  charliet90  ...
                f + "." + ai + d,                    # charlie.t1990  ...
            ]

    # ── ALIAS2 ─────────────────────────────────────────────────────────────────
    if a2:
        for sep in ["", "."]:
            combos += [
                a2 + sep + f, a2 + sep + l,
                f  + sep + a2,
                a2 + sep + a if a else "", a + sep + a2 if a else "",
                a2 + sep + init_fml,
            ]

    # ==========================================================================
    # FULL mode
    # ==========================================================================
    if full:
        # primary tokens × all dates — no digit-first, middle excluded
        cores = [x for x in [f, l, a, a2, init_fml, init_fl, ml] if x]
        for name in cores:
            for d in dates:
                combos += [name + d, name + "." + d]

        if a2:
            for sep in ["", "."]:
                combos += [
                    a2 + sep + f, a2 + sep + l, f + sep + a2,
                    a2 + sep + a if a else "", a + sep + a2 if a else "",
                    a2 + sep + init_fml,
                ]
            for d in dates:
                combos += [a2 + d, a2 + "." + d]

        if m:
            combos += [f + "." + mi + li, fi + mi + "." + l]

        if a:
            combos += [
                ai + "." + f + l,
                a  + "." + f + l,
                ai + f + "." + l,
            ]
            # extra first+alias in full mode
            for d in dates:
                combos += [
                    f + "." + a + "." + d,           # charlie.tommy.1990
                    f + a + init_fl + d,             # charlietommycb1990
                ]
        if a and m:
            combos += [a + "." + init_fml + md if md else ""]

    return trim(combos, MAX_LEN_EN)


# ─────────────────────────────────────────────────────────────────────────────
# Interactive style prompt
# ─────────────────────────────────────────────────────────────────────────────

def ask_style() -> str:
    print("\n[?] Is the target Chinese or Western?")
    print("    1) Chinese  -- surname first  (e.g. chan tai man, alias tommy)")
    print("    2) Western  -- given name first  (e.g. charlie monroe brown)")
    while True:
        choice = input("    Enter 1 or 2: ").strip()
        if choice == "1": return "chinese"
        if choice == "2": return "western"
        print("    Please enter 1 or 2.")


# ─────────────────────────────────────────────────────────────────────────────
# CLI
# ─────────────────────────────────────────────────────────────────────────────

def parse_args():
    parser = argparse.ArgumentParser(
        description="AliasForge -- Chinese and Western naming conventions",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Name style conventions
----------------------
  Chinese  (--style chinese)
    --last   = surname / family name    e.g. Chan
    --first  = given name(s)            e.g. "Tai Man"  (used as a unit: taiman)
    --alias  = English / alias name     e.g. Tommy      (ANCHOR — generates most combos)

  Western  (--style western)
    --first  = given / first name       e.g. Charlie
    --middle = middle name              e.g. Monroe
    --last   = surname / family name    e.g. Brown

  Rules applied to all output:
    - Lowercase only
    - Separator: "." only  (Gmail-safe; "_" and "-" excluded)
    - Length: 6–16 characters
    - Month-only date suffix excluded (e.g. tommy10 skipped; tommy1015 kept)
    - Reversed names excluded
  If --style is omitted, you will be prompted interactively.

Examples
--------
  # Chinese
  python aliasforge.py --style chinese --last Chan --first "Tai Man" --alias Tommy --dob 2001/10/15
  python aliasforge.py --style chinese --last Chan --first "Tai Man" --alias Tommy --dob 2001/10/15 --full

  # Western
  python aliasforge.py --style western --first Charlie --middle Monroe --last Brown --dob 1990/03/22
  python aliasforge.py --style western --first Charlie --middle Monroe --last Brown --dob 1990/03/22 --full -o out.txt

  # Interactive prompt  (no --style given)
  python aliasforge.py --last Chan --first "Tai Man" --alias Tommy --dob 2001/10/15
        """,
    )

    parser.add_argument("--style", choices=["chinese", "western"],
        help="'chinese' or 'western'. Omit to be prompted.")
    parser.add_argument("--first", required=True,
        help="Chinese: given name(s) e.g. 'Tai Man' | Western: first name e.g. Charlie")
    parser.add_argument("--last",  required=True,
        help="Chinese: surname e.g. Chan | Western: surname e.g. Brown")
    parser.add_argument("--middle", default="",
        help="Western only: middle name e.g. Monroe")
    parser.add_argument("--alias", default="",
        help="Chinese: English alias e.g. Tommy | Western: nickname")
    parser.add_argument("--alias2", default="", help="Second alias / nickname")
    parser.add_argument("--year",   default="", help="Year of birth e.g. 2001")
    parser.add_argument("--dob",    default="",
        help="Date of birth YYYY/MM/DD or YYYY-MM-DD e.g. 2001/10/15")
    parser.add_argument("--full", action="store_true",
        help="Full result mode (more combos)")
    parser.add_argument("-o", "--output", default="",
        help="Save results to file (one per line)")
    parser.add_argument("--no-print", action="store_true",
        help="Suppress terminal output (useful with -o)")

    return parser.parse_args()


# ─────────────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────────────

def main():
    args = parse_args()
    style = args.style or ask_style()

    if style == "chinese":
        usernames = generate_chinese(
            last=args.last, first=args.first,
            alias=args.alias, alias2=args.alias2,
            year=args.year, dob=args.dob, full=args.full,
        )
        print(f"\n[+] Style   : Chinese (surname first)")
        print(f"[+] Surname : {args.last.lower()}")
        print(f"[+] Given   : {args.first.lower()}")
        if args.alias: print(f"[+] Alias   : {args.alias.lower()}")
    else:
        usernames = generate_western(
            first=args.first, last=args.last, middle=args.middle,
            alias=args.alias, alias2=args.alias2,
            year=args.year, dob=args.dob, full=args.full,
        )
        print(f"\n[+] Style   : Western (given name first)")
        print(f"[+] First   : {args.first.lower()}")
        if args.middle: print(f"[+] Middle  : {args.middle.lower()}")
        print(f"[+] Last    : {args.last.lower()}")
        if args.alias: print(f"[+] Alias   : {args.alias.lower()}")

    if args.dob or args.year:
        print(f"[+] DOB     : {args.dob or args.year}")

    mode   = "FULL" if args.full else "DEFAULT"
    maxlen = MAX_LEN_CN if style == "chinese" else MAX_LEN_EN
    header = (f"[+] Generated {len(usernames)} usernames "
              f"({mode} mode · {MIN_LEN}-{maxlen} chars)")
    print(header)
    print("-" * len(header))

    if not args.no_print:
        for u in usernames:
            print(u)

    if args.output:
        with open(args.output, "w") as fh:
            fh.write("\n".join(usernames) + "\n")
        print(f"\n[+] Saved to: {args.output}")


if __name__ == "__main__":
    main()
