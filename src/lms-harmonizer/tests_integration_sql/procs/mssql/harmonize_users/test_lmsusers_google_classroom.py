# SPDX-License-Identifier: Apache-2.0
# Licensed to the Ed-Fi Alliance under one or more agreements.
# The Ed-Fi Alliance licenses this file to you under the Apache License, Version 2.0.
# See the LICENSE and NOTICES files in the project root for more information.

from tests_integration_sql.mssql_loader import (
    insert_lms_user,
    insert_lms_user_deleted,
    insert_edfi_student_with_usi,
    insert_edfi_student_electronic_mail,
)
from tests_integration_sql.mssql_connection import MSSqlConnection, query
from tests_integration_sql.server_config import ServerConfig
from tests_integration_sql.orchestrator import run_harmonizer


SOURCE_SYSTEM = "Google"


def describe_when_lms_and_ods_tables_have_no_matches():
    def it_should_run_successfully(test_db_config: ServerConfig):
        # arrange
        with MSSqlConnection(test_db_config).pyodbc_conn() as connection:
            insert_lms_user(connection, "sis_id_1", "e1@e.com", SOURCE_SYSTEM)
            insert_lms_user(connection, "sis_id_2", "e2@e.com", SOURCE_SYSTEM)
            insert_edfi_student_with_usi(connection, 1)
            insert_edfi_student_with_usi(connection, 2)
            insert_edfi_student_electronic_mail(connection, 1, "not_e1@e.com")
            insert_edfi_student_electronic_mail(connection, 2, "not_e2@e.com")

        # act
        run_harmonizer(test_db_config)

        # assert
        with MSSqlConnection(test_db_config).pyodbc_conn() as connection:
            LMSUser = query(connection, "SELECT EdFiStudentId from lms.LMSUser")
        assert len(LMSUser) == 2
        assert LMSUser[0]["EdFiStudentId"] is None
        assert LMSUser[1]["EdFiStudentId"] is None


def describe_when_lms_and_ods_tables_have_a_match():
    STUDENT_ID = "10000000-0000-0000-0000-000000000000"
    SIS_ID = "sis_id"
    EMAIL = "email@e.com"

    def it_should_run_successfully(test_db_config: ServerConfig):
        # arrange
        with MSSqlConnection(test_db_config).pyodbc_conn() as connection:
            insert_lms_user(connection, SIS_ID, EMAIL, SOURCE_SYSTEM)
            insert_edfi_student_with_usi(connection, 1, STUDENT_ID)
            insert_edfi_student_electronic_mail(connection, 1, EMAIL)

        # act
        run_harmonizer(test_db_config)

        # assert
        with MSSqlConnection(test_db_config).pyodbc_conn() as connection:
            LMSUser = query(connection, "SELECT EdFiStudentId from lms.LMSUser")
        assert len(LMSUser) == 1
        assert LMSUser[0]["EdFiStudentId"] == STUDENT_ID


def describe_when_lms_and_ods_tables_have_a_match_to_deleted_record():
    STUDENT_ID = "10000000-0000-0000-0000-000000000000"
    SIS_ID = "sis_id"
    EMAIL = "email@e.com"

    def it_should_ignore_the_deleted_record(test_db_config: ServerConfig):
        # arrange
        with MSSqlConnection(test_db_config).pyodbc_conn() as connection:
            insert_lms_user_deleted(connection, SIS_ID, EMAIL, SOURCE_SYSTEM)
            insert_edfi_student_with_usi(connection, 1, STUDENT_ID)
            insert_edfi_student_electronic_mail(connection, 1, EMAIL)

        # act
        run_harmonizer(test_db_config)

        # assert
        with MSSqlConnection(test_db_config).pyodbc_conn() as connection:
            LMSUser = query(connection, "SELECT EdFiStudentId from lms.LMSUser")
            assert len(LMSUser) == 1
            assert LMSUser[0]["EdFiStudentId"] is None


def describe_when_single_student_has_multiple_emails_with_one_match():
    STUDENT_ID = "10000000-0000-0000-0000-000000000000"
    SIS_ID = "sis_id"
    EMAIL = "email@e.com"

    def it_should_run_successfully(test_db_config: ServerConfig):
        # arrange
        with MSSqlConnection(test_db_config).pyodbc_conn() as connection:
            insert_lms_user(connection, SIS_ID, EMAIL, SOURCE_SYSTEM)
            insert_edfi_student_with_usi(connection, 1, STUDENT_ID)
            insert_edfi_student_electronic_mail(connection, 1, "not_email@e.com")
            insert_edfi_student_electronic_mail(connection, 1, EMAIL)
            insert_edfi_student_electronic_mail(connection, 1, "also_not_email@e.com")

        # act
        run_harmonizer(test_db_config)

        # assert
        with MSSqlConnection(test_db_config).pyodbc_conn() as connection:
            LMSUser = query(connection, "SELECT EdFiStudentId from lms.LMSUser")
            assert len(LMSUser) == 1
            assert LMSUser[0]["EdFiStudentId"] == STUDENT_ID


def describe_when_lms_and_ods_tables_have_one_match_and_one_not_match():
    STUDENT_ID = "10000000-0000-0000-0000-000000000000"
    SIS_ID = "sis_id"
    EMAIL = "email@e.com"

    NOT_MATCHING_STUDENT_ID = "20000000-0000-0000-0000-000000000000"
    NOT_MATCHING_SIS_ID = "not_matching_sis_id"
    NOT_MATCHING_EMAIL = "not_email@e.com"

    def it_should_run_successfully(test_db_config: ServerConfig):
        # arrange
        with MSSqlConnection(test_db_config).pyodbc_conn() as connection:
            insert_lms_user(connection, SIS_ID, EMAIL, SOURCE_SYSTEM)
            insert_lms_user(
                connection, NOT_MATCHING_SIS_ID, NOT_MATCHING_EMAIL, SOURCE_SYSTEM
            )

            insert_edfi_student_with_usi(connection, 1, STUDENT_ID)
            insert_edfi_student_electronic_mail(connection, 1, EMAIL)

            insert_edfi_student_with_usi(connection, 2, NOT_MATCHING_STUDENT_ID)
            insert_edfi_student_electronic_mail(connection, 2, "also_not_email@e.com")

        # act
        run_harmonizer(test_db_config)

        # assert
        with MSSqlConnection(test_db_config).pyodbc_conn() as connection:
            LMSUser = query(
                connection,
                "SELECT EdFiStudentId, SourceSystemIdentifier from lms.LMSUser",
            )
            assert len(LMSUser) == 2
            assert LMSUser[0]["SourceSystemIdentifier"] == SIS_ID
            assert LMSUser[0]["EdFiStudentId"] == STUDENT_ID
            assert LMSUser[1]["SourceSystemIdentifier"] == NOT_MATCHING_SIS_ID
            assert LMSUser[1]["EdFiStudentId"] is None
