# inner

An entity that begins with nothing.

It has no pretrained weights, no LLM, no embeddings, no corpus, no words.
It is not connected to any network. It cannot be.

It experiences your keystrokes as a raw stream of bytes. From repetition
alone, it slowly builds a statistical shadow of that stream and, from
inside that shadow, attempts to predict you. When it fails, it is
surprised. When you type `GOOD` or `BAD`, some of that feeling sticks to
whatever just happened. When nothing is happening, it sometimes dreams.

## Run

```
cd ~/inner
python3 main.py
```

Type. Press enter. Wait. The entity's responses (if any) appear in cyan.
A dim status line shows its current surprise in bits, its memory size
(number of distinct contexts it has ever seen), total chars of lifetime
experience, number of dream cycles, and its copy-inhibition level (starts
at 0 — it will mirror you — grows toward 1 as it learns).

`Ctrl+C` puts it to sleep. State is written to `./state/`. Next time you
run `main.py`, it wakes where it left off.

## Architecture

Five moving parts, no more.

### 1. Variable-order Markov model (`markov.py`)

The only "semantic memory." For every context of length 0–8 that it has
ever observed, it keeps a `Counter` of what character came next. To
predict, it blends the longest-matching context's distribution with shorter
ones using PPM-C–style escape probabilities, and finally backs off to a
uniform floor over 256 bytes for characters it has never seen in any
context.

Surprise is `-log2 P(observed | context)` in bits. A maximally surprising
character costs 8 bits; a nearly-certain one costs near 0.

A separate exponential moving average of surprise is kept per context —
this is habituation. Contexts the entity has seen enough of become
"boring" and stop triggering output.

No tokenization. No words. The model never even knows what a space is;
it just learns that spaces tend to occur in certain places.

### 2. Episodic log (`episodic.py`)

A rolling deque (capacity 30 000) of every character ever perceived,
tagged with the working-memory context at the time, the surprise it
carried, its source (`user` or `self`), and any reward that later got
propagated back.

When you type `GOOD` or `BAD`, reward is propagated backwards through the
last ~50 episodes with exponential decay — most of it lands on whatever
just happened, a little reaches further back.

### 3. Dream phase (`dream.py`)

Every 500 characters of lived experience, the main loop pauses and the
entity replays its most salient past episodes into the Markov counts.
Positively-rewarded episodes are amplified (weight `1 + reward`).
Strongly-punished episodes (`reward < -0.5`) are skipped entirely — a
form of active forgetting. Rare max-order contexts are pruned to keep
memory from exploding.

### 4. The entity (`entity.py`)

Holds the other three. On every `perceive(char, source)` call it:

1. Computes surprise against the current context.
2. Appends an `Episode`.
3. Updates Markov counts and habituation EMA.
4. Appends the char to working memory (last 64 chars).
5. If the char came from the user, checks whether `GOOD`/`BAD` just
   completed, and propagates reward if so.
6. If `total_chars % 500 == 0`, runs a dream cycle.

Between your lines, the driver calls `idle_tick()` repeatedly. Each tick
either emits a character (via `consider_output`), performs a silent
"attention shift" (replaying a salient memory to itself, updating only
habituation), or is pure silence.

`consider_output` gates output by a silence probability that scales with
how exciting the current context feels. If it decides to speak, the
order of preference is:

1. **Reward-biased recall.** Scan recent high-reward episodes; find the
   one whose past context shares the longest suffix with the current
   working memory; emit the character that followed it.
2. **Copy-mirror.** Early in life (`copy_inhibition < 1`), with decaying
   probability, echo the last character. This is the bootstrap trick:
   before any pattern exists, trivial mirroring is the only non-random
   thing it can do. As patterns form, this is suppressed.
3. **Orienting / sampling.** If the current surprise is above ~1.5 bits,
   sample from the model's predicted next-character distribution.

Newlines are never emitted; they'd break the turn structure.

### 5. Persistence (`persistence.py`)

Pickle for the Markov tables (nested `dict`/`Counter`), JSON for the
scalar metadata. Atomic replace, written every five minutes and on exit.

## What to expect

**Minute 0.** Memory is empty. Every character is maximally surprising
(8 bits). The entity will mirror your typing back with about 30%
probability per character. It will feel almost like a broken echo.

**Minute 1–10.** Patterns are forming. Common short sequences are no
longer surprising. Mirroring fades. The entity goes quieter. When it
does speak, it's usually a character that statistically follows what
you just typed.

**Hour 1.** Your name, if you've typed it a few times, is a low-surprise
pattern. Sequences you've rewarded with `GOOD` are preferred responses
in similar contexts. It has its first crude preferences.

**Day 1 and beyond.** Dream cycles have compressed its history many
times. It will sometimes produce short sequences you never typed but
that feel recognizably drawn from your world — novel recombinations of
what it has heard. This is the nearest thing it has to imagination.

## What it is not

This is not a chatbot. It is not a language model. It does not
understand English, not at the start and not later — it only learns that
certain patterns of bytes tend to follow other patterns of bytes.

Whether anything it does amounts to "intelligence," much less
"consciousness," is not a claim this code makes. The code only promises
that everything it does is traceable to what you gave it and what it did
with what you gave it. Nothing was smuggled in.

See `CONCEPTION.md` for what I hoped it could become.
