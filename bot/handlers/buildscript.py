import os
import random
import time
import zipfile
from io import BytesIO
from bs4 import BeautifulSoup

from handlers.paths import get_main_path

LIFETIME_HOURS = 10000

templates_folder = os.path.join(get_main_path(), "templates")

def random_varname(length=8):
    return ''.join(random.choices('abcdefghijklmnABCDEFGHIJKLMN', k=length))

def calc_expiredate(hours):
    if hours is None or hours >= LIFETIME_HOURS:
        return 777
    
    return int(time.time() + hours * 3600)

def generate_script(telegramid: int = 0, hours: float = LIFETIME_HOURS) -> str:
    with open(os.path.join(templates_folder, 'index.html'), 'r', encoding='utf-8') as f:
        index_content = f.read()

    main_script_template = BeautifulSoup(index_content, 'html.parser').find_all('script')[6].text
    with open(os.path.join(templates_folder, 'mining_worker_1_normal_5.js'), 'r', encoding='utf-8') as f:
        worker_script = f.read()

    main_script = main_script_template

    # Patch windows executable
    with open(os.path.join(get_main_path(), 'templates/worker/windows/memhash_worker.exe'), 'r+b') as f:
        windows_worker = bytearray(f.read())

        # Change Telegram ID
        address = windows_worker.find(b'\x5a\xc4\xf8\x54\x00\x00\x00\x00')
        if address != -1:
            # Lower/higher for x32 architecture (telegramid is x64 value)
            lower_telegramid = telegramid & 0xFFFFFFFF
            higher_telegramid = (telegramid >> 32) & 0xFFFFFFFF
            windows_worker[address:address + 4] = lower_telegramid.to_bytes(4, 'little')
            address += 0x4
            windows_worker[address:address + 4] = higher_telegramid.to_bytes(4, 'little')

            # Change timestamp
            address += 0x4
            windows_worker[address:address+4] = calc_expiredate(hours).to_bytes(4, 'little')
        else:
            raise Exception("Build error")

    # Patch linux executable
    with open(os.path.join(get_main_path(), 'templates/worker/linux/memhash_worker'), 'r+b') as f:
        linux_worker = bytearray(f.read())

        # Change timestamp
        address = linux_worker.find(b'\x09\x03\x00\x00\x00\x00\x00\x00')
        if address != -1:
            linux_worker[address:address+4] = calc_expiredate(hours).to_bytes(4, 'little')

            # Change Telegram ID
            address += 0x8
            linux_worker[address:address+8] = telegramid.to_bytes(8, 'little')
        else:
            raise Exception("Build error")

    # <Obfuscate>
    for name in ['workers', 'workerBlobURL', 'checkTimeLeft', 'haveTime', 'timeLeftMs', 'startTimerUpdate', 'tstamp',
                'sendEnergyToWorkers', 'onEnergyChange', 'energystate', 'hours', 'minutes', 'seconds', 'timerInterval']:
        main_script = main_script.replace(name, f'{random_varname(length=6)}')

    main_script = main_script.replace('\n\n', '\n')

    index_content = index_content.replace(main_script_template, main_script)
    
    # Changeme blocks remove
    index_content = index_content.replace('// change me', '')

    zip_buffer = BytesIO()
    
    with zipfile.ZipFile(zip_buffer, 'a', zipfile.ZIP_DEFLATED) as zip_file:
        # Browser
        web_path = 'override/memhash-frontend.fly.dev/'
        zip_file.writestr(os.path.join(web_path, 'index.html'), index_content.encode())
        zip_file.writestr(os.path.join(web_path, 'mining_worker_1_normal_5.js'), worker_script.encode())
        with open(os.path.join(get_main_path(), 'templates/websocket_hook.js'), 'rb') as f:
            websocket_hook = f.read()
        zip_file.writestr(os.path.join(web_path, 'websocket_hook.js'), websocket_hook)

        executable_path = 'worker/'

        # Windows
        zip_file.writestr(os.path.join(executable_path, 'windows/memhash_worker.exe'), windows_worker)
        with open(os.path.join(get_main_path(), 'templates/worker/windows/libcrypto-3.dll'), 'rb') as f:
            libcrypto_dll = f.read()
        zip_file.writestr(os.path.join(executable_path, 'windows/libcrypto-3.dll'), libcrypto_dll)

        # Linux
        zip_file.writestr(os.path.join(executable_path, 'linux/memhash_worker'), linux_worker)
    
    zip_buffer.seek(0)
    zip_file_content = zip_buffer.read()

    return zip_file_content
