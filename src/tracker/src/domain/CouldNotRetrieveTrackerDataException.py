class CouldNotRetrieveTrackerDataException(RuntimeError):
   def __init__(self, arg):
      self.args = str(arg)