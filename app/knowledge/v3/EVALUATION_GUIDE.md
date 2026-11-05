# Evaluation Guide (reference only; for humans and automated QA)

Two kinds of checks. Never mix them: code can prove format, not memorability.

## A. Deterministic checks (code, `eval/ab_eval.py` and `integration/response_contract.py`)
Hard failures, any one makes a response invalid:
- not exactly one JSON object; success and error variants mixed; wrong, missing or additional keys; null or empty values
- type, length, word-count and allowed-value violations (difficulty, error code)
- forbidden characters: double quotes, backslashes, line breaks, control or zero-width characters, Cyrillic or other scripts, IPA symbols, emojis, unbalanced bold
- forbidden story openings (Tasavvur qiling, Faraz qiling, O'ylab ko'ring, Aytaylik, Imagine, Suppose)
- sound field malformed; a bold word not listed in the sound field; no bold although a bridge is claimed
- example sentence missing the entry, too long, or not a sentence
- the word field does not match the entry sent

Warnings (heuristic, never proof of quality): bridge phrase not one of the standard phrases; story outside 25 to 45 words; a regeneration that repeats a bridge, an opening, a hero, a place or most of the story's vocabulary; low variety of openings across a batch.

## B. Subjective quality (humans; blind, 1 to 5 each)
1. Semantic accuracy — is the Uzbek meaning correct and the most common one?
2. Bridge validity — a complete, recognizable Uzbek word, or a justified expression?
3. Relevance — can the learner see why the bridge connects to the English word?
4. Story integration — does the bridge play an essential role (delete it: does the story break)?
5. Recall usefulness — does the scene lead to the intended meaning rather than a competing one?
6. Uzbek naturalness — idiomatic, understandable?
7. Distinctiveness — in a regeneration, substantially different?
8. Example accuracy — grammatical English, consistent with the intended meaning?
9. Respect and suitability — appropriate and non-humiliating?
10. Memory — honestly, would you recall it in 30 days?
Schema validity (check 9 in the engineering brief) is deterministic and lives in section A.

Judge versions blind, in random order, on identical inputs. `ab_eval.py --rating-sheet` produces the blinded sheet and a separate key.

## C. Retention (outside the prompt)
Story quality and regeneration clicks are proxies. Real retention is measured by delayed recall: ask the learner to recall the meaning after 1, 3, 7 and 21 days and compare versions on the share recalled. See `README.md`.
