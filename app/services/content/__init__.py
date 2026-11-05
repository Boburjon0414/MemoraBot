"""Content ingestion pipeline.

This package owns everything related to processing user-supplied content
(text, PDFs, images, URLs) into a form the AI layer can reason over.

Public surface
--------------
  ContentSourceType   — enum of supported input types
  ContentProcessor    — abstract base for per-type processors
  ContentProcessorRegistry — maps types to processors; lives in PlatformContainer
  PlainTextProcessor  — concrete processor for raw text (only one in Step 5)
  ContentService      — domain service: create, process, retrieve sources

Processing pipeline (per source)
----------------------------------
  1. Handler calls ContentService.create_source(user_id, type, text=...).
  2. ContentService inserts a ContentSource row with status="pending"
     (or "ready" for plain text, which needs no processing).
  3. ContentService.process(source_id) looks up the correct processor from
     the registry, calls processor.extract_text(), stores the result, and
     sets status="ready" or "failed".
  4. Step 6 (ContentChunk + EmbeddingStore) adds ContentService.index_source()
     which chunks and embeds the extracted text for semantic search.

Future processors (added one at a time, zero schema changes each time):
  PDFProcessor         — pdfminer.six / pypdf
  ImageOCRProcessor    — pytesseract or AI vision via AIRouter
  URLScraperProcessor  — httpx + html-to-text
  AudioProcessor       — Groq Whisper API
"""
