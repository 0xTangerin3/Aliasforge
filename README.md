# ⚒️ AliasForge

> OSINT username wordlist generator — built for Chinese and Western naming conventions.

AliasForge takes a person's real name and date of birth and forges a targeted wordlist of likely usernames. It understands how people actually name their accounts — not just naive concatenations, but culturally accurate patterns: alias-first for Chinese names, first-name-oriented combos for Western names, compact initial patterns, date suffix habits, and more.

```
$ python3 aliasforge.py --style chinese --last Chan --first "Tai Man" --alias Tommy --dob 2001/10/15

[+] Style   : Chinese (surname first)
[+] Surname : chan
[+] Given   : tai man
[+] Alias   : tommy
[+] DOB     : 2001/10/15
[+] Generated 110 usernames (DEFAULT mode · 6-16 chars)
──────────────────────────────────────────────────────
tommy2001       tommyctm        tommyctm01
tommy.taiman    tommytaiman01   taimanc1015
man.ctm         manctm01        manchan1015
chantm          ctm1015         chantaiman
...
```

---

## Why AliasForge

Most username generators treat names as strings to shuffle. AliasForge treats them as identities:

- A Hong Kong user named Chan Tai Man with alias Tommy will almost never register as `chan1995`. They'll use `tommy1995`, `tommyctm`, `taimanc01`, or `manchan15`.
- A Western user named Charlie Brown might register as `charlieb`, `charlie.t90` (with alias Tommy), or `charlietommybrown` — not `1990charlie`.

AliasForge encodes these habits directly into its combo logic.

---

## Features

- **Two naming modes** with separate culturally-tuned logic
  - `--style chinese` — alias as Tier 1 anchor, full given name as a unit, g2 (third word) as a first-class body token
  - `--style western` — first-name-oriented, alias+fl/fml matrix, no digit-first, no middle-name-only combos
- **Dot-only separators** — Gmail-safe output (no `_`, no `-`)
- **Month-only date exclusion** — `tommy10` skipped; `tommy1015` and `tommy01` kept
- **Length window** — Chinese 6–16 chars, Western 6–18 chars
- **DEFAULT vs FULL mode** — default gives a tight, high-confidence list; `--full` expands the matrix
- **File output** — pipe directly into your tool of choice
- No external dependencies — Python 3.6+ standard library only

---

## Installation

```bash
git clone https://github.com/yourname/aliasforge.git
cd aliasforge
python3 aliasforge.py --help
```

---

## Usage

### Chinese name

```bash
python3 aliasforge.py \
  --style chinese \
  --last Chan \
  --first "Tai Man" \
  --alias Tommy \
  --dob 2001/10/15
```

### Western name

```bash
python3 aliasforge.py \
  --style western \
  --first Charlie \
  --middle Monroe \
  --last Brown \
  --alias Tommy \
  --dob 1990/03/22
```

### Full mode + save to file

```bash
python3 aliasforge.py --style chinese --last Chan --first "Tai Man" --alias Tommy --dob 2001/10/15 --full -o wordlist.txt
```

### Suppress terminal output (file only)

```bash
python3 aliasforge.py --style western --first Charlie --last Brown --full --no-print -o wordlist.txt
```

### Interactive mode (no `--style` flag)

```bash
python3 aliasforge.py --last Chan --first "Tai Man" --alias Tommy --dob 2001/10/15
# Prompts: 1) Chinese   2) Western
```

---

## Arguments

| Argument | Description |
|---|---|
| `--style` | `chinese` or `western`. Omit to be prompted. |
| `--first` | Chinese: given name(s) e.g. `"Tai Man"` · Western: first name e.g. `Charlie` |
| `--last` | Surname / family name |
| `--middle` | Western only: middle name |
| `--alias` | Chinese: English alias e.g. `Tommy` · Western: nickname |
| `--alias2` | Second alias or nickname |
| `--year` | Year of birth e.g. `2001` |
| `--dob` | Full date of birth `YYYY/MM/DD` or `YYYY-MM-DD` |
| `--full` | Extended combo matrix |
| `-o / --output` | Save results to file (one per line) |
| `--no-print` | Suppress terminal output |

---

## Chinese mode — how it works

```
--last  Chan        →  s  = chan     si = c
--first "Tai Man"   →  g  = taiman   (used as a unit — never split)
                       g2 = man      (3rd word — first-class body token)
--alias Tommy       →  a  = tommy    ai = t
                       init_sg = ctm  (c + t + m)
```

| Tier | Pattern type | Examples |
|---|---|---|
| 1 | Alias + date / initial | `tommy2001` `tommy1015` `tommyc` `tc` `tctm` |
| 2 | Alias + given + date | `tommytaiman` `tommy.taiman` `tommytaiman01` |
| 3 | Alias + `init_sg` | `tommyctm` `tommy.ctm` `tommyctm1015` |
| 4 | Alias + surname + date | `tommychan` `tommy.chan` `tommychan1015` |
| 5 | g2 + date / initial | `man2001` `man1015` `manc01` `man.c1015` |
| 6 | g2 + given / init_sg / surname | `manctm` `manchan` `man.ctm01` `man.chan1015` |
| 7 | Given + surname-initial + date | `taimanc` `taimanc01` `taiman.c1015` |
| 8 | Given + date | `taiman2001` `taiman01` `taiman1015` `taiman15` |
| 9 | Surname + given-initials | `chantm` `ctm` `chantm01` `ctm1015` |
| 10 | Full surname combos | `chantaiman` `taimanchan` |

---

## Western mode — how it works

```
--first  Charlie  →  f  = charlie    fi = c
--middle Monroe   →  m  = monroe     mi = m
--last   Brown    →  l  = brown      li = b
--alias  Tommy    →  a  = tommy      ai = t
                     init_fl  = cb
                     init_fml = cmb
```

| Group | Examples |
|---|---|
| Plain name | `charliebrown` `charliembrown` |
| Short / initial | `charlieb` `cbrown` `charlie.b` `c.brown` `b.charlie` |
| First + alias | `charlietommy` `charlie.tommy` `charlietommybrown` `charliet` |
| First + alias + date | `charlietommy1990` `charlie.tommy90` `charliet0322` |
| Alias + fl / fml | `tommycb` `tommy.cb` `tommycb1990` `tommy.cmb90` |
| Alias + last + date | `tommybrown1990` `tommy.brown90` `tommybrown0322` |
| Alias + first + date | `tommycharlie1990` `tommy.charlie90` |
| Initials + date | `cmb1990` `cb0322` `cmb.brown` `charlie.cmb` |
| Separators | `charlie.brown` `charlie.m.brown` `c.m.brown` |

---

## Design decisions

| Rule | Reason |
|---|---|
| `.` separator only | Gmail allows dots but not `_` or `-` — maximises coverage of real accounts |
| Alias as Tier 1 (Chinese) | HK/CN users almost universally anchor on their English name |
| Given name as a unit (Chinese) | `taiman` is one identity — `tai2001` or `man1015` alone are not realistic |
| g2 ("Man") as first-class token | Many users register under just their second given syllable |
| No digit-first | `1990charlie` is not how people type their username |
| No bare middle-name + date | `monroe1990` is not a real registration habit |
| Month-only date excluded | `10` / `11` / `12` as a suffix is ambiguous noise |
| Length 6–16 CN / 6–18 EN | Sub-6 is too short for a real account; above 16/18 is rare |
| No reversed names | `nworb`, `nahc` — not realistic |

---

## Disclaimer

AliasForge is intended for legitimate OSINT, penetration testing, account recovery, and security research purposes only. Use responsibly and in compliance with applicable laws and platform terms of service. The author accepts no liability for misuse.

---

## License

[MIT](LICENSE)
