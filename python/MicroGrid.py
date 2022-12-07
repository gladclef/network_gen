from PIL import ImageColor, Image, ImageDraw # pip install Pillow

from tools import *

class MGConnections:
	def __init__(self, side_prob: int, corner_prob: int):
		self.connections: list[list[bool]] = []
		for y in range(3):
			self.connections.append([])
			for x in range(3):
				if x == 1 and y == 1:
					self.connections[y].append(True)
				elif x == 1 or y == 1:
					self.connections[y].append(bool_prob(side_prob))
				else:
					self.connections[y].append(bool_prob(corner_prob))

		self.n  = lambda: self.is_connected("n")
		self.ne = lambda: self.is_connected("ne")
		self.e  = lambda: self.is_connected("e")
		self.se = lambda: self.is_connected("se")
		self.s  = lambda: self.is_connected("s")
		self.sw = lambda: self.is_connected("sw")
		self.w  = lambda: self.is_connected("w")
		self.nw = lambda: self.is_connected("nw")

	def _get_rel_position(self, dir: str) -> tuple[int, int]:
		if dir == "n" or dir == "north":
			return 0, -1
		elif dir == "ne" or dir == "northeast":
			return 1, -1
		elif dir == "e" or dir == "east":
			return 1, 0
		elif dir == "se" or dir == "southeast":
			return 1, 1
		elif dir == "s" or dir == "south":
			return 0, 1
		elif dir == "sw" or dir == "southwest":
			return -1, 1
		elif dir == "w" or dir == "west":
			return -1, 0
		elif dir == "nw" or dir == "northwest":
			return -1, -1
		raise RuntimeError(f"Unknown direction {dir}!")

	def is_connected(self, rel_x_or_dir: int|str, rel_y: Optional[int] = None):
		if isinstance(rel_x_or_dir, str):
			rel_x, rel_y = self._get_rel_position(rel_x_or_dir)
		else:
			rel_x: int = rel_x_or_dir
			rel_y: int = rel_y
		if rel_x < -1 or rel_y < -1 or rel_x > 1 or rel_y > 1:
			return False
		return self.connections[rel_y+1][rel_x+1]

	def set_connected(self, is_connected: bool, rel_x_or_dir: int|str, rel_y: Optional[int] = None):
		if isinstance(rel_x_or_dir, str):
			rel_x, rel_y = self._get_rel_position(rel_x_or_dir)
		else:
			rel_x: int = rel_x_or_dir
			rel_y: int = rel_y
		self.connections[rel_y+1][rel_x+1] = is_connected

	def encode(self) -> str:
		version = 1
		vals = ["MGConnections", version, len(self.connections), len(self.connections[0])]
		# unwrap connections array into a single array
		conns: list[bool] = []
		for row in self.connections:
			conns += row
		vals += conns
		strparts = [str(n) for n in vals]
		return ",".join(strparts)

	@staticmethod
	def decode(sval: str) -> tuple['MGConnections', str]:
		# verify the string value is a MGConnections
		stype, sval = decode_next(sval)
		if stype != "MGConnections":
			raise RuntimeError("Unknown type \""+stype+"\"")
		version, sval = decode_next(sval, int)
		if version != 1:
			raise RuntimeError("Unknown version \""+str(version)+"\"")

		# decode the MicroGrid
		ny, sval = decode_next(sval, int)
		nx, sval = decode_next(sval, int)
		connections: list[list[bool]] = []
		for y in range(ny):
			row: list[bool] = []
			for x in range(nx):
				bval, sval = decode_next(sval, lambda s: s == "True")
				row.append(bval)
			connections.append(row)

		ret = MGConnections(0, 0)
		ret.connections = connections
		return ret, sval

class MicroGrid:
	def __init__(self, x: int, y: int, coord_x: float, coord_y: float, side_conn_prob: int, corner_conn_prob: int):
		self.x = x
		self.y = y
		self.coord_x = coord_x
		self.coord_y = coord_y
		self.connections = MGConnections(side_conn_prob, corner_conn_prob)
		self.intensity = None

	def crop_connections(self, crop_north: bool, crop_east: bool, crop_south: bool, crop_west: bool):
		if crop_north:
			self.set_connected(False, "n")
			self.set_connected(False, "nw")
			self.set_connected(False, "ne")
		if crop_east:
			self.set_connected(False, "e")
			self.set_connected(False, "ne")
			self.set_connected(False, "se")
		if crop_south:
			self.set_connected(False, "s")
			self.set_connected(False, "sw")
			self.set_connected(False, "se")
		if crop_west:
			self.set_connected(False, "w")
			self.set_connected(False, "nw")
			self.set_connected(False, "sw")

	def use_existing_connections(self, other: 'MicroGrid', dir="north"):
		if dir == "north":
			self.set_connected(other.connections.s(), "n")
		if dir == "northwest":
			self.set_connected(other.connections.se(), "nw")
		if dir == "northeast":
			self.set_connected(other.connections.sw(), "ne")
		if dir == "west":
			self.set_connected(other.connections.e(), "w")

	def get_adjacency_matrix(self, nx: int, ny: int) -> list[list[bool]]:
		""" Returns an adjacency matrix for all connections to other MGs (and itself) within the nx x ny region. """
		ret: list[list[bool]] = []
		for y in range(ny):
			ret.append([])
			for x in range(nx):
				if x == self.x and y == self.y:
					ret[y].append(True)
				elif self.is_connected(x-self.x, y-self.y):
					ret[y].append(True)
				else:
					ret[y].append(False)
		return ret

	def is_connected(self, rel_x_or_dir: int|str, rel_y: Optional[int] = None):
		return self.connections.is_connected(rel_x_or_dir, rel_y)

	def set_connected(self, is_connected: bool, rel_x_or_dir: int|str, rel_y: Optional[int] = None):
		self.connections.set_connected(is_connected, rel_x_or_dir, rel_y)

	def encode(self) -> str:
		version = 1
		vals = ["MicroGrid", version, self.x, self.y, self.coord_x, self.coord_y, self.connections.encode()]
		strparts = [str(n) for n in vals]
		return ",".join(strparts)

	@staticmethod
	def decode(sval: str) -> tuple['MicroGrid', str]:
		# verify the string value is a MicroGrid
		stype, sval = decode_next(sval)
		if stype != "MicroGrid":
			raise RuntimeError("Unknown type \""+stype+"\"")
		version, sval = decode_next(sval, int)
		if version != 1:
			raise RuntimeError("Unknown version \""+str(version)+"\"")

		# decode the MicroGrid
		x, sval = decode_next(sval, int)
		y, sval = decode_next(sval, int)
		coord_x, sval = decode_next(sval, float)
		coord_y, sval = decode_next(sval, float)
		
		# build the microgrid
		mg = MicroGrid(x, y, coord_x, coord_y, 0, 0)
		mg.connections, sval = MGConnections.decode(sval)

		return mg, sval

def write_encoded_mgs(MGs: list[list[MicroGrid]], filename: str):
	version = 1
	vals = ["MGs", version, len(MGs), len(MGs[0])]
	strparts = [str(n) for n in vals]

	with open(filename, "w") as fout:
		fout.write(",".join(strparts) + "\n")
		for row in MGs:
			for mg in row:
				fout.write(mg.encode() + "\n")

def read_encoded_mgs(filename: str) -> list[list[MicroGrid]]:
	with open(filename, "r") as fin:
		sval = fin.readline()

		# verify the string value is a list of microgrids
		stype, sval = decode_next(sval)
		if stype != "MGs":
			raise RuntimeError("Unknown type \""+stype+"\"")
		version, sval = decode_next(sval, int)
		if version != 1:
			raise RuntimeError("Unknown version \""+str(version)+"\"")
		
		# how many microgrids?
		ny, sval = decode_next(sval, int)
		nx, sval = decode_next(sval, int)

		# decode the microgrids
		ret: list[list[MicroGrid]] = []
		for y in range(ny):
			row: list[MicroGrid] = []
			for x in range(nx):
				mgval, sval = MicroGrid.decode(fin.readline())
				row.append(mgval)
			ret.append(row)

		return ret

def draw_adjacency_matrix(MGs: list[list[MicroGrid]], filename: str, max_intensity: Optional[int] = None):
	ny = len(MGs)
	nx = len(MGs[0])

	# get the connections to be drawn
	text_lines: list[str] = []
	for y in range(ny):
		line = ""
		vert = ""
		for x in range(nx):
			MG = MGs[y][x]
			MG_next = None if x == nx-1 else MGs[y][x+1]

			if MG.connections.is_connected("east"):
				line += "*-"
			else:
				line += "* "

			s = "|" if MG.connections.is_connected("south") else " "
			if MG_next != None and MG_next.is_connected("southwest"):
				if MG.connections.is_connected("southeast"):
					vert += s+"X"
				else:
					vert += s+"/"
			else:
				if MG.connections.is_connected("southeast"):
					vert += s+"\\"
				else:
					vert += s+" "

		text_lines.append(line)
		text_lines.append(vert)
	# print("\n".join(text_lines))

	# some basic stats
	imgWidth = (nx * 2 - 1) * 20
	imgHeight = (ny * 2 - 1) * 20
	white = (255,255,255)
	black = (0,0,0)
	colorbar_width = 14
	colorbar_extended = 40
	min_intensity = max_intensity
	if max_intensity is not None:
		imgWidth += colorbar_extended

	# draw the connections
	img = Image.new('RGB', (imgWidth, imgHeight), color=white)
	draw = ImageDraw.Draw(img)
	for y in range(ny*2-1):
		for x in range(nx*2-1):
			char = text_lines[y][x]

			if char == "*":
				ex, ey = x*20+2, y*20+2
				fill = None
				MG = MGs[int(y/2)][int(x/2)]
				if (max_intensity is not None and MG.intensity is not None):
					min_intensity = min(min_intensity, MG.intensity)
					r = int(255*(MG.intensity/max_intensity))
					g = 255-r
					fill = (r, g, 0)
				draw.ellipse((ex, ey, ex+15, ey+15), outline=black, fill=fill)
			if char == "-":
				draw.line([(x*20, y*20+10), (x*20+19, y*20+10)], fill=black)
			if char == "|":
				draw.line([(x*20+10, y*20), (x*20+10, y*20+19)], fill=black)
			if char == "\\" or char == "X":
				draw.line([(x*20, y*20), (x*20+19, y*20+19)], fill=black)
			if char == "/" or char == "X":
				draw.line([(x*20+19, y*20), (x*20, y*20+19)], fill=black)

	# draw the color bar
	if max_intensity is not None:
		x1 = imgWidth - colorbar_extended/2 - colorbar_width/2
		y1 = imgHeight/10
		x2 = imgWidth - colorbar_extended/2 + colorbar_width/2
		y2 = imgHeight-imgHeight/10

		# draw the colors
		start = int(y1+1)
		end = int(y2-1)
		for y in range(start, end+1):
			rel = (y-start) / (end-start)
			scale = 1.0 - rel
			r = int(255*scale)
			g = 255-r
			color = (r, g, 0)
			draw.line(((x1, y), (x2, y)), fill=color)

		# draw the colorbar border
		draw.rectangle(((x1, y1), (x2, y2)), outline=black, fill=None)

		# draw the min and max values
		max_text = "%.1f" % (max_intensity/1_000_000)
		min_text = "%.1f" % (min_intensity/1_000_000)
		draw.text((x1, y1-24), "MB", fill=black)
		draw.text((x1, y1-12), max_text, fill=black)
		draw.text((x1, y2+1), min_text, fill=black)

	img.save(filename)