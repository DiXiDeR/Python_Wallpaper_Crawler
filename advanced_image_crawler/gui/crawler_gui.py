import asyncio
from PyQt5.QtWidgets import QMainWindow, QTextEdit, QPushButton, QVBoxLayout, QWidget
from PyQt5.QtCore import QThread, pyqtSignal
from src.crawler import AdvancedCrawler

class CrawlerThread(QThread):
    log_signal = pyqtSignal(str)
    
    def __init__(self, crawler: AdvancedCrawler):
        super().__init__()
        self.crawler = crawler

    def run(self):
        asyncio.run(self.crawler.run())

class CrawlerGUI(QMainWindow):
    def __init__(self, crawler: AdvancedCrawler):
        super().__init__()
        self.crawler = crawler
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Advanced Image Crawler")
        self.setGeometry(100, 100, 600, 400)

        self.log_view = QTextEdit(self)
        self.log_view.setReadOnly(True)

        self.start_btn = QPushButton('Start Crawling', self)
        self.start_btn.clicked.connect(self.start_crawling)

        self.pause_btn = QPushButton('Pause', self)
        self.pause_btn.clicked.connect(self.pause_crawling)

        self.resume_btn = QPushButton('Resume', self)
        self.resume_btn.clicked.connect(self.resume_crawling)

        layout = QVBoxLayout()
        layout.addWidget(self.log_view)
        layout.addWidget(self.start_btn)
        layout.addWidget(self.pause_btn)
        layout.addWidget(self.resume_btn)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

    def start_crawling(self):
        self.thread = CrawlerThread(self.crawler)
        self.thread.log_signal.connect(self.update_log)
        self.thread.start()

    def update_log(self, message: str):
        self.log_view.append(message)

    def pause_crawling(self):
        # Implement pause functionality
        pass

    def resume_crawling(self):
        # Implement resume functionality
        pass