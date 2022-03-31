"""Functions to work with PostGres."""
import json

import psycopg2.extras

def add_data(
    psql,
    db_name: str,
    language: str,
    pkg_name: str,
    pkg_ver: str,
    import_name: str,
    lang_ver: list[str],
    pkg_lic: list[str],
    pkg_err: dict,
    pkg_dep: list[str],
    force: bool = False,
):
    """
    Add data in correct format into Postgres DB
    """
    try:
        with psql as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.NamedTupleCursor) as cur:
                if force:
                    cur.execute(f'DROP TABLE IF EXISTS {db_name}')
                create_script = f''' 
                CREATE TABLE IF NOT EXISTS {db_name} (
                    ID          BIGINT NOT NULL PRIMARY KEY,
                    LANGUAGE    varchar NOT NULL,
                    PKG_NAME    varchar NOT NULL,
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

                insert_script  = f'INSERT INTO {db_name} ' \
                                 '(ID, LANGUAGE, PKG_NAME, PKG_VER, IMPORT_NAME,' \
                                 ' LANG_VER, PKG_LIC, PKG_ERR, PKG_DEP) ' \
                                 'VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)'
                insert_values = [
                    (
                        hash(language + pkg_name + pkg_ver),
                        language, pkg_name, pkg_ver,
                        import_name, lang_ver, pkg_lic,
                        json.dumps(pkg_err), pkg_dep
                    )
                ]
                for record in insert_values:
                    cur.execute(insert_script, record)
    except Exception as error:
        print(error)


def get_data(
        psql,
        db_name: str,
        language: str,
        pkg_name: str,
        pkg_ver: str,
):
    """
    Fetch info about a specific package version from DB
    """
    pkg_id = hash(language + pkg_name + pkg_ver)
    try:
        with psql as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.NamedTupleCursor) as cur:
                read_script = f'SELECT * FROM {db_name} WHERE ID = %s'
                read_record = (pkg_id,)
                cur.execute(read_script, read_record)
                return cur.fetchone()
    except Exception as error:
        print(error)
        return None


def del_data(
        psql,
        db_name: str,
        language: str,
        pkg_name: str,
        pkg_ver: str,
):
    """
    Fetch info about a specific package version from DB
    """
    pkg_id = hash(language + pkg_name + pkg_ver)
    try:
        with psql as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
                del_script = f'DELETE FROM {db_name} WHERE ID = %s'
                del_record = (pkg_id,)
                cur.execute(del_script, del_record)
    except Exception as error:
        print(error)


def upd_data(
        psql,
        db_name: str,
        language: str,
        pkg_name: str,
        pkg_ver: str,
        import_name: str,
        lang_ver: list[str],
        pkg_lic: list[str],
        pkg_err: dict,
        pkg_dep: list[str]
):
    """
    Update info about a specific package version from DB
    """
    del_data(psql, db_name, language, pkg_name, pkg_ver)
    add_data(
        psql, db_name, language, pkg_name, pkg_ver,
        import_name, lang_ver, pkg_lic, pkg_err,pkg_dep
    )
