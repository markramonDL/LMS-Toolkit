# SPDX-License-Identifier: Apache-2.0
# Licensed to the Ed-Fi Alliance under one or more agreements.
# The Ed-Fi Alliance licenses this file to you under the Apache License, Version 2.0.
# See the LICENSE and NOTICES files in the project root for more information.

import time
import random

from requests_oauthlib import OAuth1Session


DEFAULT_URL = "https://api.schoology.com/v1/"


class RequestClient:
    """
    The RequestClient class wraps all the configuration complexity related to authentication and http requests for Schoology API

    Args:
        schoology_key (str): The consumer key given by Schoology
        schoology_secret (str): The consumer secret given by Schoology
        base_url (str, optional): The API base url. Default value: https://api.schoology.com/v1/

    Attributes:
        oauth (OAuth1Session): The two-legged authenticated OAuth1 session
"""

    def __init__(self, schoology_key, schoology_secret, base_url=DEFAULT_URL):
        self.oauth = OAuth1Session(schoology_key, schoology_secret)
        self.base_url = base_url
        self.consumer_key = schoology_key
        self.consumer_secret = schoology_secret


    @property
    def _request_header(self):
        """The _request_header property helps to build the Request Header for oauth requests
            Returns:
                dict: Request headers
        """
        auth_header = (
            'OAuth realm="Schoology API",',
            f'oauth_consumer_key="{self.consumer_key}",',
            'oauth_token="",',
            f'oauth_nonce="{"".join( [str(random.randint(0, 9)) for i in range(8)] )}",',
            f'oauth_timestamp="{time.time()}",',
            'oauth_signature_method="PLAINTEXT",',
            'oauth_version="1.0",',
            'oauth_signature="%s%%26%s"' % ( self.consumer_secret, "",)
        )

        return {
            "Authorization": ''.join(auth_header),
            "Accept": "application/json",
            "Host": "api.schoology.com",
            "Content-Type": "application/json",
        }


    def _get(self, url):
        """Internal method to create requests and parse responses
        Args:
            url (string): The endpoint that you want to request

        Returns:
            dict: A parsed response from the server
        """
        assert url is not None

        response = self.oauth.get(
            url=self.base_url + url,
            headers=self._request_header,
            auth=self.oauth.auth,
        )
        return response.json()


    def get_assignments_by_section_ids(self, section_ids):
        """
        Args:
            section_ids (list): A list of section ids

        Returns:
            dict: A parsed response from the server
        """
        assert section_ids is not None

        assignments = []
        for section_id in section_ids:
            url = f"sections/{section_id}/assignments"
            response = self._get(url)
            if "assignment" in response:
                assignments = assignments + response["assignment"]

        return assignments


    def get_section_by_id(self, section_id):
        """
        Args:
            section_id (list): The id of the section

        Returns:
            dict: A parsed response from the server
        """
        assert section_id is not None

        response = self._get(f"sections/{section_id}")
        return response


    def get_submissions_by_section_id(self, section_id):
        """
        Args:
            section_id (list): The id of the section

        Returns:
            dict: A parsed response from the server
        """
        assert section_id is not None

        response = self._get(f"sections/{section_id}/submissions")
        return response


    def get_users(self):
        """Gets all the users from the Schoology API
        Returns:
            dict: A parsed response from the server
        """
        response = self._get("users")
        if "user" in response:
            return response["user"]
        return []