import os
import pickle
import re
import requests
import logging
import time

from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from telegram import InlineKeyboardMarkup
from bot.helper.telegram_helper import button_builder
from bot import  DRIVES_NAMES, DRIVES_IDS, INDEX_URLS, VIEW_LINK,  TITLE_NAME
from bot.helper.ext_utils.telegraph_helper import telegraph
from bot.helper.ext_utils.bot_utils import get_readable_file_size

LOGGER = logging.getLogger(__name__)
logging.getLogger('googleapiclient.discovery').setLevel(logging.ERROR)

SIZE_UNITS = ['B', 'KB', 'MB', 'GB', 'TB', 'PB']
TELEGRAPHLIMIT = 90

class GoogleDriveHelper:
    def __init__(self, name=None, listener=None):
        self.__G_DRIVE_TOKEN_FILE = "token.pickle"
        # Check https://developers.google.com/drive/scopes for all available scopes
        self.__OAUTH_SCOPE = ['https://www.googleapis.com/auth/drive']
        self.__service = self.authorize()
        self.telegraph_content = []
        self.path = []

    def get_readable_file_size(size_in_bytes) -> str:
        if size_in_bytes is None:
            return '0B'
        index = 0
        while size_in_bytes >= 1024:
            size_in_bytes /= 1024
            index += 1
        try:
            return f'{round(size_in_bytes, 2)}{SIZE_UNITS[index]}'
        except IndexError:
            return 'File too large'

    def authorize(self):
        # Get credentials
        credentials = None
        if os.path.exists(self.__G_DRIVE_TOKEN_FILE):
            with open(self.__G_DRIVE_TOKEN_FILE, 'rb') as f:
                credentials = pickle.load(f)
        if credentials is None or not credentials.valid:
            if credentials and credentials.expired and credentials.refresh_token:
                credentials.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    'credentials.json', self.__OAUTH_SCOPE)
                LOGGER.info(flow)
                credentials = flow.run_console(port=0)

            # Save the credentials for the next run
            with open(self.__G_DRIVE_TOKEN_FILE, 'wb') as token:
                pickle.dump(credentials, token)
        return build('drive', 'v3', credentials=credentials, cache_discovery=False)

    def get_recursive_list(self, file, rootid = "root"):
        rtnlist = []
        if not rootid:
            rootid = file.get('teamDriveId')
        if rootid == "root":
            rootid = self.__service.files().get(fileId = 'root', fields="id").execute().get('id')
        x = file.get("name")
        y = file.get("id")
        while(y != rootid):
            rtnlist.append(x)
            file = self.__service.files().get(
                fileId=file.get("parents")[0],
                supportsAllDrives=True,
                fields='id, name, parents'
            ).execute()
            x = file.get("name")
            y = file.get("id")
        rtnlist.reverse()
        return rtnlist

    def drive_query(self, parent_id, fileName, stopDup, isRecursive, itemType):
        try:
            if isRecursive:
                if stopDup:
                    query = f"name = '{fileName}' and "
                else:
                    fileName = fileName.split(' ')
                    query = "".join(
                        f"name contains '{name}' and "
                        for name in fileName
                        if name != ''
                    )
                    if itemType == "files":
                        query += "mimeType != 'application/vnd.google-apps.folder' and "
                    elif itemType == "folders":
                        query += "mimeType = 'application/vnd.google-apps.folder' and "
                query += "trashed = false"
                if parent_id == "root":
                    return (
                        self.__service.files()
                            .list(q=query + " and 'me' in owners",
                                  pageSize=200,
                                  spaces='drive',
                                  fields='files(id, name, mimeType, size, parents)',
                                  orderBy='folder, name asc'
                                  )
                            .execute()
                    )
                else:
                    return (
                        self.__service.files()
                            .list(supportsTeamDrives=True,
                                  includeTeamDriveItems=True,
                                  teamDriveId=parent_id,
                                  q=query,
                                  corpora='drive',
                                  spaces='drive',
                                  pageSize=200,
                                  fields='files(id, name, mimeType, size, teamDriveId, parents)',
                                  orderBy='folder, name asc'
                                  )
                            .execute()
                    )
            else:
                if stopDup:
                    query = f"'{parent_id}' in parents and name = '{fileName}' and "
                else:
                    query = f"'{parent_id}' in parents and "
                    fileName = fileName.split(' ')
                    for name in fileName:
                        if name != '':
                            query += f"name contains '{name}' and "
                    if itemType == "files":
                        query += "mimeType != 'application/vnd.google-apps.folder' and "
                    elif itemType == "folders":
                        query += "mimeType = 'application/vnd.google-apps.folder' and "
                query += "trashed = false"
                return (
                    self.__service.files()
                        .list(
                        supportsTeamDrives=True,
                        includeTeamDriveItems=True,
                        q=query,
                        spaces='drive',
                        pageSize=200,
                        fields='files(id, name, mimeType, size)',
                        orderBy='folder, name asc',
                    )
                        .execute()
                )
        except Exception as err:
            err = str(err).replace('>', '').replace('<', '')
            LOGGER.error(err)
            return {'files': []}

    def edit_telegraph(self):
        nxt_page = 1
        prev_page = 0
        for content in self.telegraph_content:
            if nxt_page == 1:
                content += f'<b><a href="https://telegra.ph/{self.path[nxt_page]}">Next</a></b>'
                nxt_page += 1
            else:
                if prev_page <= self.num_of_path:
                    content += f'<b><a href="https://telegra.ph/{self.path[prev_page]}">Prev</a></b>'
                    prev_page += 1
                if nxt_page < self.num_of_path:
                    content += f'<b> | <a href="https://telegra.ph/{self.path[nxt_page]}">Next</a></b>'
                    nxt_page += 1
            telegraph.edit_page(
                path=self.path[prev_page],
                title='Helios-search',
                content=content
            )
        return
    def escapes(self, str):
        chars = ['\\', "'", '"', r'\a', r'\b', r'\f', r'\n', r'\r', r'\s', r'\t']
        for char in chars:
            str = str.replace(char, ' ')
        return str

    def get_recursive_list(self, file, rootid = "root"):
        rtnlist = []
        if not rootid:
            rootid = file.get('teamDriveId')
        if rootid == "root":
            rootid = self.__service.files().get(fileId = 'root', fields="id").execute().get('id')
        x = file.get("name")
        y = file.get("id")
        while(y != rootid):
            rtnlist.append(x)
            file = self.__service.files().get(
                                            fileId=file.get("parents")[0],
                                            supportsAllDrives=True,
                                            fields='id, name, parents'
                                            ).execute()
            x = file.get("name")
            y = file.get("id")
        rtnlist.reverse()
        return rtnlist

    def drive_query(self, parent_id, fileName, stopDup, isRecursive , itemType):
        try:
            if isRecursive:
                if stopDup:
                    query = f"name = '{fileName}' and "
                else:
                    fileName = fileName.split(' ')
                    query = "".join(
                        f"name contains '{name}' and "
                        for name in fileName
                        if name != ''
                    )
                    if itemType == "files":
                        query += "mimeType != 'application/vnd.google-apps.folder' and "
                    elif itemType == "folders":
                        query += "mimeType = 'application/vnd.google-apps.folder' and "
                query += "trashed = false"
                if parent_id == "root":
                    return (
                        self.__service.files()
                        .list(q=query + " and 'me' in owners",
                            pageSize=200,
                            spaces='drive',
                            fields='files(id, name, mimeType, size, parents)',
                            orderBy='folder, name asc'
                        )
                        .execute()
                    )
                else:
                    return (
                        self.__service.files()
                        .list(supportsTeamDrives=True,
                            includeTeamDriveItems=True,
                            teamDriveId=parent_id,
                            q=query,
                            corpora='drive',
                            spaces='drive',
                            pageSize=200,
                            fields='files(id, name, mimeType, size, teamDriveId, parents)',
                            orderBy='folder, name asc'
                        )
                        .execute()
                    )
            else:
                if stopDup:
                    query = f"'{parent_id}' in parents and name = '{fileName}' and "
                else:
                    query = f"'{parent_id}' in parents and "
                    fileName = fileName.split(' ')
                    for name in fileName:
                        if name != '':
                            query += f"name contains '{name}' and "
                    if itemType == "files":
                        query += "mimeType != 'application/vnd.google-apps.folder' and "
                    elif itemType == "folders":
                        query += "mimeType = 'application/vnd.google-apps.folder' and "
                query += "trashed = false"
                return (
                    self.__service.files()
                    .list(
                        supportsTeamDrives=True,
                        includeTeamDriveItems=True,
                        q=query,
                        spaces='drive',
                        pageSize=200,
                        fields='files(id, name, mimeType, size)',
                        orderBy='folder, name asc',
                    )
                    .execute()
                )
        except Exception as err:
            err = str(err).replace('>', '').replace('<', '')
            LOGGER.error(err)
            return {'files': []}


    def drive_list(self, fileName, stopDup=False, noMulti=False, isRecursive=True, itemType=""):
        msg = ""
        if not stopDup:
            fileName = self.escapes(str(fileName))
        contents_count = 0
        Title = False
        if len(DRIVES_IDS) > 1:
            token_service = self.alt_authorize()
            if token_service is not None:
                self.__service = token_service
        for index, parent_id in enumerate(DRIVES_IDS):
            if isRecursive and len(parent_id) > 23:
                isRecur = False
            else:
                isRecur = isRecursive
            response = self.drive_query(parent_id, fileName, stopDup, isRecur, itemType)
            if not response["files"] and noMulti:
                break
            elif not response["files"]:
                continue
            if not Title:
                msg += f'<h4>Search Result For {fileName}</h4><br><br>'
                Title = True
            if len(DRIVES_NAMES) > 1 and DRIVES_NAMES[index] is not None:
                msg += f"╾────────────╼<br><b>{DRIVES_NAMES[index]}</b><br>╾────────────╼<br>"
            for file in response.get('files', []):
                mime_type = file.get('mimeType')
                if mime_type == "application/vnd.google-apps.folder":
                    furl = f"https://drive.google.com/drive/folders/{file.get('id')}"
                    msg += f"📁 <code>{file.get('name')}<br>(folder)</code><br>"
                    msg += f"<b><a href={furl}>Drive Link</a></b>"
                    if INDEX_URLS[index] is not None:
                        if isRecur:
                            url_path = "/".join(
                                [requests.utils.quote(n, safe='') for n in self.get_recursive_list(file, parent_id)])
                        else:
                            url_path = requests.utils.quote(f'{file.get("name")}')
                        url = f'{INDEX_URLS[index]}/{url_path}/'
                        msg += f' <b>| <a href="{url}">Index Link</a></b>'
                elif mime_type == 'application/vnd.google-apps.shortcut':
                    msg += f"⁍<a href='https://drive.google.com/drive/folders/{file.get('id')}'>{file.get('name')}" \
                           f"</a> (shortcut)"
                    # Excluded index link as indexes cant download or open these shortcuts
                else:
                    furl = f"https://drive.google.com/uc?id={file.get('id')}&export=download"
                    msg += f"📄 <code>{file.get('name')}<br>({get_readable_file_size(int(file.get('size', 0)))})</code><br>"
                    msg += f"<b><a href={furl}>Drive Link</a></b>"
                    if INDEX_URLS[index] is not None:
                        if isRecur:
                            url_path = "/".join(
                                requests.utils.quote(n, safe='')
                                for n in self.get_recursive_list(file, parent_id)
                            )

                        else:
                            url_path = requests.utils.quote(f'{file.get("name")}')
                        url = f'{INDEX_URLS[index]}/{url_path}'
                        msg += f' <b>| <a href="{url}">Index Link</a></b>'
                        if VIEW_LINK:
                            urls = f'{INDEX_URLS[index]}/{url_path}?a=view'
                            msg += f' <b>| <a href="{urls}">View Link</a></b>'
                msg += '<br><br>'
                contents_count += 1
                if len(msg.encode('utf-8')) > 40000:
                    self.telegraph_content.append(msg)
                    msg = ""
            if noMulti:
                break

        if msg != '':
            self.telegraph_content.append(msg)

        if len(self.telegraph_content) == 0:
            return "", None

        for content in self.telegraph_content:
            self.path.append(
                telegraph.create_page(
                    title=f'{TITLE_NAME}',
                    content=content
                )["path"]
            )
        time.sleep(0.5)
        self.num_of_path = len(self.path)
        if self.num_of_path > 1:
            self.edit_telegraph()

        msg = f"<b>Found {contents_count} result for <i>{fileName}</i></b>"
        buttons = button_builder.ButtonMaker()
        buttons.buildbutton("🔎 VIEW", f"https://telegra.ph/{self.path[0]}")

        return msg, InlineKeyboardMarkup(buttons.build_menu(1))
