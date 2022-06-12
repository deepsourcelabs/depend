"""Functions to work with PostGres."""
import json
import os

import psycopg2.extras as pypsql
from psycopg2 import errors, sql

table_name = os.environ.get("TABLE_NAME") or "test"


def add_data(
    psql,
    language: str,
    pkg_name: str,
    pkg_ver: str,
    import_name: str,
    lang_ver: list[str],
    pkg_lic: list[str],
    pkg_err: dict,
    pkg_dep: list[str],
    clear_old_data: bool = False,
):
    """
    Add data in correct format into Postgres DB
    """
    try:
        with psql as conn, conn.cursor(cursor_factory=pypsql.NamedTupleCursor) as cur:
            if clear_old_data:
                cur.execute(
                    sql.SQL("DROP TABLE IF EXISTS {table_name}").format(
                        table_name=sql.Identifier(table_name),
                    )
                )
            create_script = sql.SQL(
                """ 
                CREATE TABLE IF NOT EXISTS {table_name} (
                    ID          BIGINT NOT NULL PRIMARY KEY,
                    LANGUAGE    varchar NOT NULL,
                    PKG_NAME    varchar NOT NULL,
                    PKG_VER     varchar NOT NULL,
                    IMPORT_NAME varchar,
                    LANG_VER    text[], 
                    PKG_LIC     text[],
                    PKG_ERR     json,
                    PKG_DEP     text[],
                    timestamp   timestamptz default current_timestamp
                )                        
                """
            ).format(
                table_name=sql.Identifier(table_name),
            )
            cur.execute(create_script)

            insert_script = sql.SQL(
                "INSERT INTO {table_name} "
                "(ID, LANGUAGE, PKG_NAME, PKG_VER, IMPORT_NAME,"
                " LANG_VER, PKG_LIC, PKG_ERR, PKG_DEP) "
                "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)"
                "ON CONFLICT (ID) DO NOTHING"
            ).format(
                table_name=sql.Identifier(table_name),
            )
            insert_values = [
                (
                    hash(language + pkg_name + pkg_ver),
                    language,
                    pkg_name,
                    pkg_ver,
                    import_name,
                    lang_ver,
                    pkg_lic,
                    json.dumps(pkg_err),
                    pkg_dep,
                )
            ]
            for record in insert_values:
                cur.execute(insert_script, record)
    except errors.InFailedSqlTransaction as error:
        print(error)


def get_data(
    psql,
    language: str,
    pkg_name: str,
    pkg_ver: str,
):
    """
    Fetch info about a specific package version from DB
    """
    pkg_id = hash(language + pkg_name + pkg_ver)
    try:
        with psql as conn, conn.cursor(cursor_factory=pypsql.NamedTupleCursor) as cur:
            read_script = sql.SQL("SELECT * FROM {table_name} WHERE ID = %s").format(
                table_name=sql.Identifier(table_name),
            )
            read_record = (pkg_id,)
            cur.execute(read_script, read_record)
            return cur.fetchone()
    except (errors.InFailedSqlTransaction, errors.UndefinedTable) as error:
        print(error)
        return None


def del_data(
    psql,
    language: str,
    pkg_name: str,
    pkg_ver: str,
):
    """
    Fetch info about a specific package version from DB
    """
    pkg_id = hash(language + pkg_name + pkg_ver)
    try:
        with psql as conn, conn.cursor(cursor_factory=pypsql.NamedTupleCursor) as cur:
            del_script = sql.SQL("DELETE FROM {table_name} WHERE ID = %s").format(
                table_name=sql.Identifier(table_name)
            )
            del_record = (pkg_id,)
            cur.execute(del_script, del_record)
    except errors.InFailedSqlTransaction as error:
        print(error)


def upd_data(
    psql,
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
    Update info about a specific package version from DB
    """
    del_data(psql, language, pkg_name, pkg_ver)
    add_data(
        psql,
        language,
        pkg_name,
        pkg_ver,
        import_name,
        lang_ver,
        pkg_lic,
        pkg_err,
        pkg_dep,
    )
