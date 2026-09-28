"""
Logging Trail Visualization
including:
    (1) Machine passes frequency in diferent color 
    (2) Site boundary 
    (3) Legend (right bottom)
    (4) Logging trail characteristics (left top), including:

        Harvest_area, TLT, LTP, DT, LTA, LTAS, GBRC, NBRC, CI, ADT, KEI, RFA

        1. Harvest_area: Total harvest area: Harvest_area (ha) 
        2. CI: Compactness Index, Shape irregularity index

        3. TLT: Logging trail network length: Total (m) 
           LTP: Logging trail network length per hectare (m/ha)

        4. DT: Distance travelled: SUM(length of each segments * the pass number)
        5. ADT:Average distance between trails: (m)
        6. LTA: Logging trail area: total length of the center lines * 4.5 m - intersection areas
        7. LTAS: Share of logging trail area: Logging trail area  / Total harvest area (percentage, around 25%) 
        8. Gross boom reach coverage (ha)
        9. Net boom reach coverage: Gross boom reach coverage - intersection areas (where two buffers overlap)(ha)
        10. KEI: Logging trail efficiency factor
        11. RFA: relative forest accessibility

    (5) North Arrow
    (6) Resolution (from shapefile to png)
The input files include:  
    (1) Polyline shapefile: trails and pass number
    (2) Polygone shapefile: logging site boundary
"""

import geopandas as gpd
import numpy as np
import matplotlib.pyplot as plt
import cv2
import Trail_analysis
import os

# Trail color and width mapping
color_width_mapping = {
    "1": ((156, 151, 150), 1),    # 1 
    "6-7": ((255, 255, 0), 2.8),    # 
    "2": ((25, 182, 221), 1.5),   # 
    "8-9": ((248, 186, 75), 3.2),   # 
    "3": ((54, 229, 29), 1.8),    # 
    "10-11": ((244, 124, 41), 3.4),# 
    "4": ((22, 194, 135), 2),   # 
    "12-13": ((231, 73, 39), 3.6),# 
    "5": ((194, 22, 167),  2.4),   # 
    "14+": ((180, 35, 4),  4) # 
}

def caculate_resolution(img_width, img_height, ax, logging_trail):
    minx, miny, maxx, maxy = logging_trail.total_bounds
    xlim, ylim = ax.get_xlim(), ax.get_ylim()
    # Get the coordinate range automatically calculated by Matplotlib
    xlim = ax.get_xlim()  # (xmin, xmax)
    ylim = ax.get_ylim()  # (ymin, ymax)

    # Calculate the number of pixels per meter
    x_scale = img_width / (xlim[1] - xlim[0])
    y_scale = img_height / (ylim[1] - ylim[0])

    # Calculate the pixel extent of a Shapefile on a PNG
    x_min_pixel = int((minx - xlim[0]) * x_scale)
    x_max_pixel = int((maxx - xlim[0]) * x_scale)
    y_min_pixel = int((ylim[1] - maxy) * y_scale)  # Y-axis flip
    y_max_pixel = int((ylim[1] - miny) * y_scale)

    # Calculate the actual pixel dimensions of a Shapefile in a PNG image
    shapefile_width = x_max_pixel - x_min_pixel
    shapefile_height = y_max_pixel - y_min_pixel
    #print(f"Shapefile in PNG pixel width = {shapefile_width} px, height = {shapefile_height} px")
    resolution_x = (xlim[1] - xlim[0])/shapefile_width
    resolution_y = (ylim[1] - ylim[0])/shapefile_height
    return resolution_x, resolution_y

# gnerate M_passes color and width mapping
def get_color_width(m_passes):
    if m_passes == 1:
        return color_width_mapping["1"]
    elif m_passes == 2:
        return color_width_mapping["2"]
    elif m_passes == 3:
        return color_width_mapping["3"]
    elif m_passes == 4:
        return color_width_mapping["4"]
    elif m_passes == 5:
        return color_width_mapping["5"]
    elif 6 <= m_passes <= 7:
        return color_width_mapping["6-7"]
    elif 8 <= m_passes <= 9:
        return color_width_mapping["8-9"]
    elif 10 <= m_passes <= 11:
        return color_width_mapping["10-11"]
    elif 12 <= m_passes <= 13:
        return color_width_mapping["12-13"]
    elif 14 <= m_passes:
        return color_width_mapping["14+"]
    else:
        return ((128, 128, 128), 1)  

def format_number(x):
    x_float = float(x)  # to float
    if x_float >= 100:
        return str(int(x_float))
    elif 100 > x_float >= 10:
        return f"{x_float:.1f}"[:4]
    else:
        return f"{x_float:.2f}"


def Vis_Trail(logging_trail_shp, boundary_shp, save_png_folder):
    
    # read logging trail data
    #logging_trail_shp  = "../data/FinalOutput_example/centerline_withpasses.shp"  # input shape polyline trails
    logging_trail = gpd.read_file(logging_trail_shp)

    # read bounday data
    # boundary_shp  = "../data/boundary/boundary_1.shp"  # input boundary shape polygon
    boundary = gpd.read_file(boundary_shp)
    boundary_crs_info = boundary.crs  # CRS 
    print('boundary_crs_info:', boundary_crs_info)
    #exit(0)
    # save result image resolution
    dpi = 400 # output resolution
    xmin, ymin, xmax, ymax = boundary.total_bounds  # extend of shapefile
    #map_unit = "meters"  # or "degrees"
    # scale factor 
    if boundary.crs.is_geographic:
        avg_lat = (ymin + ymax) / 2  # Mean latitude
        scale_factor = 111320 * np.cos(np.radians(avg_lat))  # 1 degree ≈ 111320m
    else:
        scale_factor = 1  # The projected coordinate system unit is meters

    # Calculate image size (pixels)
    width_px = int((xmax - xmin) / scale_factor * dpi)
    height_px = int((ymax - ymin) / scale_factor * dpi)

    img_width = int(width_px * 0.01) + 1100 # outpu png size
    img_height = int(height_px * 0.01) #+ 520 # outpu png size
    #print('width_px:', width_px)
    #print('height_px:', height_px)

    # minimum pixel size of the ouput png file
    min_width = 1800
    min_height = 1600
    img_width = max(img_width, min_width)
    img_height = max(img_height, min_height)

    
    fig, ax = plt.subplots(figsize= (img_width / dpi, img_height / dpi), dpi=dpi)
    offset_x = 100  # Move right 100 units
    ax.set_xlim(xmin - offset_x, xmax)
    ax.set_ylim(ymin, ymax)  # The y direction remains unchanged
    ax.set_aspect('equal') #auto  equal
    ax.set_axis_off() # Show Axes

    # # ---------------- draw logging trail ----------------
    Harvest_area, TLT, LTP, DT, LTA, LTAS, GBRC, NBRC, GBRC_out, NBRC_rate, CI, ADT, KEI, RFA = Trail_analysis.Trail_analysis(logging_trail_shp, boundary_shp)

    # round() Keep 2 decimal places
    #Harvest_area, TLT, LTP, DT, LTA, LTAS, GBRC, NBRC, CI, ADT, KEI, RFA = map(lambda x: round(x, 3), 
                                                                #[Harvest_area, TLT, LTP, DT, LTA, LTAS, GBRC, NBRC, CI, ADT, KEI, RFA])

    [Harvest_area, TLT, LTP, DT, LTA, LTAS, GBRC, NBRC, GBRC_out, NBRC_rate, CI, ADT, KEI, RFA] = [format_number(val) for val in [Harvest_area, TLT, LTP, DT, LTA, LTAS, GBRC, NBRC, GBRC_out, NBRC_rate, CI, ADT, KEI, RFA]]

    # # ---------------- draw logging trail ----------------
    for _, row in logging_trail.iterrows():
        m_passes = row["M_passes"]
        color, linewidth = get_color_width(m_passes)
        color = np.array(color) / 255
        # draw trail segments
        gpd.GeoSeries(row.geometry).plot(ax=ax, color=color, linewidth=linewidth)


    # ---------------- draw boundary ----------------
    #facecolor: color of site boundary
    facecolor = np.array((212, 212, 212)) / 255
    # boundary color
    boundary_color = (255, 255, 255)  # 
    boundary.plot(ax=ax, edgecolor=np.array(boundary_color) / 255, linewidth=1, facecolor=facecolor)


    # output resolution of trail map
    resolution_x, resolution_y = caculate_resolution(img_width, img_height, ax, logging_trail)

    # save image 
    fig.canvas.draw()
    image = np.array(fig.canvas.renderer.buffer_rgba())
    # Convert the RGBA image to BGR format (since OpenCV uses BGR)
    image = cv2.cvtColor(image, cv2.COLOR_RGBA2BGR)
    plt.close(fig)

    # ----------------draw Legend  ----------------
    legend_x, legend_y = img_width - 400, img_height - 350  # start point of legend
    legend_box_w, legend_box_h = 360, 380  # size of legend
    # Box parameters (position and size)
    box_x1, box_y1 = legend_x - 15, legend_y - 110  # Top left corner position
    box_w1, box_h1 = 370, 400  # Width and Height of the box
    # Draw the black box for ledgend

    padding = 30
    #text_offset = 50
    font = cv2.FONT_HERSHEY_SIMPLEX
    font_scale = 1.1
    font_thickness = 2

    # draw legend background
    cv2.rectangle(image, (legend_x - padding, legend_y - padding),
                (legend_x + legend_box_w, legend_y + legend_box_h), (255, 255, 255), -1)  # fill in with white

    # Draw legend title (split into two lines)
    cv2.putText(image, "Machine Passes", 
                (legend_x, legend_y - 70),  # position above the legend
                font, font_scale, (0, 0, 0), font_thickness, cv2.LINE_AA)
    cv2.putText(image, "Frequency", 
                (legend_x, legend_y - 30),  # position below the first line
                font, font_scale, (0, 0, 0), font_thickness, cv2.LINE_AA)
    
    # draw ledgend
    items_per_row = 2  
    y_offset = 0
    x_offset = 0  
    row_height = 60  

    for idx, (label, (color, linewidth)) in enumerate(color_width_mapping.items()):
        start_point = (legend_x + x_offset, legend_y + y_offset + 10)  # start
        end_point = (legend_x + x_offset + 40, legend_y + y_offset + 10)  # end

        bgr_color = (color[2], color[1], color[0])  #  RGB → BGR
        cv2.line(image, start_point, end_point, bgr_color, 10)  # draw segments of legend

        cv2.putText(image, label, (legend_x + x_offset + 50, legend_y + y_offset + 15),
                    font, font_scale, (0, 0, 0), font_thickness, cv2.LINE_AA)  # legend label

        # update y_offset and x_offset
        if (idx + 1) % items_per_row == 0:  # If it is the last item on each line, wrap
            y_offset += row_height
            x_offset = 0
        else:
            x_offset += 130  # h padding
        
    cv2.rectangle(image, (box_x1, box_y1), (box_x1 + box_w1, box_y1 + box_h1), (0, 0, 0), 1)  # Black border, thickness = 2

    # ---------------- Draw  Box in Top Left Corner to inpur logging trail characteristics ----------------
    # Box parameters (position and size)
    box_x, box_y = 10, 10  # Top left corner position 20, 20 
    #box_w, box_h = 860, 620  # Width and Height of the box

    base_h_padding = 50
    base_w_padding = 55

    h_padding = 42
    w_padding = 35

    static_color = (0, 0, 0)  # black for static text
    dynamic_color = (0, 0, 0)  # highlight values in blue
    bold_size = 3

    # Draw the black box
    #cv2.rectangle(image, (box_x, box_y), (box_x + box_w, box_y + box_h), (255, 255, 255), 0)  # Black border, thickness = 2

    # Draw the title text inside the box
    cv2.putText(image, "Logging Trail Characteristics ", 
                (box_x + base_w_padding, box_y + base_h_padding + 10), font, 1.6, (0, 0, 0), 3, cv2.LINE_AA)

    # Harvest_area
    #Harvest_area = 13.1 
    # Position for the static part - Harvest position
    text_position_HA = (box_x + base_w_padding, box_y + base_h_padding + 2*h_padding)
    cv2.putText(image, "- Total harvest area: ", text_position_HA, font, font_scale, static_color, 2, cv2.LINE_AA)
    cv2.putText(image, str(Harvest_area) + ' ha', (text_position_HA[0] + cv2.getTextSize("- Total harvest area: ", font, font_scale, bold_size)[0][0], text_position_HA[1]), font, 1, dynamic_color, bold_size, cv2.LINE_AA) #font_scale: 1

    # Position for the static part - Harvest position
    text_position_CI = (box_x + base_w_padding, box_y + base_h_padding + 3*h_padding)
    cv2.putText(image, "- Shape irregularity index: ", text_position_CI, font, font_scale, static_color, 2, cv2.LINE_AA)
    cv2.putText(image, str(CI) + ' ', (text_position_CI[0] + cv2.getTextSize("- Shape irregularity index: ", font, font_scale, bold_size)[0][0], text_position_CI[1]), font, 1, dynamic_color, bold_size, cv2.LINE_AA) #font_scale: 1



    cv2.putText(image, "- Logging trail network length ", 
                (box_x + base_w_padding, box_y + base_h_padding + 4*h_padding), font, 1, (0, 0, 0), 2, cv2.LINE_AA)

    # TLT: Total Length of Trails
    text_position_TLT = (box_x + base_w_padding + w_padding, box_y + base_h_padding + 5 * h_padding)
    cv2.putText(image, " Total: ", text_position_TLT, font, font_scale, static_color, 2, cv2.LINE_AA)
    cv2.putText(image, str(TLT) + ' (m)', (text_position_TLT[0] + cv2.getTextSize(" Total: ", font, font_scale, bold_size)[0][0], text_position_TLT[1]), font, 1, dynamic_color, bold_size, cv2.LINE_AA)

    # Length of Trails Per hectare
    #LTP = 498
    text_position_LTP = (box_x + base_w_padding + w_padding, box_y + base_h_padding + 6*h_padding)
    cv2.putText(image, " Per hectare: ", text_position_LTP, font, font_scale, static_color, 2, cv2.LINE_AA)
    cv2.putText(image, str(LTP) + ' (m/ha)', (text_position_LTP[0] + cv2.getTextSize(" Per hectare: ", font, font_scale, bold_size)[0][0], text_position_LTP[1]), font, 1, dynamic_color, bold_size, cv2.LINE_AA)

    # Distance travelled (DT): SUM(length of each segments * the pass number)

    text_position_DT = (box_x + base_w_padding, box_y + base_h_padding + 7*h_padding)
    cv2.putText(image, "- Distance travelled: ", text_position_DT, font, font_scale, static_color, 2, cv2.LINE_AA)
    cv2.putText(image, str(DT) + ' m', (text_position_DT[0] + cv2.getTextSize("- Distance travelled: ", font, font_scale, bold_size)[0][0], text_position_DT[1]), font, 1, dynamic_color, bold_size, cv2.LINE_AA) #font_scale: 1


    # Average distance between trails
    #ADT = 21.2
    text_position_ADT = (box_x + base_w_padding, box_y + base_h_padding + 8*h_padding)
    cv2.putText(image, "- Average distance between trails: ", text_position_ADT, font, font_scale, static_color, 2, cv2.LINE_AA)
    cv2.putText(image, str(ADT) + ' (m)', (text_position_ADT[0] + cv2.getTextSize("- Average distance between trails: ", font, font_scale, bold_size)[0][0], text_position_ADT[1]), font, 1, dynamic_color, bold_size, cv2.LINE_AA) #font_scale: 1

    # Logging trail area (with 4.5 m wdith)
    cv2.putText(image, "- Logging trail area (with 4.5 m wdith): ", 
                (box_x + base_w_padding, box_y + base_h_padding + 9*h_padding), font, 1, (0, 0, 0), 2, cv2.LINE_AA)

    # LTA: Total Logging trail area 
    text_position_LTA = (box_x + base_w_padding + w_padding, box_y + base_h_padding + 10*h_padding)
    cv2.putText(image, " Total: ", text_position_LTA, font, font_scale, static_color, 2, cv2.LINE_AA)
    cv2.putText(image, str(LTA) + ' (m2)', (text_position_LTA[0] + cv2.getTextSize(" Total: ", font, font_scale, bold_size)[0][0], text_position_LTA[1]), font, 1, dynamic_color, bold_size, cv2.LINE_AA)

    #  Share hectare: XXX (%)
    text_position_LTAS = (box_x + base_w_padding + w_padding, box_y + base_h_padding + 11*h_padding)
    cv2.putText(image, " Share: ", text_position_LTAS, font, font_scale, static_color, 2, cv2.LINE_AA)
    cv2.putText(image, str(LTAS) + ' (%)', (text_position_LTAS[0] + cv2.getTextSize(" Share: ", font, font_scale, bold_size)[0][0], text_position_LTAS[1]), font, 1, dynamic_color, bold_size, cv2.LINE_AA)

    cv2.putText(image, "- Forest area reached with 10m " , 
                (box_x + base_w_padding, box_y + base_h_padding + 12*h_padding), font, 1, (0, 0, 0), 2, cv2.LINE_AA)
    
    # Gross boom reach coverage
    GBRC_ha = float(GBRC)/10000
    GBRC_ha = format_number(GBRC_ha)
    text_position_GBRC = (box_x + base_w_padding + w_padding, box_y + base_h_padding + 13*h_padding)
    cv2.putText(image, " Gross boom reach coverage: ", text_position_GBRC, font, font_scale, static_color, 2, cv2.LINE_AA)
    cv2.putText(image, str(GBRC_ha) + ' (ha)', (text_position_GBRC[0] + cv2.getTextSize(" Gross boom reach coverage: ", font, font_scale, bold_size)[0][0], text_position_GBRC[1]), font, 1, dynamic_color, bold_size, cv2.LINE_AA)

    #GBRC_out, 
    GBRC_out = float(GBRC_out)/10000
    GBRC_out = format_number(GBRC_out)
    text_position_GBRC_out = (box_x + base_w_padding + w_padding, box_y + base_h_padding + 14*h_padding)
    cv2.putText(image, " GBRC outside: ", text_position_GBRC_out , font, font_scale, static_color, 2, cv2.LINE_AA)
    cv2.putText(image, str(GBRC_out) + ' (ha)', (text_position_GBRC_out [0] + cv2.getTextSize(" GBRC outside: ", font, font_scale, bold_size)[0][0], text_position_GBRC_out [1]), font, 1, dynamic_color, bold_size, cv2.LINE_AA)

    # Net boom reach coverage
    NBRC_ha = float(NBRC)/10000
    NBRC_ha = format_number(NBRC_ha)
    text_position_NBRC = (box_x + base_w_padding + w_padding, box_y + base_h_padding + 15*h_padding)
    cv2.putText(image, " Net boom reach coverage: ", text_position_NBRC, font, font_scale, static_color, 2, cv2.LINE_AA)
    cv2.putText(image, str(NBRC_ha) + ' (ha)', (text_position_NBRC[0] + cv2.getTextSize(" Net boom reach coverage: ", font, font_scale, bold_size)[0][0], text_position_NBRC[1]), font, 1, dynamic_color, bold_size, cv2.LINE_AA)

    # NBRC_rate
    text_position_NBRC_rate = (box_x + base_w_padding + w_padding, box_y + base_h_padding + 16*h_padding)
    cv2.putText(image, " NBRC Rate: ", text_position_NBRC_rate, font, font_scale, static_color, 2, cv2.LINE_AA)
    cv2.putText(image, str(NBRC_rate) + ' ', (text_position_NBRC_rate[0] + cv2.getTextSize(" NBRC Rate: ", font, font_scale, bold_size)[0][0], text_position_NBRC_rate[1]), font, 1, dynamic_color, bold_size, cv2.LINE_AA)


    # KEI: Logging trail efficiency factor
    text_position_KEI = (box_x + base_w_padding, box_y + base_h_padding + 17*h_padding)
    cv2.putText(image, "- Logging trail efficiency factor: ", text_position_KEI, font, font_scale, static_color, 2, cv2.LINE_AA)
    cv2.putText(image, str(KEI) + ' ', (text_position_KEI[0] + cv2.getTextSize("- Logging trail efficiency factor: ", font, font_scale, bold_size)[0][0], text_position_KEI[1]), font, 1, dynamic_color, bold_size, cv2.LINE_AA) #font_scale: 1


    # RFA: relative forest accessibility
    text_position_RFA = (box_x + base_w_padding, box_y + base_h_padding + 18*h_padding)
    cv2.putText(image, "- Forest accessibility factor: ", text_position_RFA, font, font_scale, static_color, 2, cv2.LINE_AA)
    cv2.putText(image, str(RFA) + ' ', (text_position_RFA[0] + cv2.getTextSize("- Forest accessibility factor: ", font, font_scale, bold_size)[0][0], text_position_RFA[1]), font, 1, dynamic_color, bold_size, cv2.LINE_AA) #font_scale: 1

    # ------------------ draw North Arrow -------------------
    # Top left
    north_x, north_y = img_width - 200, 200  
    # length
    arrow_length = 30  
    start_point = (north_x, north_y + arrow_length)  
    end_point = (north_x, north_y - arrow_length)  

    cv2.arrowedLine(image, start_point, end_point, (0, 0, 0), 10, tipLength=0.4)  # arrow
    cv2.putText(image, "N", (north_x - 10, north_y - arrow_length - 10),
                cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 4, cv2.LINE_AA)

    # ------------------ draw scale -------------------
    resolution_x = round(resolution_x, 2)
    resolution_y = round(resolution_y, 2)
    # The starting point coordinates of the scale bar (lower left corner)
    cv2.putText(image, 'resolution_x: ' + str(resolution_x) + ' m' , (200, img_height - 120), font, font_scale, static_color, 2, cv2.LINE_AA)
    cv2.putText(image, 'resolution_y: ' + str(resolution_y) + ' m' , (200, img_height - 80), font, font_scale, static_color, 2, cv2.LINE_AA)

    # ------------------ save results -------------------
    # Get the file name (with suffix)
    file_name = os.path.basename(boundary_shp)  # "Area1.shp"
    # Remove suffix
    file_name_no_ext = os.path.splitext(file_name)[0]  # "Area1"
    png_filename = file_name_no_ext.replace('boundary', 'cw') + '.png' #cw_sitenum.png
    png_path = os.path.join(save_png_folder, png_filename)  # save visulization .png image
    cv2.imwrite(png_path, image)
    print("Results saved !")


if __name__ == "__main__":
    #file name: 
    # logging_trail_shp: '/centerline_withpasses_' + site_num + '.shp'
    # boundary_shp: boundary_' + site_num + '.shp'
    root_folder = './data/LTA_outputs/'
    boundary_folder  =  './data/example/site02/' 
    save_png_folder = './data/Output_vis_NEW/'

    if not os.path.exists(save_png_folder):
        os.mkdir(save_png_folder)

    # logging_trail_shp is centerlines_withpasses, # input shape polyline trails
    logging_trail_shp = os.path.join(root_folder, 'centerline_withpasses_Trails2.shp') 

    # input boundary shape polygon 
    boundary_shp = os.path.join(boundary_folder, 'Area2.shp') 
    Vis_Trail(logging_trail_shp, boundary_shp, save_png_folder)
