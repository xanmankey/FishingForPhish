# Testing postgres
# 3 files for testing basic functionality ALONE and then specific tests for the code itself
# Original clang CFLAGS:
# '-ferror-limit=1 -gdwarf-4 -ggdb3 -O0 -std=c11 -Wall -Werror -Wextra -Wno-gnu-folding-constant -Wno-sign-compare -Wno-unused-parameter -Wno-unused-variable -Wno-unused-but-set-variable -Wshadow'
# Current error: psycopg2.OperationalError: connection to server on socket "/var/run/postgresql/.s.PGSQL.5432" failed: No such file or directory
        # Is the server running locally and accepting connections on that socket?
# There's no file there; do I need to start a Postgresql server or is it an issue with compiled via env (apt) files?
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