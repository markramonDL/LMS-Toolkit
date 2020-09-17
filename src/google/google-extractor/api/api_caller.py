from opnieuw import retry
from tail_recursive import tail_recursive


@retry(
    retry_on_exceptions=(Exception),
    max_calls_total=4,
    retry_window_after_first_call_in_seconds=60,
)
def execute(executable_resource):
    return executable_resource.execute()


@tail_recursive
def call_api(resource_method, resource_parameters, response_property, results=None):
    """
    Call a Google Classroom/Admin SDK API

    Parameters
    ----------
    resource_method: function
        is the get/list SDK function to call
    resource_parameters: dict
        is the parameters for get/list
    response_property: string
        is the property in the API response we want
    results: list
        is the list of dicts of the API response accumulated across pages

    Returns
    -------
    list
        a list of dicts of the API response property requested
    """
    if results is None:
        results = []
    response = execute(resource_method(**resource_parameters))
    results.extend(response.get(response_property, []))
    next_page_token = response.get("nextPageToken", None)
    if not next_page_token:
        return results
    resource_parameters["pageToken"] = next_page_token
    return call_api.tail_call(
        resource_method, resource_parameters, response_property, results
    )
