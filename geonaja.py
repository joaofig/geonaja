import urllib
import os.path
import zipfile
import numpy as np
import math


class ElevationProvider(object):

    def __init__(self):
        pass

    @staticmethod
    def get_tile_name(latitude, longitude):
        x = int((longitude + 180.0) / 5.0) + 1
        y = int(-latitude / 5.0) + 12
        return "srtm_{0:02d}_{1:02d}".format(x, y)

    @staticmethod
    def download_tile(tile_name, dir_name):
        url = "http://srtm.csi.cgiar.org/wp-content/uploads/files/srtm_5x5/ASCII/" + tile_name + ".zip"
        file_name = os.path.join(dir_name, tile_name + ".zip")
        urllib.urlretrieve(url, file_name)


class ElevationTile(object):

    def __init__(self, rows, cols, x_ll, y_ll, cell_size):
        self.array = np.zeros((rows, cols), dtype=np.int32)
        self.x_ll = x_ll
        self.y_ll = y_ll
        self.cell_size = cell_size

    def get_elevation(self, latitude, longitude):
        row = math.trunc((latitude - self.y_ll) / self.cell_size + 0.5)
        col = math.trunc((longitude - self.x_ll) / self.cell_size + 0.5)
        return self.array[self.array.shape[0] - row, col]


class FileElevationProvider(ElevationProvider):

    def __init__(self, cache_dir):
        self.cache_dir = cache_dir
        self.tile_dict = {}

    @staticmethod
    def parse_text(content):
        rows = 0
        cols = 0
        x_ll = 0.0
        y_ll = 0.0
        cell = 0.0
        for i in range(6):
            line = content[i].decode("utf-8")
            items = line.split()
            if items[0] == "ncols":
                cols = int(items[1])
            elif items[0] == "nrows":
                rows = int(items[1])
            elif items[0] == "xllcorner":
                x_ll = float(items[1])
            elif items[0] == "yllcorner":
                y_ll = float(items[1])
            elif items[0] == "cellsize":
                cell = float(items[1])
        tile = ElevationTile(rows, cols, x_ll, y_ll, cell)

        # Read in all the elevation values
        for i in range(6, len(content)):
            line = content[i].decode("utf-8")
            items = line.split()
            row = np.array(list(map(int, items)))
            tile.array[i - 6, :] = row
        return tile

    def get_tile(self, tile_name):
        tile = None
        if tile_name in self.tile_dict:
            tile = self.tile_dict[tile_name]
        else:
            file_name = os.path.join(self.cache_dir, tile_name + ".zip")

            if not os.path.exists(file_name):
                self.download_tile(tile_name, self.cache_dir)

            if os.path.exists(file_name):
                with zipfile.ZipFile(file_name) as z:
                    with z.open(tile_name + ".asc") as asc:
                        content = asc.readlines()
                        tile = self.parse_text(content)
                        self.tile_dict[tile_name] = tile
        return tile

    def get_elevation(self, latitude, longitude):
        tile_name = self.get_tile_name(latitude, longitude)

        tile = self.get_tile(tile_name)
        if tile is not None:
            return tile.get_elevation(latitude, longitude)
        else:
            return -9999


class SqliteElevationProvider(ElevationProvider):

    def __init__(self, database):
        self.db_file = database

    def get_elevation(self, latitude, longitude):
        return -9999


if __name__ == "__main__":
    elevation = FileElevationProvider("/Users/jpf/data/srtm/ascii")
    print(elevation.get_elevation(34.1225696, -118.2181179))
