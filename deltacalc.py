import ee           # api documentation referred from
ee.Authenticate()   # https://developers.google.com/earth-engine/apidocs
ee.Initialize(project = "ee-ww-1")                          # this is the project I"ve created
                                                            # throuh my google developer console

bits_audi_coords = [78.5706124275664, 17.545331001776212]   # roughly the auditorium coords
bits_audi = ee.Geometry.Point(bits_audi_coords)             # from google maps
bits_audi_buffer = bits_audi.buffer(5000)                   # 5 km radius

init_date      = ee.Date("2025-02-20")                      # february 20 2025
one_year_ago   = init_date.advance(-1, "year")              # february 20 2024
five_years_ago = init_date.advance(-5, "year")              # february 20 2020

param_names = [
    "trees",
    "water",
    "built",
    "shrub_and_scrub"
]   # parameters to be used

def dw_col(init_date):  # function to get specific dynamic world data
    return (ee.ImageCollection("GOOGLE/DYNAMICWORLD/V1")
        .filterBounds(bits_audi_buffer)
        .filterDate(init_date.advance(-4, "day"), init_date) # get data over the past 4 days
        .select(param_names)                                 # this is the minimum time range
        .mean())                                             # i could find through trial & error

current_dw   = dw_col(init_date)
one_year_dw  = dw_col(one_year_ago)
five_year_dw = dw_col(five_years_ago)

def calc_area_change(old_col, new_col):
    old_area = old_col.multiply(ee.Image.pixelArea()).reduceRegion( # multiply by pixel area
        reducer=ee.Reducer.sum(), # sum to get total area           # to get area in m^2
        geometry=bits_audi_buffer
    )
    new_area = new_col.multiply(ee.Image.pixelArea()).reduceRegion( # reducer is efficient for
        reducer=ee.Reducer.sum(),                                   # aggregating pixel values
        geometry=bits_audi_buffer                                   # over large area as this
    )
    return {band: (new_area.get(band).getInfo() - old_area.get(band).getInfo()) / 10000 # hectares
            for band in param_names}

five_year_change = calc_area_change(five_year_dw, current_dw)
one_year_change = calc_area_change(one_year_dw, current_dw)

print("Change in area (hectares) over the last 5 years:")
for band, change in five_year_change.items():
    print(f"{band}: {change:.2f}")

print("\nChange in area (hectares) over the last year:")
for band, change in one_year_change.items():
    print(f"{band}: {change:.2f}")