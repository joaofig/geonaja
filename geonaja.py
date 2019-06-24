import urllib.request
import os.path
import zipfile
import numpy as np
import math
import joblib


class ElevationProvider(object):

    def __init__(self):
        pass

    @staticmethod
    def get_tile_xy(latitude, longitude):
        x = int((longitude + 180.0) / 5.0) + 1
        y = int(-latitude / 5.0) + 12
        return x, y

    @staticmethod
    def get_tile_name_xy(x, y):
        return "srtm_{0:02d}_{1:02d}".format(x, y)

    def get_tile_name(self, latitude, longitude):
        x, y = self.get_tile_xy(latitude, longitude)
        return self.get_tile_name_xy(x, y)

    @staticmethod
    def download_tile(tile_name, dir_name):
        zip_name = tile_name + ".zip"
        url = "http://srtm.csi.cgiar.org/wp-content/uploads/files/" \
              "srtm_5x5/ASCII/" + zip_name
        file_name = os.path.join(dir_name, zip_name)
        urllib.request.urlretrieve(url, file_name)
        return file_name


class ElevationTile(object):

    def __init__(self, rows, cols, x_ll, y_ll, cell_size, x=-1, y=-1):
        self.array = None
        self.rows = rows
        self.cols = cols
        self.x_ll = x_ll
        self.y_ll = y_ll
        self.cell_size = cell_size
        self.x = x
        self.y = y

    def get_row_col(self, latitude, longitude):
        row = self.rows - math.trunc((latitude - self.y_ll) /
                                     self.cell_size + 0.5)
        col = math.trunc((longitude - self.x_ll) / self.cell_size + 0.5)
        return row, col

    def get_elevation(self, latitude, longitude):
        row, col = self.get_row_col(latitude, longitude)
        return self.array[row, col]

    def create_array(self):
        if self.array is None:
            self.array = np.zeros((self.rows, self.cols), dtype=np.int32)

    def get_tile_xy(self):
        return self.x * 100 + self.y

    def get_xy(self, x, y):
        return x * self.cols + y


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
        tile.create_array()
        for i in range(6, len(content)):
            line = content[i].decode("utf-8")
            row = np.fromstring(line, dtype=np.int16, count=cols, sep=' ')
            tile.array[i - 6, :] = row
        return tile

    def get_tile(self, tile_name: str) -> ElevationTile:
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


class JoblibElevationProvider(FileElevationProvider):

    def __init__(self, cache_dir):
        super().__init__(cache_dir)

    def get_tile(self, tile_name: str) -> ElevationTile:
        if tile_name in self.tile_dict:
            tile = self.tile_dict[tile_name]
        else:
            elev_file_name = os.path.join(self.cache_dir, tile_name + ".elev")

            if not os.path.exists(elev_file_name):
                self.download_tile(tile_name, self.cache_dir)

                file_name = os.path.join(self.cache_dir, tile_name + ".zip")
                with zipfile.ZipFile(file_name) as z:
                    with z.open(tile_name + ".asc") as asc:
                        content = asc.readlines()
                        tile = self.parse_text(content)
                        self.tile_dict[tile_name] = tile
                os.remove(file_name)
                joblib.dump(tile, elev_file_name)
            else:
                tile = joblib.load(elev_file_name)
        return tile


if __name__ == "__main__":
    elevation = JoblibElevationProvider("/Users/joafigu/data/srtm/ascii")
    # elevation = SqliteElevationProvider("/Users/jpf/data/srtm.sqlite")
    print(elevation.get_elevation(34.1225696, -118.2181179))
    print(elevation.get_elevation(34.0095999, -117.53678559999999))
    print(elevation.get_elevation(37.6047911, -122.0384952))
