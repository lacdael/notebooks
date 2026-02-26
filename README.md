# Python Notebooks Collection

This repository contains a set of **interactive Python notebooks** exploring various computer science concepts, algorithms, and applications. Each notebook is designed as a self-contained playground for experimentation and learning.

Before running the notebooks, ensure that all dependencies are installed in the same virtual environment:

```bash
env/bin/python3 -m pip install <library>
```

---

## Repository Structure

```
├── assets/
├── libs/
├── Digital_Signal_Processing.ipynb
├── Markov_Chains.ipynb
├── merkleTree.ipynb
├── PID_controller.ipynb
├── Q_learning.ipynb
└── README.md
```

---

## Notebooks Overview

### 1. Merkle Trees

A playground for **Merkle Trees**, featuring ASCII visualizations using a `crc8` function for hashing.
Merkle Trees allow efficient grouping of hashes and provide a **proof of membership** for data integrity verification.

---

### 2. Digital Signal Processing (DSP)

Implements an **IIR digital signal processing class** along with:

* A **steady-state detection (SSD)** function
* A **peak detection** function
* Animated visualizations using `matplotlib`

Useful for experimenting with signals and understanding real-time signal analysis.

---

### 3. PID Controller

An implementation of a **PID (Proportional–Integral–Derivative) controller**, including:

* Graphical visualizations of the PID in operation
* Step-by-step feedback control simulations

PID controllers are widely used to maintain a system output at a **target value** using feedback loops.

---

### 4. Markov Chains

Explore **Markov Chains** to predict the next state of a system based on the **current state** and learned patterns.
Includes example implementations and experiments with state transitions.

---

### 5. Q-Learning

A hands-on introduction to **reinforcement learning** using **Q-learning**, demonstrated with a **MACD trading strategy** example.
Learn how an agent can optimize decisions over time based on **reward signals**.

---

### Additional Resources

* `libs/` – Contains helper libraries, including indicator functions for trading strategies.
* `assets/` – Example data files, audio samples, and CSVs used in the notebooks.

---

### Notes

* Some notebooks rely on **external data files** in the `assets/` folder. Make sure the paths are correct.
* Designed for Python 3.11+






# Python Notebooks

Interactive Notebook on topics that are useful in Computer Science applications.

Ensure dependencies are installed in the same virtual environment.
`env/bin/python3 -m pip install <library>`

## Merkle Trees
    
    A playground for Merkle Trees, with ascii visualisation using a crc8 function for hashes.  
    Merkel trees allows the grouping of hashes, and for a means of proof of membership.  

## Digital Signal Processing DSP

    IIR digital signal processing class, along with a simple steady state detection (SSD) function and a peak detection function. With a matplot function to animate the signal processing.

## PID Controller

    An implimentation of a PID controller, with graphical representations of the PID controller in opperation.

    A PID controler utilises a feedback loop to correct an output signal to meet a target value.

## Markov Chains

    Predict the next state of a system based on learned experience and the current state.

## Q - Learning

A look at reinforcence learning, using the MACD trading stratagy as an example.
