import unittest
import pandas as pd
import pandas.testing as pdt
from src import sandbox, data, gpx


class TestSandbox(unittest.TestCase):

    def test_main(self):
        self.assertTrue(isinstance(sandbox.main(), pd.DataFrame))


class TestData(unittest.TestCase):

    def test_load_walk_data(self):
        self.assertTrue(isinstance(data.load_walk_data(), pd.DataFrame))


class TestGpx(unittest.TestCase):

    def test_positive_long(self):

        inp = pd.DataFrame([
            {"lon": 360},
            {"lon": 0},
            {"lon": -5}
        ])

        out = pd.DataFrame([
            {"lon": 360},
            {"lon": 0},
            {"lon": 355}
        ])

        res = gpx.positive_long(inp)
        pdt.assert_frame_equal(res, out)

    def test_get_lat_long_tuples(self):

        inp = pd.DataFrame([
            {"lat": 10, "lon": 30},
            {"lat": 40, "lon": 20}
        ])

        out = [(10, 30), (40, 20)]

        self.assertListEqual(gpx.get_lat_long_tuples(inp), out)


if __name__ == '__main__':
    unittest.main()
