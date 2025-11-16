import streamlit as st
import random
import time
import logging
import sys
import json
from typing import Dict, Any, List

# --- CONSTANTS ---
# Configuration for logging
LOG_LEVEL = logging.INFO
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

# Session state key
SESSION_STATE_KEY = 'game_state'

# Game parameters
TOTAL_ROUNDS = 20
SESSION_TIME_LIMIT_SECONDS = 300  # 5 minutes for the whole session

# --- NEW: Phase and Point constants ---
PHASE_1_RANGE = (1, 10)  # Small multiplication table
PHASE_2_RANGE = (11, 20) # Large multiplication table

PHASE_1_END_ROUND = 7    # Rounds 1-7
PHASE_2_END_ROUND = 14   # Rounds 8-14
# Phase 3 is rounds 15-20

POINTS_PHASE_1 = 1
POINTS_PHASE_2 = 5
POINTS_PHASE_3 = 10
# --- End of new constants ---

# Highscore constants
HIGHSCORE_FILE = 'highscores.json'
MAX_HIGHSCORES = 10

# --- LOGIC FUNCTIONS (No Streamlit) ---

def setup_logging() -> logging.Logger:
    """Configures and returns a logger."""
    logger = logging.getLogger("MathGameApp")
    if not logger.handlers:
        logger.setLevel(LOG_LEVEL)
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(logging.Formatter(LOG_FORMAT))
        logger.addHandler(handler)
    return logger

def initialize_game_state() -> Dict[str, Any]:
    """
    Creates a dictionary with the default state for a new game.
    """
    logger.info("Initializing new game state.")
    return {
        'status': 'welcome',  # 'welcome', 'playing', 'game_over'
        'current_round': 0,
        'score': 0,
        'current_question': None,
        'start_time': None,
        'last_message': '',
        'show_highscore_form': False
    }

def generate_question(current_round: int) -> Dict[str, int]:
    """
    Generates a new multiplication question based on the current round's phase.
    """
    if current_round <= PHASE_1_END_ROUND:
        # Phase 1: Small * Small
        a = random.randint(PHASE_1_RANGE[0], PHASE_1_RANGE[1])
        b = random.randint(PHASE_1_RANGE[0], PHASE_1_RANGE[1])
        level = 1
        
    elif current_round <= PHASE_2_END_ROUND:
        # Phase 2: Small * Large
        a = random.randint(PHASE_1_RANGE[0], PHASE_1_RANGE[1])
        b = random.randint(PHASE_2_RANGE[0], PHASE_2_RANGE[1])
        # Randomly swap to vary the question (e.g., 15x7 or 7x15)
        if random.random() > 0.5:
            a, b = b, a
        level = 2
        
    else:
        # Phase 3: Large * Large
        a = random.randint(PHASE_2_RANGE[0], PHASE_2_RANGE[1])
        b = random.randint(PHASE_2_RANGE[0], PHASE_2_RANGE[1])
        level = 3
        
    answer = a * b
    logger.info(f"Generated Phase {level} question (Round {current_round}): {a} * {b} = {answer}")
    return {'a': a, 'b': b, 'answer': answer}

def get_points_for_round(current_round: int) -> int:
    """
    Returns the points awarded for the current round's phase.
    """
    if current_round <= PHASE_1_END_ROUND:
        return POINTS_PHASE_1
    elif current_round <= PHASE_2_END_ROUND:
        return POINTS_PHASE_2
    else:
        return POINTS_PHASE_3

def get_phase_for_round(current_round: int) -> int:
    """
    Returns the current phase number (1, 2, or 3).
    """
    if current_round <= PHASE_1_END_ROUND:
        return 1
    elif current_round <= PHASE_2_END_ROUND:
        return 2
    else:
        return 3

def check_answer(game_state: Dict[str, Any], user_input: int) -> Dict[str, Any]:
    """
    Checks the user's answer and updates the game state.
    Returns the modified game_state dictionary.
    """
    updated_state = game_state.copy()
    
    if 'current_question' not in updated_state or updated_state['current_question'] is None:
        logger.warning("check_answer called with no current_question.")
        return updated_state
        
    correct_answer = updated_state['current_question']['answer']
    
    if user_input == correct_answer:
        logger.info("User answer was correct.")
        # --- MODIFIED: Get points based on phase ---
        points_to_add = get_points_for_round(updated_state['current_round'])
        updated_state['score'] += points_to_add
        updated_state['current_round'] += 1
        updated_state['last_message'] = f"Great job! That was correct. +{points_to_add} points."
        # --- End of modification ---
        
        if updated_state['current_round'] > TOTAL_ROUNDS:
            logger.info("User completed all rounds.")
            updated_state['status'] = 'game_over'
            updated_state['last_message'] = "Wow! You finished all rounds! You are a math star!"
            updated_state['current_question'] = None
            if updated_state['score'] > 0:
                updated_state['show_highscore_form'] = True
        else:
            updated_state['current_question'] = generate_question(updated_state['current_round'])
            
    else:
        logger.warning("User answer was incorrect. Game over.")
        updated_state['status'] = 'game_over'
        updated_state['last_message'] = f"Oh no! The correct answer was {correct_answer}. Game over."
        updated_state['current_question'] = None
        if updated_state['score'] > 0:
            updated_state['show_highscore_form'] = True
            
    return updated_state

def check_timer(game_state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Checks if the session time limit has been reached.
    """
    if game_state['status'] != 'playing':
        return game_state

    elapsed_time = time.time() - game_state['start_time']
    if elapsed_time > SESSION_TIME_LIMIT_SECONDS:
        logger.info("Time limit reached. Game over.")
        updated_state = game_state.copy()
        updated_state['status'] = 'game_over'
        updated_state['last_message'] = "Time is up! Game over."
        updated_state['current_question'] = None
        if updated_state['score'] > 0:
            updated_state['show_highscore_form'] = True
        return updated_state
    
    return game_state

# --- HIGHSCORE LOGIC FUNCTIONS ---

def load_highscores(filepath: str) -> List[Dict[str, Any]]:
    """
    Loads the highscore list from a JSON file.
    """
    try:
        with open(filepath, 'r') as f:
            scores = json.load(f)
        scores.sort(key=lambda x: x.get('score', 0), reverse=True)
        return scores
    except FileNotFoundError:
        logger.info("Highscore file not found, will be created.")
        return []
    except json.JSONDecodeError:
        logger.error(f"Error decoding {filepath}. Returning empty list.")
        return []
    except Exception as e:
        logger.error(f"An unexpected error occurred loading highscores: {e}")
        return []

def save_highscores(filepath: str, scores: List[Dict[str, Any]]):
    """
    Saves the highscore list to a JSON file.
    """
    try:
        with open(filepath, 'w') as f:
            json.dump(scores, f, indent=4)
        logger.info(f"Highscores saved to {filepath}.")
    except IOError as e:
        logger.error(f"Could not write highscores to {filepath}: {e}")
    except Exception as e:
        logger.error(f"An unexpected error occurred saving highscores: {e}")


def add_highscore(name: str, score: int, current_scores: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Adds a new score to the list, sorts, and trims it.
    """
    entry_time = time.strftime('%Y-%m-%d %H:%M', time.localtime(time.time()))
    new_entry = {'name': name, 'score': score, 'date': entry_time}
    
    updated_scores = current_scores + [new_entry]
    updated_scores.sort(key=lambda x: x.get('score', 0), reverse=True)
    return updated_scores[:MAX_HIGHSCORES]

# --- CALLBACK FUNCTIONS (Bridge between View and Logic) ---

def start_game_callback():
    """
    Called when the 'Start Game' button is pressed.
    """
    logger.info("Start button clicked. Starting game.")
    new_state = initialize_game_state()
    new_state['status'] = 'playing'
    new_state['start_time'] = time.time()
    new_state['current_round'] = 1
    new_state['current_question'] = generate_question(1)
    new_state['last_message'] = "Here is your first question. Good luck!"
    st.session_state[SESSION_STATE_KEY] = new_state

def restart_game_callback():
    """
    Called when the 'Play Again' button is pressed.
    """
    logger.info("Restart button clicked. Resetting game.")
    st.session_state[SESSION_STATE_KEY] = initialize_game_state()

# --- VIEW FUNCTIONS (Streamlit) ---

def display_welcome_screen():
    """
    Displays the initial welcome message, start button, and high scores.
    """
    st.title("Welcome to the Multiplication Game! 🚀")
    st.write("Let's practice your math skills.")
    st.write(f"You will have **{TOTAL_ROUNDS} questions** in 3 phases.")
    
    # --- MODIFIED: Explain new phases and points ---
    st.write(f"**Phase 1 (Rounds 1-{PHASE_1_END_ROUND}):** Small 1x1 (e.g., 5x7). **{POINTS_PHASE_1} point** per answer.")
    st.write(f"**Phase 2 (Rounds {PHASE_1_END_ROUND + 1}-{PHASE_2_END_ROUND}):** Mixed 1x1 (e.g., 8x15). **{POINTS_PHASE_2} points** per answer.")
    st.write(f"**Phase 3 (Rounds {PHASE_2_END_ROUND + 1}-{TOTAL_ROUNDS}):** Large 1x1 (e.g., 14x18). **{POINTS_PHASE_3} points** per answer.")
    # --- End of modification ---
    
    st.write(f"You have **{SESSION_TIME_LIMIT_SECONDS // 60} minutes** for the whole game.")
    st.warning("If you get one answer wrong, the game is over!")
    
    st.button("Start Game", on_click=start_game_callback, type="primary")
    
    st.divider()
    st.header("High Scores 🏆")
    highscores = load_highscores(HIGHSCORE_FILE)
    if not highscores:
        st.write("No high scores yet. Be the first!")
    else:
        st.dataframe(highscores, use_container_width=True)

def display_game_screen(game_data: Dict[str, Any]):
    """
    Displays the main game interface: stats, question, and answer form.
    """
    elapsed_time = time.time() - game_data['start_time']
    time_left = int(SESSION_TIME_LIMIT_SECONDS - elapsed_time)
    percent_remaining = max(0.0, time_left / SESSION_TIME_LIMIT_SECONDS)
    
    # --- NEW: Get current phase ---
    current_phase = get_phase_for_round(game_data['current_round'])

    st.header("Let's do some math!")
    st.write("Time remaining:")
    st.progress(percent_remaining)
    
    # --- MODIFIED: Added Phase metric ---
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Score", game_data['score'])
    col2.metric("Round", f"{game_data['current_round']}/{TOTAL_ROUNDS}")
    col3.metric("Phase", current_phase)
    col4.metric("Time Left (s)", time_left)
    # --- End of modification ---
    
    if game_data['last_message']:
        st.info(game_data['last_message'])
        
    question = game_data.get('current_question')
    if question is None:
        st.warning("No question to display. This might happen briefly.")
        return

    st.subheader(f"What is {question['a']} x {question['b']}?")
    
    # --- MODIFIED: Changed value to None for empty field, added clear_on_submit ---
    with st.form(key="answer_form", clear_on_submit=True):
        user_answer = st.number_input(
            "Your answer:", 
            min_value=0, 
            step=1,
            value=None # Use None to show an empty field
        )
        submitted = st.form_submit_button("Submit Answer")
        
        if submitted:
            # Prevent submitting an empty field
            if user_answer is None:
                st.warning("Please enter a number.")
                st.rerun()
            else:
                logger.info(f"User submitted answer: {user_answer}")
                updated_state = check_answer(game_data, user_answer)
                st.session_state[SESSION_STATE_KEY] = updated_state
                st.rerun()

def display_game_over_screen(game_data: Dict[str, Any]):
    """
    Displays the game over message, final score, and highscore form if eligible.
    """
    st.title("Game Over! 🛑")
    st.write(game_data['last_message'])
    st.metric("Your Final Score", game_data['score'])

    if game_data.get('show_highscore_form', False):
        st.subheader("🎉 New High Score! 🎉")
        st.write("Enter your name to save your score:")
        
        with st.form(key="highscore_form"):
            player_name = st.text_input("Your Name:", max_chars=20)
            submit_score = st.form_submit_button("Save High Score")
            
            if submit_score:
                if not player_name:
                    st.warning("Please enter a name.")
                else:
                    logger.info(f"Submitting high score for {player_name} with score {game_data['score']}.")
                    current_scores = load_highscores(HIGHSCORE_FILE)
                    new_scores = add_highscore(player_name.strip(), game_data['score'], current_scores)
                    # --- FIXED: Corrected constant name ---
                    save_highscores(HIGHSCORE_FILE, new_scores)
                    
                    updated_state = game_data.copy()
                    updated_state['show_highscore_form'] = False
                    st.session_state[SESSION_STATE_KEY] = updated_state
                    
                    st.success(f"Score for {player_name} saved!")
                    time.sleep(1) 
                    st.rerun() 
    
    st.button("Play Again", on_click=restart_game_callback)

# --- MAIN FUNCTION ---

def main():
    """
    Main function to run the Streamlit app.
    """
    st.set_page_config(page_title="Math Practice", page_icon="🧮")
    
    logger.info("Main app function started.")
    
    if SESSION_STATE_KEY not in st.session_state:
        st.session_state[SESSION_STATE_KEY] = initialize_game_state()
        
    game_state = st.session_state[SESSION_STATE_KEY]
    
    # --- Controller ---
    if game_state['status'] == 'playing':
        game_state = check_timer(game_state)
        st.session_state[SESSION_STATE_KEY] = game_state

    # --- View Routing ---
    status = game_state.get('status', 'welcome')

    if status == 'welcome':
        display_welcome_screen()
        
    elif status == 'playing':
        display_game_screen(game_state)
        
    elif status == 'game_over':
        display_game_over_screen(game_state)

if __name__ == "__main__":
    logger = setup_logging()
    main()