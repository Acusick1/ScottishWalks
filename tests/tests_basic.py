import unittest
import pandas as pd
from src import sandbox, data


class TestSandbox(unittest.TestCase):

    def test_main(self):
        self.assertTrue(isinstance(sandbox.main(), pd.DataFrame))


class TestData(unittest.TestCase):

    def test_load_walk_data(self):
        self.assertTrue(isinstance(data.load_walk_data(), pd.DataFrame))


if __name__ == '__main__':
    unittest.main()
