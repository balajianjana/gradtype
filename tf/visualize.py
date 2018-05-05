import matplotlib
import sys

# Do not display GUI only when generating output
if __name__ != '__main__' or len(sys.argv) >= 3:
  matplotlib.use('Agg')

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.axes as axes
import numpy as np
import sklearn.decomposition
import tensorflow as tf

# Internal
import dataset
from model import Model

COLOR_MAP = plt.cm.gist_rainbow
LABELS = dataset.load_labels()

def to_color(index):
  return index / (len(LABELS) - 1)

def pca(train, validate, fname=None):
  fig = plt.figure(1, figsize=(8, 6))
  pca = sklearn.decomposition.PCA(n_components=2, random_state=0x7ed1ae6e)

  # ax.set_xlim(left=-0.9, right=0.9)
  # ax.set_ylim(bottom=-0.9, top=0.9)
  # ax.set_zlim(bottom=-0.9, top=0.9)

  # Fit coordinates
  pca.fit([ seq['features'] for seq in (train + validate) ])

  train_coords = pca.transform([ seq['features'] for seq in train ])
  validate_coords = pca.transform([ seq['features'] for seq in validate ])

  for seq, coords in zip(train, train_coords):
    seq['coords'] = coords

  for seq, coords in zip(validate, validate_coords):
    seq['coords'] = coords

  for kind, dataset in zip([ 'train', 'validate' ], [ train, validate ]):
    colors = []
    all_x = []
    all_y = []

    for seq in dataset:
      category = seq['category']

      x = seq['coords'][0]
      y = seq['coords'][1]

      label = seq['label']
      color = COLOR_MAP(to_color(category))

      marker = 'o' if kind is 'train' else '^'
      size = 5 if kind is 'train' else 8
      plt.scatter(x, y, c=color, marker=marker,
                  edgecolor='k', s=size, alpha=0.9, linewidths=0.0,
                  edgecolors='none')

  if fname == None:
    plt.show()
  else:
    plt.savefig(fname=fname)
    print("Saved image to " + fname)

model = Model(training=False)

input_shape = (None, dataset.MAX_SEQUENCE_LEN,)

p_codes = tf.placeholder(tf.int32, shape=input_shape, name='codes')
p_deltas = tf.placeholder(tf.float32, shape=input_shape, name='deltas')

output = model.build(p_codes, p_deltas)

with tf.Session() as sess:
  sess.run(tf.global_variables_initializer())

  saver = tf.train.Saver(max_to_keep=0, name='visualize')
  saver.restore(sess, sys.argv[1])

  train_dataset, validate_dataset = dataset.load()

  train_dataset, _ = dataset.trim_dataset(train_dataset)
  validate_dataset, _ = dataset.trim_dataset(validate_dataset)

  train_dataset = dataset.flatten_dataset(train_dataset)
  validate_dataset = dataset.flatten_dataset(validate_dataset)

  codes = []
  deltas = []

  for seq in train_dataset:
    codes.append(seq['codes'])
    deltas.append(seq['deltas'])

  for seq in validate_dataset:
    codes.append(seq['codes'])
    deltas.append(seq['deltas'])

  features = sess.run(output, feed_dict={
    p_codes: codes,
    p_deltas: deltas,
  })

  train_features = []
  for seq in train_dataset:
    seq = dict(seq)
    seq.update({ 'features': features[0] })
    train_features.append(seq)
    features = features[1:]

  validate_features = []
  for seq in validate_dataset:
    seq = dict(seq)
    seq.update({ 'features': features[0] })
    validate_features.append(seq)
    features = features[1:]

  pca(train_features, validate_features)