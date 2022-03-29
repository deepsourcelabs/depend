"""Functions to work with PostGres."""
import json

import psycopg2.extras

from handle_env import get_db


def add_data(
    language: str,
    pkg_name: str,
    pkg_ver: str,
    import_name: str,
    lang_ver: list[str],
    pkg_lic: list[str],
    pkg_err: dict,
    pkg_dep: list[str],
):
    """
    Add data in correct format into Postgres DB
    """
    try:
        with get_db() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
                # TODO remove this
                cur.execute('DROP TABLE IF EXISTS package')

                create_script = ''' 
                CREATE TABLE IF NOT EXISTS package (
                    LANGUAGE    varchar,
                    PKG_NAME    varchar NOT NULL PRIMARY KEY,
                    PKG_VER     varchar NOT NULL,
                    IMPORT_NAME varchar,
                    LANG_VER    text[], 
                    PKG_LIC     text[],
                    PKG_ERR     json,
                    PKG_DEP     text[],
                    timestamp timestamp default current_timestamp
                )                        
                '''
                cur.execute(create_script)

                insert_script  = 'INSERT INTO package (LANGUAGE, PKG_NAME, PKG_VER, IMPORT_NAME, LANG_VER, PKG_LIC, PKG_ERR, PKG_DEP) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)'
                insert_values = [
                    (
                        language, pkg_name, pkg_ver,
                        import_name, lang_ver, pkg_lic,
                        json.dumps(pkg_err), pkg_dep
                    )
                ]
                for record in insert_values:
                    cur.execute(insert_script, record)
    except Exception as error:
        print(error)

# update_script = 'UPDATE employee SET salary = salary + (salary * 0.5)'
# cur.execute(update_script)
#
# delete_script = 'DELETE FROM employee WHERE name = %s'
# delete_record = ('James',)
# cur.execute(delete_script, delete_record)
#
# cur.execute('SELECT * FROM EMPLOYEE')
# for record in cur.fetchall():
#     print(record['name'], record['salary'])