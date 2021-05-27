
class ChartLayer:
	def __init__(self, path, ctype, enabled = True):
		self.path = path
		self.ctype = ctype
		self.enabled = enabled

	def onRegister(self, onTickHandler = None):
		""" Called when the dataset is registered on the software """
		pass