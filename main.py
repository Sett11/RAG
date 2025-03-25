from tqdm import tqdm
from math import sqrt

t=0

for i in tqdm(range(1000000)):
    t+=sqrt(i)

print(t)