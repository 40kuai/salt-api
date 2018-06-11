#!/usr/bin/env python
# -*- coding:utf-8 -*-
__author__ = '40kuai'
__version__ = 'v0.0.1'
"""
1. 整合 salt-api 功能
2. 获取token多次使用，发现token过期后重新获取token从当前失败任务重新继续执行
3. 可选：出现接口或服务异常（501），本次操作尝试几次重新执行
arg 为模块需要传入的参数，kwargs为pillar或grains参数。

分为以下几个类：
    1. salt-api 方法类
    2. 发送请求的类
"""

from urlparse import urljoin
import requests


class Salt_Api():
    def __init__(self, url, username, password):
        self.url = url
        self._username = username
        self._password = password
        self.get_token()

    def get_token(self, eauth='pam', ):
        """获取salt-api使用的token"""
        get_token_url = urljoin(self.url, 'login')
        json_data = {'username': self._username, 'password': self._password, 'eauth': eauth}
        token_obj = requests.post(get_token_url, json=json_data, verify=False)
        if token_obj.status_code != 200:
            raise Exception(token_obj.status_code)
        self.token = token_obj.json()['return'][0]['token']

    def post(self, prefix='/', json_data=None, headers=None):
        post_url = urljoin(self.url, prefix)
        if headers is None:
            headers = {'X-Auth-Token': self.token, 'Accept': 'application/json'}
        else:
            headers = {'X-Auth-Token': self.token, }.update(headers)
        post_requests = requests.post(post_url, json=json_data, headers=headers, verify=False)
        return post_requests.json()

    def get(self, prefix='/', json_data=None, headers=None):
        post_url = urljoin(self.url, prefix)
        if headers is None:
            headers = {'X-Auth-Token': self.token, 'Accept': 'application/json'}
        else:
            headers = {'X-Auth-Token': self.token, }.update(headers)
        get_requests = requests.get(post_url, json=json_data, headers=headers, verify=False)
        return get_requests.json()

    def get_all_key(self):
        """获取所有minion的key"""
        json_data = {'client': 'wheel', 'fun': 'key.list_all'}
        content = self.post(json_data=json_data)
        minions = content['return'][0]['data']['return']['minions']
        minions_pre = content['return'][0]['data']['return']['minions_pre']
        return minions, minions_pre

    def accept_key(self, minion_id):
        """认证minion_id，返回Ture or False"""
        json_data = {'client': 'wheel', 'fun': 'key.accept', 'match': minion_id}
        content = self.post(json_data=json_data)
        return content['return'][0]['data']['success']

    def delete_key(self, node_name):
        """删除minion_id，返回Ture or False"""
        json_data = {'client': 'wheel', 'fun': 'key.delete', 'match': node_name}
        content = self.post(json_data=json_data)
        return content['return'][0]['data']['success']

    def host_remote_module(self, tgt, fun, arg=None):
        """根据主机执行函数或模块，模块的参数为arg"""
        json_data = {'client': 'local', 'tgt': tgt, 'fun': fun, }
        if arg:
            json_data.update({'arg': arg})
        content = self.post(json_data=json_data)
        return content['return']

    def group_remote_module(self, tgt, fun, arg=None):
        """根据分组执行函数或模块，模块的参数为arg"""
        json_data = {'client': 'local', 'tgt': tgt, 'fun': fun, 'expr_form': 'nodegroup'}
        if arg:
            json_data.update({'arg': arg})
        content = self.post(json_data=json_data)
        return content['return']

    def host_sls_async(self, tgt, arg):
        '''主机异步sls '''
        json_data = {'client': 'local_async', 'tgt': tgt, 'fun': 'state.sls', 'arg': arg}
        content = self.post(json_data=json_data)
        return content['return']

    def group_sls_async(self, tgt, arg):
        '''分组异步sls '''
        json_data = {'client': 'local_async', 'tgt': tgt, 'fun': 'state.sls', 'arg': arg, 'expr_form': 'nodegroup'}
        content = self.post(json_data=json_data)
        return content['return']

    def server_hosts_pillar(self, tgt, arg, **kwargs):
        '''针对主机执行sls and pillar '''
        print kwargs
        kwargs = {'pillar': kwargs['kwargs']}
        json_data = {"client": "local", "tgt": tgt, "fun": "state.sls", "arg": arg, "kwarg": kwargs}
        content = self.post(json_data=json_data)
        return content['return']

    def server_group_pillar(self, tgt, arg, **kwargs):
        '''分组进行sls and pillar'''
        kwargs = {'pillar': kwargs['kwargs']}
        json_data = {'client': 'local', 'tgt': tgt, 'fun': 'state.sls', 'arg': arg, 'expr_form': 'nodegroup',
                     'kwarg': kwargs}
        content = self.post(json_data=json_data)
        return content['return']

    def jobs_all_list(self):
        '''打印所有jid缓存'''
        json_data = {"client": "runner", "fun": "jobs.list_jobs"}
        content = self.post(json_data=json_data)
        return content['return']

    def jobs_jid_status(self, jid):
        '''查看jid运行状态'''
        json_data = {"client": "runner", "fun": "jobs.lookup_jid", "jid": jid}
        content = self.post(json_data=json_data)
        return content['return']

    def keys_minion(self, hostname):
        """Show the list of minion keys or detail on a specific key"""
        content = self.get('keys/%s' % hostname)
        return content


if __name__ == '__main__':
    url = 'https://local:8000/'
    obj = Salt_Api(url, 'username', 'password')
    print obj.keys_minion('minionid')
