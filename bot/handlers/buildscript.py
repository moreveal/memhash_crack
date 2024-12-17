import os
import random
import time
import zipfile
from io import BytesIO
from bs4 import BeautifulSoup

from handlers.paths import get_main_path

templates_folder = os.path.join(get_main_path(), "templates")
vmp_keygen_path = os.path.join(get_main_path(), '../vmp-keygen.js')

def random_varname(length=8):
    return ''.join(random.choices('abcdefghijklmnABCDEFGHIJKLMN', k=length))

def calc_expiredate(hours):
    if hours is None:
        return 777
    
    return int(time.time() + hours * 3600)

def generate_build() -> bytes:
    '''
    Generates a default build instance
    * Need the .key-file for running
    '''
    
    with open(os.path.join(templates_folder, 'override/index.html'), 'r', encoding='utf-8') as f:
        index_content = f.read()

    main_script_template = BeautifulSoup(index_content, 'html.parser').find_all('script')[6].text
    with open(os.path.join(templates_folder, 'override/mining_worker_1_normal_5.js'), 'r', encoding='utf-8') as f:
        worker_script = f.read()

    main_script = main_script_template

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
        zip_file.write(os.path.join(templates_folder, 'override/websocket_hook.js'), os.path.join(web_path, 'websocket_hook.js'))

        executable_path = 'worker/'

        # Windows
        zip_file.write(os.path.join(templates_folder, 'worker/windows/memhash_worker.vmp.exe'), os.path.join(executable_path, 'windows/memhash_worker.exe'))
        zip_file.write(os.path.join(templates_folder, 'worker/windows/libcrypto-3.dll'), os.path.join(executable_path, 'windows/libcrypto-3.dll'))
        zip_file.write(os.path.join(templates_folder, 'worker/windows/README.txt'), os.path.join(executable_path, 'windows/README.txt'))

        # Linux
        zip_file.write(os.path.join(templates_folder, 'worker/linux/memhash_worker_vmp'), os.path.join(executable_path, 'linux/memhash_worker'))
        zip_file.write(os.path.join(templates_folder, 'worker/linux/README.txt'), os.path.join(executable_path, 'linux/README.txt'))
    
    zip_buffer.seek(0)
    zip_file_content = zip_buffer.read()

    return zip_file_content

def generate_key(username: str, telegramid: int, expiredate: int) -> bytes:
    from handlers.vmp_keygen import VMP
    vmp = VMP(vmp_keygen_path)

    key_buffer = BytesIO()
    key_buffer.write(vmp.generate_key(username, telegramid, expiredate).encode())
    key_buffer.seek(0)

    content = key_buffer.read()
    return content

def get_build_info(content: bytes) -> tuple:
    '''
    Gets the user data of an already generated build
    '''

    zip_file = BytesIO(content)

    try:
        with zipfile.ZipFile(zip_file) as zf:
            with zf.open('worker/linux/memhash_worker', 'r') as f:
                linux_worker = bytearray(f.read())
            
            # Change timestamp
            address = 0x004FD010
            if address != -1:
                timestamp = int.from_bytes(linux_worker[address:address + 4], 'little')

                address += 0x8
                telegram_id = int.from_bytes(linux_worker[address:address + 8], 'little')
                return (telegram_id, timestamp)
            else:
                raise Exception("Address is not found")
    except Exception as e:
        print("Get build info exception:", e)
        return None
