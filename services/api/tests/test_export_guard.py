from hooks.pre_export import validate_exportable_project

def test_rejects_missing_coordinates():
    errors = validate_exportable_project({
        "intent": "Tell the story",
        "points": [{"id":"1","visible":True,"label":"A","symbol":"custom"}]
    })
    assert errors

def test_accepts_valid_point():
    errors = validate_exportable_project({
        "intent": "Tell the story",
        "points": [{
            "id":"1","visible":True,"label":"A","symbol":"custom",
            "latitude":32.9,"longitude":-96.7
        }]
    })
    assert errors == []
