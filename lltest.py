import map_tile_stitcher as ms
import map_tile_stitcher.util.conversion as msc

ll = input("latlong: ")
zoom = int(input("zoom: "))

lat, long = ll.split(",")
lat = float(lat)
long = float(long)

lll = msc.get_index_from_coordinate(ms.Coordinate(lat, long), zoom)

print(":".join([str(lll.x), str(lll.y), str(lll.z)]))