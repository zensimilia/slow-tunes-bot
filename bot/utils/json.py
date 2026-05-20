from pydantic import TypeAdapter


def dict_to_json(obj: dict) -> str:
    return TypeAdapter(dict).dump_json(obj).decode("utf-8")
