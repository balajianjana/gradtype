import os
import re
import time

weight_file_re = re.compile(r'.*?(\d+)\.h5$')

def load(model, prefix, what='weights'):
  weight_files = [
    name for name in os.listdir('./out') if name.endswith('.h5') and
      name.startswith(prefix)
  ]

  saved_epochs = []
  for name in weight_files:
    match = weight_file_re.match(name)
    if match == None:
      continue
    saved_epochs.append({ 'name': name, 'epoch': int(match.group(1)) })
  saved_epochs.sort(key=lambda entry: entry['epoch'], reverse=True)

  for save in saved_epochs:
    try:
      if what == 'weights':
        model.load_weights(os.path.join('./out', save['name']), by_name=True)
      else:
        model.load(os.path.join('./out', save['name']))
    except IOError:
      continue
    print("Loaded weights from " + save['name'])
    return save['epoch']

  return 0

def get_tensorboard_logdir():
  name = os.environ.get('GRADTYPE_RUN')
  if name is None:
    name = time.asctime()
  return os.path.join('./logs', name)
