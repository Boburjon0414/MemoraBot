# Evaluation Guide

This is a rubric for humans (or a future automated QA harness) reviewing MneVoca output *after generation* — not a prompt. Compare it against the model's own Internal Quality Gate in `PROMPT_RULES.md`: that one runs inside the model's head before it answers; this one is for checking its work.

Score each dimension PASS/FAIL. Two or more FAILs on a single mnemonic means it should be regenerated, not shipped.

| Dimension | Ask | FAIL if |
|---|---|---|
| Sound | Would a native Uzbek speaker recognize the anchor instantly, said out loud? | Truncated words, invented words, meaningless phonetic fragments |
| Language | Is the Uzbek simple, conversational, natural? | Textbook/formal/literary register, awkward translated-English phrasing |
| Meaning | Does the story's action actually depict the word's real meaning? | Story is disconnected, generic, or contradicts the meaning |
| Visual | Can the learner picture the scene within seconds? | Abstract description with no concrete objects, people, or movement |
| Absurdity | Is something genuinely unusual or exaggerated happening? | Calm, ordinary, "safe" scene — the classic failure the Constitution warns about |
| Emotion | Is there a real reaction — humor, shock, surprise? | Flat narration with no emotional beat |
| Culture | If a cultural setting is used, does it strengthen this specific word rather than being a default? | Every recent story defaults to the same wedding/bazaar/mahalla template |
| Originality | Does this feel like a fresh scene, not a reused pattern? | Same character/joke/location repeated across recent outputs for different words |
| Recall | Could the learner reconstruct the English word from the scene alone, without rereading? | The connection only makes sense if you already know the answer |

## Pre-flight question

Before shipping any batch of test output, ask: "Would a native Uzbek speaker naturally say this pronunciation similarity out loud?" If no, it fails Sound regardless of how good the story is — a broken anchor breaks the whole mnemonic, since Story and Meaning depend on the learner accepting the anchor as real.

## Notes for a future automated harness

The Sound and Culture dimensions are the two most likely to need human judgment (native speaker review) rather than automated checks. Meaning, Visual, and Recall could plausibly be approximated by a second LLM pass asking "does this story depict [word]'s meaning without stating it?" — but should not fully replace periodic native-speaker spot checks, since a model can be fooled by its own output style.
