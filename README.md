# lang-learn

An adaptive language learning tool to assist with vocabulary through a terminal-based quiz.

## Features

- **Adaptive Learning**: Focuses on a "working set" of words. As you master them, the set grows. If you struggle, it shrinks to help you focus.
- **Weighted Selection**: Words you find difficult (lower scores) appear more frequently than those you've mastered.
- **Persistence**: Saves your progress automatically in `.langlearn_progress.json`. You can stop and resume anytime.
- **Bidirectional Quiz**: Randomly swaps the translation direction.
- **Visual Feedback**: ANSI color-coded output for a better experience.

## Usage

You can use the new Python implementation directly or via the shell wrapper.

### Python (Recommended)

```bash
python3 langlearn.py <datafile> [limit]
```

- **datafile**: Path to a colon-separated text file (e.g., `basics.dat`).
- **limit** (optional): Restrict the quiz to the first *N* lines of the data file.
- **--forget-progress**: Reset your progress for the specified datafile.

Example:
```bash
python3 langlearn.py top1000.dat 100
```

### Shell Wrapper

```bash
./langlearn.sh <datafile> [limit]
```

## How it Works

The tool maintains an "active window" into your vocabulary list.
1. It picks words from this window using weighted random selection (lower scores = higher priority).
2. Correct answers increase a word's score; incorrect answers decrease it.
3. If your average score in the current window is high, the window expands to include new words.
4. If you start forgetting words, the window may shrink to help you focus on the basics.

## Data Format

The script expects a simple colon-separated text file:

```text
me:mina
you:sina
and:ja
```

## Exiting

Press `Ctrl+C` at any time to exit and see your session summary. Progress is saved after every question.
