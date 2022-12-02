from typing import Optional

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

class MicroGrid:
	def __init__(self, x: int, y: int, coord_x: float, coord_y: float, side_conn_prob: int, corner_conn_prob: int):
		self.x = x
		self.y = y
		self.coord_x = coord_x
		self.coord_y = coord_y
		self.connections = MGConnections(side_conn_prob, corner_conn_prob)

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