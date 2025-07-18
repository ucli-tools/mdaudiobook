# YAML Frontmatter Metadata Guide

## Overview

mdaudiobook uses YAML frontmatter for document metadata. This standardized format is shared with mdtexpdf for unified metadata handling across both tools.

## Template Structure

The metadata is organized into three distinct sections:

1. **Common Metadata** - Used by both mdtexpdf and mdaudiobook
2. **PDF-Specific Metadata** - Used only by mdtexpdf (ignored by mdaudiobook)
3. **Audio-Specific Metadata** - Used only by mdaudiobook

## Complete Template

```yaml
---
# =============================================================================
# COMMON METADATA (used by both mdtexpdf and mdaudiobook)
# =============================================================================
title: "Document Title"
author: "Author Name"
date: "2025-01-01"
description: "Brief description of the document content"
language: "en"

# =============================================================================
# PDF-SPECIFIC METADATA (mdtexpdf only)
# =============================================================================
# Document structure
format: "article"                    # article, book, report
section: "chapter_name"              # Section identifier
slug: "document-slug"                # URL-friendly identifier

# Table of contents
toc: true                           # Enable table of contents
toc_depth: 2                        # TOC depth (1-6)

# Section numbering
no_numbers: false                   # Disable section numbering (or use section_numbers: true)

# Headers and footers
header_footer_policy: "default"     # default, partial, all
footer: "© 2025 Author Name"        # Custom footer text
no_footer: false                    # Disable footer completely
pageof: true                        # Show "Page X of Y"
date_footer: "DD/MM/YY"            # Date format in footer
no_date: false                      # Disable date in footer

# =============================================================================
# AUDIO-SPECIFIC METADATA (mdaudiobook only)
# =============================================================================
genre: "Educational"                # Audiobook genre
narrator_voice: "en-us-standard-c"  # TTS voice identifier
reading_speed: "medium"             # slow, medium, fast
narrator: "AI Narrator"             # Narrator name for metadata
---
```

## Field Reference

### Common Metadata

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| `title` | string | Document title | "Bell's Theorem Analysis" |
| `author` | string | Author name | "Arithmoi Foundation" |
| `date` | string | Publication date | "2025-01-01" |
| `description` | string | Brief description | "Mathematical exploration of Bell's theorem" |
| `language` | string | ISO language code | "en" |

### PDF-Specific Metadata (ignored by mdaudiobook)

| Field | Type | Description | Options |
|-------|------|-------------|---------|
| `format` | string | Document format | "article", "book", "report" |
| `section` | string | Section identifier | Any string |
| `slug` | string | URL-friendly identifier | "bells-theorem" |
| `toc` | boolean | Enable table of contents | true, false |
| `toc_depth` | integer | TOC depth | 1-6 |
| `no_numbers` | boolean | Disable section numbering | true, false |
| `header_footer_policy` | string | Header/footer policy | "default", "partial", "all" |
| `footer` | string | Custom footer text | Any string |
| `no_footer` | boolean | Disable footer | true, false |
| `pageof` | boolean | Show "Page X of Y" | true, false |
| `date_footer` | string | Date format in footer | "DD/MM/YY", "MM/DD/YYYY" |
| `no_date` | boolean | Disable date in footer | true, false |

### Audio-Specific Metadata

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| `genre` | string | Audiobook genre | "Educational", "Science" |
| `narrator_voice` | string | TTS voice identifier | "en-us-standard-c" |
| `reading_speed` | string | Reading speed | "slow", "medium", "fast" |
| `narrator` | string | Narrator name | "AI Narrator" |

## Usage Examples

### Academic Paper
```yaml
---
title: "Quantum Entanglement in Bell's Theorem"
author: "Dr. Jane Smith"
date: "2025-01-15"
description: "A comprehensive analysis of quantum entanglement phenomena"
language: "en"

format: "article"
section: "physics"
no_numbers: false
toc: true
toc_depth: 3
footer: "© 2025 University Physics Department"
header_footer_policy: "default"

genre: "Educational"
narrator_voice: "en-us-standard-c"
reading_speed: "medium"
---
```

### Technical Documentation
```yaml
---
title: "API Reference Guide"
author: "Development Team"
date: "2025-01-15"
description: "Complete API documentation and examples"
language: "en"

format: "book"
section: "documentation"
toc: true
toc_depth: 4
no_numbers: false
header_footer_policy: "all"
footer: "© 2025 TechCorp - Internal Use Only"
pageof: true

genre: "Technical"
narrator_voice: "en-us-standard-b"
reading_speed: "slow"
---
```

### Audiobook-Focused Document
```yaml
---
title: "Introduction to Machine Learning"
author: "AI Research Team"
date: "2025-01-15"
description: "Beginner-friendly introduction to ML concepts"
language: "en"

# PDF fields (ignored by mdaudiobook)
format: "book"
section: "education"
toc: true

# Audio-specific configuration
genre: "Educational"
narrator_voice: "en-us-neural2-c"
reading_speed: "medium"
narrator: "Dr. Sarah Chen"
---
```

## Processing Modes

mdaudiobook supports multiple processing modes that affect how metadata is used:

- **Basic Mode**: Uses title, author, description for file naming
- **API Mode**: Enhanced with genre, narrator_voice for premium TTS
- **Hybrid Mode**: Intelligent fallback based on available metadata

## Integration with mdtexpdf

Documents with this metadata format work seamlessly with both tools:

```bash
# Generate PDF
mdtexpdf convert document.md --read-metadata

# Generate audiobook
python scripts/process_audiobook.py document.md
```

Both tools will use the appropriate metadata sections while ignoring irrelevant fields.

## Best Practices

1. **Always include common metadata** - title, author, date, description
2. **Use the 3-section structure** - Keep sections clearly separated with comments
3. **Choose appropriate voices** - Match narrator_voice to content type
4. **Set reading speed** - Consider audience and content complexity
5. **Test with both tools** - Verify metadata works with both mdtexpdf and mdaudiobook

## Troubleshooting

- **YAML parsing errors**: Check indentation and quote usage
- **Missing metadata**: Ensure required fields (title, author) are present
- **Voice not found**: Verify narrator_voice is supported by your TTS provider
- **Boolean values**: Use `true`/`false`, not `yes`/`no`
