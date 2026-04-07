---
name: render-explainer
description: Render the activation projection explainer markdown to PDF with LaTeX math
user_invocable: true
---

Run this command to regenerate the PDF:

```bash
pandoc docs/activation_projection_explainer.md -o docs/activation_projection_explainer.pdf --pdf-engine=pdflatex -V geometry:margin=1in -V fontsize=11pt
```

Report success or any errors to the user.
