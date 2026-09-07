import random,string,tempfile,unittest
from minidb import Database
from minidb.errors import MiniDBError


class FuzzTests(unittest.TestCase):
    def test_random_sql_never_crashes_with_internal_exception(self):
        rng=random.Random(20260907)
        alphabet=string.ascii_letters+string.digits+" '_(),;=<>!+-*/\n@"
        with tempfile.TemporaryDirectory() as d:
            db=Database(d)
            for _ in range(300):
                sql="".join(rng.choice(alphabet) for _ in range(rng.randint(0,120)))
                try:db.inspect(sql)
                except MiniDBError:pass
                except Exception as exc:self.fail(f"unclassified crash for {sql!r}: {type(exc).__name__}: {exc}")

if __name__=="__main__":unittest.main()
