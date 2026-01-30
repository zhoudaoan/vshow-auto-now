import datetime
import logging
from requests import request
from Vshow_TOOLS.read_cfg import get_config

logger = logging


class VshowCommonApi:
    """
    vshowAPI通用方法
    """

    def __init__(self, connect_info, service):
        self.protocol = get_config(section="protocol", option="vshow_protocol")
        self.authorization = get_config(section="authorization", option="vshow_authorization")
        self.cookie = get_config(section="authorization", option="vshow_admin_cookie")
        self.vshow_ip = connect_info.get(service)
        self.headers = {"authorization": self.authorization}
        self.headers_cookie = {"Cookie": self.cookie}

    def _get_url(self, uri):
        logger.info(f"请求的url：{self.protocol}://{self.vshow_ip}/{uri}")
        return f"{self.protocol}://{self.vshow_ip}/{uri}"

    def _request(self, method, uri, data=None, **kwargs):
        """
        封装后request方法，接口统一通道
        """
        if not data:
            data = {}
        logger.info(f"非GET请求的参数：{data}")
        start_time = datetime.datetime.now()
        logger.info(f"接口的请求开始时间：{start_time}")
        if "test3397-admin.v.show" in self._get_url(uri):
            logger.info(f"获取到的cookie: {self.cookie}")
            if method == 'GET':
                response = request(method, self._get_url(uri), params=kwargs.pop('params', None), headers=self.headers_cookie, verify=False,
                                   **kwargs)
            else:
                response = request(method, self._get_url(uri), json=data, headers=self.headers_cookie, verify=False,
                                   **kwargs)
        else:
            response = request(method, self._get_url(uri), json=data, headers=self.headers, verify=False,
                               **kwargs)
        end_time = datetime.datetime.now()
        logger.info(f"接口的请求结束时间：{end_time}")
        logger.info(f"请求时间差：{end_time - start_time} 秒")
        if "add-coin" in uri:
            logger.info(f"特殊接口，跳过JSON解析: {method} {uri} {response.status_code}")
            return response
        try:
            json_data = response.json()
        except Exception as e:
            logger.error(f"JSON 解析失败: {str(e)}，响应内容: {response.text[:500]}")
            raise Exception("Failed to parse response as JSON")

        # 判断是否为有效非空响应（假设业务数据至少是一个非空字典）
        if isinstance(json_data, dict) and json_data:
            logger.info(f"返回的结果: {method} {uri} {response.status_code}")
            return json_data
        else:
            logger.error(f"无效或空响应: {json_data}")
            raise Exception("Received empty or invalid response")

    def get(self, uri, timeout=120, **kwargs):
        kwargs.setdefault('allow_redirects', True)
        return self._request('GET', uri=uri, timeout=timeout, **kwargs)

    def options(self, uri, timeout=120, **kwargs):
        kwargs.setdefault('allow_redirects', True)
        return self._request('OPTIONS', uri=uri, timeout=timeout, **kwargs)

    def head(self, uri, timeout=120, **kwargs):
        kwargs.setdefault('allow_redirects', True)
        return self._request('HEAD', uri=uri, timeout=timeout, **kwargs)

    def post(self, uri, timeout=120, **kwargs):
        return self._request('POST', uri=uri, timeout=timeout, **kwargs)

    def put(self, uri, timeout=120, **kwargs):
        return self._request('PUT', uri=uri, timeout=timeout, **kwargs)

    def patch(self, uri, timeout=120, **kwargs):
        return self._request('PATCH', uri=uri, timeout=timeout, **kwargs)

    def delete(self, uri, timeout=120, **kwargs):
        return self._request('DELETE', uri=uri, timeout=timeout, **kwargs)
