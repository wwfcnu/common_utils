# Selenium4.0以上版本使用该方法
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

# 使用 ChromeDriverManager 安装 ChromeDriver，并返回驱动程序的路径
driver_path = ChromeDriverManager().install()
# 打印驱动程序的路径
print(driver_path)

# 创建 ChromeDriver 服务，并指定驱动程序的路径
service = Service(driver_path)
# 创建 Chrome WebDriver，并指定服务
driver = webdriver.Chrome(service=service)
# 打开百度网页
driver.get("https://www.baidu.com")
