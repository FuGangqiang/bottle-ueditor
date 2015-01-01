# encoding: utf-8

import os
import random
import urllib
import datetime

from bottle import request, abort, template

MEDIA_ROOT = './static/media/'
MEDIA_URL = '/static/media/'

# 请参阅php文件夹里面的config.json进行配置
settings = {
    # 上传图片配置项
    "imageActionName": "uploadimage",
    "imageMaxSize": 10485760,
    "imageFieldName": "upfile",
    "imageUrlPrefix": "",
    "imagePathFormat": "",
    "imageAllowFiles": [".png", ".jpg", ".jpeg", ".gif", ".bmp"],

    # 涂鸦图片上传配置项
    "scrawlActionName": "uploadscrawl",
    "scrawlFieldName": "upfile",
    "scrawlMaxSize": 10485760,
    "scrawlUrlPrefix": "",
    "scrawlPathFormat": "",

    # 截图工具上传
    "snapscreenActionName": "uploadimage",
    "snapscreenPathFormat": "",
    "snapscreenUrlPrefix": "",

    # 抓取远程图片配置
    "catcherLocalDomain": ["127.0.0.1", "localhost", "img.baidu.com"],
    "catcherPathFormat": "",
    "catcherActionName": "catchimage",
    "catcherFieldName": "source",
    "catcherMaxSize": 10485760,
    "catcherAllowFiles": [".png", ".jpg", ".jpeg", ".gif", ".bmp"],
    "catcherUrlPrefix": "",

    # 上传视频配置
    "videoActionName": "uploadvideo",
    "videoPathFormat": "",
    "videoFieldName": "upfile",
    "videoMaxSize": 102400000,
    "videoUrlPrefix": "",
    "videoAllowFiles": [
        ".flv", ".swf", ".mkv", ".avi", ".rm", ".rmvb", ".mpeg", ".mpg",
        ".ogg", ".ogv", ".mov", ".wmv", ".mp4", ".webm", ".mp3", ".wav",
        ".mid"
    ],

    # 上传文件配置
    "fileActionName": "uploadfile",
    "filePathFormat": "",
    "fileFieldName": "upfile",
    "fileMaxSize": 204800000,
    "fileUrlPrefix": "",
    "fileAllowFiles": [
        ".png", ".jpg", ".jpeg", ".gif", ".bmp",
        ".flv", ".swf", ".mkv", ".avi", ".rm", ".rmvb", ".mpeg", ".mpg",
        ".ogg", ".ogv", ".mov", ".wmv", ".mp4", ".webm", ".mp3", ".wav",
        ".mid", ".rar", ".zip", ".tar", ".gz", ".7z", ".bz2", ".cab",
        ".iso", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx",
        ".pdf", ".txt", ".md", ".xml"
    ],

    # 列出指定目录下的图片
    "imageManagerActionName": "listimage",
    "imageManagerListPath": "",
    "imageManagerListSize": 30,
    "imageManagerAllowFiles": [".png", ".jpg", ".jpeg", ".gif", ".bmp"],
    "imageManagerUrlPrefix": "",

    # 列出指定目录下的文件
    "fileManagerActionName": "listfile",
    "fileManagerListPath": "",
    "fileManagerUrlPrefix": "",
    "fileManagerListSize": 30,
    "fileManagerAllowFiles": [
        ".png", ".jpg", ".jpeg", ".gif", ".bmp", ".tif", ".psd", ".flv",
        ".swf", ".mkv", ".avi", ".rm", ".rmvb", ".mpeg", ".mpg", ".ogg",
        ".ogv", ".mov", ".wmv", ".mp4", ".webm", ".mp3", ".wav", ".mid",
        ".rar", ".zip", ".tar", ".gz", ".7z", ".bz2", ".cab", ".iso",
        ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx", ".pdf",
        ".txt", ".md", ".xml", ".exe", ".com", ".dll", ".msi"
    ]
}

upload_actions = ["uploadimage", "uploadfile", "uploadvideo", "uploadscrawl"]
list_actions = ["listimage", "listfile"]
actions = ['config', "catchimage"]
actions.extend(list_actions)
actions.extend(upload_actions)

upload_allow_type_field = {
    "uploadimage": "imageAllowFiles",
    "uploadfile": "fileAllowFiles",
    "uploadvideo": "videoAllowFiles",
    "catchimage": "catcherAllowFiles"
}
list_allow_type_field = {
    "listimage": "imageManagerAllowFiles",
    "listfile": "fileManagerAllowFiles"
}
list_type_size_field = {
    "listimage": "imageManagerListSize",
    "listfile": "fileManagerListSize"
}
upload_max_size_field = {
    "uploadimage": "imageMaxSize",
    "uploadfile": "filwMaxSize",
    "uploadvideo": "videoMaxSize",
    "uploadscrawl": "scrawlMaxSize",
    "catchimage": "catcherMaxSize"
}


def check_action(fn):
    def wrapper(self, *args, **kwargs):
        action = request.params.get('action')
        if not action or action not in actions:
            abort(404, "Invalid request: action=%s!" % action)
        self.action = action
        return fn(self, *args, **kwargs)
    return wrapper


class UEditor(object):
    def __init__(self, app):
        app.route('/ueditor', 'GET', self.get)
        app.route('/ueditor', 'POST', self.post)
        app.route('/ueditor/test', 'GET', self.test)

    def test(self):
        return template('test_editor.html')

    @check_action
    def get(self):
        if self.action == 'config':
            return settings
        if self.action in list_actions:
            list_size = int(request.GET.get('size', settings.get(list_type_size_field[self.action], 30)))
            list_start = int(request.GET.get('start', 0))
            files = self.get_files()
            if len(files) == 0:
                return {"state": u"未找到匹配文件！",
                        "list": [],
                        "start": list_start,
                        "total": 0}
            else:
                return {"state": "SUCCESS",
                        "list": files[list_start:list_start+list_size],
                        "start": list_start,
                        "total": len(files)}
        return {'state': 'ERROR'}

    @check_action
    def post(self):
        if self.action in upload_actions:
            return self.upload()
        elif self.action == 'catchimage':
            return self.catch_image()
        else:
            return {'state': 'ERROR'}

    def get_files(self):
        files = []
        allow_file_types = settings.get(list_allow_type_field[self.action])
        root_path = os.path.join(MEDIA_ROOT)
        for (root, dirnames, filenames) in os.walk(root_path):
            for fn in filenames:
                ext = os.path.splitext(fn)[1]
                if ext in allow_file_types:
                    item_fullname = os.path.join(root, fn)
                    files.append({
                        "url": urllib.basejoin(MEDIA_URL, os.path.relpath(
                            item_fullname,
                            root_path)),
                        "mtime": os.path.getmtime(item_fullname)
                    })
        return files

    def upload(self):
        if self.action == 'uploadscrawl':
            upload_file = request.POST.get('upfile')
        else:
            upload_file = request.files.get('upfile')
        if upload_file is None:
            return {'state': 'ERROR'}
        if self.action == 'uploadscrawl':
            upload_filename = 'scrawl.png'
        else:
            upload_filename = upload_file.raw_filename
        file_name, file_ext = os.path.splitext(upload_filename)
        allow_type = settings.get(
            upload_allow_type_field.get(self.action, ''), [])
        if self.action != 'uploadscrawl' and file_ext not in allow_type:
            return {'state': 'ERROR'}
        upload_renamed_filename, upload_pathname = self.get_renamed_filename(file_ext)
        if self.action == 'uploadscrawl':
            # uploadscrawl 需要 base64 解码
            import base64
            try:
                f = open(upload_pathname, 'wb')
                f.write(base64.decodestring(upload_file))
                f.close()
            except:
                return {'state': 'ERROR'}
        else:
            upload_file.save(upload_pathname)
        return {'url': urllib.parse.urljoin(MEDIA_URL, upload_renamed_filename),
                'original': upload_filename,
                'type': file_ext,
                'state': 'SUCCESS',
                'size': 12345}

    def catch_image(self):
        remote_urls = request.POST.get('source')
        catcher_infos = []
        for url in remote_urls:
            remote_file = os.path.basename(url)
            remote_filename, remote_ext = os.path.splitext(remote_file)
            allow_type = settings.get(
                upload_allow_type_field.get(self.action, ''), [])
            if remote_ext not in allow_type:
                return {'state': 'ERROR'}
            remote_renamed_filename, remote_pathname = self.get_renamed_filename(remote_ext)
            try:
                remote_image = urllib.urlopen(url)
                f = open(remote_pathname, 'wb')
                f.write(remote_image.read())
                f.close()
            except:
                return {'state': 'ERROR'}
            catcher_infos.append({
                "state": 'SUCCESS',
                "url": urllib.parse.urljoin(MEDIA_URL , remote_renamed_filename),
                "size": 1234,
                "title": remote_renamed_filename,
                "original": remote_filename,
                "source": url
            })
        return {"state": "SUCCESS" if len(catcher_infos) > 0 else "ERROR",
                "list": catcher_infos}

    def get_renamed_filename(self, file_ext):
        while True:
            renamed_filename = "%s_%s%s" % (
                datetime.datetime.now().strftime("%Y%m%d%H%M%S"),
                random.randint(0, 999999),
                file_ext)
            renamed_pathname = os.path.join(MEDIA_ROOT, renamed_filename)
            if not os.path.exists(renamed_pathname):
                break
        path_head, _ = os.path.split(renamed_pathname)
        if not os.path.exists(path_head):
            os.makedirs(path_head)
        return renamed_filename, renamed_pathname
