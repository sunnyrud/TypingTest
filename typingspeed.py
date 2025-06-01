import curses
import time

# --- Configuration ---
TARGET_TEXT = "The quick brown fox jumps over the lazy dog."
# TARGET_TEXT = "hello world example" # Shorter for quick testing
INPUT_PROMPT = "Type here: "
RESULTS_PROMPT_WPM = "WPM: "
RESULTS_PROMPT_ACCURACY = "Accuracy: "
RESULTS_PROMPT_TIME = "Time: "
EXIT_PROMPT = "Press any key to try again, or ESC to exit..."

# --- Helper Functions ---
def calculate_metrics_word_based(target_words_list, typed_segments_list, time_taken_seconds):
    """
    Calculates WPM and Task Accuracy based on word segments.
    - target_words_list: List of words from the target text.
    - typed_segments_list: List of what the user typed for each corresponding word.
    """
    correct_chars_overall = 0
    # Calculate total characters in target text including single spaces between words
    total_target_chars_for_accuracy = sum(len(w) for w in target_words_list) + max(0, len(target_words_list) - 1)

    for i in range(len(target_words_list)):
        target_word = target_words_list[i]
        # Ensure typed_segments_list is long enough before accessing
        typed_segment = typed_segments_list[i] if i < len(typed_segments_list) else ""

        # Compare char by char for the current word
        for j in range(len(target_word)):
            if j < len(typed_segment) and typed_segment[j] == target_word[j]:
                correct_chars_overall += 1
        
        # Count a correctly implied space if it's not the last word AND the user attempted the next word
        if i < len(target_words_list) - 1: # If it's not the last target word
            if i < len(typed_segments_list) -1 : # User typed a segment for current word AND for the next
                 correct_chars_overall += 1 # Count the space as correctly typed

    if time_taken_seconds == 0:
        wpm = 0
    else:
        minutes = time_taken_seconds / 60.0
        wpm = int((correct_chars_overall / 5.0) / minutes) if minutes > 0 else 0

    if total_target_chars_for_accuracy == 0:
         task_accuracy = 100.0 if correct_chars_overall == 0 else 0.0
    else:
         task_accuracy = (correct_chars_overall / total_target_chars_for_accuracy) * 100
    
    return wpm, round(task_accuracy, 2)


def display_centered_text_line(stdscr, y_pos, text, color_pair=0, attributes=0):
    """Displays a single line of text centered at a specific y_pos."""
    h, w = stdscr.getmaxyx()
    x = w // 2 - len(text) // 2
    x = max(0, x) # Ensure x is not negative
    y = y_pos
    try:
        stdscr.addstr(y, x, text, curses.color_pair(color_pair) | attributes)
    except curses.error: # Fallback if too long or window too small
        try:
            stdscr.addstr(y, 0, text[:w-1], curses.color_pair(color_pair) | attributes)
        except curses.error:
            pass # Ultimate fallback: do nothing if window is impossibly small


# --- Main Application Logic ---
def typing_test_app(stdscr):
    curses.start_color()
    curses.use_default_colors() # Use terminal's default background
    curses.init_pair(1, curses.COLOR_GREEN, -1)  # Correct text (default background)
    curses.init_pair(2, curses.COLOR_RED, -1)    # Incorrect text (default background)
    curses.init_pair(3, curses.COLOR_CYAN, -1)   # Prompts / Info (default background)
    curses.init_pair(4, curses.COLOR_YELLOW, -1) # Titles / Important (default background)
    curses.init_pair(5, curses.COLOR_WHITE, -1) # Default text (not yet typed) (default background)
    curses.init_pair(6, curses.COLOR_BLUE, -1) # Cursor color (default background)


    curses.curs_set(0) # Hide actual terminal cursor
    stdscr.nodelay(False) # Blocking getch

    while True: # Outer loop for retrying
        active_target_text = TARGET_TEXT
        target_words = active_target_text.split(' ')
        
        typed_segments = [] 
        current_word_input = "" 
        current_word_idx = 0    
        
        start_time = 0
        time_taken = 0
        input_active = True
        
        while input_active: # Inner loop for a single typing session
            stdscr.clear()
            h, w = stdscr.getmaxyx()

            if h < 10 or w < len(active_target_text) + 10 : # Basic terminal size check
                display_centered_text_line(stdscr, h // 2, "Terminal too small. Please resize.", 2)
                stdscr.refresh()
                key = stdscr.getch()
                if key == ord('q') or key == 27: return
                continue

            # --- Display ---
            # Title
            display_centered_text_line(stdscr, h // 2 - 4, "Typing Speed Test", 4, curses.A_BOLD)
            
            # Static Target Text Line (for reference)
            target_line_y = h // 2 - 2
            display_centered_text_line(stdscr, target_line_y, "Target: " + active_target_text, 3)

            # Interactive "Type here:" line
            type_here_line_y = h // 2
            
            # Calculate starting X for centering the interactive line content
            # Max length of what could be displayed (prompt + full target text)
            full_interactive_line_len = len(INPUT_PROMPT) + len(active_target_text) + len(target_words) # spaces
            interactive_start_x = w // 2 - full_interactive_line_len // 2
            interactive_start_x = max(0, interactive_start_x) # Ensure not negative

            current_display_x = interactive_start_x
            
            # Display INPUT_PROMPT
            if current_display_x + len(INPUT_PROMPT) < w:
                stdscr.addstr(type_here_line_y, current_display_x, INPUT_PROMPT, curses.color_pair(3))
            current_display_x += len(INPUT_PROMPT)

            # Render the words (typed, current, or future target)
            for i in range(len(target_words)):
                if current_display_x >= w -1 : break 
                target_word_segment = target_words[i]
                
                if i < current_word_idx: # Word already processed (in typed_segments)
                    user_typed_segment = typed_segments[i]
                    for j, char_typed in enumerate(user_typed_segment):
                        if current_display_x >= w -1 : break
                        target_char = target_word_segment[j] if j < len(target_word_segment) else ' ' # Handle overtyping
                        color = curses.color_pair(1) if char_typed == target_char else curses.color_pair(2)
                        stdscr.addch(type_here_line_y, current_display_x, char_typed, color)
                        current_display_x += 1
                    # If user typed less than target word, show remaining target chars in default
                    if len(user_typed_segment) < len(target_word_segment):
                        for j in range(len(user_typed_segment), len(target_word_segment)):
                            if current_display_x >= w-1: break
                            stdscr.addch(type_here_line_y, current_display_x, target_word_segment[j], curses.color_pair(5)) # Untyped part
                            current_display_x +=1

                elif i == current_word_idx: # Current word being typed
                    for j, char_typed in enumerate(current_word_input):
                        if current_display_x >= w -1 : break
                        target_char = target_word_segment[j] if j < len(target_word_segment) else ' '
                        color = curses.color_pair(1) if char_typed == target_char else curses.color_pair(2)
                        stdscr.addch(type_here_line_y, current_display_x, char_typed, color)
                        current_display_x += 1
                    # Display simulated cursor for current word
                    if current_display_x < w -1:
                         cursor_char = ' '
                         if len(current_word_input) < len(target_word_segment):
                             cursor_char = target_word_segment[len(current_word_input)]
                         elif len(current_word_input) == len(target_word_segment):
                             cursor_char = ' ' # Space after word
                         stdscr.addch(type_here_line_y, current_display_x, cursor_char, curses.A_REVERSE | curses.color_pair(6))
                    
                    # Display remaining part of current target word if not yet typed
                    for j in range(len(current_word_input), len(target_word_segment)):
                        if current_display_x >= w -1 : break
                        # Skip the char at cursor position as it's handled by cursor display
                        if j == len(current_word_input) and current_display_x < w -1 :
                            current_display_x +=1 # Advance past cursor
                            if current_display_x >= w -1 : break
                        
                        if j < len(target_word_segment): # Check again due to cursor advance
                            stdscr.addch(type_here_line_y, current_display_x, target_word_segment[j], curses.color_pair(5))
                            current_display_x += 1


                else: # Future words (not yet reached by user)
                    for char_target in target_word_segment:
                        if current_display_x >= w -1 : break
                        stdscr.addch(type_here_line_y, current_display_x, char_target, curses.color_pair(5))
                        current_display_x += 1
                
                # Add space after word if not the last word
                if i < len(target_words) - 1:
                    if current_display_x >= w -1 : break
                    stdscr.addch(type_here_line_y, current_display_x, ' ')
                    current_display_x += 1
            
            stdscr.refresh()

            # --- Input Handling ---
            if not start_time and (current_word_input or typed_segments):
                start_time = time.time()

            key = stdscr.getch()

            if key:
                if not start_time: start_time = time.time()

                if key == curses.KEY_ENTER or key == 10 or key == 13:
                    if current_word_input or typed_segments : 
                        if current_word_idx < len(target_words):
                             typed_segments.append(current_word_input)
                             while len(typed_segments) < len(target_words):
                                 typed_segments.append("")
                        input_active = False 
                        if start_time: time_taken = time.time() - start_time
                        else: time_taken = 0
                    continue 

                elif key == ord(' '): # Space key
                    if not current_word_input: # Case: Space pressed when current word input is empty
                        curses.flash() # User must type something in the current word first
                    elif current_word_idx < len(target_words):
                        typed_segments.append(current_word_input)
                        current_word_input = ""
                        current_word_idx += 1
                        if current_word_idx == len(target_words): # Test ends if space after last word
                            input_active = False 
                            if start_time: time_taken = time.time() - start_time
                            else: time_taken = 0
                    # If current_word_idx is already at/past len(target_words), space might end test
                    elif current_word_idx >= len(target_words):
                        input_active = False 
                        if start_time: time_taken = time.time() - start_time
                        else: time_taken = 0


                elif key == curses.KEY_BACKSPACE or key == 127 or key == 8:
                    if current_word_input:
                        current_word_input = current_word_input[:-1]
                    elif typed_segments and current_word_idx > 0: # Can backspace into previous word
                        current_word_idx -= 1
                        current_word_input = typed_segments.pop()
                
                elif 32 < key <= 126: # Printable characters
                    if current_word_idx < len(target_words):
                        # Allow typing slightly beyond target word length for flexibility
                        if len(current_word_input) < len(target_words[current_word_idx]) + 5:
                             current_word_input += chr(key)
                        else:
                            curses.flash() 
                    elif current_word_idx >= len(target_words): # Typing after all target words
                        curses.flash() # Or handle as "extra typing" not scored

                elif key == 27: # ESC
                    return 
        
        # --- Results Display ---
        while len(typed_segments) < len(target_words): # Ensure segments list matches target words length
            typed_segments.append("")

        wpm, accuracy = calculate_metrics_word_based(target_words, typed_segments, time_taken)

        stdscr.clear()
        results_y_start = h // 2 - 2
        display_centered_text_line(stdscr, results_y_start -1 , "--- Results ---", 4, curses.A_BOLD)
        display_centered_text_line(stdscr, results_y_start + 1, f"{RESULTS_PROMPT_WPM}{wpm}", 3)
        display_centered_text_line(stdscr, results_y_start + 2,  f"{RESULTS_PROMPT_ACCURACY}{accuracy}%", 3)
        display_centered_text_line(stdscr, results_y_start + 3,  f"{RESULTS_PROMPT_TIME}{time_taken:.2f}s", 3)
        display_centered_text_line(stdscr, results_y_start + 5, EXIT_PROMPT, 3)
        stdscr.refresh()

        key = stdscr.getch()
        if key == 27: 
            return

if __name__ == "__main__":
    try:
        curses.wrapper(typing_test_app)
        print("Typing test finished. Goodbye!")
    except curses.error as e:
        print(f"Curses error: {e}. Your terminal might not be fully compatible or was resized/closed.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")


