INSUNITS_SCALE_TO_METERS = {
    0: 1.0,        # Unitless (assumir 1.0, ou parametrizar)
    1: 0.0254,     # Inches
    2: 0.3048,     # Feet
    3: 1.0,        # Miles (não padrão DXF antigo; ajustar se necessário)
    4: 0.001,      # Millimeters
    5: 0.01,       # Centimeters
    6: 1.0,        # Meters
    7: 1000.0,     # Kilometers
    8: 1.0,        # Microinches (se usar, ajustar)
    9: 1.0,        # Mils (milésimos de polegada)
    10: 0.0000254, # Angstroms
    11: 1e-9,      # Nanometers
    12: 1e-6,      # Microns
    13: 0.001,     # Decimeters
    14: 10.0,      # Dekameters
    15: 100.0,     # Hectometers
    16: 1609.344,  # Miles (algumas tabelas usam este ID)
    17: 1852.0,    # Nautical Miles
}

def scale_factor_to_meters(doc) -> float:
    insunits = int(doc.header.get("$INSUNITS", 0))
    return INSUNITS_SCALE_TO_METERS.get(insunits, 1.0)
