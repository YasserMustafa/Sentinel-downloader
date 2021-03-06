import signal, time

def request(arg):
  """Your http request"""
  time.sleep(2)
  return arg

class Timeout():
  """Timeout class using ALARM signal"""
  class Timeout(Exception): pass

  def __init__(self, sec):
    self.sec = sec

  def __enter__(self):
    signal.signal(signal.SIGALRM, self.raise_timeout)
    signal.alarm(self.sec)

  def __exit__(self, *args):
    signal.alarm(0) # disable alarm

  def raise_timeout(self, *args):
    raise Timeout.Timeout()

# Run block of code with timeouts
try:
  with Timeout(3):
    print request("Request 1")
  with Timeout(1):
    print request("Request 2")
except Timeout.Timeout:
  print "Timeout"
