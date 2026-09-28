import geopandas as gpd
from shapely.geometry import Point, LineString, MultiLineString
import os

# Input file paths
# Input Predicted logging lines: center lines
# Input original GNSS data, after spliting the segments
root_folder = './data/LTA_outputs/'
GPS_split_shapefile = os.path.join(root_folder, 'split_lines_Trails2.shp')  # GNSS trials with splited segments
print('processing site:', GPS_split_shapefile)
input_shapefile = os.path.join(root_folder, 'smoothed_centerlines_Trails2.shp') #  Center lines of GNSS trials
# Output file paths
# Output buffer shapefile
buffer_shapefile = os.path.join(root_folder, 'BufferZones_Trails2.shp') 
# Output summar machine passes
output_summary_shapefile = os.path.join(root_folder, 'SummaryBufferMachinePasses_Trails2.shp')
# Output shapefile of centerline segments and their machine passes
centerlines_withpasses = os.path.join(root_folder, 'centerline_withpasses_Trails2.shp') 

# Load the polyline shapefile
gdf = gpd.read_file(input_shapefile)

# Step 1: Create a list to store the buffer geometries
buffer_geometries = []

# Step 2: Loop through each feature in the GeoDataFrame
for _, row in gdf.iterrows():
    # Get the geometry of the polyline
    polyline = row.geometry
    
    # Check if the geometry is a MultiLineString (or LineString)
    if isinstance(polyline, (LineString, MultiLineString)):
        # Calculate the midpoint for MultiLineString geometries (just an example)
        if isinstance(polyline, MultiLineString):
            midpoint = polyline.geoms[0].interpolate(0.5, normalized=True)  # Taking the first geometry for midpoint
        else:
            midpoint = polyline.interpolate(0.5, normalized=True)  # Normalized means 50% along the line
        
        # Create a circular buffer around the midpoint (5-meter radius)
        buffer = midpoint.buffer(2)  # 5 meters buffer. You can modify this
        
        # Add the buffer geometry to the list
        buffer_geometries.append(buffer)

# Step 3: Create a new GeoDataFrame with the buffers
buffer_gdf = gpd.GeoDataFrame(geometry=buffer_geometries, crs=gdf.crs)

# Save the buffer GeoDataFrame to a new shapefile
buffer_gdf.to_file(buffer_shapefile)

# Step 4: Read the files again after creating the buffer zones
buffers = gpd.read_file(buffer_shapefile)
original_data = gpd.read_file(GPS_split_shapefile)

# Ensure CRS match
if buffers.crs != original_data.crs:
    original_data = original_data.to_crs(buffers.crs)

# Step 5: List to store buffer zone information with the count of intersecting lines
buffer_zone_data = []

# Iterate through each buffer zone
for index, buffer_row in buffers.iterrows():
    buffer_geom = buffer_row.geometry  # Get the buffer geometry

    # Find the polylines that intersect this buffer
    intersecting_lines = original_data[original_data.geometry.intersects(buffer_geom)]
    
    # Count the number of intersecting lines
    count = len(intersecting_lines)
    
    # Get the IDs of the intersecting polylines
    intersecting_ids = intersecting_lines.index.tolist()
    
    # Convert list of IDs to a string (comma-separated)
    intersecting_ids_str = ', '.join(map(str, intersecting_ids))
    
    # Append the data to the list
    buffer_zone_data.append({
        'geometry': buffer_geom,
        'M_passes': count,
        'Intersecting_Line_IDs': intersecting_ids_str  # Store as a string
    })
    
    # Print the intersecting lines for the buffer
    print(f"Buffer {index}: {count} Machine passes")
    print(f"Intersecting Line IDs: {intersecting_ids_str}")

# Step 6: Create a new GeoDataFrame with the buffer zones and counts
summary_gdf = gpd.GeoDataFrame(buffer_zone_data, crs=buffers.crs)

# Step 7: Add M_passes column to the smoothed centerlines
# Ensure both GeoDataFrames use the same FID/index
gdf = gdf.reset_index()  # Ensure index is FID for smoothed centerlines
summary_gdf = summary_gdf.reset_index()  # Ensure index is FID for buffer summary

# Merge the GeoDataFrames based on FID (assuming FID is the default index)
merged_gdf = gdf.merge(summary_gdf[['index', 'M_passes']], left_on='index', right_on='index', how='left')

# Step 8: Save the merged GeoDataFrame to a new shapefile
merged_gdf.to_file(centerlines_withpasses)


# Save the summary GeoDataFrame to a new shapefile
summary_gdf.to_file(output_summary_shapefile)

# Print completion message
print(f"Summary shapefile created: {output_summary_shapefile}")
