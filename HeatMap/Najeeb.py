import numpy as np
import pandas as pd

print(np.mean(np.array([1, 2, 3, 4, 5])))

print(np.std(np.mean(np.array([1, 16, 3, 8, 10]), dtype=np.float32)))

data = pd.read_csv("D:\\Study and Extras\\Dr Nawaz Sb Paper\\Bedar Bhi\\Bedar\\PCA\\Replaced1.csv")

d1 = data.mean(axis=0)
d2 = data.std(axis=0)
d1.to_csv("D:\\Study and Extras\\Dr Nawaz Sb Paper\\Bedar Bhi\\Bedar\\PCA\\Mean.csv")
d2.to_csv("D:\\Study and Extras\\Dr Nawaz Sb Paper\\Bedar Bhi\\Bedar\\PCA\\Std.csv")
