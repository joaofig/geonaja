# geonaja
Python geographic elevation package

## Using the code
You can use either the `FileElevationProvider` or the `JoblibElevationProvider`
classes, although the latter is preferred for performance reasons. While the 
former caches all elevation tiles as ZIP files, the latter stores them as
serialized Python objects of the `EWlevationTile` class, through the `Joblib`
package, hence the name.

Start by instantiating an object of the `JoblibElevationProvider` class. The 
constructor has as its single parameter the file cache folder path. 

