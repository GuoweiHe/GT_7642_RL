import numpy as np

sizes = [8, 8, 2]

all_states = np.indices(sizes).reshape(len(sizes), -1).T

print(all_states)