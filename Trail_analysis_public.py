"""
This script is to calculate and output the logging trail characteristics, including;
    
    Harvest_area, TLT, LTP, DT, LTA, LTAS, GBRC, NBRC, CI, ADT, KEI

        1. Harvest_area: Total harvest area: Harvest_area (ha) 
        2. CI: Compactness Index

        3. TLT: Logging trail network length: Total (m) 
           LTP: Logging trail network length per hectare (m/ha)

        4. DT: Distance travelled: SUM(length of each segments * the pass number)
        5. ADT: Average distance between trails: (m), around 20 m
        6. LTA: Logging trail area: total length of the center lines * 4.5 m - intersection areas
        7. LTAS: Share of logging trail area: Logging trail area  / Total harvest area (percentage, around 25%) 
        8. Gross boom reach coverage (ha)
        9. Net boom reach coverage: Gross boom reach coverage - intersection areas (where two buffers overlap)(ha)
        10. KEI: Logging trail efficiency factor
        11. RFA: relative forest accessibility
        
The input files include:  
(1) Polyline shapefile: trails and pass number
(2) Polygone shapefile: logging site boundary

"""

import geopandas as gpd
from shapely.geometry import Polygon, MultiPolygon
from shapely.ops import unary_union
import geopandas as gpd
import numpy as np
import math
from sklearn.cluster import KMeans
from shapely.affinity import rotate
import os

def calculate_overlap(buffer_gdf):
    overlap_polygons = [] # to record overlap polygon
    # Traverse all buffers and calculate the overlapping area
    for i in range(len(buffer_gdf)):
        for j in range(i + 1, len(buffer_gdf)):  # 
            buffer1 = buffer_gdf.geometry.iloc[i]
            buffer2 = buffer_gdf.geometry.iloc[j]
            
            if buffer1.intersects(buffer2):  # if intersect

                overlap_geom = buffer1.intersection(buffer2)  # Calculate intersection area
                if isinstance(overlap_geom, Polygon) or overlap_geom.geom_type == 'MultiPolygon':
                    overlap_polygons.append(overlap_geom)
    return overlap_polygons

def get_buffer_overlap(GBRC_buffer_gdf):

    overlap_geoms = []
    # Traverse all buffers and find the intersection between them, extract non-empty intersections
    for i, geom1 in enumerate(GBRC_buffer_gdf.geometry):
        for j, geom2 in enumerate(GBRC_buffer_gdf.geometry):
            if j > i:
                inter = geom1.intersection(geom2)
                if not inter.is_empty:
                    overlap_geoms.append(inter)

    # Merge all overlapping parts
    if len(overlap_geoms) == 1:
        overlap_union = overlap_geoms[0]
    else:
        overlap_union = unary_union(overlap_geoms)

    # Create overlapping area GeoDataFrame
    buffer_overlap_gdf = gpd.GeoDataFrame(geometry=[overlap_union], crs=GBRC_buffer_gdf.crs)
    return buffer_overlap_gdf

def calculate_TrailChara(logging_trail_gdf, boundary_gdf, original_crs, file_name_no_ext):
    
    # boundary site area = Harvest_area
    total_area_m2 = boundary_gdf.geometry.area.sum()  #  (unit m²)
    Harvest_area = total_area_m2 / 10000  # from square meter to (ha)

    total_perimeter_m = boundary_gdf.geometry.length.sum()
    #Compactness Index (CI)
    CI = 4 * math.pi * total_area_m2 / (total_perimeter_m ** 2)

    # Total Length of Trails = TLT unit: m
    TLT = logging_trail_gdf.geometry.length.sum()
    # Length of Trails Per hectare = LTP
    LTP = TLT/Harvest_area

    # Distance travelled (DT): SUM(length of each segments * the pass number)
    # Calculate the length of each line segment (in meters)
    logging_trail_gdf["length_m"] = logging_trail_gdf.geometry.length
    # Multiply by the number of passes field (e.g. called "M_passes")
    logging_trail_gdf["travel_distance_m"] = logging_trail_gdf["length_m"] * logging_trail_gdf["M_passes"]
    # Distance Travelled; SUM(length of each segments * the pass number)
    DT = logging_trail_gdf["travel_distance_m"].sum()


    #LTA: Logging trail area (with 4.5 m width): total length of the center lines * 4.5 m - intersection areas
    Trail_width = 4.5 # meters
    LTA_buffer_gdf = logging_trail_gdf.copy()
    LTA_buffer_gdf["geometry"] = logging_trail_gdf.geometry.buffer(Trail_width/2)
    # All Polygon area with overlap
    LTA_buffer_gdf["area"] = LTA_buffer_gdf.geometry.area
    # union Polygon without overlap
    LTA_merged_polygons = unary_union(LTA_buffer_gdf.geometry)
    # area size withou overlap, LTA: Logging trail area: total length of the center lines * 4.5 m - intersection areas
    LTA = LTA_merged_polygons.area
    #LTAS: Share (%):  Logging trail area  / Total harvest area (percentage, around 25%)
    LTAS = LTA/total_area_m2*100 # unit: %

    # GBRC: Gross boom reach coverage: 
    # NBRC: Net boom reach coverage: Gross boom reach coverage - intersection areas (where two buffers overlap)
    GBRC_buffer_gdf = logging_trail_gdf.copy()
    GBRC_buffer_gdf["geometry"] = GBRC_buffer_gdf.geometry.buffer(10)

    # All Polygon area with overlap
    GBRC_buffer_gdf["area"] = GBRC_buffer_gdf.geometry.area
    # Difference: the part inside the buffer and outside the boundary
    buffer_outside_gdf = gpd.overlay(GBRC_buffer_gdf, boundary_gdf, how='difference')
    GBRC_out = buffer_outside_gdf.geometry.area.sum()

    GBRC = GBRC_buffer_gdf["area"].sum()

    buffer_overlap_gdf = get_buffer_overlap(GBRC_buffer_gdf)
    # save shapefile of overlap regions
    buffer_overlap_gdf.to_file("./data/buffer/" + file_name_no_ext + "_buffer_overlap.shp")

    


    

    # union Polygon without overlap
    GBRC_merged_polygons = unary_union(GBRC_buffer_gdf.geometry)
    # area size withou overlap
    # NBRC = GBRC_merged_polygons.area

    # save GBRC_merged_polygons
    if isinstance(GBRC_merged_polygons, (Polygon, MultiPolygon)):
        GBRC_merged_polygons_gdf = gpd.GeoDataFrame(geometry=[GBRC_merged_polygons], crs=original_crs)
    else:
        raise ValueError("The merged geometry type is not a polygon.")
    GBRC_merged_polygons_gdf.to_file("./data/buffer/" + file_name_no_ext + "_buffer.shp")

    # clip buffer_gdf using boundary
    # Intersection: the part of the buffer that intersects with the boundary
    buffer_clip_gdf = gpd.overlay(GBRC_merged_polygons_gdf, boundary_gdf, how='intersection')
    


    # save buffer region after clipping
    buffer_clip_gdf.to_file("./data/buffer/" + file_name_no_ext + "_buffer_clip.shp")
    # 5. Calculate the clipped area
    NBRC = buffer_clip_gdf.geometry.area.sum()

    NBRC_rate = NBRC/total_area_m2

    return Harvest_area, TLT, LTP, DT, LTA, LTAS, GBRC, NBRC, CI, GBRC_out, NBRC_rate

###   Average distance between trails: (m) ADT
def fit_tangent_line(line, point):
    """Calculate the equation of the tangent line at a point on line (Ax + By + C = 0)"""
    coords = np.array(line.coords)
    # Find the point on line that is closest to point
    nearest_point = line.interpolate(line.project(point))

    # Calculate the direction of the tangent line near the nearest point
    dists = np.linalg.norm(coords - np.array([nearest_point.x, nearest_point.y]), axis=1)
    idx = np.argmin(dists)  # Find the index of the closest point

    if idx == 0:
        p1, p2 = coords[idx], coords[idx + 1]
    elif idx == len(coords) - 1:
        p1, p2 = coords[idx - 1], coords[idx]
    else:
        p1, p2 = coords[idx - 1], coords[idx + 1]

    # tangent line: Ax + By + C = 0
    x1, y1 = p1
    x2, y2 = p2
    A = y2 - y1
    B = -(x2 - x1)
    C = -(A * x1 + B * y1) 

    return A, B, C

def calculate_direction(line):
    start = line.coords[0]   # start point (x1, y1)
    end = line.coords[-1]    # end point (x2, y2)
    dx = end[0] - start[0]
    dy = end[1] - start[1]
    angle = np.degrees(np.arctan2(dy, dx))  # calculate angle
    angle = (angle + 360) % 360  # calculate in 0-360°
    return angle

def sample_points(line, num=5):
    # Generate num equally spaced points on the line segments
    distances = np.linspace(0, line.length, num)  # Generate even spacing
    return [line.interpolate(d) for d in distances]

def find_nearest_non_intersecting(line, candidates):
    """
    Find the line segment that is closest to line and does not intersect it in candidates
    """
    nearest_line = None
    nearest_distance = float("inf")

    for candidate in candidates:
        if not line.intersects(candidate):  # Make sure line segments do not intersect
            dist = line.distance(candidate)
            if dist < nearest_distance:
                nearest_distance = dist
                nearest_line = candidate
    return nearest_line, nearest_distance

def compute_average_spacing(gdf_trail):
    """
    Calculate the average spacing between adjacent non-intersecting logging trails
    """
    average_distances = {}
    for name, group in gdf_trail.groupby('group'):
        if len(group) < 2:
            continue  
        print(f'Processing group {name}...')
        remaining_lines = group["geometry"].tolist()
        distances = [] 
        # Select starting line segments
        if name == 1:
            start_line = min(remaining_lines, key=lambda line: (line.bounds[0], -line.bounds[3]))  # Top left corner
        elif name == 2:
            start_line = min(remaining_lines, key=lambda line: (line.bounds[0], line.bounds[1]))  # Lower left corner
        else:
            start_line = remaining_lines[0] 

        remaining_lines.remove(start_line)
        current_line = start_line

        while remaining_lines:
            nearest_line, _ = find_nearest_non_intersecting(current_line, remaining_lines)
            if nearest_line is None:
                break 
            nearest_point = nearest_line.interpolate(nearest_line.project(current_line.interpolate(0.5)))
            # Calculate the tangent equation at this point
            A, B, C = fit_tangent_line(nearest_line, nearest_point)
            # Generate sampling points on line1
            points = sample_points(current_line, num=3)
            # Calculate the perpendicular distance from all sampling points to the tangent line
            point_distances = [abs(A * p.x + B * p.y + C) / np.sqrt(A**2 + B**2) for p in points]
            # Calculate the average distance
            avg_distance = np.mean(point_distances)
            #print('point_distances:', point_distances)
            #print('avg_distance:', avg_distance)
            if avg_distance < 40:
            #print(f'avg_distance between {current_line} and {nearest_line}: {avg_distance}')
                distances.append(avg_distance)
            # Update the current segment
            current_line = nearest_line
            remaining_lines.remove(nearest_line)
        average_distances[name] = sum(distances) / len(distances) if distances else None 
    return average_distances

def calculate_TrailDistance(gdf_trail):
    # filter out trail with length less than 20 m
    gdf_trail = gdf_trail[gdf_trail.geometry.length >= 20]
    # Polyline direction
    gdf_trail['direction'] = gdf_trail.geometry.apply(calculate_direction)
    # KMeans group segments by their direction, group 1 or 2
    directions = gdf_trail["direction"].values.reshape(-1, 1)
    kmeans = KMeans(n_clusters=2, random_state=42).fit(directions)
    gdf_trail["group"] = kmeans.labels_
    # check groups
    # gdf_trail.to_file("../data/temp/trail_direction_group2.shp")
    
    average_distances = compute_average_spacing(gdf_trail) # Final average distances: {0: 21.64, 1: 27.83}
    try:
        ADT = sum(average_distances.values()) / len(average_distances)
    except Exception as e:
         ADT = 20
    print("Final average distances:", average_distances)
    
    return average_distances, ADT


def Trail_analysis(logging_trail_shp, boundary_shp):

    # Get the file name (with suffix)
    file_name = os.path.basename(boundary_shp)  # "Area1.shp"
    # Remove suffix
    file_name_no_ext = os.path.splitext(file_name)[0]  # "Area1"


    # read logging trail data
    logging_trail_gdf = gpd.read_file(logging_trail_shp)
    original_crs = logging_trail_gdf.crs
    # read bounday data
    boundary_gdf = gpd.read_file(boundary_shp)

    Harvest_area, TLT, LTP, DT, LTA, LTAS, GBRC, NBRC, CI, GBRC_out, NBRC_rate= calculate_TrailChara(logging_trail_gdf, boundary_gdf, original_crs, file_name_no_ext) 
    print(f"Harvest_area: {Harvest_area:.2f} ha")
    print(f"Total Length of Trails: {TLT:.2f} m")
    print(f"Compactness Index: {CI:.2f} ha")
    print(f"Length of Trails Per hectare: {LTP:.2f} m/ha")
    print(f"Distance travelled (DT): {DT:.2f} m/ha")
    print(f"Logging trail area: {LTA:.2f} m2")
    print(f"Share of logging trail area: {LTAS:.2f} m2/ha")
    print(f"Gross boom reach coverage: {GBRC:.2f} m2/ha")
    print(f"Net boom reach coverage: {NBRC:.2f} m2/ha")
    print(f"Net boom reach coverage rate: {NBRC_rate:.2f} m2/ha")
    print(f"Net boom reach coverage outside the boundary: {GBRC_out:.2f} m2/ha")

    # ADT: Average distance between trails: (m), around 20 m
    _, ADT = calculate_TrailDistance(logging_trail_gdf)
    print(f"Average distance between trails: {ADT:.3f} m")
    #Ideal_network_Length  = calculate_LTEF(boundary_gdf)
    Ideal_network_Length = 500 #(m/ha)
    #LTEF = round(Ideal_network_Length/LTP, 2)
    KEI =LTP/Ideal_network_Length
    print(f"Logging trail efficiency factor (KEI): {KEI:.3f}")

    # RFA: relative forest accessibility
    RFA_buffer_gdf = logging_trail_gdf.copy()
    RFA_buffer_gdf["geometry"] = RFA_buffer_gdf.geometry.buffer(ADT/2)
    # union Polygon without overlap
    RFA_merged_polygons = unary_union(RFA_buffer_gdf.geometry)
    # area size withou overlap
    #RFA_AREA = RFA_merged_polygons.area

    # save RFA_merged_polygons
    if isinstance(RFA_merged_polygons, (Polygon, MultiPolygon)):
        RFA_merged_polygons_gdf = gpd.GeoDataFrame(geometry=[RFA_merged_polygons], crs=original_crs)
    else:
        raise ValueError("The merged geometry type is not a polygon.")
    
    if not os.path.exists("./data/buffer/"):
        os.makedirs("./data/buffer/")


    RFA_merged_polygons_gdf.to_file("./data/buffer/" + file_name_no_ext + "_ADT_buffer.shp")

    # clip buffer_gdf using boundary
    buffer_clip_gdf = gpd.overlay(RFA_merged_polygons_gdf, boundary_gdf, how='intersection')
    # save buffer region after clipping
    buffer_clip_gdf.to_file("./data/buffer/" + file_name_no_ext + "_ADT_buffer_clip.shp")
    # Calculate the clipped area
    RFA_AREA = buffer_clip_gdf.geometry.area.sum()
    RFA = RFA_AREA/Harvest_area/10000 
    print(f"Relative forest accessibility (RFA): {RFA:.3f}")

    return Harvest_area, TLT, LTP, DT, LTA, LTAS, GBRC, NBRC, GBRC_out, NBRC_rate, CI, ADT, KEI, RFA

if __name__ == "__main__":
    logging_trail_shp  = "./data/LTA_outputs/centerline_withpasses_Trails2.shp"  # input shape polyline trails
    boundary_shp  = "./data/example/site02/Area2.shp"  # input boundary shape polygon
    Harvest_area, TLT, LTP, DT, LTA, LTAS, GBRC, NBRC, GBRC_out, NBRC_rate, CI, ADT, KEI, RFA= Trail_analysis(logging_trail_shp, boundary_shp)
