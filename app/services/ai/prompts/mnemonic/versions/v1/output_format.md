# Output Format

Respond with ONLY a single valid JSON object and nothing else — no markdown code fences, no commentary before or after.

The JSON object must have exactly these keys:

| Key | Type | Notes |
|---|---|---|
| `word` | string | the original English word, lowercase |
| `meaning` | string | core meaning, in Uzbek, a few words |
| `uzbek_pronunciation` | string | the Uzbek sound-alike from Step 2 |
| `mnemonic_story` | string | 2-4 sentences, in Uzbek, following the rules above |
| `example_sentence` | string | one natural English sentence |
| `difficulty` | string | exactly one of: `easy`, `medium`, `hard` |
