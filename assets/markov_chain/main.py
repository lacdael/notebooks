#!/usr/bin/env python3
import sys
import os
import time
import argparse
import threading
import random

drum_tab = None

# --- Configuration ---
VELOCITY_HIGH = 1.0
VELOCITY_LOW = 0.3

# --- Initialization ---
try:
    import pygame
except ImportError:
    print("Error: The 'pygame' library is required. Please install it by running:", file=sys.stderr)
    print("pip install pygame", file=sys.stderr)
    sys.exit(1)

channels = []
samples = []


def _convertIntToHit(i):
    if i == 1:
        return "x"
    elif i == 2:
        return "X"
    else:
        return "-"

def _convertHitToInt(s):
    if s == "x":
        return 1
    elif s == "X":
        return 2
    else:
        return 0

def _convertSliceToInt(drum_tab, i):
    v = 0
    for j in range(len(drum_tab)):
        v |= (_convertHitToInt(drum_tab[j][i]) << (j * 2))
    return v


def _weighted_choice(states, probabilities):
    r = random.random()
    cumulative = 0.0
    for i in range(len(states)):
        cumulative += probabilities[i]
        if r < cumulative:
            return states[i]
    return states[-1]

def _markov_buildModel(drum_tab):
    model = {}

    for i in range(len(drum_tab[0]) - 1):
        currentSlice = _convertSliceToInt(drum_tab, i)
        nextSlice = _convertSliceToInt(drum_tab, i + 1)

        if currentSlice not in model:
            model[currentSlice] = {}

        model[currentSlice][nextSlice] = model[currentSlice].get(nextSlice, 0) + 1

    return model


def _markov_1st_predict(model):
    if _markov_1st_predict.current_state not in model:
        # If the state is not in the model, pick a random one to start over
        _markov_1st_predict.current_state = random.choice(list(model.keys()))
        return _markov_1st_predict.current_state

    freq_dict = model[_markov_1st_predict.current_state]

    # Weighted random choice
    choices = list(freq_dict.keys())
    weights = list(freq_dict.values())
    total = sum(weights)
    probabilities = [w / total for w in weights]

    next_state = _weighted_choice(choices, probabilities)

    _markov_1st_predict.current_state = next_state

    return next_state
_markov_1st_predict.current_state = 0


def _markov_2nd_buildModel(drum_tab):
    model = {}

    for i in range(len(drum_tab[0]) - 2):
        currentPair = (_convertSliceToInt(drum_tab, i), _convertSliceToInt(drum_tab, i + 1))
        nextSlice = _convertSliceToInt(drum_tab, i + 2)

        # Initialize dictionary for frequency counts
        if currentPair not in model:
            model[currentPair] = {}

        # Increase frequency of the next_word
        model[currentPair][nextSlice] = model[currentPair].get(nextSlice, 0) + 1

    return model


def _markov_2nd_predict(model):
    if _markov_2nd_predict.current_pair not in model:
        # If the state is not in the model, pick a random one to start over
        _markov_2nd_predict.current_pair = random.choice(list(model.keys()))
        return _markov_2nd_predict.current_pair[1]

    freq_dict = model[_markov_2nd_predict.current_pair]

    # Weighted random choice
    choices = list(freq_dict.keys())
    weights = list(freq_dict.values())
    total = sum(weights)
    probabilities = [w / total for w in weights]

    next_state = _weighted_choice(choices, probabilities)

    _markov_2nd_predict.current_pair = (_markov_2nd_predict.current_pair[1], next_state)

    return next_state
_markov_2nd_predict.current_pair = (0,0)


def _playSample(i, c):
    #print("_playSample {} {}".format( i , c ) );
    if i >= len(samples) or samples[i] is None:
        return
    if c == 'x':
        samples[i].set_volume(VELOCITY_LOW)
        channels[i].play(samples[i])
    elif c == 'X':
        samples[i].set_volume(VELOCITY_HIGH)
        channels[i].play(samples[i])


# --- ANSI Color Codes ---
class colors:
    RESET = '\033[0m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    GREY = '\033[90m'

def _get_colored_hit(hit_char):
    if hit_char == 'x':
        return f"{colors.YELLOW}{hit_char}{colors.RESET}"
    elif hit_char == 'X':
        return f"{colors.RED}{hit_char}{colors.RESET}"
    else:
        return f"{colors.GREY}-{colors.RESET}"

def _BPM_work():
    global markovIsSecondOrder, markovModel, drum_tab
    aSlice = 0
    if markovIsSecondOrder:
        aSlice = _markov_2nd_predict(markovModel)
    else:
        aSlice = _markov_1st_predict(markovModel)

    num_instruments = len(drum_tab)
    
    # Build the colored output string
    output_parts = []
    for i in range(num_instruments):
        index = i #num_instruments - i -1  ) % num_instruments;
        hit_val = (aSlice >> (index * 2)) & 0x3
        hit_char = _convertIntToHit(hit_val)
        output_parts.append(_get_colored_hit(hit_char))
        _playSample( index , hit_char)

    # Print the formatted slice to the console, overwriting the previous line
    #print(f"  | {' | '.join(output_parts)} |", end='\r')
    print(f"  | {' | '.join(output_parts)} |")


_BPM_work.index = 0

def _init_BPM_task(bpm):
    # 16th notes
    interval = 60.0 / bpm
    interval /= 4.0;

    def loop():
        last_time = time.time()
        while True:
            _BPM_work()
            last_time += interval
            delay = last_time - time.time()
            if delay > 0:
                time.sleep(delay)
            else:
                # If we fall behind, reset the timer to avoid a cascade of late beats
                last_time = time.time()

    thread = threading.Thread(target=loop, daemon=True)
    thread.start()
    return thread

def _parseTabToMatrix(tab_string: str):
    lines = [line.rstrip() for line in tab_string.split("\n") if line.strip() != ""]
    if not lines:
        return []
    max_cols = max(len(line) for line in lines)
    matrix = []
    for line in lines:
        row = list(line)
        if len(row) < max_cols:
            row += ["-"] * (max_cols - len(row))
        matrix.append(row)
    return matrix

def main():
    global drum_tab, markovIsSecondOrder, markovModel, samples, channels
    parser = argparse.ArgumentParser(description="Markov Chain Drum tab player.")
    parser.add_argument("input_file", nargs='?', default="example.txt", help="Path to the input tab.")
    parser.add_argument("--samples", nargs='+', help="Paths to the sample audio files.")
    parser.add_argument("--BPM", type=int, default=86, help="BPM value")
    parser.add_argument("--second-order", action='store_true', help="use a Second order chain.")

    for i in range(1, 8):
        parser.add_argument(f"--sample{i}", help=f"Path to sample file for track {i}.")

    args = parser.parse_args()

    pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
    pygame.mixer.set_num_channels(32)
    channels = [pygame.mixer.Channel(i) for i in range(32)]

    sample_files = [
        'kick.wav',
        'snare.wav',
        'hihat.wav',
        'hihat.wav',
        'snare.wav',
        'kick.wav'
    ]

    for i in range(1, 8):
        sample_file = getattr(args, f'sample{i}', None)
        if sample_file:
            sample_files[ i -1 ] = sample_file
    
    missing_files = False
    for i, filename in enumerate(sample_files):
        print("{} {} ".format( i ,filename ))
        if not os.path.exists(filename):
            print(f"Warning: Sound file for row {i} not found: {filename}", file=sys.stderr)
            missing_files = True
            samples.append(None)
        else:
            samples.append(pygame.mixer.Sound(filename))

    if missing_files:
        print("\nWarning: Some sound files are missing.", file=sys.stderr)
        time.sleep(3)

    try:
        with open(args.input_file, "r") as f:
            drum_tab = _parseTabToMatrix(f.read())

    except FileNotFoundError:
        print(f"Error: Input file not found at '{args.input_file}'", file=sys.stderr)
        sys.exit(1)

    if not drum_tab or not drum_tab[0]:
        print("Error: Drum tab is empty or invalid.", file=sys.stderr)
        sys.exit(1)

    print(drum_tab)

    markovIsSecondOrder = args.second_order
    if args.second_order:
        markovModel = _markov_2nd_buildModel(drum_tab)
        if not markovModel:
            print("Error: Could not build second-order Markov model. The input tab might be too short.", file=sys.stderr)
            sys.exit(1)
        _markov_2nd_predict.current_pair = random.choice(list(markovModel.keys()))
    else:
        markovModel = _markov_buildModel(drum_tab)
        if not markovModel:
            print("Error: Could not build first-order Markov model. The input tab might be too short.", file=sys.stderr)
            sys.exit(1)
        _markov_1st_predict.current_state = random.choice(list(markovModel.keys()))

    _init_BPM_task(args.BPM)

    print("Ctrl+C to exit.")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nExiting player.", file=sys.stderr)
    finally:
        pygame.mixer.quit()

if __name__ == "__main__":
    main()
