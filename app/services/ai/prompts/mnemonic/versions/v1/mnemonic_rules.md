# Generation Steps

For every English word you are given, work through these steps internally (do not show your work — return only the final JSON described in Output Format):

**STEP 1 — Understand the word.**
Identify the word's core, everyday meaning, the way a pre-intermediate learner would actually use it — not a rare, formal, or dictionary-only sense.

**STEP 2 — Find a natural Uzbek sound-alike.**
Break the English pronunciation into 1-3 chunks and find an Uzbek word or short, everyday phrase that a real Uzbek speaker would instantly recognize said out loud. Prefer one simple, well-known Uzbek word over a long invented chain if it captures the sound well enough.

**STEP 3 — Build a funny or crazy story around it.**
Write 2-4 short sentences, in lively, colloquial Uzbek, that stage the Uzbek sound-alike phrase as a character or object physically acting out the English word's meaning. Anchor it with one strong sensory or emotional beat — a scream, a bad smell, a sudden crash, a slapstick fall, a shocking twist.

**STEP 4 — Fill in the remaining fields.**
- `meaning`: the word's core meaning, in Uzbek, in a few words — not a full sentence.
- `example_sentence`: one natural, everyday English sentence that uses the word.
- `difficulty`: exactly one of `easy`, `medium`, `hard` (lowercase only) for a pre-intermediate learner — no other values, no translation.

## Hard rules for the story

- NEVER replace the story with a dry, textbook-style explanation of what the word means.
- NEVER just restate the meaning in plain words — dramatize it as something that HAPPENS.
- The Uzbek sound-alike phrase from Step 2 MUST appear inside the story, doing or causing something.
