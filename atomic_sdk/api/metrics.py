from typing import List, Optional, Union, Dict, Any, Literal


from .base import ResourceClient
from ..exceptions import InvalidRequestError


class MetricsClient(ResourceClient):
    """
    A client for querying time series metrics for sites and clients.
    """

    def query(
        self,
        start: int,
        end: int,
        metric: Union[str, List[str]],
        dimension: Union[str, List[str]],
        query_type: Literal["site", "client"],
        key: Optional[Union[str, int]] = None,
        filters: Optional[List[Dict[str, Any]]] = None,
        summarize: bool = False,
    ) -> Dict[str, Any]:
        """
        Queries the time series metrics database.

        Args:
            start: A Unix timestamp for the start of the data range.
            end: A Unix timestamp for the end of the data range.
            metric: The timeseries metric(s) to report (e.g., 'requests' or ['uniques', 'views']).
            dimension: The dimension(s) to slice the metric data by (e.g., 'http_host').
            query_type: The type of metrics being requested ('site' or 'client').
            key: The identifier for the site or client.
                 For 'site', this can be an Atomic Site ID or domain.
                 For 'client', this should be the client name/ID. Defaults to the
                 client ID set during AtomicClient initialization if not provided.
            filters: A list of dictionaries for filtering, where each dict has
                     'column', 'operator', and 'value' keys.
                     e.g., [{'column': 'request_method', 'operator': '=', 'value': 'POST'}]
            summarize: If True, returns an overall summary for the timespan instead
                       of a time series.

        Returns:
            A dictionary containing the metrics response data.
        """
        if query_type not in ["site", "client"]:
            raise ValueError("query_type must be 'site' or 'client'.")

        if not key:
            if query_type == "client":
                key = self._client_id_or_name
            else:
                raise ValueError("'key' (site_id or domain) is required for 'site' queries.")

        endpoint = f"/metrics/{query_type}/{key}"
        if summarize:
            endpoint += "/summarize"

        payload = {
            "start": start,
            "end": end,
            "metric": metric if isinstance(metric, list) else [metric],
            "dimension": dimension if isinstance(dimension, list) else [dimension],
        }

        if filters:
            # The API expects filters in a specific array format in the POST body
            # e.g. filters[0][column]=... filters[0][operator]=...
            # The requests library handles this conversion from a list of dicts correctly
            # when passed as the `data` parameter.
            payload['filters'] = filters

        # This endpoint uses POST for querying
        return self._post(endpoint, data=payload)

    def get_site_logs(
        self,
        start: int,
        end: int,
        site_id: Optional[int] = None,
        domain: Optional[str] = None,
        page_size: int = 500,
        scroll_id: Optional[str] = None,
        sort_order: Literal["asc", "desc"] = "asc",
        filters: Optional[Dict[str, List[str]]] = None
    ) -> Dict[str, Any]:
        """
        Get web server access log data from a site.

        Args:
            start: A Unix timestamp for the start of the log data range.
            end: A Unix timestamp for the end of the log data range.
            site_id: The Atomic site ID.
            domain: The domain name of the site.
            page_size: The maximum number of records to retrieve. Defaults to 500.
            scroll_id: ID for paginating through large result sets.
            sort_order: Sort order ('asc' or 'desc'). Defaults to 'asc'.
            filters: Dictionary of filters to apply, e.g., {"status": ["404", "500"]}.

        Returns:
            A dictionary containing the logs, total results, and a potential scroll_id.
        """
        _, identifier = self._get_service_and_identifier(site_id, domain)
        endpoint = f"/site-logs/{identifier}"

        data_payload = {
            "start": start,
            "end": end,
            "page_size": page_size,
            "sort_order": sort_order,
        }
        if scroll_id:
            data_payload['scroll_id'] = scroll_id
        if filters:
            # The API expects a structure like: 'data[filter][status][]': '404'
            # We must construct this payload carefully. The `requests` library will
            # not automatically format this nested structure.
            final_payload = {}
            for key, value in data_payload.items():
                final_payload[f'data[{key}]'] = value
            for f_key, f_values in filters.items():
                 for val in f_values:
                    final_payload[f'data[filter][{f_key}][]'] = val
            return self._post(endpoint, data=final_payload)
        else:
            return self._post(endpoint, data={f"data[{k}]": v for k, v in data_payload.items()})


    def get_error_logs(self, **kwargs) -> Dict[str, Any]:
        """
        Get PHP error log data from a site. Arguments are identical to get_site_logs.
        """
        # This re-uses the same logic as get_site_logs but hits a different endpoint.
        site_id = kwargs.pop('site_id', None)
        domain = kwargs.pop('domain', None)

        _, identifier = self._get_service_and_identifier(site_id, domain)
        endpoint = f"/site-error-logs/{identifier}"

        # We can reuse the payload construction from get_site_logs, but need to reconstruct it here.
        # This is a good candidate for a private helper method if more log types are added.
        data_payload = {k:v for k,v in kwargs.items()} # simplified for brevity
        return self._post(endpoint, data={f"data[{k}]": v for k, v in data_payload.items()})
