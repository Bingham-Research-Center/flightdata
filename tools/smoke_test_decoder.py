"""Minimal offline smoke checks for adsbdecoder helper logic."""

from adsbdecoder import _prepare_output_frames


def main() -> None:
    records = [
        {
            "timestamp": 1_700_000_000.0,
            "datetime_utc": "2023-11-14T00:00:00Z",
            "icao": "abc123",
            "df": 17,
            "msg_hash": "deadbeefcafebabe",
            "velocity": (123.44, 181.26, 752.1, "GS"),
            "airborne_velocity": (121.19, 179.95, 740.5, "AS"),
            "latitude": 40.460123,
            "longitude": -109.565777,
            "altitude": 5087,
            "typecode": 11,
        }
    ]

    data_df, core_df, derived_df = _prepare_output_frames(records)

    assert data_df.height == 1
    assert core_df.height == 1
    assert derived_df.height == 1

    # Flattened tuple fields must exist.
    assert "velocity_gs" in data_df.columns
    assert "velocity_track" in data_df.columns
    assert "airborne_speed" in data_df.columns

    # Quantization checks.
    row = data_df.row(0, named=True)
    assert row["altitude"] == 5075.0
    assert row["velocity_gs"] == 123.4
    assert row["velocity_track"] == 181.3

    # Join keys should be present in derived output.
    for key in ("timestamp", "datetime_utc", "icao", "msg_hash"):
        assert key in derived_df.columns

    print("smoke_test_decoder: PASS")


if __name__ == "__main__":
    main()
