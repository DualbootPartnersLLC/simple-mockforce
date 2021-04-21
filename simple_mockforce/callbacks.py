import json
import uuid

from urllib.parse import urlparse

from python_soql_parser import parse

from simple_mockforce.virtual import virtual_salesforce


def query_callback(request):
    parse_results = parse(request.params["q"])
    sobject = parse_results["sobject"]
    fields = parse_results["fields"].asList()
    limit = parse_results["limit"].asList()
    objects = virtual_salesforce.data[sobject]
    # TODO: construct attributes
    records = [*map(lambda record: {field: record[field] for field in fields}, objects)]
    if limit:
        limit: int = limit[0]
        records = records[:limit]

    body = {
        "totalSize": len(records),
        "done": True,
        "records": records,
    }
    return (200, {}, json.dumps(body))


def get_callback(request):
    url = request.url
    path = urlparse(url).path
    split_up = url.split("/")
    # TODO: use pyparsing
    sobject = split_up[-2]
    record_id = split_up[-1]

    objects = virtual_salesforce.data[sobject.lower()]

    narrowed = [*filter(lambda object_: object_["id"] == record_id, objects)][0]

    return (
        200,
        {},
        json.dumps({"attributes": {"type": sobject, "url": path}, **narrowed}),
    )


def create_callback(request):
    url = request.url
    path = urlparse(url).path
    body = json.loads(request.body)

    split_up = url.split("/")
    # TODO: use pyparsing
    sobject = split_up[-2]

    normalized = {key.lower(): value for key, value in body.items()}

    id_ = str(uuid.uuid4())

    normalized["id"] = id_

    normalized_object_name = sobject.lower()
    if sobject.lower() in virtual_salesforce.data:
        virtual_salesforce.data[normalized_object_name].append(normalized)
    else:
        virtual_salesforce.data[normalized_object_name] = [normalized]

    return (
        200,
        {},
        # yep, salesforce lowercases id on create's response
        json.dumps({"id": id_, "success": True, "errors": []}),
    )


def update_callback(request):
    url = request.url
    path = urlparse(url).path
    body = json.loads(request.body)

    split_up = url.split("/")
    # TODO: use pyparsing
    sobject = split_up[-2]
    record_id = split_up[-1]

    normalized = {key.lower(): value for key, value in body.items()}

    normalized_object_name = sobject.lower()

    objects = virtual_salesforce.data[normalized_object_name]
    narrowed = [*filter(lambda object_: object_["id"] == record_id, objects)][0]

    narrowed = {**narrowed, **normalized}

    print(virtual_salesforce.data[normalized_object_name])

    return (
        204,
        {},
        json.dumps({}),
    )