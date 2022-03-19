import base64
from itertools import permutations
from pyremoteplay.fec_utils import fec


TESTS = [
    {
        "k": 6,
        "m": 1,
        "erasures": (3,),
        "data": (
            "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"
            "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
            "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
            "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
            "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
            "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAUEARcajES/FE7o2MUSi7VW0jKLuyPuS//q9LMIkzrm452Gi8REe8WNp6vXp5GQI9TdAk6YLQuI3CrGNzk4oafO8u3q0lgTanQaA"
            "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"
            "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
            "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
            "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
            "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
            "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAQAAAAFBAE9GoxEv8Pv6QB2OfhKBInFMUoYNPT3Jyi4PPP/RCaVkNbLm1s5k7VzVvd/3PBXhuYGCKo9PwZIt1gi2OOD8b7amPu3oyaEx59G+atRGb74RKFTM9In+6sygFCkJA7Gwtkuiz9uuubhuUVYIRiGpJGSAE1IMRXMHiKjGai5Ln+zsFC3s5YvKgiiSeK3BbltnmSjL35KkMdkL"
            "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"
            "Qsp9TUxKhkE="
        ),
        "size": 1400,
    },
    {
        "k": 7,
        "m": 2,
        "erasures": (1, 2),
        "data": (
            "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"
            "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
            "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
            "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
            "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
            "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
            "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"
            "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
            "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
            "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
            "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
            "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
            "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"
            "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
            "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
            "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
            "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
            "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
            "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"
        ),
        "size": 1400,
    },
]


def test_fec_decode():
    """Test FEC decode for test cases."""
    for test in TESTS:
        data = base64.b64decode(test["data"].encode())
        size = test["size"]
        erasures = test["erasures"]
        total = test["k"] + test["m"]
        packets = [
            data[(i * size) + 2 : (i + 1) * size].ljust(size, b"\x00")
            for i in range(total)
        ]
        original = b"".join(packets)
        for e in erasures:
            packets[e] = bytes(size)
        erased = b"".join(packets)
        assert erased != original
        result = fec.decode(test["k"], test["m"], size, erased, test["erasures"])
        assert result == original


def test_fec_decode_single_full():
    """Test FEC decode for all possible erasures."""
    test = TESTS[0]
    data = base64.b64decode(test["data"].encode())
    size = test["size"]
    total = test["k"] + test["m"]
    for index in range(test["k"]):
        packets = [
            data[(i * size) + 2 : (i + 1) * size].ljust(size, b"\x00")
            for i in range(total)
        ]
        original = b"".join(packets)
        packets[index] = bytes(size)
        erased = b"".join(packets)
        assert erased != original
        result = fec.decode(test["k"], test["m"], size, erased, (index,))
        assert result == original


def test_fec_decode_multiple_full():
    """Test FEC decode for all permutations with multiple erasures."""
    test = TESTS[1]
    data = base64.b64decode(test["data"].encode())
    size = test["size"]
    total = test["k"] + test["m"]
    cases = permutations(range(test["k"]), 2)
    for erasures in cases:
        packets = [
            data[(i * size) + 2 : (i + 1) * size].ljust(size, b"\x00")
            for i in range(total)
        ]
        original = b"".join(packets)
        for e in erasures:
            packets[e] = bytes(size)
        erased = b"".join(packets)
        assert erased != original
        result = fec.decode(test["k"], test["m"], size, erased, erasures)
        assert result == original