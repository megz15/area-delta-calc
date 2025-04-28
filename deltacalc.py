import ee           # api documentation referred from
ee.Authenticate()   # https://developers.google.com/earth-engine/apidocs
ee.Initialize(project = "ee-ww-1")

bits_audi_coords = [78.32674059291753, 17.4534271]          # UoH lon, lat
bits_audi = ee.Geometry.Point(bits_audi_coords)             # from google maps
bits_audi_buffer = bits_audi.buffer(5000)                   # 5 km radius

# init_date      = ee.Date("2025-04-10")          # april 10 2025
# one_year_ago   = init_date.advance(-1, "year")  # april 10 2024
# five_years_ago = init_date.advance(-5, "year")  # april 10 2020

before_end = ee.Date("2025-01-28")  # january 28 2025
after_end = ee.Date("2025-04-28")   # april 28 2025

param_names = [
    "trees",
    "water",
    "built",
    "shrub_and_scrub"
]   # parameters to be used

def dw_col(end_date):  # function to get specific dynamic world data
    img = (ee.ImageCollection("GOOGLE/DYNAMICWORLD/V1")
        .filterBounds(bits_audi_buffer)
        .filterDate(end_date.advance(-3, "month"), end_date)
        .select(param_names)
        .mean())
    mask = img.reduce(ee.Reducer.max()).gt(0.2)  # remove noise
    return img.updateMask(mask)

def calc_area_change(old_col, new_col):
    old_area = old_col.multiply(ee.Image.pixelArea()).reduceRegion( # multiply by pixel area
        reducer=ee.Reducer.sum(), # sum to get total area           # to get area in m^2
        geometry=bits_audi_buffer,
        scale = 10, # scale is 10m for dynamic world data
        maxPixels=1e13
    )
    new_area = new_col.multiply(ee.Image.pixelArea()).reduceRegion( # reducer is efficient for
        reducer=ee.Reducer.sum(),                                   # aggregating pixel values
        geometry=bits_audi_buffer,                                  # over large area as this
        scale = 10, maxPixels=1e13
    )
    return {band: (new_area.get(band).getInfo() - old_area.get(band).getInfo()) / 10000 # hectares
            for band in param_names}

# current_dw   = dw_col(init_date)
# one_year_dw  = dw_col(one_year_ago)
# five_year_dw = dw_col(five_years_ago)

before_dw = dw_col(before_end)
after_dw = dw_col(after_end)

# five_year_change = calc_area_change(five_year_dw, current_dw)
# one_year_change = calc_area_change(one_year_dw, current_dw)

before_after_change = calc_area_change(before_dw, after_dw)

# print("Change in area (hectares) over the last 5 years:")
# for band, change in five_year_change.items():
#     print(f"{band}: {change:.2f}")

# print("\nChange in area (hectares) over the last year:")
# for band, change in one_year_change.items():
#     print(f"{band}: {change:.2f}")

print("Change in area (hectares):")
for band, change in before_after_change.items():
    print(f"{band}: {change:.2f}")