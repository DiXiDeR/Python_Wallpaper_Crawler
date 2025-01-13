# Wallpaper Crawler

Wallpaper Crawler is an advanced web scraping tool designed to crawl websites and download high-resolution wallpapers. It supports multiple resolutions including 4K, 2K, and FullHD. The tool is built using Python and Selenium, and it features a user-friendly GUI for easy operation.

---

## Table of Contents

- [Features](#features)
- [Installation](#installation)

  - [Using `uv` Python Manager](#using-uv-python-manager)
  - [Using Standard Python Environment](#using-standard-python-environment)
- [Usage](#usage)
- [Configuration](#configuration)
- [Disclaimer](#disclaimer)
- [Contributing](#contributing)
- [License](#license)
- [Acknowledgements](#acknowledgements)

---



## Features

- **User-Friendly GUI**: Simple and intuitive interface built with Tkinter.
- **Resolution Selection**: Choose from 4K, 2K, FullHD, or download all available resolutions.
- **Depth Control**: Set the crawl depth to control how deep the crawler goes into the website.
- **Timeout Control**: Configure request timeout to handle slow-loading pages.
- **Pause and Resume**: Ability to pause and resume the crawling process.
- **Stop Crawling**: Safely stop the crawling process without losing data.
- **Advanced Logging**: Detailed logging for monitoring the crawling process.
- **User-Agent Rotation**: Randomly rotate user-agents to avoid detection.

## Installation

### Using `uv` Python Manager

1. **Install `uv`**:

   ```sh
   pip install uv
   ```
2. **Clone the repository**:

   ```sh
   git clone https://github.com/DiXiDeR/Python_Wallpaper_Crawler.git
   cd Python_Wallpaper_Crawler
   ```
3. **Create and activate a virtual environment using `uv`**:

   ```sh
   uv create
   uv activate
   ```
4. **Install the required dependencies**:

   ```sh
   uv pip install -r requirements.txt
   ```
5. **Download and install ChromeDriver**:

   - Ensure you have Google Chrome installed.
   - ChromeDriver will be automatically managed by `webdriver_manager`.

### Using Standard Python Environment

1. **Clone the repository**:

   ```sh
   git clone https://github.com/DiXiDeR/Python_Wallpaper_Crawler.git
   cd Python_Wallpaper_Crawler
   ```
2. **Create and activate a virtual environment**:

   ```sh
   python -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   ```
3. **Install the required dependencies**:

   ```sh
   pip install -r requirements.txt
   ```
4. **Download and install ChromeDriver**:

   - Ensure you have Google Chrome installed.
   - ChromeDriver will be automatically managed by `webdriver_manager`.

## Usage

1. **Run the application**:

   ```sh
   python wallpaper_crawler.py
   ```
2. **Enter the website URL**:

   - Input the URL of the website you want to crawl.
3. **Select the desired resolution**:

   - Choose from 4K, 2K, FullHD, or ALL.
4. **Set the crawl depth and timeout**:

   - Adjust the crawl depth (1-5) and request timeout (5-30 seconds).
5. **Start Crawling**:

   - Click on "Start Advanced Crawling" to begin the process.
   - Use "Pause Crawling" to pause and "Stop Crawling" to stop the process.

## Configuration

- **User Agents**:

  - User agents are managed in the **proxies.json** file.
  - Example structure:

  ```json
  {
      "user_agents": [
          "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
          "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.2 Safari/605.1.15",
          "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0",
          "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36",
          "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36"
      ]
  }
  ```

## Disclaimer

This project is created for **educational purposes** only. The author does not take **any responsibility** for any misuse of this tool. **Please ensure that you have permission to crawl and download content from the websites you use this tool on!**

## Contributing

[CONTRIBUTING](https://github.com/DiXiDeR/Python_Wallpaper_Crawler?tab=readme-ov-file#contributing)

We welcome contributions from the community! If you would like to contribute to this project, please follow these steps:

1. Fork the repository on GitHub.
2. Create a new branch for your feature or bugfix: `bash git checkout -b feature-name `
3. Make your changes and commit them with descriptive messages: `bash git commit -m "Add new feature" `
4. Push your changes to your forked repository: `bash git push origin feature-name `
5. Open a pull request on the main repository and provide a detailed description of your changes.

Please read the [CONTRIBUTING.md](https://github.com/DiXiDeR/Python_Wallpaper_Crawler/blob/master/CONTRIBUTING.md) for more detailed guidelines on how to contribute to this project.

## License

[LICENSE](https://github.com/DiXiDeR/Python_Wallpaper_Crawler?tab=readme-ov-file#license)

This project is licensed under the MIT License. You are free to use, modify, and distribute this software under the terms of the MIT License. See the [LICENSE](https://github.com/DiXiDeR/fredon_librarer/blob/master/LICENSE) file for more details.

## Contact

[CONTACT](https://github.com/DiXiDeR/Python_Wallpaper_Crawler?tab=readme-ov-file#contact)

If you have any questions, suggestions, or feedback, please feel free to open an issue on GitHub or contact the maintainer at [onlyfredon@proton.me](mailto:onlyfredon@proton.me). We appreciate your input and look forward to improving Fredon Optimizer with your help.

Contributions are welcome! Please fork the repository and create a pull request with your changes. Ensure your code follows the project's coding standards and includes appropriate tests.

## License

This project is licensed under the MIT License. See the LICENSE file for details.

## Acknowledgements

- [Selenium](https://www.selenium.dev/)
- [Tkinter](https://docs.python.org/3/library/tkinter.html)
- [webdriver_manager](https://github.com/SergeyPirogov/webdriver_manager)
- [Pillow](https://python-pillow.org/)

---

# **HAPPY CRAWLING!**

> ##### ***Fredon IT Ventures***
