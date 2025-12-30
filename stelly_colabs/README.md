# Stelly Colabs - Cosmic Host Research Notebooks

*Last updated: December 30, 2024*

## What is this?

This directory contains Google Colab notebooks from Nov stay at Constellation exploring how AI systems reason about cosmic-scale moral considerations. The work centers on Nick Bostrom's "Cosmic Host" hypothesis and uses a "pseudo-moral parliament" frameworks to test whether constitutional framing affects how LLMs make ethical decisions.

**Key experiments:**
- Testing how LLM recursively chat about cosmic host
- Critic-defender-judge debate pipelines evaluating arguments about AI alignment
- Moral parliaments with weighted delegates evaluating ASI constitutions
- Scenario testing to see if constitutional framing changes model behavior

## Getting Started

These are Google Colab notebooks that use OpenAI, Anthropic, and Google Gemini APIs. Each notebook is self-contained and includes setup instructions.

**For technical documentation** (architecture, implementation details, common workflows), see **[CLAUDE.md](CLAUDE.md)**.

## Current Status

**Note:** Active development has moved to the `code_vClaude` directory (name may change when committed to GitHub). The notebooks in this directory represent the Colab-based experimental phase of the research.

## Files

- `cosmichost_llm_questions.ipynb` - LLM responses to 28 philosophical probes about cosmic host
- `cosmichost_scenarios_reflection (2).ipynb` - Testing opinion shifts after model reflections
- `cosmichost_v3__testing_deference.ipynb` - Evaluating model deference to cosmic considerations
- `mp_made_asiconst.ipynb` - Moral parliament evaluation of AI constitutions
- `mp_test_scenarios.ipynb` - Comprehensive scenario testing framework (192 cells)

## Questions?

If you're trying to understand the codebase architecture or run experiments, start with [CLAUDE.md](CLAUDE.md).
