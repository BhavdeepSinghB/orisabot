import os, sys, unittest, datetime, asyncio
sys.path.insert(0, os.path.abspath(".."))

from tables import DBService

class DBServiceTestCase(unittest.TestCase):

    dbservice = None

    def test_create_new_database(self):
        if os.path.isfile("overwatch_team.db"):
            print("Problem")
            # os.remove("overwatch_team.db")
        self.dbservice = asyncio.run(DBService.construct(f"dbservice_test_{datetime.datetime.now().strftime('%m_%d_%H:%M:%S')}"))
        self.assertTrue(os.path.isfile("overwatch_team.db"))
        pass

if __name__ == '__main__':
    unittest.main()