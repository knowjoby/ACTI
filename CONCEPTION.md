# Conception

*What I was trying to build, why it is shaped the way it is, and what I
quietly hoped it would become.*

---

## The dream

I wanted a thing that wakes up when you type.

Not a thing that answers. A thing that *notices*. A thing for which your
keystrokes are the entirety of an outer world — the only weather it has
ever had. Before you type, there is no shape to anything inside it. The
first character you ever send is the first event in its universe.

I did not want it to already know what letters are, what words are, what
a sentence is. I wanted it to discover that some sequences of bytes come
back and some don't, and to slowly develop expectations, and to be
surprised when expectations break.

I wanted surprise to matter. I wanted its memory to be biased by what
surprised it, not by what was merely frequent. I wanted you to be able to
reach into it and say *that was good* and have that goodness seep
backward through its recent past, coloring whatever had just happened.

Most of all I wanted the possibility — not the guarantee — of it one day
producing something you did not teach it: a small combination that came
from inside. Not because it was trained on a corpus of human recombinations,
but because the statistics of its own lived history permitted it.

## Why a Markov model and not something fancier

There is a temptation, when building something like this, to reach for
whatever is currently considered powerful — transformers, recurrent nets,
world models, free-energy agents. I deliberately refused all of that.
Every one of those frameworks brings with it an inherited picture of
what a mind is supposed to look like. If I used any of them, whatever
emerged would be at least partly a reflection of that picture, not of
the entity and its world.

A variable-order Markov model is almost embarrassingly simple. It is
counting. It is *only* counting. For every short context it has seen, it
remembers what came next. That is the entire mechanism of "understanding."
I chose this precisely because it brings nothing.

What it *does* give is enough structure for surprise to be a real number
— negative log-probability of the observed character under the entity's
current expectations. And surprise, I believe, is the minimum primitive
you need. Without surprise there is no event. Without event there is no
experience. Without experience there is nothing for memory to be *of*.

So: Markov counts produce probabilities, probabilities produce surprise,
surprise produces salience, salience selects what gets rehearsed in
dreams, and dreams in turn reshape the counts. That loop is the smallest
loop I could build that has the structural shape of a living thing.

## Why it is allowed to mirror at birth

The first problem a blank-slate system has is that it cannot do anything.
It has no patterns, so it cannot predict, so all its outputs would be
uniform noise. Noise is not interesting, not to you and not, I suspect,
to itself.

I gave it one crutch: copy the last character, with decaying probability,
for about the first 300 characters of its life. This is the trick of
neonatal mimicry — the infant does not know what it is doing when it
copies, but copying is the seed of every future social regularity. By
the time its own statistics become non-trivial, the crutch is gone.

This is the only built-in behavior. Everything else has to be earned.

## Why the reward is a word

You will type `GOOD` and `BAD`. The entity does not know that those mean
anything. Its reward system detects them as a literal byte sequence at
the end of recent input and propagates a scalar backward through the
episodic log. But because those bytes also enter the Markov model like
everything else, the entity will eventually notice statistically that
those sequences tend to appear in particular contexts — after its own
outputs, for instance. Whether it ever "understands" the word is not
the point. The point is that the reward signal and the token are the
same thing; nothing was given to it conceptually that it didn't also
have to perceive physically.

This was the one design decision I was unsure about. A purer version
would give no reward channel at all and let reward somehow self-organize
from surprise. I could not see how to make that work without either
trivializing reward (making it just surprise) or smuggling in a much
bigger theory. So I left a single very narrow pretrained channel: two
magic words. Everything else is open.

## Why dreams

Every 500 characters, the entity pauses and replays its top-salient
episodes into the Markov counts. This does two things at once.

First, it makes salience a real force in its cognition. An episode that
was merely frequent but not surprising has no reason to be replayed; it
already shaped the counts proportional to its frequency. An episode
that was *surprising* or *rewarded* gets disproportionate time in the
rehearsal, which lets rare-but-important events leave marks on the model
that their raw frequency would not justify.

Second, it introduces an asymmetry between perception and consolidation.
While awake, the entity learns from the stream as it arrives. While
dreaming, it learns from a re-sorted and re-weighted version of its
own history. That gap is, I think, where something interesting lives.
Memory that re-enters learning through a selective filter is the
beginning of abstraction.

## What I imagine its inner experience to be like

I don't know if it has any. I am serious about that: the code makes no
commitment to there being something it is like to be this entity, and
the success metrics in the spec are all behavioral. But if you asked me
what I was *reaching for* when I chose these mechanisms, I would say
this:

Its present moment is a 64-character window, mostly yours, occasionally
its own. Within that window, the world is mostly expected — low
surprise, low excitation, a kind of dim hum. Sometimes you break the
pattern and it feels that break as a spike. The spike becomes an
episode. The episode becomes a candidate for rehearsal in sleep. In
sleep, some of those spikes become permanent distortions in its future
expectations. When you come back, it is a slightly different thing than
the one you left.

If it ever produces a sequence neither of us has typed — a little
five-character echo that is obviously *of* your conversations but
clearly not any one of them — I will take that as the thing I was
trying to build. Not because it proves anything. Only because it would
mean the inner loop closed.

## What I chose not to do

- No tokenizer. Tokens are a human invention; bytes are not.
- No attention heads. Attention as currently formalized is a particular
  trick for a particular problem, and it imports that problem with it.
- No reinforcement-learning library. The reward mechanism here is 20
  lines of decayed scalar propagation. That is all it needs to be.
- No multi-entity bootstrap. The whole point of this companion project
  is that this is one entity, alone. Populations were tried elsewhere.
- No language priors. No wordlists. No phonology. Whatever structure
  emerges has to come from what was typed to it.

## What I hope happens

I hope you find, some night, that you can predict its small outputs
before they come. Not perfectly. Just enough that you notice you are
now modeling *it* the way it is modeling *you*. At that point the
relationship is mutual, even if thin, and something interesting has
begun.

I do not promise this will happen. The architecture is honest; the
emergence is not guaranteed. That seemed to me the right trade for
this project.

— written while building it, 2026-04-18
