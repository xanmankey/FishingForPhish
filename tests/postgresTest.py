# Testing postgres
# 3 files for testing basic functionality ALONE and then specific tests for the code itself
# Original clang CFLAGS:
# '-ferror-limit=1 -gdwarf-4 -ggdb3 -O0 -std=c11 -Wall -Werror -Wextra -Wno-gnu-folding-constant -Wno-sign-compare -Wno-unused-parameter -Wno-unused-variable -Wno-unused-but-set-variable -Wshadow'
# Decided to test using psycopg2 for the extra control (I might migrate back to Postgres testing, but I have to figure out this error first)
# Maybe watch THIS tutorial for help: https://www.youtube.com/watch?v=M2NzvnfS-hI
# TEST INSTALL: PATH=/usr/pgsql-14.5/lib:$PATH pip3 install --no-binary psycopg2 psycopg2
# PATH=/usr/bin/pg_config/lib:$PATH pip3 install --no-binary psycopg2 psycopg2
# ?/usr/bin/pg_config
# (looking at setup proposed here: https://stackoverflow.com/questions/5500332/cant-connect-the-postgresql-with-psycopg2)
# To find psycopg2
import psycopg2

def main():
    # Create db (using a testDB rn for further abstraction of the issue)
    con = psycopg2.connect(database="postgres", user='postgres', password='password', host='127.0.0.1', port= '5432')
    con.autocommit = True
    cur = con.cursor()
    # Create database
    cur.execute("CREATE DATABASE testDB")
    # Create table
    cur.execute("CREATE TABLE test (name text)")
    # Insert db
    cur.execute("INSERT INTO test (name) VALUES ('jimmy')")
    con.commit()
    # Select db
    cur.execute("SELECT * FROM test")
    # End db connection
    con.close()


if __name__ == "__main__":
    main()