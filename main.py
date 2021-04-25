import sys
import vk_api
import time
import requests
import os

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap, QImage, QIcon, QFont
from PyQt5.QtWidgets import QApplication, QMainWindow, QDialog, QLineEdit
from PyQt5.QtWidgets import QTableWidgetItem, QHeaderView, QLabel, QAbstractItemView
from PyQt5.QtWidgets import QMessageBox, QInputDialog, QPushButton, QTableWidget


class Auth(QMainWindow):
    def __init__(self):
        super().__init__()
        # main settings
        self.setFixedSize(280, 300)
        self.setWindowTitle('Авторизация ВКонтакте')
        self.setWindowIcon(QIcon('icons/main.png'))
        # buttons
        self.authButton = QPushButton('Auth', self)
        self.authButton.resize(137, 23)
        self.authButton.move(0, 254)
        self.authButton.clicked.connect(self.authorization)
        self.quitButton = QPushButton('Quit', self)
        self.quitButton.resize(137, 23)
        self.quitButton.move(142, 254)
        self.quitButton.clicked.connect(self.quit)
        # line edit
        self.login = QLineEdit(self)
        self.login.resize(210, 30)
        self.login.move(35, 120)
        self.login.setPlaceholderText('Телефон или E-Mail')
        self.password = QLineEdit(self)
        self.password.resize(210, 30)
        self.password.move(35, 160)
        self.password.setPlaceholderText('Пароль')
        self.password.setEchoMode(QLineEdit.Password)
        # labels
        self.label1 = QLabel(self)
        self.label1.setText('Авторизуйтесь ВКонтакте, чтобы продолжить.')
        self.label1.move(20, 80)
        self.label1.resize(280, 20)
        self.label2 = QLabel(self)
        self.label2.setText('PyVKDownloader')
        self.label2.setFont(QFont("", 20, QFont.Bold))
        self.label2.resize(280, 40)
        self.label2.move(0, 22)
        self.label2.setAlignment(Qt.AlignCenter)

    def get_html(self, url):
        r = requests.get(url)
        if r.ok:
            return r.text
        print(r.status_code)

    def auth_handler(self):
        text, ok = QInputDialog.getText(self, 'Two-Factor', 'Введите код:')
        if ok:
            key = str(text)
            remember_device = False
            return key, remember_device
        else:
            self.quit()

    def authorization(self):
        from vk_api import audio
        login, password = self.login.text().strip(), self.password.text().strip()
        try:
            auth = self.auth_handler
            self.vk_session = vk_api.VkApi(login, password, auth_handler=auth)
            self.vk_session.auth()
            self.vk = self.vk_session.get_api()
            self.user_id = self.vk.users.get()[0]['id']
            self.vk_audio = audio.VkAudio(self.vk_session)
            self.hide()
            self.main1 = Main(self.vk_session, self.user_id, self.vk_audio)
            self.main1.show()
        except Exception as e:
            e = f'Ошибка: {e}'
            self.statusBar().showMessage(e)

    def quit(self):
        self.close()


class Main(QMainWindow):
    def __init__(self, vk_session, user_id, vk_audio):
        super().__init__()
        # main settings
        self.setWindowTitle('PyVKDownloader')
        self.setFixedSize(710, 460)
        self.setWindowIcon(QIcon('icons/main.png'))
        # pixmap
        self.image = QImage('icons/warning.png')
        q = Qt.SmoothTransformation
        self.pixmap = QPixmap(self.image).scaledToHeight(32, q)
        # table
        self.table = QTableWidget(self)
        self.table.resize(690, 380)
        self.table.move(10, 10)
        self.table.setRowCount(0)
        self.table.setColumnCount(3)
        self.table.resizeRowsToContents()
        self.table.resizeColumnsToContents()
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.itemClicked.connect(self.changer_table)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.vk_session, self.user_id = vk_session, user_id
        self.vk_audio = vk_audio
        self.load_audio()

    def changer_table(self, item):
        row = item.row()
        self.currently = self.audio[row]
        if self.currently:
            self.statusBar().showMessage(f'Выбрана аудиозапись: '
                                          f'{self.currently["artist"]}'
                                          f' — {self.currently["title"]}')
        else:
            self.statusBar().showMessage('Аудиозапись не выбрана')

    def load_audio(self):
        self.audio = []
        for i in self.vk_audio.get(owner_id=f'{self.user_id}'):
            self.audio.append(i)
        for i in self.audio:
            self.view_data(i)
        self.currently = None

    def view_data(self, audio):
        title = audio['title']
        artist = audio['artist']
        url = audio['url']
        count = self.table.rowCount() + 1
        c1 = count - 1
        self.table.setRowCount(count)
        self.table.setHorizontalHeaderLabels(["Title", "Artist", "URL"])
        self.table.setItem(c1, 0, QTableWidgetItem(title))
        self.table.setItem(c1, 1, QTableWidgetItem(artist))
        self.button = QPushButton("Скачать")
        self.button.clicked.connect(self.download)
        self.table.setCellWidget(c1, 2, self.button)

    def download(self):
        i = self.currently
        if i:
            try:
                r = requests.get(i["url"])
                if r.status_code == 200:
                    with open(i["artist"] + ' — ' +
                              i["title"] + '.mp3', 'wb') as output_file:
                        output_file.write(r.content)
            except OSError:
                error = QMessageBox()
                error.setWindowIcon(QIcon('icons/error.png'))
                error.setWindowTitle(' ')
                image = QImage('icons/error.png')
                q = Qt.SmoothTransformation
                pixmap = QPixmap(image).scaledToHeight(32, q)
                error.setIconPixmap(pixmap)
                error.setText('<html><b style="font-size: 13px;">'
                              'Ошибка при сохранении файла!</b</html>')
                error.exec_()
            ok = QMessageBox()
            ok.setWindowIcon(QIcon('icons/ok.png'))
            ok.setWindowTitle(' ')
            image = QImage('icons/ok.png')
            q = Qt.SmoothTransformation
            pixmap = QPixmap(image).scaledToHeight(32, q)
            ok.setIconPixmap(pixmap)
            ok.setText('<html><b style="font-size: 13px;">'
                       'Скачано!</b</html>')
            ok.exec_()
        else:
            warning = QMessageBox()
            warning.setWindowIcon(QIcon('icons/warning.png'))
            warning.setWindowTitle(' ')
            warning.setIconPixmap(self.pixmap)
            warning.setText('<html><b style="font-size: 13px;">'
                            'Выберите аудиозапись!</b</html>')
            warning.exec_()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = Auth()
    ex.show()
    sys.exit(app.exec_())
