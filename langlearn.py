import argparse
import json
import os
import random
import sys

# Constants
PROGRESS_FILE = ".langlearn_progress.json"
INITIAL_WINDOW_SIZE = 10
MIN_WINDOW_SIZE = 5
SCORE_STEP = 1
SCORE_PENALTY = 2
INCREASE_THRESHOLD = 3.0  # Average score to increase window
DECREASE_THRESHOLD = 1.0  # Average score to decrease window

# ANSI Color codes for better UI
RED = '\033[0;31m'
GREEN = '\033[0;32m'
BLUE = '\033[0;34m'
NC = '\033[0m' # No Color

def load_data(file_path, limit=None):
    if not os.path.exists(file_path):
        print(f"{RED}Error: File '{file_path}' not found.{NC}")
        sys.exit(1)
    
    data = []
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line or ':' not in line:
                continue
            data.append(line)
    
    if limit:
        data = data[:limit]
    
    if not data:
        print(f"{RED}Error: Data file '{file_path}' is empty or invalid.{NC}")
        sys.exit(1)
        
    return data

def load_progress():
    if os.path.exists(PROGRESS_FILE):
        try:
            with open(PROGRESS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return {}
    return {}

def save_progress(progress):
    try:
        with open(PROGRESS_FILE, 'w', encoding='utf-8') as f:
            json.dump(progress, f, indent=2)
    except IOError as e:
        print(f"{RED}Warning: Could not save progress: {e}{NC}")

def main():
    parser = argparse.ArgumentParser(description="Adaptive language learning quiz.")
    parser.add_argument("datafile", help="Colon-separated text file (word:translation)")
    parser.add_argument("limit", type=int, nargs='?', help="Optional. Only use the first N lines of the file.")
    parser.add_argument("--forget-progress", action="store_true", help="Erase existing progress for this file.")
    
    args = parser.parse_args()
    
    # Resolve absolute path for consistent progress tracking
    datafile_abs = os.path.abspath(args.datafile)
    
    if args.forget_progress:
        progress = load_progress()
        if datafile_abs in progress:
            del progress[datafile_abs]
            save_progress(progress)
            print(f"Progress for '{args.datafile}' forgotten.")
        else:
            print(f"No progress found for '{args.datafile}'.")
        return

    data = load_data(args.datafile, args.limit)
    progress_all = load_progress()
    
    # Get progress for this file
    file_progress = progress_all.get(datafile_abs, {
        "window_size": INITIAL_WINDOW_SIZE,
        "scores": {}
    })
    
    scores = file_progress.setdefault("scores", {})
    window_size = file_progress.get("window_size", INITIAL_WINDOW_SIZE)
    
    # Main Loop
    points = 0
    total = 0
    
    print(f"\nDatabase size: {len(data)}")
    print(f"Active window size: {window_size}")
    print("Press Ctrl-C to exit.\n")
    
    try:
        while True:
            # Ensure window size is within bounds
            current_window_size = min(window_size, len(data))
            active_data = data[:current_window_size]
            
            weights = []
            for pair in active_data:
                score = scores.get(pair, 0)
                # Weighted selection: lower score = higher probability
                weight = 1.0 / (max(0, score) + 1.0)
                weights.append(weight)
            
            # Choice
            pair = random.choices(active_data, weights=weights, k=1)[0]
            
            parts = pair.split(':', 1)
            word1 = parts[0].strip().lower()
            word2 = parts[1].strip().lower()
            
            if random.randint(0, 1) == 1:
                q, a = word2, word1
            else:
                q, a = word1, word2
                
            print(f"---")
            print(f"Translate {BLUE}{q}{NC}: ", end="", flush=True)
            
            try:
                user_input = sys.stdin.readline()
                if not user_input: # EOF
                    break
                user_input = user_input.strip().lower()
            except KeyboardInterrupt:
                break
            
            total += 1
            if user_input == a:
                print(f"{GREEN}Correct!{NC}")
                points += 1
                scores[pair] = scores.get(pair, 0) + SCORE_STEP
            else:
                print(f"{RED}Wrong - correct answer is: {a}{NC}")
                print(f"Type the pair to remember: {q} - {a}: ", end="", flush=True)
                sys.stdin.readline()
                scores[pair] = max(0, scores.get(pair, 0) - SCORE_PENALTY)
            
            # Adaptive window logic:
            avg_score = sum(scores.get(p, 0) for p in active_data) / len(active_data)
            
            if avg_score > INCREASE_THRESHOLD and window_size < len(data):
                window_size += 1
                print(f"{GREEN}Nice! Performance is good. Increasing window size to {window_size}{NC}")
            elif avg_score < DECREASE_THRESHOLD and window_size > MIN_WINDOW_SIZE:
                window_size -= 1
                print(f"{RED}Difficulty adjusted. Decreasing window size to {window_size}{NC}")
            
            file_progress["window_size"] = window_size
            progress_all[datafile_abs] = file_progress
            save_progress(progress_all)
            
            print(f"Score: {points} / {total}\n")
            
    except KeyboardInterrupt:
        pass
    finally:
        print("\n\n--- Session Summary ---")
        if total > 0:
            percent = (points * 100) // total
            print(f"Final Score: {GREEN}{points}{NC} / {total} ({BLUE}{percent}%{NC})")
        else:
            print("No questions answered.")
        print("Goodbye!\n---\n")

if __name__ == "__main__":
    main()
