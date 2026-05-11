from cerberus import Validator

_F = {"type": "float", "required": True}
_FO = {"type": "float", "required": False}
_TS = {"type": "string", "required": True}

schema_3d_cpii = Validator({
    "timestamp": _TS,
    "na2o": _F, "fe2o3": _F, "cao": _F, "so3": _F,
    "blaine": _F, "sio2": _F, "pf": _F, "#400": _F, "r.i": _F, "mgo": _F,
    "compressive_strength_1d": _FO,
    "compressive_strength_3d": _FO,
    "growth_7d": _FO,
})

schema_7d_cpii = Validator({
    "timestamp": _TS,
    "na2o": _F, "fe2o3": _F, "cao": _F, "so3": _F,
    "blaine": _F, "sio2": _F, "pf": _F, "#400": _F, "r.i": _F, "mgo": _F,
    "compressive_strength_3d": _F,
    "compressive_strength_7d": _FO,
    "growth_7d": _FO,
})

schema_28d_cpii = Validator({
    "timestamp": _TS,
    "na2o": _F, "fe2o3": _F, "cao": _F, "so3": _F,
    "blaine": _F, "sio2": _F, "pf": _F, "#400": _F, "r.i": _F, "mgo": _F,
    "compressive_strength_3d": _F, "compressive_strength_7d": _F,
    "compressive_strength_1d": _FO, "compressive_strength_28d": _FO,
    "growth_7d": _FO, "growth_28d": _FO,
})

schema_7d_cpiii = Validator({
    "timestamp": _TS,
    "na2o": _F, "fe2o3": _F, "cao": _F, "so3": _F,
    "blaine": _F, "sio2": _F, "pf": _F, "#400": _F, "r.i": _F, "mgo": _F,
    "resistance_3d": _F,
    "resistance_7d": _FO,
    "growth_7d": _FO,
})

schema_28d_cpiii = Validator({
    "timestamp": _TS,
    "na2o": _F, "fe2o3": _F, "cao": _F, "so3": _F,
    "blaine": _F, "sio2": _F, "pf": _F, "#400": _F, "r.i": _F, "mgo": _F,
    "resistance_3d": _F, "resistance_7d": _F,
    "resistance_28d": _FO,
    "growth_7d": _FO, "growth_28d": _F,
})

schema_3d_cpv = Validator({
    "timestamp": _TS,
    "na2o": _F, "fe2o3": _F, "cao": _F, "so3": _F,
    "blaine": _F, "sio2": _F, "pf": _F, "#400": _F, "r.i": _F, "mgo": _F,
    "resistance_1d": _F,
    "resistance_3d": _FO,
    "growth_3d": _F,
})

schema_7d_cpv = Validator({
    "timestamp": _TS,
    "na2o": _F, "fe2o3": _F, "cao": _F, "so3": _F,
    "blaine": _F, "sio2": _F, "pf": _F, "#400": _F, "r.i": _F, "mgo": _F,
    "resistance_1d": _F, "resistance_3d": _F,
    "resistance_7d": _FO,
    "growth_7d": _F,
})

schema_3d_cpiv = Validator({
    "timestamp": _TS,
    "na2o": _F, "fe2o3": _F, "cao": _F, "k2o": _F,
    "so3": _F, "blaine": _F, "sio2": _F, "al2o3": _F, "pf": _F, "#325": _F,
})

schema_7d_cpiv = Validator({
    "timestamp": _TS,
    "na2o": _F, "fe2o3": _F, "cao": _F, "k2o": _F,
    "so3": _F, "blaine": _F, "sio2": _F, "al2o3": _F, "pf": _F, "#325": _F,
    "resistance_3d": _F,
    "resistance_7d": _FO,
    "growth_7d": _F, "growth_28d": _FO,
})

schema_28d_cpiv = Validator({
    "timestamp": _TS,
    "na2o": _F, "fe2o3": _F, "cao": _F, "k2o": _F,
    "so3": _F, "blaine": _F, "sio2": _F, "al2o3": _F, "pf": _F, "#325": _F,
    "resistance_3d": _F, "resistance_7d": _F,
    "growth_28d": _F, "growth_7d": _FO,
})

schema_3d_cpiiz32rs = Validator({
    "timestamp": _TS,
    "na2o": _F, "fe2o3": _F, "cao": _F, "k2o": _F,
    "so3": _F, "blaine": _F, "sio2": _F, "al2o3": _F, "pf": _F, "#325": _F,
})

schema_7d_cpiiz32rs = Validator({
    "timestamp": _TS,
    "na2o": _F, "fe2o3": _F, "cao": _F, "k2o": _F,
    "so3": _F, "blaine": _F, "sio2": _F, "al2o3": _F, "pf": _F, "#325": _F,
    "resistance_3d": _F,
    "resistance_7d": _FO,
    "growth_7d": _F, "growth_28d": _FO,
})

schema_28d_cpiiz32rs = Validator({
    "timestamp": _TS,
    "na2o": _F, "fe2o3": _F, "cao": _F, "k2o": _F,
    "so3": _F, "blaine": _F, "sio2": _F, "al2o3": _F, "pf": _F, "#325": _F,
    "resistance_3d": _F, "resistance_7d": _F,
    "growth_28d": _F, "growth_7d": _FO,
})

schema_3d_cpiii_pec = Validator({
    "timestamp": _TS,
    "na2o": _F, "fe2o3": _F, "cao": _F, "so3": _F,
    "blaine": _F, "sio2": _F, "pf": _F, "#400": _F, "r.i": _F, "mgo": _F,
    "compressive_strength_1d": _F,
    "compressive_strength_3d": _FO,
    "growth_3d": _FO,
})

schema_7d_cpiii_pec = Validator({
    "timestamp": _TS,
    "na2o": _F, "fe2o3": _F, "cao": _F, "so3": _F,
    "blaine": _F, "sio2": _F, "pf": _F, "#400": _F, "r.i": _F, "mgo": _F,
    "compressive_strength_3d": _F,
    "compressive_strength_7d": _FO,
    "growth_7d": _FO,
})

schema_28d_cpiii_pec = Validator({
    "timestamp": _TS,
    "na2o": _F, "fe2o3": _F, "cao": _F, "so3": _F,
    "blaine": _F, "sio2": _F, "pf": _F, "#400": _F, "r.i": _F, "mgo": _F,
    "compressive_strength_3d": _F, "compressive_strength_7d": _F,
    "compressive_strength_1d": _FO, "compressive_strength_28d": _FO,
    "growth_7d": _FO, "growth_28d": _FO,
})
