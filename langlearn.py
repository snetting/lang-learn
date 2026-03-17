import argparse
import json
import os
import random
import sys
import tkinter as tk
from tkinter import ttk, messagebox

# Constants
PROGRESS_FILE = ".langlearn_progress.json"
INITIAL_WINDOW_SIZE = 10
MIN_WINDOW_SIZE = 5
SCORE_STEP = 1
SCORE_PENALTY = 2
INCREASE_THRESHOLD = 3.0  # Average score to increase window
DECREASE_THRESHOLD = 1.0  # Average score to decrease window

# ANSI Color codes for better UI (CLI only)
RED = '\033[0;31m'
GREEN = '\033[0;32m'
BLUE = '\033[0;34m'
NC = '\033[0m' # No Color

class LanguageLearner:
    def __init__(self, datafile, limit=None):
        self.datafile = datafile
        self.limit = limit
        self.datafile_abs = os.path.abspath(datafile)
        self.data = []
        self.progress_all = {}
        self.file_progress = {}
        self.scores = {}
        self.window_size = INITIAL_WINDOW_SIZE
        self.points = 0
        self.total = 0
        
        self.current_question = None
        
        self.load_data()
        self.load_progress()

    def load_data(self):
        if not os.path.exists(self.datafile):
            raise FileNotFoundError(f"File '{self.datafile}' not found.")
        
        with open(self.datafile, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line or ':' not in line:
                    continue
                self.data.append(line)
        
        if self.limit:
            self.data = self.data[:self.limit]
        
        if not self.data:
            raise ValueError(f"Data file '{self.datafile}' is empty or invalid.")

    def load_progress(self):
        if os.path.exists(PROGRESS_FILE):
            try:
                with open(PROGRESS_FILE, 'r', encoding='utf-8') as f:
                    self.progress_all = json.load(f)
            except (json.JSONDecodeError, IOError):
                self.progress_all = {}
        
        self.file_progress = self.progress_all.get(self.datafile_abs, {
            "window_size": INITIAL_WINDOW_SIZE,
            "scores": {}
        })
        self.scores = self.file_progress.setdefault("scores", {})
        self.window_size = self.file_progress.get("window_size", INITIAL_WINDOW_SIZE)

    def save_progress(self):
        self.file_progress["window_size"] = self.window_size
        self.file_progress["scores"] = self.scores
        self.progress_all[self.datafile_abs] = self.file_progress
        try:
            with open(PROGRESS_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.progress_all, f, indent=2)
        except IOError as e:
            print(f"Warning: Could not save progress: {e}")

    def reset_progress(self):
        if self.datafile_abs in self.progress_all:
            del self.progress_all[self.datafile_abs]
            self.save_progress()
            self.load_progress() # Reload default

    def get_next_question(self):
        current_window_size = min(self.window_size, len(self.data))
        active_data = self.data[:current_window_size]
        
        weights = []
        for pair in active_data:
            score = self.scores.get(pair, 0)
            # Weighted selection: lower score = higher probability
            weight = 1.0 / (max(0, score) + 1.0)
            weights.append(weight)
            
        pair = random.choices(active_data, weights=weights, k=1)[0]
        parts = pair.split(':', 1)
        word1 = parts[0].strip().lower()
        word2 = parts[1].strip().lower()
        
        # Decide direction
        direction = random.randint(0, 1)
        if direction == 1:
            q, a = word2, word1
        else:
            q, a = word1, word2
            
        self.current_question = {
            'pair': pair,
            'question': q,
            'answer': a,
            'word1': word1,
            'word2': word2
        }
        return self.current_question

    def check_answer(self, user_input):
        if not self.current_question:
            return False, "No active question", None
        
        pair = self.current_question['pair']
        correct_answer = self.current_question['answer']
        
        is_correct = user_input.strip().lower() == correct_answer.lower()
        self.total += 1
        
        if is_correct:
            self.points += 1
            self.scores[pair] = self.scores.get(pair, 0) + SCORE_STEP
        else:
            self.scores[pair] = max(0, self.scores.get(pair, 0) - SCORE_PENALTY)
            
        adjustment_msg = self._adjust_window()
        self.save_progress()
        
        return is_correct, correct_answer, adjustment_msg

    def _adjust_window(self):
        current_window_size = min(self.window_size, len(self.data))
        active_data = self.data[:current_window_size]
        if not active_data:
            return None

        avg_score = sum(self.scores.get(p, 0) for p in active_data) / len(active_data)
        
        if avg_score > INCREASE_THRESHOLD and self.window_size < len(self.data):
            self.window_size += 1
            return f"Nice! Performance is good. Increasing window size to {self.window_size}"
        elif avg_score < DECREASE_THRESHOLD and self.window_size > MIN_WINDOW_SIZE:
            self.window_size -= 1
            return f"Difficulty adjusted. Decreasing window size to {self.window_size}"
        return None


class LanguageLearnerGUI:
    def __init__(self, root, learner):
        self.learner = learner
        self.root = root
        self.root.title("Language Learner")
        self.root.geometry("600x450")
        
        self.style = ttk.Style()
        self.style.theme_use('clam')
        self.style.configure("TLabel", font=("Helvetica", 12))
        self.style.configure("Header.TLabel", font=("Helvetica", 14))
        self.style.configure("Question.TLabel", font=("Helvetica", 28, "bold"))
        self.style.configure("Feedback.TLabel", font=("Helvetica", 14, "italic"))
        
        self.main_frame = ttk.Frame(root, padding="30")
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Header
        self.header_label = ttk.Label(self.main_frame, text="Translate the word:", style="Header.TLabel")
        self.header_label.pack(pady=(0, 10))
        
        # Question
        self.question_var = tk.StringVar()
        self.question_label = ttk.Label(self.main_frame, textvariable=self.question_var, style="Question.TLabel", foreground="#2c3e50")
        self.question_label.pack(pady=20)
        
        # Input
        self.answer_entry = ttk.Entry(self.main_frame, font=("Helvetica", 18), justify='center')
        self.answer_entry.pack(pady=10, fill=tk.X)
        self.answer_entry.focus()
        
        # Feedback
        self.feedback_var = tk.StringVar()
        self.feedback_label = ttk.Label(self.main_frame, textvariable=self.feedback_var, style="Feedback.TLabel")
        self.feedback_label.pack(pady=15)
        
        # Adjustment Message
        self.adjustment_var = tk.StringVar()
        self.adjustment_label = ttk.Label(self.main_frame, textvariable=self.adjustment_var, font=("Helvetica", 10), foreground="#e67e22")
        self.adjustment_label.pack(pady=5)
        
        # Stats
        self.stats_var = tk.StringVar()
        self.stats_label = ttk.Label(self.main_frame, textvariable=self.stats_var, font=("Helvetica", 11), foreground="#7f8c8d")
        self.stats_label.pack(side=tk.BOTTOM, pady=10)
        
        # Buttons
        self.btn_frame = ttk.Frame(self.main_frame)
        self.btn_frame.pack(pady=20)
        
        button_font = ("Helvetica", 12, "bold")
        
        self.submit_btn = tk.Button(self.btn_frame, text="Submit (Enter)", command=self.submit_answer,
                                    font=button_font, width=15, height=2, bg="#e1e1e1")
        self.submit_btn.pack(side=tk.LEFT, padx=10)
        
        self.next_btn = tk.Button(self.btn_frame, text="Next (Enter)", command=self.next_question, 
                                  state=tk.DISABLED, font=button_font, width=15, height=2, bg="#e1e1e1")
        self.next_btn.pack(side=tk.LEFT, padx=10)

        # Global bindings
        self.root.bind('<Return>', self.handle_enter)
        self.root.bind('<Escape>', lambda e: self.root.quit())

        self.next_question()

    def handle_enter(self, event=None):
        if self.next_btn['state'] == tk.NORMAL:
            self.next_question()
        else:
            self.submit_answer()

    def next_question(self):
        self.learner.get_next_question()
        self.question_var.set(self.learner.current_question['question'])
        
        self.answer_entry.config(state=tk.NORMAL)
        self.answer_entry.delete(0, tk.END)
        self.answer_entry.focus()
        
        self.feedback_var.set("")
        self.adjustment_var.set("")
        self.next_btn.config(state=tk.DISABLED)
        self.submit_btn.config(state=tk.NORMAL)
        self.update_stats()

    def submit_answer(self, event=None):
        user_input = self.answer_entry.get().strip()

        is_correct, correct_answer, adjustment_msg = self.learner.check_answer(user_input)
        
        if adjustment_msg:
             self.adjustment_var.set(adjustment_msg)

        if is_correct:
            self.feedback_var.set("✓ Correct!")
            self.feedback_label.config(foreground="#27ae60")
        else:
            self.feedback_var.set(f"✗ Wrong! Correct: {correct_answer}")
            self.feedback_label.config(foreground="#c0392b")
            
        self.answer_entry.config(state=tk.DISABLED)
        self.submit_btn.config(state=tk.DISABLED)
        self.next_btn.config(state=tk.NORMAL)
        self.next_btn.focus()
        self.update_stats()

    def update_stats(self):
        stats = f"Score: {self.learner.points}/{self.learner.total} | Window: {self.learner.window_size}"
        self.stats_var.set(stats)


def run_cli(learner):
    print(f"\nDatabase size: {len(learner.data)}")
    print(f"Active window size: {learner.window_size}")
    print("Press Ctrl-C to exit.\n")
    
    try:
        while True:
            q_data = learner.get_next_question()
            q_word = q_data['question']
            correct_ans = q_data['answer']
            
            print(f"---")
            print(f"Translate {BLUE}{q_word}{NC}: ", end="", flush=True)
            
            try:
                user_input = sys.stdin.readline()
                if not user_input:
                    break
                user_input = user_input.strip()
            except KeyboardInterrupt:
                break
            
            is_correct, _, adjustment_msg = learner.check_answer(user_input)
            
            if is_correct:
                print(f"{GREEN}Correct!{NC}")
            else:
                print(f"{RED}Wrong - correct answer is: {correct_ans}{NC}")
                print(f"Type the pair to remember: {q_word} - {correct_ans}: ", end="", flush=True)
                sys.stdin.readline()
            
            if adjustment_msg:
                color = GREEN if "Increasing" in adjustment_msg else RED
                print(f"{color}{adjustment_msg}{NC}")

            percent = 0

            if learner.total > 0:
                percent = (learner.points * 100) // learner.total
            print(f"Score: {learner.points} / {learner.total} ({percent}%)\n")
            
    except KeyboardInterrupt:
        pass
    finally:
        print("\n\n--- Session Summary ---")
        if learner.total > 0:
            percent = (learner.points * 100) // learner.total
            print(f"Final Score: {GREEN}{learner.points}{NC} / {learner.total} ({BLUE}{percent}%{NC})")
        else:
            print("No questions answered.")
        print("Goodbye!\n---\n")


def main():
    parser = argparse.ArgumentParser(description="Adaptive language learning quiz.")
    parser.add_argument("datafile", help="Colon-separated text file (word:translation)")
    parser.add_argument("limit", type=int, nargs='?', help="Optional. Only use the first N lines of the file.")
    parser.add_argument("--forget-progress", action="store_true", help="Erase existing progress for this file.")
    parser.add_argument("--gui", action="store_true", help="Launch in GUI mode.")
    
    args = parser.parse_args()
    
    try:
        learner = LanguageLearner(args.datafile, args.limit)
    except Exception as e:
        print(f"{RED}Error: {e}{NC}")
        sys.exit(1)

    if args.forget_progress:
        learner.reset_progress()
        print(f"Progress for '{args.datafile}' forgotten.")
        return

    if args.gui:
        root = tk.Tk()
        app = LanguageLearnerGUI(root, learner)
        root.mainloop()
    else:
        run_cli(learner)

if __name__ == "__main__":
    main()
