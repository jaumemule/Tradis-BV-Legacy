from keras.callbacks import LearningRateScheduler, EarlyStopping, Callback
import time
import signal
from ruamel.yaml import YAML
import os


yaml = YAML()
yaml.default_flow_style = False
yaml.preserve_quotes = True
yaml.boolean_representation = ['False', 'True']
with open("config.yml", 'r') as ymlfile:
    cfg = yaml.load(ymlfile)

min_delta = cfg['net']['min_delta']
patience = cfg['net']['patience']
l_rate_decay = cfg['net']['l_rate_decay']
learning_rate = cfg['net']['learning_rate']


# Configure learning rate and early stopping for keras:
er = EarlyStopping(monitor='val_loss',
                   min_delta=min_delta,
                   patience=patience,
                   verbose=1,
                   mode='auto')

if l_rate_decay:
    lrate = LearningRateScheduler(lambda x: learning_rate / (1. + x), verbose=1)
else:
    lrate = LearningRateScheduler(lambda x: learning_rate / (1. + 0), verbose=1)


class SignalStopping(Callback):
    """Stop training when an interrupt signal (or other) was received
    # Arguments:
    sig: the signal to listen to. Defaults to signal.SIGINT.
    doubleSignalExits: Receiving the signal twice exits the python
        process instead of waiting for this epoch to finish.
    patience: number of epochs with no improvement
        after which training will be stopped.
    verbose: verbosity mode.
    """
    def __init__(self, sig=signal.SIGINT, double_signal_exits=True, verbose=1, stop_file=None, stop_file_delta=10):
        # SBW 2018.10.15 Since ctrl-c trapping isn't working, watch for existence of file, e.g. .\path\_StopTraining.txt.
        super(SignalStopping, self).__init__()
        self.signal_received = False
        self.verbose = verbose
        self.double_signal_exits = double_signal_exits
        self.stop_file = stop_file
        self.stop_file_time = time.time()
        self.stop_file_delta = stop_file_delta

        def signal_handler(sig, frame):
            if self.signal_received and self.double_signal_exits:
                if self.verbose > 0:
                    print('')  #new line to not print on current status bar. Better solution?
                    print('Received signal to stop ' + str(sig)+' twice. Exiting..')
                exit(sig)
            self.signal_received = True
            if self.verbose > 0:
                print('') #new line to not print on current status bar. Better solution?
                print('Received signal to stop: ' + str(sig))

        signal.signal(sig, signal_handler)
        self.stopped_epoch = 0

    def on_epoch_end(self, epoch, logs={}):
        # SBW 2018.10.15 Since ctrl-c trapping isn't working, watch for existence of file, e.g. .\path\_StopTraining.txt.
        if self.stop_file is not None:
            # Checking file system is slow in training loop, don't check every epoch.
            delta = time.time() - self.stop_file_time
            if delta>self.stop_file_delta:
                self.stop_file_time += delta
                if os.path.isfile(self.stop_file):
                    self.signal_received = True
        if self.signal_received:
            self.stopped_epoch = epoch
            self.model.stop_training = True

    def on_train_end(self, logs={}):
        if self.stopped_epoch > 0 and self.verbose > 0:
            print('Epoch %05d: stopping due to signal' % (self.stopped_epoch))


sigint_stop = SignalStopping()
