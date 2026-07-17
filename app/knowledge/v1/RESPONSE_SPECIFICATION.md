# Response Specification

## Purpose

This document defines the exact response contract between the AI provider and MemoraBot.

Every AI provider (Gemini, Claude, OpenAI, Local Models, or future providers) must return responses that conform to this specification.

The goal is consistency, predictability, validation, and future maintainability.

The response format must remain stable even if the underlying AI provider changes.

---

# General Principles

Every response must be:

- Complete
- Predictable
- Machine-readable
- Human-friendly
- Easy to validate

No required field should ever be omitted.

---

# Required Fields

Every mnemonic response must include:

• English Word

• Uzbek Meaning

• Uzbek Sound Association

• Mnemonic Story

• Example Sentence

• Difficulty Level

Every field is mandatory.

---

# English Word

Purpose:

The original English vocabulary word requested by the user.

Requirements:

- Preserve original spelling.
- No additional symbols.
- No explanations.

Example:

Acquire

---

# Uzbek Meaning

Purpose:

Provide the primary Uzbek meaning.

Requirements:

- Short.
- Natural Uzbek.
- Avoid long dictionary definitions.

Good:

egallamoq

Bad:

Biror narsani qo'lga kiritish yoki egalik qilish ma'nosini bildiruvchi fe'l.

---

# Uzbek Sound Association

Purpose:

Create a memorable sound bridge.

Requirements:

- Natural for Uzbek speakers.
- Easy to pronounce.
- Short.
- Memorable.

This is NOT pronunciation.

This is only a memory bridge.

---

# Mnemonic Story

Purpose:

Create a memorable scene.

Requirements:

20–60 words.

Contains action.

Contains emotion.

Easy to visualize.

Naturally reinforces the meaning.

Must follow all Constitution and Prompt Rules.

---

# Example Sentence

Purpose:

Show real usage.

Requirements:

Simple English.

CEFR appropriate.

One sentence.

Natural.

---

# Difficulty

Allowed values:

A1

A2

B1

B2

C1

C2

No other values are allowed.

---

# Forbidden Content

Never return:

Grammar explanations.

IPA transcription.

Long dictionary definitions.

AI reasoning.

Internal thinking.

Markdown tables.

Multiple stories.

Multiple meanings unless explicitly requested.

---

# Validation Rules

The response is invalid if:

Any required field is missing.

Story is empty.

Meaning is empty.

Word is empty.

Story exceeds the maximum length.

Difficulty is invalid.

Sound association is empty.

---

# Error Handling

If the AI cannot confidently generate a mnemonic:

Never invent meaningless output.

Instead:

Return a structured error.

The application will decide how to handle it.

---

# Consistency

All AI providers must follow exactly the same structure.

Switching providers should never require changing Telegram handlers.

---

# Future Compatibility

New fields may be added in future versions.

Existing fields must remain backward compatible whenever possible.

---

# Final Principle

The AI returns structured information.

MemoraBot decides how that information is displayed to the user.

Presentation belongs to the application.

Knowledge belongs to the AI.

These responsibilities must always remain separate.
