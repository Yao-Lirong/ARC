class state():
	def __init__(self, canvas = [], cost = 0, command_cost = 0, parent = None, edge = None, hash = None):
		self.canvas = canvas
		self.cost = cost
		self.command_cost = command_cost
		self.parent = parent
		self.edge = edge
		self.hash = self.hash_aux() if hash == None else hash
	
	def hash_aux(self):
		return hash(tuple(map(tuple, self.canvas)))

	def __hash__(self):
		return self.hash

	def __lt__(self, obj):
		"""self < obj."""
		return self.cost < obj.cost

	def __le__(self, obj):
		"""self <= obj."""
		return self.cost <= obj.cost
	
	def __str__(self):
		s = ""
		for o in self.canvas:
			s += o.__str__() + '\n'
		return s


class obj():
	def __init__(self, tp = "", xs = -1, ys = -1, color = -1, l = -1, xlen = -1, ylen = -1):
		"""
		type : str
			type of this object, can be 
			- 'dot'
			- line (
			  'vertical': vertical line starts from lower end pointing to higher end
			  'parallel': parallel line starts from left pointing to right
			  'diagonal_ur': diagonal line pointing upper right, 
			  'diagonal_lr': diagonal line pointing lower right), 
			- rectangle (
			  'rectangle': filled rectangle starts from lower-left to upper-right
			  'outline': unfilled rectangle starts from lower-left to upper-right), 
			- 'cheat' : bitmap, starts from upper-left to lower-right
		xs : int 
			x coordinate of the starting point 
		ys : int
			y coordinate of the starting point
		color : int
			color of this object
		l : int, optional
			length of a line, -1 if not a line 
		xlen : int, optional
			x-axis length of a rectangle/bitmap, -1 if not a rec/bm
		ylen : int, optional
			y-axis length of a rectangle/bitmap, -1 if not a rec/bm
		"""
		self.type = tp
		self.len = l
		self.xlen = xlen
		self.ylen = ylen
		self.xs = xs
		self.ys = ys
		self.color = color
	
	def __hash__(self):
		return hash((self.type, self.len, self.xlen, self.ylen, self.xs, self.ys, self.color))

	def __str__(self):
		general = str.format(" at ({0}, {1}) of color {2}", self.xs, self.ys, self.color)
		if self.type == "dot": return "dot" + general
		if self.type == "vertical": return "vertical line of length " + str(self.len) + general
		if self.type == "parallel": return "parallel line of length " + str(self.len) + general
		if self.type == "diagonal_ur" or self.type == "diagonal_lr": return "diagonal line of length " + str(self.len) + general
		if self.type == "rectangle": return "rectangle of xlength " + str(self.xlen) + " ylength " + str(self.ylen) + general
		if self.type == "new": return "a new object"
		if self.type == "cheat": return "bitmap of xlength " + str(self.xlen) + " ylength " + str(self.ylen) + general

	def __repr__(self):
		return self.__str__()