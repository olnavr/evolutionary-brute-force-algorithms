class Demand(object):
	def __init__(self, start_node, end_node, volume):
		self.start_node = start_node
		self.end_node = end_node
		self.volume = volume
		self.paths = {}
		
	def add_path(self, path_id, link_list):
		self.paths[path_id] = link_list
		
	def print_object(self):
		print('########## DEMAND ##########\nStart Node: {}\nEnd Node: {}\nVolume: {}\nPaths: {}\n############################\n'.format(
			self.start_node,
			self.end_node,
			self.volume,
			self.paths))