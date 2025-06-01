import curses
import time

# --- Configuration ---
TARGET_TEXT = "The quick brown fox jumps over the lazy dog."
# TARGET_TEXT = "hello world example"
INPUT_PROMPT = "Type here: "
RESULTS_PROMPT_WPM = "WPM: "
RESULTS_PROMPT_ACCURACY = "Accuracy: "
RESULTS_PROMPT_TIME = "Time: "
EXIT_PROMPT = "Press any key to try again, or ESC to exit..."

# --- Helper Functions ---
def calculate_metrics_word_based(target_words_list, typed_segments_list, time_taken_seconds):
    correct_chars_overall = 0
    total_target_chars_for_accuracy = sum(len(w) for w in target_words_list) + max(0, len(target_words_list) - 1)

    for i in range(len(target_words_list)):
        target_word = target_words_list[i]
        typed_segment = typed_segments_list[i] if i < len(typed_segments_list) else ""
        for j in range(len(target_word)):
            if j < len(typed_segment) and typed_segment[j] == target_word[j]:
                correct_chars_overall += 1
        if i < len(target_words_list) - 1 and i < len(typed_segments_list) - 1: # Correctly typed space implies next segment started
            correct_chars_overall += 1

    if time_taken_seconds == 0: wpm = 0
    else:
        minutes = time_taken_seconds / 60.0
        wpm = int((correct_chars_overall / 5.0) / minutes) if minutes > 0 else 0

    if total_target_chars_for_accuracy == 0: task_accuracy = 100.0 if correct_chars_overall == 0 else 0.0
    else: task_accuracy = (correct_chars_overall / total_target_chars_for_accuracy) * 100
    
    return wpm, round(task_accuracy, 2)

def display_text_in_box_line(stdscr, y, x_start_of_line, line_width, text, text_color_pair=0, text_attributes=0):
    """Displays text centered within a single line of a conceptual box."""
    actual_text_x = x_start_of_line + (line_width - len(text)) // 2
    actual_text_x = max(x_start_of_line, actual_text_x) 
    
    try:
        stdscr.addstr(y, actual_text_x, text, curses.color_pair(text_color_pair) | text_attributes)
    except curses.error:
        try: 
            stdscr.addstr(y, x_start_of_line, text[:line_width], curses.color_pair(text_color_pair) | text_attributes)
        except: pass

def draw_box_border(stdscr, start_y, start_x, height, width, color_pair, title=""):
    """Draws a box with an optional title centered on the top border."""
    try:
        # Create a new window for the box content to avoid border overwriting
        box_win = stdscr.derwin(height, width, start_y, start_x)
        box_win.attron(curses.color_pair(color_pair))
        box_win.border(curses.ACS_VLINE, curses.ACS_VLINE, curses.ACS_HLINE, curses.ACS_HLINE,
                       curses.ACS_ULCORNER, curses.ACS_URCORNER, curses.ACS_LLCORNER, curses.ACS_LRCORNER)
        box_win.attroff(curses.color_pair(color_pair))
        
        if title:
            title_x = (width - len(title)) // 2
            title_x = max(1, title_x) # Ensure title is within border
            if title_x + len(title) < width -1:
                 box_win.addstr(0, title_x, title, curses.color_pair(color_pair) | curses.A_BOLD)
        box_win.refresh() # Refresh the subwindow
    except curses.error: # Fallback if derwin or border fails
        pass


# --- Main Application Logic ---
def typing_test_app(stdscr):
    curses.start_color()
    curses.use_default_colors()
    curses.init_pair(1, curses.COLOR_GREEN, -1)   # Correct typed text
    curses.init_pair(2, curses.COLOR_RED, -1)     # Incorrect typed text
    curses.init_pair(3, curses.COLOR_CYAN, -1)    # Prompts ("Type here:") & Typing Box Border
    curses.init_pair(4, curses.COLOR_YELLOW, -1)  # Main Titles & Results Box Border
    curses.init_pair(5, curses.COLOR_WHITE, -1)   # Default target text color
    curses.init_pair(6, curses.COLOR_BLUE, -1)    # Cursor
    curses.init_pair(7, curses.COLOR_MAGENTA, -1) # Static "Target:" label color
    curses.init_pair(8, curses.COLOR_RED, -1)     # Brief error indication on cursor / Error Box Border

    curses.curs_set(0)
    stdscr.nodelay(False)

    while True: # Outer loop for retrying
        active_target_text = TARGET_TEXT
        target_words = active_target_text.split(' ')
        
        typed_segments = [] 
        current_word_input = "" 
        current_word_idx = 0    
        
        start_time = 0
        time_taken = 0
        input_active = True
        
        # --- Initial Target Text Flash ---
        stdscr.clear()
        h, w = stdscr.getmaxyx()
        
        # Define box parameters early for consistent use
        # Typing Box
        typing_box_content_h = 5 # For Target line, empty line, Type here line
        typing_box_border_h = typing_box_content_h + 2 # Add 2 for top/bottom border
        # Width based on target text, prompt, plus some padding
        typing_box_w = min(w - 4, len(active_target_text) + len(INPUT_PROMPT) + 20) 
        typing_box_w = max(typing_box_w, 50) # Min width
        typing_box_start_y = h // 2 - typing_box_border_h // 2 -1 # Move up slightly for title
        typing_box_start_x = (w - typing_box_w) // 2

        title_text = "Typing Speed Test"
        title_y = typing_box_start_y - 2 # Place title above the box

        display_text_in_box_line(stdscr, title_y, 0, w, title_text, text_color_pair=4, text_attributes=curses.A_BOLD)

        # Flash target text (inside where the box will be)
        target_line_y_abs = typing_box_start_y + 1 # y relative to stdscr
        target_label_x_abs = typing_box_start_x + 2
        target_text_x_abs = target_label_x_abs + len("Target: ")

        for i in range(2): 
            clr = 4 if i % 2 == 0 else 7 
            if target_label_x_abs + len("Target: ") < typing_box_start_x + typing_box_w -1:
                 stdscr.addstr(target_line_y_abs, target_label_x_abs, "Target: ", curses.color_pair(clr) | curses.A_BOLD)
            if target_text_x_abs + len(active_target_text) < typing_box_start_x + typing_box_w -1:
                 stdscr.addstr(target_line_y_abs, target_text_x_abs, active_target_text, curses.color_pair(clr))
            stdscr.refresh()
            curses.napms(150)

        while input_active: 
            stdscr.clear() # Clear for each frame
            h, w = stdscr.getmaxyx() 

            # Recalculate box params in case of resize, though less critical in nodelay(False)
            typing_box_w = min(w - 4, len(active_target_text) + len(INPUT_PROMPT) + 20)
            typing_box_w = max(typing_box_w, 50)
            typing_box_start_y = h // 2 - typing_box_border_h // 2 -1
            typing_box_start_x = (w - typing_box_w) // 2
            title_y = typing_box_start_y - 2

            if h < typing_box_border_h + 4 or w < typing_box_w + 2 : 
                display_text_in_box_line(stdscr, h//2, 0, w, "Terminal too small!", text_color_pair=2)
                stdscr.refresh()
                key = stdscr.getch()
                if key == ord('q') or key == 27: return
                continue
            
            display_text_in_box_line(stdscr, title_y, 0, w, title_text, text_color_pair=4, text_attributes=curses.A_BOLD)
            draw_box_border(stdscr, typing_box_start_y, typing_box_start_x, typing_box_border_h, typing_box_w, 3) # Cyan border

            # --- Display Inside the Typing Box ---
            content_start_x = typing_box_start_x + 2 # Inner padding
            content_width = typing_box_w - 4

            # Static Target Text Line (current word underlined)
            # y is relative to stdscr, using absolute calculated positions
            stdscr.addstr(target_line_y_abs, content_start_x, "Target: ", curses.color_pair(7) | curses.A_BOLD)
            current_target_char_x = content_start_x + len("Target: ")
            for i, word in enumerate(target_words):
                if current_target_char_x >= content_start_x + content_width : break
                attr = curses.A_UNDERLINE if i == current_word_idx else 0
                for char_target in word:
                    if current_target_char_x >= content_start_x + content_width: break
                    stdscr.addch(target_line_y_abs, current_target_char_x, char_target, curses.color_pair(5) | attr)
                    current_target_char_x += 1
                if i < len(target_words) - 1: 
                    if current_target_char_x >= content_start_x + content_width: break
                    stdscr.addch(target_line_y_abs, current_target_char_x, ' ', curses.color_pair(5) | attr)
                    current_target_char_x += 1

            # Interactive "Type here:" line
            type_here_line_y_abs = typing_box_start_y + 3 # y relative to stdscr
            current_display_x = content_start_x
            
            stdscr.addstr(type_here_line_y_abs, current_display_x, INPUT_PROMPT, curses.color_pair(3))
            current_display_x += len(INPUT_PROMPT)

            for i in range(current_word_idx): 
                if i >= len(typed_segments): continue 
                segment = typed_segments[i]
                target_w = target_words[i]
                for j, char_typed in enumerate(segment):
                    if current_display_x >= content_start_x + content_width : break
                    tc = target_w[j] if j < len(target_w) else ' '
                    clr = 1 if char_typed == tc else 2
                    stdscr.addch(type_here_line_y_abs, current_display_x, char_typed, curses.color_pair(clr))
                    current_display_x += 1
                if current_display_x < content_start_x + content_width:
                    stdscr.addch(type_here_line_y_abs, current_display_x, ' ')
                    current_display_x += 1
            
            if current_word_idx < len(target_words): 
                target_curr_w = target_words[current_word_idx]
                for j, char_typed in enumerate(current_word_input):
                    if current_display_x >= content_start_x + content_width : break
                    tc = target_curr_w[j] if j < len(target_curr_w) else ' '
                    clr = 1 if char_typed == tc else 2
                    stdscr.addch(type_here_line_y_abs, current_display_x, char_typed, curses.color_pair(clr))
                    current_display_x += 1
                
                if current_display_x < content_start_x + content_width: 
                    cursor_char = ' '
                    if len(current_word_input) < len(target_curr_w):
                        cursor_char = target_curr_w[len(current_word_input)]
                    elif len(current_word_input) == len(target_curr_w) and current_word_idx < len(target_words) - 1:
                        cursor_char = ' ' 
                    stdscr.addch(type_here_line_y_abs, current_display_x, cursor_char, curses.A_REVERSE | curses.color_pair(6))
            
            stdscr.refresh()

            # --- Input Handling ---
            if not start_time and (current_word_input or typed_segments): start_time = time.time()
            key = stdscr.getch()

            if key:
                if not start_time: start_time = time.time()

                if key == curses.KEY_ENTER or key == 10 or key == 13:
                    if current_word_input or typed_segments:
                        if current_word_idx < len(target_words): typed_segments.append(current_word_input)
                        while len(typed_segments) < len(target_words): typed_segments.append("")
                        input_active = False 
                        if start_time: time_taken = time.time() - start_time
                    continue 

                elif key == ord(' '):
                    if not current_word_input: 
                        # Try to flash cursor char red
                        can_flash_cursor = current_display_x < content_start_x + content_width
                        if can_flash_cursor:
                            flash_char_display = ' '
                            if current_word_idx < len(target_words):
                                tc_w = target_words[current_word_idx]
                                if len(current_word_input) < len(tc_w): flash_char_display = tc_w[len(current_word_input)]
                                elif len(current_word_input) == len(tc_w) and current_word_idx < len(target_words) -1: flash_char_display = ' '
                            
                            stdscr.addch(type_here_line_y_abs, current_display_x, flash_char_display, curses.A_REVERSE | curses.color_pair(8)) # Red
                            stdscr.refresh()
                            curses.napms(100)
                            stdscr.addch(type_here_line_y_abs, current_display_x, flash_char_display, curses.A_REVERSE | curses.color_pair(6)) # Blue
                            stdscr.refresh()
                        else:
                            # Fallback: Flash typing box border red
                            draw_box_border(stdscr, typing_box_start_y, typing_box_start_x, typing_box_border_h, typing_box_w, 8) # Red border
                            stdscr.refresh()
                            curses.napms(100)
                            draw_box_border(stdscr, typing_box_start_y, typing_box_start_x, typing_box_border_h, typing_box_w, 3) # Restore Cyan border
                            stdscr.refresh()
                    elif current_word_idx < len(target_words):
                        typed_segments.append(current_word_input)
                        current_word_input = ""
                        current_word_idx += 1
                        if current_word_idx == len(target_words): 
                            input_active = False 
                            if start_time: time_taken = time.time() - start_time
                    elif current_word_idx >= len(target_words):
                        input_active = False 
                        if start_time: time_taken = time.time() - start_time
                elif key == curses.KEY_BACKSPACE or key == 127 or key == 8:
                    if current_word_input: current_word_input = current_word_input[:-1]
                    elif typed_segments and current_word_idx > 0: 
                        current_word_idx -= 1
                        current_word_input = typed_segments.pop()
                elif 32 < key <= 126: 
                    if current_word_idx < len(target_words):
                        if len(current_word_input) < len(target_words[current_word_idx]) + 5:
                             current_word_input += chr(key)
                        else: curses.flash() # Overtyped current word too much
                    elif current_word_idx >= len(target_words): curses.flash() # Typing past end
                elif key == 27: return 
        
        # --- Results Display (with border) ---
        stdscr.clear()
        results_box_h = 7 # Content height
        results_box_border_h = results_box_h + 2
        results_box_w = 45
        res_box_start_y = h // 2 - results_box_border_h // 2
        res_box_start_x = (w - results_box_w) // 2
        
        results_title_text = "--- Results ---"
        results_title_y = res_box_start_y - 2

        if h < results_box_border_h + 4 or w < results_box_w + 2: 
            display_text_in_box_line(stdscr, h//2, 0, w, "Terminal too small for results!", text_color_pair=2)
        else:
            display_text_in_box_line(stdscr, results_title_y, 0, w, results_title_text, text_color_pair=4, text_attributes=curses.A_BOLD)
            draw_box_border(stdscr, res_box_start_y, res_box_start_x, results_box_border_h, results_box_w, 4, title="") # Yellow border, no title in border
            
            res_content_start_x = res_box_start_x + 2
            res_content_width = results_box_w - 4
            
            while len(typed_segments) < len(target_words): typed_segments.append("")
            wpm, accuracy = calculate_metrics_word_based(target_words, typed_segments, time_taken)

            display_text_in_box_line(stdscr, res_box_start_y + 1, res_content_start_x, res_content_width, f"{RESULTS_PROMPT_WPM}{wpm}", text_color_pair=3)
            display_text_in_box_line(stdscr, res_box_start_y + 2, res_content_start_x, res_content_width, f"{RESULTS_PROMPT_ACCURACY}{accuracy}%", text_color_pair=3)
            display_text_in_box_line(stdscr, res_box_start_y + 3, res_content_start_x, res_content_width, f"{RESULTS_PROMPT_TIME}{time_taken:.2f}s", text_color_pair=3)
            display_text_in_box_line(stdscr, res_box_start_y + 5, res_content_start_x, res_content_width, EXIT_PROMPT, text_color_pair=3)
        
        stdscr.refresh()
        key = stdscr.getch()
        if key == 27: return

if __name__ == "__main__":
    try:
        curses.wrapper(typing_test_app)
        print("Typing test finished. Goodbye!")
    except curses.error as e:
        print(f"Curses error: {e}. Check terminal size/compatibility.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")


