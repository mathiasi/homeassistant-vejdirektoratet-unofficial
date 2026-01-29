"""Minimal Mapbox Vector Tile decoder for extracting feature IDs.

This is a pure-Python implementation that only extracts feature properties,
avoiding the need for mapbox-vector-tile which requires C++ compilation.
"""

import gzip
import struct


def decode_varint(data: bytes, pos: int) -> tuple[int, int]:
    """Decode a varint from the data at position pos."""
    result = 0
    shift = 0
    while True:
        if pos >= len(data):
            raise ValueError("Unexpected end of data while reading varint")
        byte = data[pos]
        pos += 1
        result |= (byte & 0x7F) << shift
        if (byte & 0x80) == 0:
            break
        shift += 7
    return result, pos


def decode_sint(value: int) -> int:
    """Decode a zigzag-encoded signed integer."""
    return (value >> 1) ^ -(value & 1)


def skip_field(data: bytes, pos: int, wire_type: int) -> int:
    """Skip a field based on its wire type."""
    if wire_type == 0:  # Varint
        _, pos = decode_varint(data, pos)
    elif wire_type == 1:  # 64-bit
        pos += 8
    elif wire_type == 2:  # Length-delimited
        length, pos = decode_varint(data, pos)
        pos += length
    elif wire_type == 5:  # 32-bit
        pos += 4
    else:
        raise ValueError(f"Unknown wire type: {wire_type}")
    return pos


def decode_value(data: bytes) -> str | int | float | bool | None:
    """Decode a protobuf Value message."""
    pos = 0
    while pos < len(data):
        tag, pos = decode_varint(data, pos)
        field_num = tag >> 3
        wire_type = tag & 0x7

        if field_num == 1 and wire_type == 2:  # string_value
            length, pos = decode_varint(data, pos)
            return data[pos : pos + length].decode("utf-8")
        elif field_num == 2 and wire_type == 5:  # float_value
            return struct.unpack("<f", data[pos : pos + 4])[0]
        elif field_num == 3 and wire_type == 1:  # double_value
            return struct.unpack("<d", data[pos : pos + 8])[0]
        elif field_num == 4 and wire_type == 0:  # int_value
            val, pos = decode_varint(data, pos)
            return val
        elif field_num == 5 and wire_type == 0:  # uint_value
            val, pos = decode_varint(data, pos)
            return val
        elif field_num == 6 and wire_type == 0:  # sint_value
            val, pos = decode_varint(data, pos)
            return decode_sint(val)
        elif field_num == 7 and wire_type == 0:  # bool_value
            val, pos = decode_varint(data, pos)
            return val != 0
        else:
            pos = skip_field(data, pos, wire_type)

    return None


def decode_feature(data: bytes, keys: list[str], values: list) -> dict:
    """Decode a Feature message and return its properties."""
    pos = 0
    tags = []
    properties = {}

    while pos < len(data):
        tag, pos = decode_varint(data, pos)
        field_num = tag >> 3
        wire_type = tag & 0x7

        if field_num == 2 and wire_type == 2:  # tags (packed uint32)
            length, pos = decode_varint(data, pos)
            end = pos + length
            while pos < end:
                val, pos = decode_varint(data, pos)
                tags.append(val)
        else:
            pos = skip_field(data, pos, wire_type)

    # Convert tags to properties
    for i in range(0, len(tags), 2):
        if i + 1 < len(tags):
            key_idx = tags[i]
            val_idx = tags[i + 1]
            if key_idx < len(keys) and val_idx < len(values):
                properties[keys[key_idx]] = values[val_idx]

    return properties


def decode_layer(data: bytes) -> list[dict]:
    """Decode a Layer message and return feature properties."""
    pos = 0
    keys = []
    values = []
    features_data = []

    while pos < len(data):
        tag, pos = decode_varint(data, pos)
        field_num = tag >> 3
        wire_type = tag & 0x7

        if field_num == 3 and wire_type == 2:  # keys
            length, pos = decode_varint(data, pos)
            keys.append(data[pos : pos + length].decode("utf-8"))
            pos += length
        elif field_num == 4 and wire_type == 2:  # values
            length, pos = decode_varint(data, pos)
            value = decode_value(data[pos : pos + length])
            values.append(value)
            pos += length
        elif field_num == 2 and wire_type == 2:  # features
            length, pos = decode_varint(data, pos)
            features_data.append(data[pos : pos + length])
            pos += length
        else:
            pos = skip_field(data, pos, wire_type)

    # Now decode features with the collected keys and values
    features = []
    for feature_data in features_data:
        props = decode_feature(feature_data, keys, values)
        features.append(props)

    return features


def extract_feature_ids(tile_data: bytes) -> list[str]:
    """Extract all featureId values from an MVT tile.

    Args:
        tile_data: Raw MVT tile data (may be gzipped)

    Returns:
        List of feature ID strings found in the tile
    """
    # Check if gzipped
    if tile_data[:2] == b"\x1f\x8b":
        tile_data = gzip.decompress(tile_data)

    feature_ids = []
    pos = 0

    while pos < len(tile_data):
        tag, pos = decode_varint(tile_data, pos)
        field_num = tag >> 3
        wire_type = tag & 0x7

        if field_num == 3 and wire_type == 2:  # layer
            length, pos = decode_varint(tile_data, pos)
            layer_data = tile_data[pos : pos + length]
            pos += length

            features = decode_layer(layer_data)
            for props in features:
                feature_id = props.get("featureId")
                if feature_id is not None:
                    feature_ids.append(str(feature_id))
        else:
            pos = skip_field(tile_data, pos, wire_type)

    return feature_ids
