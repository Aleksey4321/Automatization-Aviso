#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Aviso YouTube Tasks Automation Script v2.0 - Termux Fixed
Автоматизация выполнения заданий по просмотру YouTube видео на сайте Aviso.bz

Исправления v2.0:
- Убрано подтверждение запуска
- Фиксированный User-Agent для каждого аккаунта
- Улучшенная установка Tor для Termux/Android
- Улучшенная обработка ошибок
- Автоматическая обработка кода подтверждения

Требования:
- Python 3.7+
- Termux/Android/Linux/Windows/macOS
- Интернет соединение

Автор: Automated Script Generator
Дата: 2025-07-09
"""

import os
import sys
import time
import random
import json
import logging
import subprocess
import platform
import re
import pickle
import hashlib
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Optional, Tuple
import math

# Попытка импорта необходимых библиотек с автоустановкой
def install_requirements():
    """Автоматическая установка необходимых зависимостей"""
    required_packages = [
        'seleniumbase',
        'selenium',
        'requests',
        'beautifulsoup4',
        'fake-useragent',
        'undetected-chromedriver',
        'selenium-stealth'
    ]
    
    logging.info("📦 Проверка и установка зависимостей...")
    
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
            logging.info(f"✓ Пакет {package} уже установлен")
        except ImportError:
            logging.info(f"⚠ Устанавливаю пакет {package}...")
            try:
                subprocess.check_call([sys.executable, "-m", "pip", "install", package], 
                                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                logging.info(f"✓ Пакет {package} успешно установлен")
            except subprocess.CalledProcessError as e:
                logging.error(f"✗ Ошибка установки пакета {package}: {e}")
                # Пробуем альтернативные методы установки
                try:
                    logging.info(f"🔄 Попытка альтернативной установки {package}...")
                    subprocess.check_call([sys.executable, "-m", "pip", "install", "--user", package],
                                        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    logging.info(f"✓ Пакет {package} установлен через --user")
                except subprocess.CalledProcessError:
                    logging.warning(f"⚠ Не удалось установить {package}, но продолжаем...")

# Настройка базового логирования до установки зависимостей
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)

# Установка зависимостей
install_requirements()

# Импорт после установки
try:
    from seleniumbase import Driver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.common.action_chains import ActionChains
    from selenium.webdriver.chrome.options import Options
    from selenium.common.exceptions import *
    from selenium.webdriver.common.keys import Keys
    import requests
    from bs4 import BeautifulSoup
    from fake_useragent import UserAgent
except ImportError as e:
    logging.error(f"❌ Критическая ошибка импорта: {e}")
    logging.error("📋 Попробуйте установить зависимости вручную:")
    logging.error("pip install seleniumbase selenium requests beautifulsoup4 fake-useragent")
    sys.exit(1)

class UserAgentManager:
    """Класс для управления User-Agent для каждого аккаунта"""
    
    def __init__(self):
        self.ua_file = "user_agents.json"
        self.user_agents = self.load_user_agents()
        
    def load_user_agents(self) -> Dict[str, str]:
        """Загрузка сохраненных User-Agent'ов"""
        try:
            if os.path.exists(self.ua_file):
                with open(self.ua_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            logging.debug(f"⚠ Ошибка загрузки User-Agent'ов: {e}")
        
        return {}
    
    def save_user_agents(self):
        """Сохранение User-Agent'ов"""
        try:
            with open(self.ua_file, 'w', encoding='utf-8') as f:
                json.dump(self.user_agents, f, indent=2, ensure_ascii=False)
            logging.debug("💾 User-Agent'ы сохранены")
        except Exception as e:
            logging.error(f"✗ Ошибка сохранения User-Agent'ов: {e}")
    
    def get_user_agent(self, username: str) -> str:
        """Получение User-Agent для конкретного пользователя"""
        # Создаем уникальный ключ для пользователя
        user_key = hashlib.md5(username.encode()).hexdigest()
        
        if user_key not in self.user_agents:
            # Генерируем новый User-Agent для этого пользователя
            try:
                ua = UserAgent()
                new_user_agent = ua.random
                self.user_agents[user_key] = new_user_agent
                self.save_user_agents()
                logging.info(f"🎭 Создан новый User-Agent для пользователя {username}")
            except Exception as e:
                logging.warning(f"⚠ Ошибка генерации User-Agent: {e}")
                # Фоллбэк User-Agent
                self.user_agents[user_key] = "Mozilla/5.0 (Linux; Android 12; SM-G991B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36"
        
        user_agent = self.user_agents[user_key]
        logging.info(f"🎭 Используется User-Agent для {username}: {user_agent[:50]}...")
        return user_agent

class HumanBehaviorSimulator:
    """Класс для имитации человеческого поведения"""
    
    @staticmethod
    def random_sleep(min_seconds: float = 0.5, max_seconds: float = 3.0):
        """Случайная пауза"""
        sleep_time = random.uniform(min_seconds, max_seconds)
        logging.debug(f"💤 Пауза {sleep_time:.2f} секунд")
        time.sleep(sleep_time)
    
    @staticmethod
    def generate_bezier_curve(start: Tuple[int, int], end: Tuple[int, int], 
                            control_points: int = 3) -> List[Tuple[int, int]]:
        """Генерация кривой Безье для движения мыши"""
        def bezier_point(t: float, points: List[Tuple[int, int]]) -> Tuple[int, int]:
            n = len(points) - 1
            x = sum(math.comb(n, i) * (1-t)**(n-i) * t**i * points[i][0] for i in range(n+1))
            y = sum(math.comb(n, i) * (1-t)**(n-i) * t**i * points[i][1] for i in range(n+1))
            return int(x), int(y)
        
        # Создаем контрольные точки
        control_pts = [start]
        for _ in range(control_points):
            x = random.randint(min(start[0], end[0]), max(start[0], end[0]))
            y = random.randint(min(start[1], end[1]), max(start[1], end[1]))
            control_pts.append((x, y))
        control_pts.append(end)
        
        # Генерируем точки кривой
        curve_points = []
        steps = random.randint(20, 50)
        for i in range(steps + 1):
            t = i / steps
            point = bezier_point(t, control_pts)
            curve_points.append(point)
        
        return curve_points
    
    @staticmethod
    def human_like_typing(element, text: str, driver):
        """Имитация человеческого набора текста"""
        element.clear()
        HumanBehaviorSimulator.random_sleep(0.2, 0.8)
        
        for char in text:
            element.send_keys(char)
            # Случайные паузы между символами
            time.sleep(random.uniform(0.05, 0.3))
            
            # Иногда делаем ошибки и исправляем их
            if random.random() < 0.05:  # 5% вероятность ошибки
                wrong_char = random.choice('abcdefghijklmnopqrstuvwxyz')
                element.send_keys(wrong_char)
                time.sleep(random.uniform(0.1, 0.5))
                element.send_keys(Keys.BACKSPACE)
                element.send_keys(Keys.BACKSPACE)
                element.send_keys(char)
        
        HumanBehaviorSimulator.random_sleep(0.3, 1.0)

class TorManager:
    """Класс для управления Tor соединением"""
    
    def __init__(self):
        self.tor_port = 9050
        self.control_port = 9051
        self.tor_process = None
        self.system = platform.system().lower()
        self.is_termux = self.detect_termux()
        
        # Пути к временным файлам (будут установлены при запуске)
        self.tor_data_dir = None
        self.torrc_path = None
        self.stdout_log = None
        self.stderr_log = None
        
    def detect_termux(self) -> bool:
        """Определение запуска в Termux"""
        return 'com.termux' in os.environ.get('PREFIX', '') or \
               '/data/data/com.termux' in os.environ.get('HOME', '')
    
    def command_exists(self, cmd: str) -> bool:
        """Проверка существования команды"""
        try:
            if self.is_termux or self.system == 'linux':
                result = subprocess.run(['command', '-v', cmd], 
                                      capture_output=True, text=True, shell=True)
                return result.returncode == 0
            elif self.system == 'windows':
                result = subprocess.run(['where', cmd], 
                                      capture_output=True, text=True)
                return result.returncode == 0
            else:  # macOS
                result = subprocess.run(['which', cmd], 
                                      capture_output=True, text=True)
                return result.returncode == 0
        except:
            return False
    
    def install_tor_termux(self) -> bool:
        """Установка Tor в Termux"""
        try:
            logging.info("📱 Установка Tor в Termux...")
            
            # Обновление пакетов
            logging.info("🔄 Обновление списка пакетов...")
            subprocess.run(['pkg', 'update'], check=True, 
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            
            # Установка Tor
            logging.info("📦 Установка Tor...")
            subprocess.run(['pkg', 'install', '-y', 'tor'], check=True,
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            
            logging.info("✓ Tor успешно установлен в Termux")
            return True
            
        except subprocess.CalledProcessError as e:
            logging.error(f"✗ Ошибка установки Tor в Termux: {e}")
            return False
        except Exception as e:
            logging.error(f"✗ Неожиданная ошибка установки Tor в Termux: {e}")
            return False
    
    def install_tor_linux(self) -> bool:
        """Установка Tor в Linux"""
        try:
            logging.info("🐧 Установка Tor в Linux...")
            
            # Проверяем менеджер пакетов
            if self.command_exists('apt-get'):
                logging.info("📦 Используется apt-get...")
                subprocess.run(['sudo', 'apt-get', 'update'], check=True,
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                subprocess.run(['sudo', 'apt-get', 'install', '-y', 'tor'], check=True,
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            elif self.command_exists('yum'):
                logging.info("📦 Используется yum...")
                subprocess.run(['sudo', 'yum', 'install', '-y', 'tor'], check=True,
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            elif self.command_exists('dnf'):
                logging.info("📦 Используется dnf...")
                subprocess.run(['sudo', 'dnf', 'install', '-y', 'tor'], check=True,
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            elif self.command_exists('pacman'):
                logging.info("📦 Используется pacman...")
                subprocess.run(['sudo', 'pacman', '-S', '--noconfirm', 'tor'], check=True,
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            else:
                logging.error("✗ Неизвестный менеджер пакетов Linux")
                return False
            
            logging.info("✓ Tor успешно установлен в Linux")
            return True
            
        except subprocess.CalledProcessError as e:
            logging.error(f"✗ Ошибка установки Tor в Linux: {e}")
            return False
        except Exception as e:
            logging.error(f"✗ Неожиданная ошибка установки Tor в Linux: {e}")
            return False
    
    def install_tor_windows(self) -> bool:
        """Установка Tor в Windows"""
        try:
            logging.info("🪟 Для Windows необходимо установить Tor Browser вручную")
            logging.info("📋 Скачайте Tor Browser с: https://www.torproject.org/download/")
            logging.info("⚠ После установки перезапустите скрипт")
            return False
        except Exception as e:
            logging.error(f"✗ Ошибка в процессе Windows Tor: {e}")
            return False
    
    def install_tor_macos(self) -> bool:
        """Установка Tor в macOS"""
        try:
            logging.info("🍎 Установка Tor в macOS...")
            
            if self.command_exists('brew'):
                logging.info("📦 Используется Homebrew...")
                subprocess.run(['brew', 'install', 'tor'], check=True,
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                logging.info("✓ Tor успешно установлен через Homebrew")
                return True
            else:
                logging.info("📦 Установка Homebrew...")
                install_homebrew = '/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"'
                subprocess.run(install_homebrew, shell=True, check=True)
                
                subprocess.run(['brew', 'install', 'tor'], check=True,
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                logging.info("✓ Tor успешно установлен")
                return True
                
        except subprocess.CalledProcessError as e:
            logging.error(f"✗ Ошибка установки Tor в macOS: {e}")
            return False
        except Exception as e:
            logging.error(f"✗ Неожиданная ошибка установки Tor в macOS: {e}")
            return False
    
    def install_tor(self) -> bool:
        """Автоматическая установка Tor"""
        if self.is_termux:
            return self.install_tor_termux()
        elif self.system == 'linux':
            return self.install_tor_linux()
        elif self.system == 'windows':
            return self.install_tor_windows()
        elif self.system == 'darwin':
            return self.install_tor_macos()
        else:
            logging.error(f"✗ Неподдерживаемая система: {self.system}")
            return False
    
    def check_tor_port(self) -> bool:
        """Быстрая проверка доступности порта Tor"""
        import socket
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(2)
                result = s.connect_ex(('127.0.0.1', self.tor_port))
                return result == 0
        except Exception as e:
            logging.debug(f"⚠ Ошибка проверки порта Tor: {e}")
            return False

    def is_tor_running(self) -> bool:
        """Проверка работы Tor"""
        # Сначала быстрая проверка порта
        if not self.check_tor_port():
            logging.debug("⚠ Tor порт недоступен")
            return False
        
        try:
            # Проверяем через простой HTTP запрос с коротким таймаутом
            response = requests.get(
                'http://check.torproject.org/api/ip',
                proxies={
                    'http': f'socks5://127.0.0.1:{self.tor_port}',
                    'https': f'socks5://127.0.0.1:{self.tor_port}'
                },
                timeout=10
            )
            data = response.json()
            is_tor = data.get('IsTor', False)
            if is_tor:
                logging.info("✓ Tor соединение активно")
            else:
                logging.debug("⚠ Tor соединение не активно")
            return is_tor
        except requests.exceptions.Timeout:
            logging.debug("⚠ Таймаут проверки Tor, но порт доступен")
            return True
        except Exception as e:
            logging.debug(f"⚠ Ошибка проверки Tor: {e}")
            return True
    
    def find_tor_executable(self) -> Optional[str]:
        """Поиск исполняемого файла Tor"""
        possible_paths = []
        
        if self.is_termux:
            possible_paths = [
                '/data/data/com.termux/files/usr/bin/tor',
                f"{os.environ.get('PREFIX', '')}/bin/tor"
            ]
        elif self.system == 'linux':
            possible_paths = [
                '/usr/bin/tor',
                '/usr/local/bin/tor',
                '/opt/tor/bin/tor'
            ]
        elif self.system == 'windows':
            username = os.getenv('USERNAME', 'User')
            possible_paths = [
                f"C:\\Users\\{username}\\Desktop\\Tor Browser\\Browser\\TorBrowser\\Tor\\tor.exe",
                r"C:\Program Files\Tor Browser\Browser\TorBrowser\Tor\tor.exe",
                r"C:\Program Files (x86)\Tor Browser\Browser\TorBrowser\Tor\tor.exe",
                r"C:\Tor\tor.exe"
            ]
        elif self.system == 'darwin':
            possible_paths = [
                '/usr/local/bin/tor',
                '/opt/homebrew/bin/tor',
                '/Applications/Tor Browser.app/Contents/MacOS/Tor/tor'
            ]
        
        # Проверяем каждый путь
        for path in possible_paths:
            if os.path.exists(path) and os.access(path, os.X_OK):
                logging.info(f"✓ Найден Tor: {path}")
                return path
        
        # Проверяем через PATH
        if self.command_exists('tor'):
            logging.info("✓ Tor найден в PATH")
            return 'tor'
        
        return None
    
    def find_free_port(self, start_port: int) -> int:
        """Поиск свободного порта начиная с указанного"""
        import socket
        
        for port in range(start_port, start_port + 100):
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.bind(('127.0.0.1', port))
                    return port
            except OSError:
                continue
        
        # Если не нашли свободный порт, возвращаем случайный
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(('127.0.0.1', 0))
            return s.getsockname()[1]

    def log_tor_errors(self):
        """Вывод ошибок Tor из логов"""
        try:
            stderr_log = getattr(self, 'stderr_log', './tor_stderr.log')
            stdout_log = getattr(self, 'stdout_log', './tor_stdout.log')
            
            if os.path.exists(stderr_log):
                with open(stderr_log, "r") as f:
                    stderr_content = f.read().strip()
                    if stderr_content:
                        logging.error(f"📋 Ошибки Tor: {stderr_content}")
            
            if os.path.exists(stdout_log):
                with open(stdout_log, "r") as f:
                    stdout_content = f.read().strip()
                    if stdout_content:
                        logging.info(f"📋 Вывод Tor: {stdout_content}")
        except Exception as e:
            logging.debug(f"⚠ Ошибка чтения логов Tor: {e}")
    
    def start_tor(self) -> bool:
        """Запуск Tor с простой конфигурацией"""
        # Быстрая проверка через порт
        if self.check_tor_port():
            logging.info("✓ Tor уже запущен (порт доступен)")
            return True
        
        logging.info("🔄 Запуск Tor...")
        
        # Поиск Tor
        tor_executable = self.find_tor_executable()
        
        if not tor_executable:
            logging.info("⚠ Tor не найден, попытка установки...")
            if self.install_tor():
                tor_executable = self.find_tor_executable()
                if not tor_executable:
                    logging.error("✗ Tor не найден даже после установки")
                    return False
            else:
                logging.error("✗ Не удалось установить Tor")
                return False
        
        try:
            # Убиваем существующие процессы Tor
            try:
                if self.is_termux:
                    subprocess.run(['pkill', '-f', 'tor'], capture_output=True)
                else:
                    subprocess.run(['killall', 'tor'], capture_output=True)
                time.sleep(2)
            except:
                pass
            
            # Найдем свободные порты
            self.tor_port = self.find_free_port(9050)
            self.control_port = self.find_free_port(9051)
            
            logging.info(f"🔌 Используем порты: SOCKS={self.tor_port}, Control={self.control_port}")
            
            # Создаем временную директорию для данных Tor
            import tempfile
            import getpass
            
            try:
                current_user = getpass.getuser()
            except:
                current_user = "user"
            
            temp_dir = tempfile.gettempdir()
            tor_data_dir = os.path.join(temp_dir, f"tor_data_{current_user}_{os.getpid()}")
            
            # Полностью удаляем старую директорию если существует
            if os.path.exists(tor_data_dir):
                import shutil
                shutil.rmtree(tor_data_dir, ignore_errors=True)
            
            # Создаем новую директорию
            os.makedirs(tor_data_dir, mode=0o700, exist_ok=True)
            
            logging.info(f"📁 Используется директория данных Tor: {tor_data_dir}")
            
            # ПРОСТАЯ конфигурация Tor без мостов
            tor_config = f"""
SocksPort {self.tor_port}
ControlPort {self.control_port}
DataDirectory {tor_data_dir}
Log notice stdout
"""
            
            # Записываем конфиг во временную директорию
            torrc_path = os.path.join(temp_dir, f"torrc_temp_{os.getpid()}")
            with open(torrc_path, "w") as f:
                f.write(tor_config)
            
            # Запускаем Tor
            cmd = [tor_executable, "-f", torrc_path]
            
            logging.info(f"🚀 Запуск Tor: {' '.join(cmd)}")
            
            # Создаем файлы для логов
            stdout_log = os.path.join(temp_dir, f"tor_stdout_{os.getpid()}.log")
            stderr_log = os.path.join(temp_dir, f"tor_stderr_{os.getpid()}.log")
            
            with open(stdout_log, "w") as stdout_file, \
                 open(stderr_log, "w") as stderr_file:
                
                if self.system == 'windows':
                    self.tor_process = subprocess.Popen(
                        cmd,
                        stdout=stdout_file,
                        stderr=stderr_file,
                        creationflags=subprocess.CREATE_NEW_PROCESS_GROUP
                    )
                else:
                    self.tor_process = subprocess.Popen(
                        cmd,
                        stdout=stdout_file,
                        stderr=stderr_file,
                        preexec_fn=os.setsid
                    )
            
            # Сохраняем пути для очистки
            self.tor_data_dir = tor_data_dir
            self.torrc_path = torrc_path
            self.stdout_log = stdout_log
            self.stderr_log = stderr_log
            
            # Ждем запуска Tor
            logging.info("⏳ Ожидание запуска Tor...")
            port_ready = False
            
            for i in range(30):  # 30 попыток по 2 секунды = 1 минута
                time.sleep(2)
                
                # Проверяем что процесс еще жив
                if self.tor_process.poll() is not None:
                    logging.error(f"✗ Процесс Tor завершился с кодом {self.tor_process.poll()}")
                    self.log_tor_errors()
                    return False
                
                if self.check_tor_port():
                    logging.info("✓ Tor порт готов")
                    port_ready = True
                    break
                    
                if i % 5 == 0:  # Каждые 10 секунд
                    logging.info(f"⏳ Ожидание порта Tor... ({i*2}/60 секунд)")
            
            if not port_ready:
                logging.error("✗ Tor порт не запустился в течение отведенного времени")
                self.log_tor_errors()
                return False
            
            # Проверяем интернет соединение
            logging.info("🌐 Проверка интернет соединения через Tor...")
            for attempt in range(3):  # 3 попытки
                if self.is_tor_running():
                    logging.info("✅ Tor успешно запущен и проверен")
                    return True
                time.sleep(5)  # Ждем между попытками
            
            logging.warning("⚠ Tor запущен, но интернет соединение не подтверждено. Продолжаем...")
            return True  # Все равно возвращаем True, так как порт работает
            
        except Exception as e:
            logging.error(f"✗ Ошибка запуска Tor: {e}")
            self.log_tor_errors()
            return False
    
    def stop_tor(self):
        """Остановка Tor"""
        try:
            if self.tor_process:
                logging.info("🛑 Остановка Tor...")
                
                if self.system == 'windows':
                    self.tor_process.terminate()
                else:
                    try:
                        os.killpg(os.getpgid(self.tor_process.pid), 15)  # SIGTERM
                    except:
                        self.tor_process.terminate()
                
                # Ждем завершения
                try:
                    self.tor_process.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    if self.system == 'windows':
                        self.tor_process.kill()
                    else:
                        try:
                            os.killpg(os.getpgid(self.tor_process.pid), 9)  # SIGKILL
                        except:
                            self.tor_process.kill()
                    
                    self.tor_process.wait(timeout=5)
                
                self.tor_process = None
                logging.info("✓ Tor остановлен")
                
            # Очистка временных файлов
            temp_files = [
                getattr(self, 'torrc_path', './torrc_temp'),
                getattr(self, 'stdout_log', './tor_stdout.log'),
                getattr(self, 'stderr_log', './tor_stderr.log')
            ]
            
            for temp_file in temp_files:
                try:
                    if os.path.exists(temp_file):
                        os.remove(temp_file)
                        logging.debug(f"🗑 Удален файл: {temp_file}")
                except Exception as e:
                    logging.debug(f"⚠ Ошибка удаления {temp_file}: {e}")
            
            # Очистка директории данных
            tor_data_dir = getattr(self, 'tor_data_dir', './tor_data')
            try:
                if os.path.exists(tor_data_dir):
                    import shutil
                    shutil.rmtree(tor_data_dir, ignore_errors=True)
                    logging.debug(f"🗑 Удалена директория: {tor_data_dir}")
            except Exception as e:
                logging.debug(f"⚠ Ошибка удаления директории {tor_data_dir}: {e}")
                    
        except Exception as e:
            logging.debug(f"⚠ Ошибка остановки Tor: {e}")

class AvisoAutomation:
    """Основной класс автоматизации Aviso"""
    
    def __init__(self):
        self.setup_logging()
        self.driver = None
        self.tor_manager = TorManager()
        self.ua_manager = UserAgentManager()
        self.cookies_file = "aviso_cookies.pkl"
        self.backup_counter = 1
        
        # Данные для авторизации
        self.username = "Aleksey345"
        self.password = "123456"
        self.base_url = "https://aviso.bz"
        
        logging.info("🚀 Инициализация Aviso Automation Bot v2.0")
        
    def setup_logging(self):
        """Настройка детального логирования"""
        # Создаем имя файла с текущей датой и временем
        log_filename = f"aviso_bot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        
        # Настраиваем логирование
        log_format = "%(asctime)s [%(levelname)s] %(message)s"
        
        # Удаляем существующие обработчики
        for handler in logging.root.handlers[:]:
            logging.root.removeHandler(handler)
        
        # Добавляем новые обработчики
        logging.basicConfig(
            level=logging.DEBUG,
            format=log_format,
            handlers=[
                logging.StreamHandler(sys.stdout),
                logging.FileHandler(log_filename, encoding='utf-8')
            ]
        )
        
        logging.info(f"📝 Логирование настроено: {log_filename}")
        
    def create_backup(self, version_info: str):
        """Создание резервной копии скрипта"""
        try:
            script_name = os.path.basename(__file__)
            backup_name = f"aviso_automation_v{self.backup_counter}_{version_info}.py"
            
            with open(script_name, 'r', encoding='utf-8') as original:
                with open(backup_name, 'w', encoding='utf-8') as backup:
                    backup.write(original.read())
            
            logging.info(f"💾 Создана резервная копия: {backup_name}")
            self.backup_counter += 1
            
        except Exception as e:
            logging.error(f"✗ Ошибка создания резервной копии: {e}")
    
    def setup_driver(self) -> bool:
        """Настройка и запуск браузера с Tor"""
        logging.info("🌐 Настройка браузера...")
        
        # Запуск Tor ОБЯЗАТЕЛЬНО
        if not self.tor_manager.start_tor():
            logging.error("✗ Не удалось запустить Tor")
            logging.error("❌ РАБОТА БЕЗ TOR ЗАПРЕЩЕНА!")
            return False
        
        try:
            # Получаем фиксированный User-Agent для этого аккаунта
            user_agent = self.ua_manager.get_user_agent(self.username)
            
            # ВАЖНО: Используем socks5:// префикс для SeleniumBase
            proxy_string = f"socks5://127.0.0.1:{self.tor_manager.tor_port}"
            logging.info(f"🔌 Используется Tor прокси: {proxy_string}")
            
            # КРИТИЧЕСКИ ВАЖНО: Устанавливаем переменные окружения для принудительного использования прокси
            logging.info("🔒 Установка переменных окружения для принудительного использования прокси...")
            proxy_env = {
                'HTTP_PROXY': proxy_string,
                'HTTPS_PROXY': proxy_string,
                'SOCKS_PROXY': proxy_string,
                'ALL_PROXY': proxy_string,
                'http_proxy': proxy_string,
                'https_proxy': proxy_string,
                'socks_proxy': proxy_string,
                'all_proxy': proxy_string
            }
            
            # Применяем переменные окружения
            for env_var, proxy_value in proxy_env.items():
                os.environ[env_var] = proxy_value
                logging.debug(f"✓ Установлена переменная окружения: {env_var}={proxy_value}")
            
            # Создаем расширенные аргументы Chrome для SOCKS прокси
            chrome_args = [
                f"--proxy-server={proxy_string}",  # Основной SOCKS5 прокси
                "--proxy-bypass-list=<-loopback>",  # Исключаем localhost из прокси  
                "--host-resolver-rules=MAP * ~NOTFOUND , EXCLUDE 127.0.0.1",  # Принудительное использование прокси для DNS
                "--disable-web-security",
                "--disable-features=VizDisplayCompositor",
                "--allow-running-insecure-content",
                "--ignore-certificate-errors",
                "--ignore-ssl-errors",
                "--ignore-certificate-errors-spki-list",
                "--ignore-certificate-errors-skip-list",
                "--disable-dev-shm-usage",
                "--no-sandbox",
                "--disable-gpu",
                "--disable-extensions",
                "--disable-background-networking",  # Отключаем фоновые соединения
                "--disable-background-timer-throttling",  # Отключаем фоновые таймеры
                "--disable-renderer-backgrounding",  # Отключаем фоновые процессы рендеринга
                "--disable-backgrounding-occluded-windows",  # Отключаем фоновые окна
                "--disable-ipc-flooding-protection",  # Отключаем защиту от флуда IPC
                "--disable-default-apps",  # Отключаем приложения по умолчанию
                "--no-default-browser-check",  # Отключаем проверку браузера по умолчанию
                "--no-first-run",  # Отключаем первый запуск
                "--disable-sync"  # Отключаем синхронизацию
            ]
            
            # Для Termux добавляем дополнительные настройки
            if self.tor_manager.is_termux:
                chrome_args.extend([
                    "--single-process",
                    "--no-zygote"
                ])
            
            # Инициализация драйвера SeleniumBase с DUAL прокси конфигурацией
            # Используем И proxy параметр И chromium_arg для максимальной надежности
            logging.info("🚀 Инициализация браузера с ДВОЙНОЙ прокси конфигурацией...")
            self.driver = Driver(
                uc=True,  # Undetected Chrome
                headless=False,  # Показываем браузер
                agent=user_agent,  # User-Agent
                proxy=proxy_string,  # ОСНОВНОЙ способ передачи прокси в SeleniumBase
                chromium_arg=" ".join(chrome_args)  # ДОПОЛНИТЕЛЬНЫЙ способ через аргументы Chrome
            )
            
            # Устанавливаем таймауты
            self.driver.set_page_load_timeout(45)  # Увеличиваем таймаут
            self.driver.implicitly_wait(15)
            
            # Дополнительные настройки для скрытия автоматизации
            try:
                self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            except Exception as e:
                logging.debug(f"⚠ Не удалось скрыть webdriver: {e}")
            
            # КРИТИЧЕСКИ ВАЖНАЯ проверка соединения с детальной диагностикой
            logging.info("🔍 УСИЛЕННАЯ проверка Tor соединения с IP-диагностикой...")
            
            # Сначала получим оригинальный IP для сравнения (через системные библиотеки)
            original_ip = None
            try:
                import requests
                # Делаем запрос БЕЗ прокси для получения оригинального IP
                original_response = requests.get("https://httpbin.org/ip", timeout=10)
                if original_response.status_code == 200:
                    original_data = original_response.json()
                    original_ip = original_data.get('origin', '').split(',')[0].strip()
                    logging.info(f"🌐 Оригинальный IP (без прокси): {original_ip}")
            except Exception as e:
                logging.warning(f"⚠ Не удалось получить оригинальный IP: {e}")
            
            try:
                # Тест 1: Проверяем что страница вообще загружается
                logging.info("📡 Тест 1: Базовая проверка загрузки...")
                self.driver.get("https://www.google.com")
                self.driver.sleep(10)
                
                page_content = self.driver.get_page_source()
                page_title = self.driver.get_title()
                
                logging.info(f"📄 Заголовок страницы: {page_title}")
                logging.info(f"📄 Размер контента: {len(page_content)} символов")
                
                # Проверяем что контент действительно загрузился
                if len(page_content) < 1000:
                    logging.error("❌ Тест 1 ПРОВАЛЕН: Слишком мало контента (страница не загрузилась)")
                    logging.error(f"📋 Содержимое: {page_content[:500]}...")
                    return False
                
                if "google" not in page_content.lower():
                    logging.error("❌ Тест 1 ПРОВАЛЕН: Google контент не найден")
                    logging.error(f"📋 Содержимое: {page_content[:500]}...")
                    return False
                
                logging.info("✅ Тест 1 ПРОЙДЕН: Базовая загрузка работает")
                
                # Тест 2: КРИТИЧЕСКАЯ проверка IP через браузер
                logging.info("📡 Тест 2: КРИТИЧЕСКАЯ проверка IP через браузер...")
                self.driver.get("https://httpbin.org/ip")
                self.driver.sleep(10)
                
                ip_content = self.driver.get_page_source()
                logging.info(f"📍 IP ответ (полный): {ip_content[:300]}...")
                
                current_ip = None
                if "origin" in ip_content.lower():
                    # Извлекаем IP из JSON ответа
                    try:
                        import json
                        import re
                        
                        # Ищем JSON в содержимом страницы
                        json_match = re.search(r'\{[^}]*"origin"[^}]*\}', ip_content)
                        if json_match:
                            json_data = json.loads(json_match.group())
                            current_ip = json_data.get('origin', '').split(',')[0].strip()
                        else:
                            # Альтернативный поиск IP
                            ip_match = re.search(r'"origin":\s*"([^"]+)"', ip_content)
                            if ip_match:
                                current_ip = ip_match.group(1).split(',')[0].strip()
                            
                    except Exception as e:
                        logging.warning(f"⚠ Ошибка парсинга IP: {e}")
                
                if current_ip:
                    logging.info(f"🌐 Текущий IP (через браузер): {current_ip}")
                    
                    # КРИТИЧЕСКАЯ проверка: IP должен измениться
                    if original_ip and current_ip == original_ip:
                        logging.error("❌ IP НЕ ИЗМЕНИЛСЯ! Tor НЕ РАБОТАЕТ!")
                        logging.error(f"❌ Оригинальный IP: {original_ip}")
                        logging.error(f"❌ Текущий IP: {current_ip}")
                        logging.error("❌ ПРОКСИ НЕ ИСПОЛЬЗУЕТСЯ!")
                        return False
                    else:
                        logging.info("✅ IP ИЗМЕНИЛСЯ! Прокси работает!")
                        if original_ip:
                            logging.info(f"✅ Оригинальный IP: {original_ip}")
                        logging.info(f"✅ Новый IP через Tor: {current_ip}")
                else:
                    logging.error("❌ Тест 2 ПРОВАЛЕН: Не удалось извлечь IP из ответа")
                    return False
                
                # Тест 3: Проверяем Tor Project сайт
                logging.info("📡 Тест 3: Проверка Tor Project...")
                self.driver.get("https://check.torproject.org")
                self.driver.sleep(15)  # Даем больше времени для Tor
                
                tor_content = self.driver.get_page_source()
                tor_title = self.driver.get_title()
                
                logging.info(f"📄 Tor заголовок: {tor_title}")
                logging.info(f"📄 Tor контент размер: {len(tor_content)} символов")
                
                if len(tor_content) < 500:
                    logging.warning("⚠ Тест 3: Tor Project страница маленькая, но IP уже проверен")
                    logging.info(f"📋 Tor содержимое: {tor_content[:300]}...")
                else:
                    tor_content_lower = tor_content.lower()
                    
                    if "congratulations" in tor_content_lower:
                        logging.info("✅ Тест 3 ПРОЙДЕН: Tor Project ПОДТВЕРЖДАЕТ соединение!")
                    elif "using tor" in tor_content_lower or "tor browser" in tor_content_lower:
                        logging.info("✅ Тест 3 ПРОЙДЕН: Tor соединение обнаружено Tor Project!")
                    else:
                        logging.warning("⚠ Тест 3: Tor Project не подтвердил, но IP изменился")
                        logging.debug(f"📋 Tor содержимое: {tor_content_lower[:500]}...")
                
                logging.info("🎉 ВСЕ ТЕСТЫ ПРОЙДЕНЫ: TOR ПРОКСИ РАБОТАЕТ КОРРЕКТНО!")
                return True
                    
            except Exception as e:
                logging.error(f"❌ КРИТИЧЕСКАЯ ОШИБКА во время проверки соединения: {e}")
                logging.error("❌ Tor соединение ТОЧНО НЕ РАБОТАЕТ")
                return False
            
        except Exception as e:
            logging.error(f"✗ Ошибка настройки браузера: {e}")
            return False

    def save_cookies(self):
        """Сохранение cookies"""
        try:
            cookies = self.driver.get_cookies()
            with open(self.cookies_file, 'wb') as f:
                pickle.dump(cookies, f)
            logging.info(f"💾 Cookies сохранены в {self.cookies_file}")
        except Exception as e:
            logging.error(f"✗ Ошибка сохранения cookies: {e}")
    
    def load_cookies(self) -> bool:
        """Загрузка cookies"""
        try:
            if os.path.exists(self.cookies_file):
                self.driver.get(self.base_url)
                HumanBehaviorSimulator.random_sleep(2, 4)
                
                with open(self.cookies_file, 'rb') as f:
                    cookies = pickle.load(f)
                
                for cookie in cookies:
                    try:
                        self.driver.add_cookie(cookie)
                    except Exception as e:
                        logging.debug(f"⚠ Ошибка добавления cookie: {e}")
                
                logging.info("✓ Cookies загружены")
                return True
        except Exception as e:
            logging.error(f"✗ Ошибка загрузки cookies: {e}")
        
        return False
    
    def check_authorization(self) -> bool:
        """Проверка авторизации"""
        try:
            self.driver.get(f"{self.base_url}/tasks-youtube")
            HumanBehaviorSimulator.random_sleep(3, 5)
            
            # Проверяем, есть ли форма авторизации
            login_forms = self.driver.find_elements(By.NAME, "username")
            if not login_forms:
                logging.info("✓ Пользователь авторизован")
                return True
            else:
                logging.info("⚠ Требуется авторизация")
                return False
                
        except Exception as e:
            logging.error(f"✗ Ошибка проверки авторизации: {e}")
            return False
    
    def login(self) -> bool:
        """Авторизация на сайте"""
        logging.info("🔐 Начало авторизации...")
        
        try:
            # Переход на страницу авторизации
            self.driver.get(f"{self.base_url}/login")
            HumanBehaviorSimulator.random_sleep(3, 6)
            
            # Ожидание загрузки страницы
            wait = WebDriverWait(self.driver, 20)
            
            # Поиск поля логина
            logging.info("🔍 Поиск поля логина...")
            username_field = wait.until(
                EC.presence_of_element_located((By.NAME, "username"))
            )
            logging.info("✓ Поле логина найдено")
            
            # Имитация человеческого клика и ввода
            ActionChains(self.driver).move_to_element(username_field).click().perform()
            HumanBehaviorSimulator.random_sleep(0.5, 1.5)
            
            HumanBehaviorSimulator.human_like_typing(username_field, self.username, self.driver)
            logging.info(f"✓ Логин '{self.username}' введен")
            
            # Поиск поля пароля
            logging.info("🔍 Поиск поля пароля...")
            password_field = self.driver.find_element(By.NAME, "password")
            logging.info("✓ Поле пароля найдено")
            
            # Ввод пароля
            ActionChains(self.driver).move_to_element(password_field).click().perform()
            HumanBehaviorSimulator.random_sleep(0.5, 1.5)
            
            HumanBehaviorSimulator.human_like_typing(password_field, self.password, self.driver)
            logging.info("✓ Пароль введен")
            
            # Поиск и нажатие кнопки входа
            logging.info("🔍 Поиск кнопки входа...")
            login_button = self.driver.find_element(By.ID, "button-login")
            logging.info("✓ Кнопка входа найдена")
            
            # Случайная пауза перед нажатием
            HumanBehaviorSimulator.random_sleep(1, 3)
            
            ActionChains(self.driver).move_to_element(login_button).click().perform()
            logging.info("✓ Кнопка входа нажата")
            
            # Ожидание результата авторизации
            HumanBehaviorSimulator.random_sleep(3, 6)
            
            # Проверка на запрос кода подтверждения
            max_attempts = 3
            for attempt in range(max_attempts):
                code_fields = self.driver.find_elements(By.NAME, "code")
                if code_fields:
                    logging.info("🔐 Требуется код подтверждения")
                    
                    # Автоматический запрос кода у пользователя
                    verification_code = None
                    attempts = 0
                    max_code_attempts = 3
                    
                    while attempts < max_code_attempts:
                        try:
                            print("\n" + "="*50)
                            print("🔐 ТРЕБУЕТСЯ КОД ПОДТВЕРЖДЕНИЯ")
                            print("📧 Проверьте вашу почту и введите код")
                            print("="*50)
                            
                            verification_code = input("Введите код подтверждения: ").strip()
                            
                            if verification_code and verification_code.isdigit():
                                break
                            else:
                                print("❌ Пожалуйста, введите корректный числовой код")
                                attempts += 1
                                
                        except KeyboardInterrupt:
                            logging.info("❌ Авторизация прервана пользователем")
                            return False
                        except Exception as e:
                            logging.error(f"✗ Ошибка ввода кода: {e}")
                            attempts += 1
                    
                    if not verification_code:
                        logging.error("❌ Не удалось получить код подтверждения")
                        return False
                    
                    # Ввод кода подтверждения
                    code_field = code_fields[0]
                    ActionChains(self.driver).move_to_element(code_field).click().perform()
                    HumanBehaviorSimulator.random_sleep(0.5, 1.0)
                    
                    HumanBehaviorSimulator.human_like_typing(code_field, verification_code, self.driver)
                    logging.info("✓ Код подтверждения введен")
                    
                    # Нажатие кнопки входа с кодом
                    confirm_buttons = self.driver.find_elements(By.CSS_SELECTOR, "button.button_theme_blue")
                    if confirm_buttons:
                        HumanBehaviorSimulator.random_sleep(1, 2)
                        ActionChains(self.driver).move_to_element(confirm_buttons[0]).click().perform()
                        logging.info("✓ Подтверждение с кодом отправлено")
                    
                    HumanBehaviorSimulator.random_sleep(3, 5)
                    break
                else:
                    # Проверяем, может быть уже авторизованы
                    if self.check_authorization():
                        break
                    
                    # Если это не последняя попытка, ждем еще
                    if attempt < max_attempts - 1:
                        logging.info(f"⏳ Ожидание ({attempt + 1}/{max_attempts})...")
                        HumanBehaviorSimulator.random_sleep(2, 4)
            
            # Проверка успешной авторизации
            if self.check_authorization():
                logging.info("✅ Авторизация успешна!")
                self.save_cookies()
                return True
            else:
                logging.error("❌ Авторизация не удалась")
                return False
                
        except TimeoutException:
            logging.error("⏰ Таймаут при авторизации")
            return False
        except Exception as e:
            logging.error(f"❌ Ошибка авторизации: {e}")
            return False
    
    def random_mouse_movement(self):
        """Случайные движения мыши"""
        try:
            viewport_size = self.driver.get_window_size()
            
            current_position = (
                random.randint(50, viewport_size['width'] - 50),
                random.randint(50, viewport_size['height'] - 50)
            )
            
            new_position = (
                random.randint(50, viewport_size['width'] - 50),
                random.randint(50, viewport_size['height'] - 50)
            )
            
            curve_points = HumanBehaviorSimulator.generate_bezier_curve(
                current_position, new_position
            )
            
            actions = ActionChains(self.driver)
            for i, point in enumerate(curve_points):
                if i == 0:
                    continue
                    
                prev_point = curve_points[i-1]
                offset_x = point[0] - prev_point[0]
                offset_y = point[1] - prev_point[1]
                
                actions.move_by_offset(offset_x, offset_y)
                time.sleep(random.uniform(0.01, 0.05))
            
            actions.perform()
            logging.debug(f"🖱 Движение мыши: {current_position} → {new_position}")
            
        except Exception as e:
            logging.debug(f"⚠ Ошибка движения мыши: {e}")
    
    def random_scroll(self):
        """Случайная прокрутка страницы"""
        try:
            scroll_direction = random.choice(['up', 'down'])
            scroll_amount = random.randint(100, 500)
            
            if scroll_direction == 'down':
                self.driver.execute_script(f"window.scrollBy(0, {scroll_amount});")
                logging.debug(f"📜 Прокрутка вниз: {scroll_amount}px")
            else:
                self.driver.execute_script(f"window.scrollBy(0, -{scroll_amount});")
                logging.debug(f"📜 Прокрутка вверх: {scroll_amount}px")
            
            HumanBehaviorSimulator.random_sleep(0.5, 2.0)
            
        except Exception as e:
            logging.debug(f"⚠ Ошибка прокрутки: {e}")
    
    def get_youtube_tasks(self) -> List[Dict]:
        """Получение списка заданий YouTube"""
        logging.info("📋 Поиск заданий YouTube...")
        
        try:
            # Переход на страницу заданий
            self.driver.get(f"{self.base_url}/tasks-youtube")
            HumanBehaviorSimulator.random_sleep(3, 6)
            
            # Имитация чтения страницы
            for _ in range(random.randint(2, 5)):
                self.random_scroll()
                HumanBehaviorSimulator.random_sleep(1, 3)
                self.random_mouse_movement()
            
            # Поиск всех заданий
            task_rows = self.driver.find_elements(By.CSS_SELECTOR, "tr[class^='ads_']")
            tasks = []
            
            for i, row in enumerate(task_rows):
                try:
                    # Извлечение ID задания
                    class_name = row.get_attribute('class')
                    task_id_match = re.search(r'ads_(\d+)', class_name)
                    if not task_id_match:
                        continue
                    
                    task_id = task_id_match.group(1)
                    
                    # Поиск кнопки "Посмотреть видео"
                    start_button = row.find_element(
                        By.CSS_SELECTOR, 
                        f"span[id='link_ads_start_{task_id}']"
                    )
                    
                    # Извлечение времени просмотра из onclick
                    onclick_attr = start_button.get_attribute('onclick')
                    time_match = re.search(r"start_youtube_new\(\d+,\s*'(\d+)'\)", onclick_attr)
                    watch_time = int(time_match.group(1)) if time_match else 10
                    
                    # Извлечение URL видео
                    video_url = start_button.get_attribute('title') or "unknown"
                    
                    task_info = {
                        'id': task_id,
                        'element': start_button,
                        'watch_time': watch_time,
                        'video_url': video_url,
                        'row': row
                    }
                    
                    tasks.append(task_info)
                    logging.info(f"✓ Найдено задание {task_id}: {watch_time}с, {video_url}")
                    
                    # Имитация чтения задания
                    if random.random() < 0.3:  # 30% вероятность
                        ActionChains(self.driver).move_to_element(row).perform()
                        HumanBehaviorSimulator.random_sleep(0.5, 2.0)
                
                except Exception as e:
                    logging.debug(f"⚠ Ошибка обработки задания {i}: {e}")
                    continue
            
            logging.info(f"📊 Найдено заданий: {len(tasks)}")
            return tasks
            
        except Exception as e:
            logging.error(f"❌ Ошибка получения заданий: {e}")
            return []
    
    def wait_for_element(self, by: By, value: str, timeout: int = 10) -> Optional[object]:
        """Ожидание появления элемента"""
        try:
            wait = WebDriverWait(self.driver, timeout)
            element = wait.until(EC.presence_of_element_located((by, value)))
            logging.debug(f"✓ Элемент найден: {value}")
            return element
        except TimeoutException:
            logging.debug(f"⏰ Элемент не найден в течение {timeout}с: {value}")
            return None
        except Exception as e:
            logging.debug(f"⚠ Ошибка ожидания элемента {value}: {e}")
            return None
    
    def handle_youtube_ads(self) -> bool:
        """Обработка рекламы на YouTube"""
        logging.info("📺 Проверка рекламы на YouTube...")
        
        try:
            # Ожидание загрузки страницы
            HumanBehaviorSimulator.random_sleep(3, 6)
            
            # Проверка наличия рекламы
            ad_indicators = [
                "ytp-ad-badge",
                "[id*='ad-badge']",
                ".ytp-ad-text",
                "[aria-label*='реклама']",
                "[aria-label*='Реклама']",
                "[aria-label*='Ad']",
                "[aria-label*='advertisement']"
            ]
            
            ad_found = False
            for selector in ad_indicators:
                try:
                    ad_elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    if ad_elements and any(el.is_displayed() for el in ad_elements):
                        ad_found = True
                        logging.info("📺 Обнаружена реклама")
                        break
                except:
                    continue
            
            if ad_found:
                # Ожидание кнопки пропуска или автозапуска
                skip_found = False
                auto_start_found = False
                
                for attempt in range(30):  # 30 секунд максимум
                    # Проверка кнопки пропуска
                    skip_selectors = [
                        ".ytp-ad-skip-button",
                        ".ytp-ad-skip-button-modern",
                        "[class*='skip']",
                        "button[class*='skip']"
                    ]
                    
                    for selector in skip_selectors:
                        try:
                            skip_buttons = self.driver.find_elements(By.CSS_SELECTOR, selector)
                            for button in skip_buttons:
                                if button.is_displayed() and button.is_enabled():
                                    logging.info("⏭ Нажатие кнопки пропуска рекламы")
                                    ActionChains(self.driver).move_to_element(button).click().perform()
                                    skip_found = True
                                    HumanBehaviorSimulator.random_sleep(2, 4)
                                    break
                            if skip_found:
                                break
                        except:
                            continue
                    
                    if skip_found:
                        break
                    
                    # Проверка автозапуска видео (появление таймера)
                    timer_selectors = [
                        ".ytwPlayerTimeDisplayTime",
                        "[class*='time-display']",
                        ".ytp-time-current"
                    ]
                    
                    for selector in timer_selectors:
                        try:
                            timers = self.driver.find_elements(By.CSS_SELECTOR, selector)
                            if timers and any(t.is_displayed() and t.text.strip() for t in timers):
                                logging.info("⏰ Видео запустилось автоматически")
                                auto_start_found = True
                                break
                        except:
                            continue
                    
                    if auto_start_found:
                        break
                    
                    # Случайные движения во время ожидания
                    if random.random() < 0.3:
                        self.random_mouse_movement()
                    
                    time.sleep(1)
                
                if not skip_found and not auto_start_found:
                    logging.warning("⚠ Реклама не обработана корректно")
            
            return True
            
        except Exception as e:
            logging.error(f"❌ Ошибка обработки рекламы: {e}")
            return False
    
    def wait_for_video_time(self, required_seconds: int) -> bool:
        """Ожидание достижения требуемого времени просмотра"""
        logging.info(f"⏱ Ожидание {required_seconds} секунд просмотра...")
        
        try:
            last_time = 0
            pause_counter = 0
            no_timer_counter = 0
            
            while True:
                # Поиск элементов таймера
                timer_selectors = [
                    ".ytwPlayerTimeDisplayTime",
                    "[class*='time-display']",
                    ".ytp-time-current",
                    "[role='text'][aria-label*='Продолжительность']"
                ]
                
                current_time_seconds = 0
                timer_found = False
                
                for selector in timer_selectors:
                    try:
                        timers = self.driver.find_elements(By.CSS_SELECTOR, selector)
                        for timer in timers:
                            if timer.is_displayed():
                                timer_text = timer.text.strip()
                                if ':' in timer_text:
                                    try:
                                        # Парсинг времени (mm:ss или hh:mm:ss)
                                        time_parts = timer_text.split(':')
                                        if len(time_parts) == 2:  # mm:ss
                                            minutes, seconds = map(int, time_parts)
                                            current_time_seconds = minutes * 60 + seconds
                                        elif len(time_parts) == 3:  # hh:mm:ss
                                            hours, minutes, seconds = map(int, time_parts)
                                            current_time_seconds = hours * 3600 + minutes * 60 + seconds
                                        
                                        timer_found = True
                                        no_timer_counter = 0
                                        break
                                    except (ValueError, IndexError):
                                        continue
                        
                        if timer_found:
                            break
                    except:
                        continue
                
                if timer_found:
                    logging.debug(f"⏰ Текущее время: {current_time_seconds}с (требуется: {required_seconds}с)")
                    
                    # Проверка на паузу
                    if current_time_seconds == last_time:
                        pause_counter += 1
                        if pause_counter >= 3:  # 3 секунды без изменений
                            logging.info("⏸ Видео на паузе, попытка запуска...")
                            self.try_play_video()
                            pause_counter = 0
                    else:
                        pause_counter = 0
                    
                    last_time = current_time_seconds
                    
                    # Проверка достижения требуемого времени
                    if current_time_seconds >= required_seconds:
                        logging.info(f"✅ Достигнуто время просмотра: {current_time_seconds}с")
                        return True
                else:
                    no_timer_counter += 1
                    logging.debug(f"⚠ Таймер не найден (попытка {no_timer_counter})")
                    
                    # Если долго нет таймера, пробуем запустить видео
                    if no_timer_counter >= 5:
                        logging.info("🎬 Попытка запуска видео (таймер не найден)")
                        self.try_play_video()
                        no_timer_counter = 0
                
                # Случайные действия во время просмотра
                if random.random() < 0.1:  # 10% вероятность
                    self.random_mouse_movement()
                
                if random.random() < 0.05:  # 5% вероятность
                    self.random_scroll()
                
                time.sleep(1)
            
        except Exception as e:
            logging.error(f"❌ Ошибка ожидания времени: {e}")
            return False
    
    def try_play_video(self):
        """Попытка запуска видео если оно на паузе"""
        try:
            # Поиск кнопки play
            play_selectors = [
                ".yt-icon-shape svg[viewBox*='24']",
                "button[title*='воспроизвести']",
                "button[title*='Play']",
                ".ytp-play-button",
                "[aria-label*='воспроизведение']",
                "[aria-label*='Play']"
            ]
            
            for selector in play_selectors:
                try:
                    play_buttons = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for button in play_buttons:
                        if button.is_displayed():
                            try:
                                # Проверяем, что это именно кнопка play (треугольник)
                                svg_path = button.find_elements(By.TAG_NAME, "path")
                                for path in svg_path:
                                    path_d = path.get_attribute("d")
                                    if path_d and ("m7 4 12 8-12 8V4z" in path_d or "M8 5v14l11-7z" in path_d):
                                        logging.info("▶ Нажатие кнопки воспроизведения")
                                        ActionChains(self.driver).move_to_element(button).click().perform()
                                        HumanBehaviorSimulator.random_sleep(1, 2)
                                        return
                            except:
                                continue
                except:
                    continue
            
            # Если кнопка не найдена, пробуем кликнуть по видео
            try:
                video_elements = self.driver.find_elements(By.TAG_NAME, "video")
                if video_elements:
                    video = video_elements[0]
                    if video.is_displayed():
                        logging.info("🎬 Клик по видео для запуска")
                        ActionChains(self.driver).move_to_element(video).click().perform()
                        HumanBehaviorSimulator.random_sleep(1, 2)
            except:
                pass
            
        except Exception as e:
            logging.debug(f"⚠ Ошибка запуска видео: {e}")
    
    def execute_youtube_task(self, task: Dict) -> bool:
        """Выполнение одного задания YouTube"""
        task_id = task['id']
        watch_time = task['watch_time']
        video_url = task['video_url']
        
        logging.info(f"🎯 Выполнение задания {task_id}: {watch_time}с")
        
        original_window = self.driver.current_window_handle
        
        try:
            # Прокрутка к заданию
            ActionChains(self.driver).move_to_element(task['row']).perform()
            HumanBehaviorSimulator.random_sleep(1, 3)
            
            # Случайная пауза перед кликом
            random_delay = random.uniform(1, 15)
            logging.info(f"⏳ Случайная пауза {random_delay:.1f}с перед выполнением")
            time.sleep(random_delay)
            
            # Клик по кнопке "Посмотреть видео"
            start_button = task['element']
            
            # Движение к кнопке по кривой
            try:
                viewport_size = self.driver.get_window_size()
                current_pos = (viewport_size['width'] // 2, viewport_size['height'] // 2)
                button_rect = start_button.rect
                target_pos = (
                    button_rect['x'] + button_rect['width'] // 2,
                    button_rect['y'] + button_rect['height'] // 2
                )
                
                curve_points = HumanBehaviorSimulator.generate_bezier_curve(current_pos, target_pos)
                actions = ActionChains(self.driver)
                
                for i, point in enumerate(curve_points[1:], 1):  # Пропускаем первую точку
                    prev_point = curve_points[i-1]
                    offset_x = point[0] - prev_point[0]
                    offset_y = point[1] - prev_point[1]
                    actions.move_by_offset(offset_x, offset_y)
                    time.sleep(random.uniform(0.01, 0.03))
                
                actions.click(start_button).perform()
            except Exception as e:
                logging.debug(f"⚠ Ошибка движения мыши, обычный клик: {e}")
                ActionChains(self.driver).move_to_element(start_button).click().perform()
            
            logging.info(f"🖱 Клик по заданию {task_id}")
            
            # Ожидание открытия YouTube
            HumanBehaviorSimulator.random_sleep(3, 6)
            
            # Переключение на новую вкладку YouTube
            all_windows = self.driver.window_handles
            
            youtube_window = None
            for window in all_windows:
                if window != original_window:
                    self.driver.switch_to.window(window)
                    if "youtube.com" in self.driver.current_url.lower():
                        youtube_window = window
                        break
            
            if not youtube_window:
                logging.error("❌ Не удалось найти вкладку YouTube")
                return False
            
            logging.info("📺 Переключение на вкладку YouTube")
            
            # Обработка рекламы
            self.handle_youtube_ads()
            
            # Ожидание требуемого времени просмотра
            if self.wait_for_video_time(watch_time):
                # Дополнительная случайная пауза
                extra_delay = random.uniform(1, 30)
                logging.info(f"⏳ Дополнительная пауза {extra_delay:.1f}с")
                
                # Случайные действия во время паузы
                for _ in range(int(extra_delay // 3)):
                    self.random_mouse_movement()
                    time.sleep(random.uniform(1, 3))
                
                # Возврат на исходную вкладку
                self.driver.close()  # Закрываем YouTube
                self.driver.switch_to.window(original_window)
                logging.info("🔙 Возврат на страницу заданий")
                
                HumanBehaviorSimulator.random_sleep(2, 4)
                
                # Поиск и нажатие кнопки подтверждения
                confirm_button_id = f"ads_btn_confirm_{task_id}"
                confirm_button = self.wait_for_element(By.ID, confirm_button_id, 10)
                
                if confirm_button and confirm_button.is_displayed():
                    ActionChains(self.driver).move_to_element(confirm_button).click().perform()
                    logging.info(f"✅ Подтверждение просмотра задания {task_id}")
                    HumanBehaviorSimulator.random_sleep(2, 4)
                    return True
                else:
                    logging.error(f"❌ Кнопка подтверждения не найдена для задания {task_id}")
                    return False
            else:
                logging.error(f"❌ Не удалось дождаться времени просмотра для задания {task_id}")
                return False
                
        except Exception as e:
            logging.error(f"❌ Ошибка выполнения задания {task_id}: {e}")
            
            # Попытка вернуться на исходную вкладку
            try:
                all_windows = self.driver.window_handles
                if len(all_windows) > 1:
                    for window in all_windows:
                        if window != original_window:
                            self.driver.switch_to.window(window)
                            self.driver.close()
                    self.driver.switch_to.window(original_window)
                else:
                    self.driver.switch_to.window(original_window)
            except Exception as cleanup_error:
                logging.debug(f"⚠ Ошибка очистки окон: {cleanup_error}")
            
            return False
    
    def execute_all_tasks(self) -> int:
        """Выполнение всех доступных заданий"""
        logging.info("🚀 Начало выполнения всех заданий...")
        
        tasks = self.get_youtube_tasks()
        if not tasks:
            logging.info("📭 Нет доступных заданий")
            return 0
        
        completed_tasks = 0
        
        # Перемешиваем задания для случайности
        random.shuffle(tasks)
        
        for i, task in enumerate(tasks):
            logging.info(f"📝 Задание {i+1}/{len(tasks)}")
            
            try:
                if self.execute_youtube_task(task):
                    completed_tasks += 1
                    logging.info(f"✅ Задание {task['id']} выполнено ({completed_tasks}/{len(tasks)})")
                else:
                    logging.warning(f"⚠ Задание {task['id']} не выполнено")
                
                # Пауза между заданиями
                if i < len(tasks) - 1:  # Не делаем паузу после последнего задания
                    pause_time = random.uniform(30, 120)  # 30 секунд - 2 минуты
                    logging.info(f"⏳ Пауза между заданиями: {pause_time:.1f}с")
                    
                    # Случайные действия во время паузы
                    for _ in range(int(pause_time // 10)):
                        if random.random() < 0.5:
                            self.random_mouse_movement()
                        if random.random() < 0.3:
                            self.random_scroll()
                        time.sleep(random.uniform(8, 12))
                
            except Exception as e:
                logging.error(f"❌ Критическая ошибка при выполнении задания {task['id']}: {e}")
                continue
        
        logging.info(f"🏁 Завершено выполнение заданий: {completed_tasks}/{len(tasks)}")
        return completed_tasks
    
    def cleanup_proxy_environment(self):
        """Очистка переменных окружения прокси"""
        try:
            proxy_env_vars = [
                'HTTP_PROXY', 'HTTPS_PROXY', 'SOCKS_PROXY', 'ALL_PROXY',
                'http_proxy', 'https_proxy', 'socks_proxy', 'all_proxy'
            ]
            
            logging.info("🧹 Очистка переменных окружения прокси...")
            for env_var in proxy_env_vars:
                if env_var in os.environ:
                    del os.environ[env_var]
                    logging.debug(f"✓ Удалена переменная окружения: {env_var}")
                    
        except Exception as e:
            logging.debug(f"⚠ Ошибка очистки переменных окружения: {e}")
    
    def cleanup(self):
        """Очистка ресурсов"""
        try:
            if self.driver:
                self.driver.quit()
                logging.info("🚪 Браузер закрыт")
        except Exception as e:
            logging.debug(f"⚠ Ошибка закрытия браузера: {e}")
        
        try:
            self.tor_manager.stop_tor()
        except Exception as e:
            logging.debug(f"⚠ Ошибка остановки Tor: {e}")
        
        # Очищаем переменные окружения прокси
        self.cleanup_proxy_environment()
    
    def run_cycle(self) -> bool:
        """Выполнение одного цикла работы"""
        logging.info("🔄 Начало цикла выполнения заданий")
        
        try:
            # Настройка браузера
            if not self.setup_driver():
                logging.error("❌ Не удалось настроить браузер")
                return False
            
            # Попытка использовать сохраненные cookies
            cookies_loaded = self.load_cookies()
            
            # Проверка авторизации
            if not cookies_loaded or not self.check_authorization():
                # Требуется авторизация
                if not self.login():
                    logging.error("❌ Не удалось авторизоваться")
                    return False
            
            # Выполнение заданий
            completed_tasks = self.execute_all_tasks()
            
            if completed_tasks > 0:
                logging.info(f"✅ Цикл завершен успешно: выполнено {completed_tasks} заданий")
            else:
                logging.info("ℹ Цикл завершен: нет заданий для выполнения")
            
            return True
            
        except Exception as e:
            logging.error(f"❌ Ошибка в цикле выполнения: {e}")
            return False
        finally:
            self.cleanup()
    
    def run(self):
        """Основной цикл работы бота"""
        logging.info("🤖 Запуск Aviso Automation Bot v2.0")
        
        cycle_count = 0
        consecutive_failures = 0
        max_consecutive_failures = 3
        
        try:
            while True:
                cycle_count += 1
                logging.info(f"🔄 Цикл #{cycle_count}")
                
                # Создание резервной копии перед каждым циклом
                self.create_backup(f"cycle_{cycle_count}")
                
                # Выполнение цикла
                success = self.run_cycle()
                
                if success:
                    consecutive_failures = 0
                    
                    # Случайная пауза между циклами (1 минута - 2 часа)
                    pause_minutes = random.uniform(1, 120)
                    pause_seconds = pause_minutes * 60
                    
                    next_run_time = datetime.now() + timedelta(seconds=pause_seconds)
                    
                    logging.info(f"😴 Пауза до следующего цикла: {pause_minutes:.1f} минут")
                    logging.info(f"⏰ Следующий запуск: {next_run_time.strftime('%Y-%m-%d %H:%M:%S')}")
                    
                    # Разбиваем паузу на части для возможности прерывания
                    pause_intervals = max(1, int(pause_seconds // 60))  # Проверяем каждую минуту
                    interval_duration = pause_seconds / pause_intervals
                    
                    for i in range(pause_intervals):
                        time.sleep(interval_duration)
                        remaining_minutes = pause_minutes - ((i + 1) * interval_duration / 60)
                        if remaining_minutes > 1:
                            logging.debug(f"⏳ Осталось до следующего цикла: {remaining_minutes:.1f} минут")
                else:
                    consecutive_failures += 1
                    
                    if consecutive_failures >= max_consecutive_failures:
                        logging.error(f"💥 Слишком много неудачных попыток подряд ({consecutive_failures})")
                        logging.info("🛑 Увеличиваем паузу до 30 минут")
                        pause_minutes = 30
                    else:
                        # При ошибке пауза короче
                        pause_minutes = random.uniform(5, 15)
                    
                    logging.warning(f"⚠ Ошибка в цикле #{cycle_count}, пауза {pause_minutes:.1f} минут")
                    time.sleep(pause_minutes * 60)
        
        except KeyboardInterrupt:
            logging.info("🛑 Получен сигнал остановки (Ctrl+C)")
        except Exception as e:
            logging.error(f"💥 Критическая ошибка в главном цикле: {e}")
        finally:
            self.cleanup()
            logging.info("👋 Работа бота завершена")

def main():
    """Точка входа в программу"""
    print("🤖 Aviso YouTube Tasks Automation Bot v2.0")
    print("=" * 50)
    print("🚀 Автоматический запуск...")
    print("⚠  ВНИМАНИЕ: Используйте бота ответственно!")
    print("📋 Функции:")
    print("   - Автоматическая авторизация на aviso.bz")
    print("   - Выполнение заданий по просмотру YouTube")
    print("   - Имитация человеческого поведения")
    print("   - Работа через Tor прокси")
    print("   - Фиксированный User-Agent для аккаунта")
    print("   - Улучшенная поддержка Termux/Android")
    print("   - Детальное логирование")
    print("=" * 50)
    print()
    
    # Создание и запуск бота без подтверждения
    bot = AvisoAutomation()
    
    try:
        bot.run()
    except Exception as e:
        logging.error(f"💥 Критическая ошибка при запуске: {e}")
        print(f"\n❌ Критическая ошибка: {e}")
        print("📋 Проверьте логи для подробной информации")
    finally:
        print("\n👋 До свидания!")

if __name__ == "__main__":
    main()