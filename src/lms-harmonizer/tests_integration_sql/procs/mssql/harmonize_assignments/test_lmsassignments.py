# SPDX-License-Identifier: Apache-2.0
# Licensed to the Ed-Fi Alliance under one or more agreements.
# The Ed-Fi Alliance licenses this file to you under the Apache License, Version 2.0.
# See the LICENSE and NOTICES files in the project root for more information.

from tests_integration_sql.mssql_loader import (
    insert_lms_assignment,
    insert_lms_section,
    insert_edfi_section,
    insert_descriptor,
    insert_lmsx_sourcesystem_descriptor,
    insert_lmsx_assignmentcategory_descriptor,
)
from tests_integration_sql.mssql_connection import MSSqlConnection, query
from tests_integration_sql.server_config import ServerConfig
from tests_integration_sql.orchestrator import run_harmonizer


SOURCE_SYSTEM = "Test_LMS"

DESCRIPTOR_NAMESPACE = (
    "uri://ed-fi.org/edfilms/AssignmentCategoryDescriptor/" + SOURCE_SYSTEM
)


def describe_when_lms_and_ods_tables_are_both_empty():
    def it_should_run_successfully(test_db_config: ServerConfig):
        # act
        run_harmonizer(test_db_config)
        # assert - no errors


def describe_when_lms_and_ods_tables_have_no_section_matches():
    def it_should_run_successfully(test_db_config: ServerConfig):
        section_id_1 = "sis_id_1"
        section_id_2 = "sis_id_2"

        # arrange
        with MSSqlConnection(test_db_config).pyodbc_conn() as connection:
            insert_lms_section(connection, section_id_1, SOURCE_SYSTEM)
            insert_lms_section(connection, section_id_2, SOURCE_SYSTEM)
            insert_edfi_section(connection, "not_matching_sis_id_1")
            insert_edfi_section(connection, "not_matching_sis_id_2")

        # act
        run_harmonizer(test_db_config)

        # assert
        with MSSqlConnection(test_db_config).pyodbc_conn() as connection:
            LMSSection = query(
                connection,
                "SELECT AssignmentIdentifier from [lmsx].[Assignment]",
            )

            assert len(LMSSection) == 0


def describe_when_there_are_assignments_to_insert():
    SIS_SECTION_ID = "sis_section_id"
    ASSIGNMENT_SOURCE_SYSTEM_IDENTIFIER = "assignment_identifier"
    ASSIGNMENT_CATEGORY = "test_category"

    def it_should_run_successfully(test_db_config: ServerConfig):
        # arrange
        with MSSqlConnection(test_db_config).pyodbc_conn() as connection:

            insert_descriptor(connection, DESCRIPTOR_NAMESPACE, ASSIGNMENT_CATEGORY)
            insert_lmsx_assignmentcategory_descriptor(connection, 1)

            insert_descriptor(connection, DESCRIPTOR_NAMESPACE, SOURCE_SYSTEM)
            insert_lmsx_sourcesystem_descriptor(connection, 2)

            insert_lms_section(connection, SIS_SECTION_ID, SOURCE_SYSTEM)
            insert_edfi_section(connection, SIS_SECTION_ID)
            connection.execute(
                """UPDATE LMS.LMSSECTION SET
                    EdFiSectionId = (SELECT TOP 1 ID FROM EDFI.SECTION)"""
            )

            insert_lms_assignment(
                connection,
                ASSIGNMENT_SOURCE_SYSTEM_IDENTIFIER,
                SOURCE_SYSTEM,
                1,
                ASSIGNMENT_CATEGORY,
            )

        # act
        run_harmonizer(test_db_config)

        # assert
        with MSSqlConnection(test_db_config).pyodbc_conn() as connection:
            LMSAssignment = query(connection, "SELECT * from [lmsx].[Assignment]")
            assert len(LMSAssignment) == 1
            assert (
                int(LMSAssignment[0]["AssignmentIdentifier"]) == 1
            )  # It is using the identity field from lms.Assignment


def describe_when_there_are_assignments_to_update():
    SIS_SECTION_ID = "sis_section_id"
    ASSIGNMENT_SOURCE_SYSTEM_IDENTIFIER = "assignment_identifier"
    ASSIGNMENT_CATEGORY = "test_category"

    def it_should_update_existing_assignments(test_db_config: ServerConfig):
        # arrange
        with MSSqlConnection(test_db_config).pyodbc_conn() as connection:
            insert_descriptor(connection, DESCRIPTOR_NAMESPACE, ASSIGNMENT_CATEGORY)
            insert_lmsx_assignmentcategory_descriptor(connection, 1)

            insert_descriptor(connection, DESCRIPTOR_NAMESPACE, SOURCE_SYSTEM)
            insert_lmsx_sourcesystem_descriptor(connection, 2)

            insert_lms_section(connection, SIS_SECTION_ID, SOURCE_SYSTEM)
            insert_edfi_section(connection, SIS_SECTION_ID)
            connection.execute(
                """UPDATE LMS.LMSSECTION SET
                    EdFiSectionId = (SELECT TOP 1 ID FROM EDFI.SECTION)"""
            )

            insert_lms_assignment(
                connection,
                ASSIGNMENT_SOURCE_SYSTEM_IDENTIFIER,
                SOURCE_SYSTEM,
                1,
                ASSIGNMENT_CATEGORY,
            )

        run_harmonizer(test_db_config)

        with MSSqlConnection(test_db_config).pyodbc_conn() as connection:
            connection.execute(
                "UPDATE LMS.ASSIGNMENT SET TITLE = 'AN UPDATED TITLE', LastModifiedDate = GETDATE()"
            )

        # act
        run_harmonizer(test_db_config)

        # assert
        with MSSqlConnection(test_db_config).pyodbc_conn() as connection:
            LMSAssignment = query(connection, "SELECT Title from [lmsx].[Assignment]")
            assert len(LMSAssignment) == 1
            assert LMSAssignment[0]["Title"] == "AN UPDATED TITLE"


def describe_when_there_are_assignments_to_delete():
    SIS_SECTION_ID = "sis_section_id"
    ASSIGNMENT_SOURCE_SYSTEM_IDENTIFIER = "assignment_identifier"
    ASSIGNMENT_CATEGORY = "test_category"

    def it_should_update_existing_assignments(test_db_config: ServerConfig):
        # arrange
        with MSSqlConnection(test_db_config).pyodbc_conn() as connection:
            insert_descriptor(connection, DESCRIPTOR_NAMESPACE, ASSIGNMENT_CATEGORY)
            insert_lmsx_assignmentcategory_descriptor(connection, 1)

            insert_descriptor(connection, DESCRIPTOR_NAMESPACE, SOURCE_SYSTEM)
            insert_lmsx_sourcesystem_descriptor(connection, 2)

            insert_lms_section(connection, SIS_SECTION_ID, SOURCE_SYSTEM)
            insert_edfi_section(connection, SIS_SECTION_ID)
            connection.execute(
                """UPDATE LMS.LMSSECTION SET
                    EdFiSectionId = (SELECT TOP 1 ID FROM EDFI.SECTION)"""
            )

            insert_lms_assignment(
                connection,
                ASSIGNMENT_SOURCE_SYSTEM_IDENTIFIER,
                SOURCE_SYSTEM,
                1,
                ASSIGNMENT_CATEGORY,
            )

        run_harmonizer(test_db_config)

        with MSSqlConnection(test_db_config).pyodbc_conn() as connection:
            connection.execute(
                "UPDATE LMS.ASSIGNMENT SET TITLE = 'AN UPDATED TITLE', LastModifiedDate = GETDATE(), DeletedAt = GETDATE()"
            )

        # act
        run_harmonizer(test_db_config)

        # assert
        with MSSqlConnection(test_db_config).pyodbc_conn() as connection:
            LMSAssignment = query(connection, "SELECT Title from [lmsx].[Assignment]")
            assert len(LMSAssignment) == 0
