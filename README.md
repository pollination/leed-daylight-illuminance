# leed-daylight-illuminance

Evaluate LEED daylight credits using the point-in-time illuminance method (Option 2).

The input Honeybee Model should have SensorGrids that represent just the regularly
occupied floor area of the building. It is recommended that these SensorGrids have
meshes associated with them, in which case they will be used to compute percentages
of occupied floor area that pass vs. fail the LEED criteria. Otherwise, all sensors
will be assumed to represent an equal amount of floor area.

The input .wea file that is used to generate the clear skies must be for an annual
Typical Meteorological Year (TMY) with a timestep of 1.
