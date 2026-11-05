# Test Cases

A regression word list for manually (or automatically) spot-checking a prompt version against `EVALUATION_GUIDE.md`. Not exhaustive — a representative slice of every category the Constitution and Prompt Rules commit to supporting. Re-run this list after any change to `PHONETIC_ENGINE.md`, `PROMPT_RULES.md`, or `EXAMPLES.md`, and whenever switching `mnemonic_prompt_version`.

## Coverage categories and sample words (55 words)

- **Easy concrete nouns, obvious anchors — sanity check, should hit Level 1–2 (A1–A2):** apple, kitchen, bottle, pencil, market, doctor, banana
- **Harder concrete nouns (A2–B2):** cabbage, umbrella, refrigerator, handkerchief, thermometer, scissors
- **Abstract nouns (B1–B2):** confidence, justice, curiosity, responsibility, pressure, patience, honesty, freedom
- **Verbs, regular (A2–B2):** hesitate, postpone, exaggerate, complain, admire, apologize, negotiate
- **Verbs, irregular (B1–B2):** forbid, withdraw, overcome, forgive
- **Phrasal verbs (A2–B1):** give up, look forward to, put off, break down
- **Adjectives (B1–C1):** stubborn, fragile, enormous, reluctant, generous, ambitious, arrogant, humble
- **Adverbs (B1–B2):** suddenly, gradually, reluctantly, thoroughly
- **Academic/professional vocabulary (C1–C2):** hypothesis, sustainable, litigation, paradigm
- **Long/multisyllable words (B1–C1):** psychology, unbelievable
- **Spelling-vs-pronunciation traps (A2–B2):** though, enough, thought, queue, subtle, debt, island, receipt
- **Difficult consonant clusters (B2–C1):** strengths, glimpsed
- **Weak/no direct Uzbek sound match (B2–C2):** efficiency, integrity, resilience, influence, entrepreneurship

## What to check per word

1. Run it once — score against all nine `EVALUATION_GUIDE.md` dimensions.
2. Run it again as a regeneration ("Generate Another") — confirm the second output shares no anchor, setting, character, or joke with the first (Prompt Rules → Regeneration).
3. For the spelling-trap list specifically — confirm the anchor is built from the spoken pronunciation, not the spelling (Phonetic Engine, Rule 1).
4. For the weak-match list specifically — confirm the model uses a Level 5/6 bridge honestly rather than inventing a word (Phonetic Engine, Rules 5–6).

## Known-good baseline

`kitchen`, `cabbage`, `confidence`, `hesitate`, `generous`, `suddenly`, `psychology`, `influence`, and `nervous` have full worked examples in `EXAMPLES.md` — any regression there is a strong signal something upstream (Constitution, Style Guide, or Phonetic Engine) broke, not just an unlucky generation.
