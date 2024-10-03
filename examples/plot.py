import numpy as np
import matplotlib.pyplot as plt 

path = '/home/estevesjh/Documents/github/skyhunter-python/DATA/keysight/'
res = np.load(f'{path}/char_real_1926_snake_data_00001.npz.npy')

plt.plot(res['time'], res['CHAR'])
plt.xlabel('Time (s)')
plt.ylabel('Current (A)')
plt.savefig('twilight.png')
print(res)