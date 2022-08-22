# Testing postgres
# 3 files for testing basic functionality ALONE and then specific tests for the code itself
from postgres import Postgres

def main():
    # Create db
    db = Postgres()
    # Create table
    db.run("CREATE TABLE test (name text)")
    # Insert db
    db.run("INSERT INTO test (name) VALUES ('jimmy')")
    # Select db
    db.run("SELECT * FROM test")


if __name__ == "__main__":
    main()