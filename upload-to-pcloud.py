# coding: utf-8

import os
import sys

import click
import hashlib
import requests

# Load credentials
env_username = os.environ.get('PCLOUD_USERNAME')
env_password = os.environ.get('PCLOUD_PASSWORD')

if not env_username:
    print("error: missing PCLOUD_USERNAME definition")
if not env_password:
    print("error: missing PCLOUD_PASSWORD definition")
if not env_username or not env_password:
    sys.exit(1)


def sha1(s):
    return hashlib.sha1(s.encode('utf-8')).hexdigest()


class PCloudApi:
    baseurl = "https://eapi.pcloud.com"

    def __init__(self, username, password):
        self.username = username
        self.digest = self.get_digest()
        self.password_digest = sha1(password + sha1(self.username.lower()) + self.digest)
        self.auth = self.get_auth()

    def __request(self, method, route, **kwargs):
        func = getattr(requests, method.lower())
        r = func(f"{self.baseurl}/{route}", **kwargs)  # type: requests.Response
        r.raise_for_status()
        return r.json()

    def get_digest(self):
        resp = self.__request('get', 'getdigest')
        return resp['digest']

    def get_auth(self):
        params = {'getauth': '1', 'username': self.username, 'digest': self.digest,
                  'passworddigest': self.password_digest}
        resp = self.__request('get', 'userinfo', params=params)
        return resp['auth']

    def get_folder_id(self, distant_folder):
        params = {'auth': self.auth, 'path': distant_folder, 'nofiles': '1'}
        resp = self.__request('get', 'listfolder', params=params)
        if resp['result'] == 2005:
            print(f"error: distant folder {distant_folder} does not exist.")
            sys.exit(1)
        elif resp['result'] != 0:
            print(f"error: {resp['error']}")
            sys.exit(1)
        return resp['metadata']['folderid']

    def upload_file(self, local_path, distant_folder):
        folder_id = self.get_folder_id(distant_folder)
        params = {'auth': self.auth, 'folderid': folder_id, 'filename': os.path.basename(local_path)}
        with open(local_path, 'rb') as f:
            self.__request('put', 'uploadfile', params=params, data=f.read())
        print(f"{os.path.basename(local_path)} uploaded to {distant_folder}")


@click.command()
@click.option('--to', default='/', help='distant folder (root by default)')
@click.argument('input_path', type=click.Path(exists=True))
def upload_to_pcloud(input_path, to='/'):
    pcloud = PCloudApi(username=env_username, password=env_password)
    pcloud.upload_file(local_path=input_path, distant_folder=to)


if __name__ == '__main__':
    upload_to_pcloud()
