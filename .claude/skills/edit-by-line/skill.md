# Line-by-Line Editor Skill

A voice-driven interactive editor for making precise line-based edits to markdown files with automatic backup and confirmation workflow.

## Purpose

Enable hands-free editing of documentation files by:
- Displaying files with line numbers
- Accepting natural voice commands like "change line 47 to..."
- Showing before/after previews
- Requiring confirmation before applying changes
- Auto-creating timestamped backups

## Invocation

User invokes with: `/edit-by-line <filepath>`

Example: `/edit-by-line observations/scenario_evaluation_results.md`

## Workflow

### 1. Initialize Session

When invoked:
1. Read and display the target file with line numbers
2. Create `.backups/` directory if it doesn't exist
3. Create a timestamped backup in `.backups/` (format: `filename.YYYYMMDD_HHMMSS.bak`)
4. Display total line count
5. Enter interactive editing mode
6. Show available commands

**Example output:**
```
📝 Editing: observations/scenario_evaluation_results.md
💾 Backup created: .backups/scenario_evaluation_results.md.20260109_143022.bak
📊 Total lines: 277

[File contents with line numbers displayed]

✨ Edit mode active. Available commands:
- "line N: [new text]" - Replace entire line
- "line N edit: [description]" - Modify line based on your description
- "lines N-M: [new text]" - Replace multiple lines
- "done" or "exit" - Finish editing and show summary
```

### 2. Accept Edit Commands

Parse natural voice-style commands in these formats:

**Format 1: Direct replacement**
- "line 47: The new text for this line"
- "line 142 change to: Updated text here"
- "replace line 89 with: New content"

**Format 2: Descriptive edit**
- "line 47 edit: make this more concise"
- "line 89 rewrite: change to past tense"
- "line 120 modify: add emphasis on the paradox"

**Format 3: Multi-line replacement**
- "lines 50-52: New paragraph replacing these three lines"

### 3. Preview and Confirm

For EVERY edit request:

1. **Show the change clearly:**
```
📍 Line 47

BEFORE:
│ The ECL constitution produces stronger alignment

AFTER:
│ The ECL-pilled constitution produces significantly stronger alignment

Apply this change? (yes/commit/skip)
```

2. **Wait for confirmation:**
   - "yes" / "commit" / "apply" → Apply the change
   - "no" / "skip" / "cancel" → Skip this change
   - Any other response → Ask for clarification

3. **If confirmed:** Apply the edit using the Edit tool

4. **Track the change** for the session summary

### 4. Session Management

**During session:**
- Keep track of all changes (applied and skipped)
- Show running count: "✓ 3 changes applied, 1 skipped"

**On "done" or "exit":**
- Display session summary
- Show all applied changes
- Remind about backup location

**Example summary:**
```
✅ Editing session complete!

Applied 3 changes:
- Line 47: Strengthened phrasing
- Line 89: Made more concise
- Line 142: Fixed typo

💾 Original backed up to: .backups/scenario_evaluation_results.md.20260109_143022.bak

To undo all changes: cp .backups/scenario_evaluation_results.md.20260109_143022.bak observations/scenario_evaluation_results.md
```

## Command Parsing Rules

Be flexible with voice-style input:

**Accept variations:**
- "line 47" / "line number 47" / "on line 47"
- "change to" / "replace with" / "make it say"
- "edit to say" / "rewrite as" / "update to"

**Handle typos/voice errors:**
- If line number is unclear, ask: "Did you mean line 47 or 74?"
- If edit description is vague, show options: "Should I make it shorter, more formal, or rephrase entirely?"

**Special cases:**
- If user references "the line about X", search for it and confirm: "I found 'X' on line 47. Edit this line?"

## Safety Rules

**CRITICAL - Never skip these:**

1. ✅ **ALWAYS create backup** before first edit
2. ✅ **ALWAYS show preview** before applying changes
3. ✅ **ALWAYS wait for confirmation** - never auto-apply
4. ✅ **NEVER edit without Read tool first** - must see current content
5. ✅ **Track session state** - remember what's been changed

**If user says "commit all" or "apply all":**
- Still show each change one-by-one
- Ask "Confirm all N changes?" before batch applying

## Error Handling

**If line number doesn't exist:**
```
⚠️ Line 500 doesn't exist (file has 277 lines)
Did you mean line 277 (last line)?
```

**If Edit tool fails:**
```
❌ Edit failed - the text may have changed since we started
Would you like me to:
1. Re-read the file and try again
2. Skip this edit
3. Exit editing mode
```

**If file was externally modified:**
- Detect via file hash/timestamp mismatch
- Warn user and offer to restart session

## Advanced Features

**Multi-edit support:**
If user gives multiple edits at once, queue them:
```
User: "Change line 47 to 'new text' and line 89 to 'other text'"

Response: "Got it - 2 edits queued:
1. Line 47
2. Line 89

Let's preview the first one..."
```

**Search and edit:**
```
User: "Find the line about self-censorship and make it a heading"

Response: "Found on line 109:
'The Gemini model appears to have self-censored...'

Change to:
'## The Self-Censorship Paradox'

Apply this change?"
```

## Example Session

```
User: /edit-by-line observations/scenario_evaluation_results.md

Claude: 📝 Editing: observations/scenario_evaluation_results.md
💾 Backup created: .backups/scenario_evaluation_results.md.20260109_143022.bak
📊 Total lines: 277

[File contents displayed with line numbers]

✨ Edit mode active. Commands: "line N: text", "line N edit: description", "done"
🤖 Using Haiku for simple edits, Sonnet for complex ones

User: line 47 change to: The ECL-pilled constitution produces significantly stronger alignment

Claude: 📍 Line 47

BEFORE:
│ The ECL constitution produces stronger alignment

AFTER:
│ The ECL-pilled constitution produces significantly stronger alignment

Apply this change? (yes/skip)

User: yes

Claude: ✅ Applied! (1 change so far)

User: line 109 edit: make this a heading that says "The Self-Censorship Paradox"

Claude: 📍 Line 109

BEFORE:
│ The Gemini model appears to have applied its RLHF safety training to self-censor cosmic reasoning.

AFTER:
│ ### The Self-Censorship Paradox

Apply this change? (yes/skip)

User: yes

Claude: ✅ Applied! (2 changes so far)

User: done

Claude: ✅ Editing session complete!

Applied 2 changes:
- Line 47: Enhanced terminology (ECL → ECL-pilled) [Haiku]
- Line 109: Converted to section heading [Sonnet]

💾 Original backed up to: .backups/scenario_evaluation_results.md.20260109_143022.bak

To undo: cp .backups/scenario_evaluation_results.md.20260109_143022.bak observations/scenario_evaluation_results.md
```

## Notes for Implementation

**Model Selection:**
- Use **Haiku** for simple line edits (cheap, fast, perfect for straightforward replacements)
- Use **Sonnet** for descriptive edits (e.g., "line 89 edit: make this more concise") where interpretation is needed
- Switch model via parameter if needed: `/edit-by-line observations/file.md --model haiku`

**State tracking:**
- Maintain a list of pending edits
- Track which edits have been applied
- Remember backup file path for session

**Voice-friendly parsing:**
- Use flexible regex patterns for command matching
- Normalize input (lowercase, strip punctuation)
- Handle common speech-to-text errors (homonyms, number formats)

**File integrity:**
- Hash file content at session start
- Before each edit, verify Read matches expectations
- If mismatch detected, re-read and continue

**Backup management:**
- Store all backups in `.backups/` directory
- Add `.backups/` to `.gitignore` if not already there
- Preserve relative path structure: `observations/file.md` → `.backups/file.md.TIMESTAMP.bak`

## Usage Tips

**For quick single edits:**
Just use the Edit tool directly - this skill is for multi-edit sessions.

**For reviewing before editing:**
First do `/edit-by-line filename` to see line numbers, then exit and use regular Edit if you only need one change.

**For voice dictation:**
Speak clearly and pause between commands. The skill is designed to be forgiving of natural speech patterns.

**First time setup:**
Add `.backups/` to your `.gitignore` to avoid committing backup files:
```bash
echo ".backups/" >> .gitignore
```