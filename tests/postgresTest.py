# Testing postgres
# 3 files for testing basic functionality ALONE and then specific tests for the code itself
# Original clang CFLAGS:
# '-ferror-limit=1 -gdwarf-4 -ggdb3 -O0 -std=c11 -Wall -Werror -Wextra -Wno-gnu-folding-constant -Wno-sign-compare -Wno-unused-parameter -Wno-unused-variable -Wno-unused-but-set-variable -Wshadow'
# Decided to use psycopg2 for the extra control
import psycopg2

def main():
    # Create db
    con = psycopg2.connect(database="testDB", user="postgres", password="", host="127.0.0.1", port="5432")
    cur = con.cursor()
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