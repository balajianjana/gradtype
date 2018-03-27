import numpy as np
import os.path

import keras.layers
from keras import backend as K
from keras.models import Model, Sequential
from keras.layers import Input, Dense, Dropout, BatchNormalization

# [ prev char, next_char, normalized delta or one hot ]
INPUT_SHAPE=(29 * 29 * 2,)

FEATURE_COUNT = 64

# Triple loss alpha
ALPHA = 0.1

#
# Input parsing below
#

def parse_dataset():
  np_file = './out/dataset.npy.npz'
  if os.path.isfile(np_file):
    raw = np.load(np_file)
  else:
    # TODO(indutny): generate numpy
    train = np.loadtxt('./out/train.csv', delimiter=',', dtype=np.float32)
    validate = np.loadtxt('./out/validate.csv', delimiter=',', dtype=np.float32)

    np.savez_compressed(np_file, train=train, validate=validate)
    raw = { 'train': train, 'validate': validate }

  train = {
    'anchor': raw['train'][0::3],
    'positive': raw['train'][1::3],
    'negative': raw['train'][2::3],
  }

  validate = {
    'anchor': raw['validate'][0::3],
    'positive': raw['validate'][1::3],
    'negative': raw['validate'][2::3],
  }

  return { 'train': train, 'validate': validate }

def create_dummy_y(subdataset):
  return np.zeros([ subdataset['anchor'].shape[0], FEATURE_COUNT ])

print('Loading dataset')
dataset = parse_dataset()
dummy_y = {
  'train': create_dummy_y(dataset['train']),
  'validate': create_dummy_y(dataset['validate']),
}

#
# Network configuration
#

def positive_distance(y_pred):
  anchor = y_pred[:, 0::3]
  positive = y_pred[:, 1::3]
  return K.sum(K.square(anchor - positive), axis=1)

def negative_distance(y_pred):
  anchor = y_pred[:, 0::3]
  negative = y_pred[:, 2::3]
  return K.sum(K.square(anchor - negative), axis=1)

def triple_loss(y_true, y_pred):
  return K.maximum(0.0,
      positive_distance(y_pred) - negative_distance(y_pred) + ALPHA)

def pmean(y_true, y_pred):
  return K.mean(positive_distance(y_pred))

def pvar(y_true, y_pred):
  return K.var(positive_distance(y_pred))

def nmean(y_true, y_pred):
  return K.mean(negative_distance(y_pred))

def nvar(y_true, y_pred):
  return K.var(negative_distance(y_pred))

def create_siamese():
  model = Sequential()

  model.add(Dense(400, input_shape=INPUT_SHAPE, activation='relu'))
  model.add(BatchNormalization())
  model.add(Dense(FEATURE_COUNT, activation='linear'))
  model.add(BatchNormalization())

  return model

def create_model():
  siamese = create_siamese()

  anchor = Input(shape=INPUT_SHAPE, name='anchor')
  positive = Input(shape=INPUT_SHAPE, name='positive')
  negative = Input(shape=INPUT_SHAPE, name = 'negative')

  anchor_activations = siamese(anchor)
  positive_activations = siamese(positive)
  negative_activations = siamese(negative)

  merge = keras.layers.concatenate([
    anchor_activations,
    positive_activations,
    negative_activations
  ])

  return Model(inputs=[ anchor, positive, negative ], outputs=merge)

model = create_model()
model.compile('adam', loss=triple_loss, metrics=[
  pmean, pvar,
  nmean, nvar
])

model.fit(x=dataset['train'], y=dummy_y['train'], batch_size=256,
    epochs=100, validation_data=(dataset['validate'], dummy_y['validate']))
