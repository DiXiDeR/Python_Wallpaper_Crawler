import sys
from src.crawler import AdvancedCrawler
from gui.crawler_gui import CrawlerGUI
from PyQt5.QtWidgets import QApplication

def main():
    url = input("Enter URL to crawl: ")
    crawler = AdvancedCrawler(url)
    
    app = QApplication(sys.argv)
    gui = CrawlerGUI(crawler)
    gui.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()