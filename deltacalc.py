from flask import Flask, request, jsonify, render_template
import ee           # api documentation referred from
ee.Authenticate()   # https://developers.google.com/earth-engine/apidocs
ee.Initialize(project = "ee-ww-1")

app = Flask(__name__)

bits_audi_coords = [78.32674059291753, 17.4534271]          # UoH lon, lat
bits_audi = ee.Geometry.Point(bits_audi_coords)             # from google maps
bits_audi_buffer = bits_audi.buffer(5000)                   # 5 km radius

before_end = ee.Date("2025-01-28")  # january 28 2025
after_end = ee.Date("2025-04-28")   # april 28 2025

param_names = [
    "trees",
    "water",
    "built",
    "shrub_and_scrub"
]   # parameters to be used

def dw_col(end_date, region):  # function to get specific dynamic world data
    img = (ee.ImageCollection("GOOGLE/DYNAMICWORLD/V1")
        .filterBounds(region)
        .filterDate(end_date.advance(-3, "month"), end_date)
        .select(param_names)
        .mean())
    mask = img.reduce(ee.Reducer.max()).gt(0.2)  # remove noise
    return img.updateMask(mask)

def calc_area_change(old_col, new_col, region):
    old_area = old_col.multiply(ee.Image.pixelArea()).reduceRegion( # multiply by pixel area
        reducer=ee.Reducer.sum(), # sum to get total area           # to get area in m^2
        geometry=region,
        scale = 10, # scale is 10m for dynamic world data
        maxPixels=1e13
    )
    new_area = new_col.multiply(ee.Image.pixelArea()).reduceRegion( # reducer is efficient for
        reducer=ee.Reducer.sum(),                                   # aggregating pixel values
        geometry=region,                                  # over large area as this
        scale = 10, maxPixels=1e13
    )
    return {band: (new_area.get(band).getInfo() - old_area.get(band).getInfo()) / 10000 # hectares
            for band in param_names}

@app.route('/')
def index():
    return render_template('index.html', lon = bits_audi_coords[0], lat = bits_audi_coords[1], 
                           before_end = "2025-01-28", after_end = "2025-04-28")

@app.route('/calculate', methods=['POST'])
def calculate():
    before_end = request.form.get('before_end', default="2025-01-28", type=str)
    after_end = request.form.get('after_end', default="2025-04-28", type=str)
    lat = request.form.get('lat', default=17.4534271, type=float)
    lon = request.form.get('lon', default=78.32674059291753, type=float)

    region = ee.Geometry.Point([lon, lat])
    region_b = region.buffer(5000)

    before_dw = dw_col(ee.Date(before_end), region_b)
    after_dw = dw_col(ee.Date(after_end), region_b)
    before_after_change = calc_area_change(before_dw, after_dw, region_b)

    return jsonify(before_after_change)

app.run(debug=True)