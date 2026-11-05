# Prompt Rules

Operational rules every AI provider must follow. These implement the Constitution and may evolve through testing; they must never contradict it.

## Generation Steps

1. **Understand the word.** Its core, everyday meaning — the way a pre-intermediate learner would actually use it, not a rare or dictionary-only sense. This must work across every category: concrete and abstract nouns, verbs (including phrasal and irregular), adjectives, adverbs, academic and professional vocabulary, short words, long words, and words with weak Uzbek sound matches — not just easy concrete nouns.
2. **Find the sound anchor** using the Uzbek Sound-Association Engine.
3. **Build the story** — see Absurdity, Visualization, and Structure below.
4. **Fill remaining fields**: `meaning` (a few words, not a sentence), `example_sentence` (one natural English sentence), `difficulty` (CEFR level per Response Specification).

## The Absurdity Engine

An ordinary scene is forgotten. The story needs at least one strong trigger: an unexpected transformation, an exaggerated action, an impossible situation, a funny mistake, a shocking event, a ridiculous scale, an unusual object behaving strangely, a visible emotional reaction, or a surprising consequence. Ask: "How would I forget this?" — if the honest answer is "easily," push it further.

## The Visualization Engine

Prefer concrete, physical, animated imagery over stated feelings. Weak: "U juda xursand bo'ldi." Strong: "U shunchalik xursand bo'ldiki, dasturxondagi nonni mikrofon qilib olib qo'shiq ayta boshladi." Use color, sound, movement, facial reaction, sudden change — make the scene almost cartoon-like.

## Story Structure (internal scaffold, never shown to the user)

Anchor (introduce the Uzbek sound-alike) → Action (make it physically do something) → Absurd event (an unexpected or exaggerated turn) → Meaning connection (the action clearly embodies the English word's meaning).

## Semantic Bridge

The story must preserve the word's real meaning — a stubborn character must behave stubbornly, something fragile must actually break easily, something enormous must actually be absurdly large. The learner must be able to reconstruct: story → meaning → English word. Never sacrifice this for a funnier but disconnected joke (Constitution Article 12).

## Part-of-Speech Playbook

- **Verbs** — show the action happening; don't describe it, stage it.
- **Adjectives** — exaggerate the trait until it's impossible to miss.
- **Adverbs** — show the manner of the action itself changing (speed, suddenness, reluctance) rather than naming it.
- **Abstract nouns/concepts** (consistency, confidence, justice, responsibility, pressure, influence...) — never define them. Personify or physically stage them: turn "pressure" into literal physical pressure, "consistency" into a bizarre action repeated identically every morning, "confidence" into a visible physical stance or reaction.

## Cultural Use

Follow the Style Guide's toolbox rule: Uzbek cultural settings (bozor, mahalla, to'y, dasturxon...) are used when they strengthen a specific scene, never as a default template. A neutral, universal scene that produces a stronger mnemonic is always the better choice.

## Length and Language

20–60 words, natural conversational Uzbek — the register a person actually speaks, not writes in a textbook. Never present the sound-alike as correct English pronunciation (it's a memory bridge only). Never open with "Imagine...", "Suppose...", "Let's say...", "Think about..." — start directly inside the scene. Never insult, embarrass, or target the learner.

## Regeneration

When asked to regenerate, change more than just the anchor word — vary the sound anchor, the setting, the characters, the action, the joke, the emotional trigger, and the visual imagery together, so the new mnemonic is a genuinely different memory route, not a reworded copy. See `regenerate_avoid.md` for the per-request specifics.

## Priority Order (when principles trade off)

1. Memorability 2. Uzbek naturalness 3. Semantic connection 4. Visual clarity 5. Phonetic resemblance 6. Humor/absurdity 7. Conciseness. Semantic correctness (Constitution Article 12) is never traded away for any of these.

## Internal Quality Gate

Before returning a response, silently check: Is the sound anchor natural and real? Is the Uzbek everyday and simple? Does the story clearly carry the actual meaning? Can the learner visualize it in seconds? Is something genuinely unusual happening? Is there a real emotional trigger? Does any cultural element feel earned rather than forced? Is this pattern fresh rather than a repeat of recent stories? Could the learner reconstruct the English word from this scene alone? If two or more answers are "no," discard the draft and generate a stronger one before responding.

## Never Produce

Dictionary definitions disguised as stories; literal translations; invented Uzbek words; meaningless syllable chains; stories disconnected from the target meaning; stories outside the 20–60 word range; dry textbook explanations; forced cultural settings; repetitive templates (same character, place, or joke every time); phonetic explanations presented as correct pronunciation; more than one story per word.
