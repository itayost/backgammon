"""Writes the trained network in ai/weights/td.npz as web/src/ai/weights/td.json for the web app.

Run from the repository root after training a new network:
    python web/scripts/export_weights.py
"""
import json
import os

import numpy as np

ROOT = os.path.normpath(os.path.join(os.path.dirname(__file__), '..', '..'))
SOURCE = os.path.join(ROOT, 'ai', 'weights', 'td.npz')
TARGET = os.path.join(ROOT, 'web', 'src', 'ai', 'weights', 'td.json')


def main():
    data = np.load(SOURCE)
    w1, b1, w2, b2 = (data[f'arr_{i}'] for i in range(4))
    hidden, inputs = w1.shape
    weights = {
        'hidden': hidden,
        'inputs': inputs,
        'w1': w1.reshape(-1).tolist(),  # row major: w1[j * inputs + k]
        'b1': b1.tolist(),
        'w2': w2.tolist(),
        'b2': float(b2[0]),
    }
    with open(TARGET, 'w') as f:
        json.dump(weights, f, separators=(',', ':'))
        f.write('\n')
    print(f'wrote {os.path.relpath(TARGET, ROOT)}: {hidden} hidden units, {inputs} inputs')


if __name__ == '__main__':
    main()
