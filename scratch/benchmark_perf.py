import numpy as np
import time

buffer_size = 400000 * 60 # 60 seconds at 400kHz
ptr = buffer_size // 2
zoom_samples = buffer_size # Max zoom

y_history_ch1 = np.random.rand(buffer_size).astype(np.float32)

print(f"Buffer size: {buffer_size} samples ({buffer_size*4/1e6:.1f} MB)")

# Test concatenation (current logic)
start = time.time()
nb_samples = zoom_samples
p1 = buffer_size - (nb_samples - ptr)
# Simulating the wrap-around case which is the slowest
data = np.concatenate((y_history_ch1[p1:], y_history_ch1[:ptr]))
print(f"Concatenation time: {(time.time() - start)*1000:.2f} ms")

# Test downsampling
max_points = 10000
start = time.time()
factor = len(data) // (max_points // 2)
length = (len(data) // factor) * factor
y_view = data[:length].reshape(-1, factor)
y_min = y_view.min(axis=1)
y_max = y_view.max(axis=1)
env = np.empty(y_min.size * 2, dtype=data.dtype)
env[0::2] = y_min
env[1::2] = y_max
print(f"Downsampling time (24M -> 10k): {(time.time() - start)*1000:.2f} ms")

# Test math after downsampling vs before
start = time.time()
res = data + 1.0 # Current logic: math on 24M samples
print(f"Math on 24M samples: {(time.time() - start)*1000:.2f} ms")

start = time.time()
res = env + 1.0 # Proposed logic: math on 10k samples
print(f"Math on 10k samples: {(time.time() - start)*1000:.2f} ms")
