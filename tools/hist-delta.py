import csv
import numpy as np
import matplotlib.pyplot as plt
import sys

with open(sys.argv[1]) as input:
  reader = csv.reader(input, delimiter=',')
  delta = []
  for row in reader:
    ts = float(row[1])
    if ts > 0.5:
      continue
    delta.append(ts * 1000)
  delta = np.array(delta)

  # the histogram of the data
  plt.hist(delta, 1500, facecolor='g', alpha=0.75)

  plt.axis([ -2000, 2000, 0, 25 ])
  plt.xlabel('Delta')
  plt.ylabel('Count')
  plt.grid(True)
  plt.show()
