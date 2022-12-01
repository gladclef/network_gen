from random import random
from PIL import Image, ImageDraw

from MicroGrid import *
from tools import *

def create_adjacency_matrix(MGs: list[list[MicroGrid]], filename: str):
	ny = len(MGs)
	nx = len(MGs[0])

	first = True
	with open(filename, 'w') as fout:
		for MGs_row in MGs:
			for MG in MGs_row:
				if not first:
					fout.write("\n")

				for row in MG.get_adjacency_matrix(ny, nx):
					for is_connected in row:
						if is_connected:
							fout.write("1 ")
						else:
							fout.write("0 ")

				first = False

def draw_adjacency_matrix(MGs: list[list[MicroGrid]], filename: str):
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

	# draw the connections
	white = (255,255,255)
	black = (0,0,0)
	img = Image.new('RGB', ((nx*2-1)*20, (ny*2-1)*20), color=white)
	draw = ImageDraw.Draw(img)
	for y in range(ny*2-1):
		for x in range(nx*2-1):
			char = text_lines[y][x]

			if char == "*":
				ex, ey = x*20+2, y*20+2
				draw.ellipse((ex, ey, ex+15, ey+15), outline=black, fill=None)
			if char == "-":
				draw.line([(x*20, y*20+10), (x*20+19, y*20+10)], fill=black)
			if char == "|":
				draw.line([(x*20+10, y*20), (x*20+10, y*20+19)], fill=black)
			if char == "\\" or char == "X":
				draw.line([(x*20, y*20), (x*20+19, y*20+19)], fill=black)
			if char == "/" or char == "X":
				draw.line([(x*20+19, y*20), (x*20, y*20+19)], fill=black)
	img.save(filename)

def write_node_coordinates(MGs: list[list[MicroGrid]], filename: str):
	lines: list[list[str]] = []
	maxlen = 0
	
	# get all the coord strings
	for row in MGs:
		for MG in row:
			xs = "%.2f" % MG.coord_x
			ys = "%.2f" % MG.coord_y
			maxlen = max(maxlen, len(xs))
			lines.append([xs, ys])

	# write the coords to the file
	with open(filename, 'w') as fout:
		first = True
		for line in lines:
			if not first:
				fout.write("\n")
			fout.write(line[0].ljust(maxlen+2) + line[1])
			first = False

if __name__ == "__main__":
	MGs: list[list[MicroGrid]] = []

	# how many microgrids
	nx, ny = 10, 10

	# how far apart to space the microgrids, in km
	avg_dist = 10
	rand_dist = 1
	get_rand_dist = lambda: random()*2*rand_dist-rand_dist

	# generate our grid of microgrids
	for y in range(ny):
		MGs.append([])
		for x in range(nx):
			# create a microgrid with a pseudo random position and random connections
			MG = MicroGrid(x, y,
				           avg_dist*x + get_rand_dist(), avg_dist*y + get_rand_dist(),
				           side_conn_prob=90, corner_conn_prob=15)
			MGs[y].append(MG)
			
			# if this microgrid is on the edge of our network, then crop outside connections
			MG.crop_connections(y == 0, x == nx-1, y == ny-1, x == 0)

			# for connections to pre-existing MGs, use those randomly determined connections instead
			if x > 0:
				MG.use_existing_connections(MGs[y][x-1], dir="west")
				if y > 0:
					MG.use_existing_connections(MGs[y-1][x-1], dir="northwest")
					if x < nx-1:
						MG.use_existing_connections(MGs[y-1][x+1], dir="northeast")
			if y > 0:
				MG.use_existing_connections(MGs[y-1][x], dir="north")

	# save out to files
	draw_adjacency_matrix(MGs, os.path.join(dir(__file__), "output", "adjacency_matrix.png"))
	create_adjacency_matrix(MGs, os.path.join(dir(__file__), "output", "adjacency_matrix.txt"))
	write_node_coordinates(MGs, os.path.join(dir(__file__), "output", "node_coordinates.txt"))