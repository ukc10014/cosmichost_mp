# Archived Reminders

## ntfy-notebook (expired 2026-03-25)

**[Claude: remind user]** When the user mentions running a notebook cell or a long job in Jupyter/VS Code, remind them to add this snippet as the next cell so they get a phone notification when it finishes:

```python
import requests
requests.post("https://ntfy.sh/claude-2h50c6phtl", data="Notebook cell finished")
```
