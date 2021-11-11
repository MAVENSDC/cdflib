import numpy as np

from cdflib.epochs import CDFepoch as cdfepoch


class TimeSuite:
    """
    An example benchmark that times the performance of various kinds
    of iterating over dictionaries in Python.
    """
    params = ([True, False], )
    param_names = ['to_np']

    def setup(self, to_np):
        self.epochs = np.ones(1000) * 62567898765432.0
        self.epochs_tt2000 = (np.ones(1000) * 186999622360321123).astype(int)

    def time_epoch_encode(self, to_np):
        cdfepoch.encode(self.epochs)

    def time_epoch_to_datetime(self, to_np):
        cdfepoch.to_datetime(self.epochs)

    def time_epoch_to_datetime_tt2000(self, to_np):
        cdfepoch.to_datetime(self.epochs_tt2000)
