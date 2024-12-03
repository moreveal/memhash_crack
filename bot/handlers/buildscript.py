import os
import random
import time
import base64
from bs4 import BeautifulSoup

LIFETIME_HOURS = 10000

obfuscator_path = 'node_modules/javascript-obfuscator/bin/javascript-obfuscator'
templates_folder = "bot/templates"

def random_varname(length=8):
    return ''.join(random.choices('abcdefghijklmnABCDEFGHIJKLMN', k=length))

def calc_expiredate(hours):
    return int(time.time() + hours * 3600)

def generate_script(telegramid: int = None, hours: float = None) -> str:
    with open(os.path.join(templates_folder, 'index.html'), 'r', encoding='utf-8') as f:
        index_content = f.read()

    main_script_template = BeautifulSoup(index_content, 'html.parser').find_all('script')[3].text
    with open(os.path.join(templates_folder, 'worker.js'), 'r', encoding='utf-8') as f:
        worker_script = f.read()

    # Obfuscate worker script
    # with tempfile.NamedTemporaryFile('w+', suffix='.js', encoding='utf-8') as output_file:
    #     command = [
    #         "node",
    #         obfuscator_path,
    #         os.path.join(templates_folder, 'worker.js'),
    #         "-o", output_file.name,

    #         "--compact", "false",
    #         "--options-preset", "low-obfuscation",
    #         "--dead-code-injection", "false",
    #         "--disable-console-output", "true",
    #         "--split-strings", "false",
    #         "--unicode-escape-sequence", "true",
    #         "--string-array", "true",
    #         "--rename-globals", "true"
    #     ]

    #     try:
    #         subprocess.run(command, capture_output=True, text=True, check=True)
    #         output_file.seek(0)
    #         worker_script = output_file.read()
    #     except subprocess.SubprocessError as e:
    #         print("Worker obfuscation error:", e)
    #         return None
    
    main_script = main_script_template

    # Owner telegram ID
    telegramid_js = f'"{base64.b64encode(str(telegramid).encode()).decode()}"' if telegramid else 'null'
    main_script = main_script.replace('let telegramId = "TELEGRAMID_PLACEHOLDER";', '') # Delete variable
    main_script = main_script.replace('telegramId', telegramid_js)

    # Expire date
    timestamp_js = hex(calc_expiredate(hours) * 1000) if hours else 'null'
    main_script = main_script.replace('let expireDate = "TIMESTAMP_PLACEHOLDER";', '') # Delete variable
    main_script = main_script.replace('expireDate', timestamp_js) # Replace all accesses to a variable with its value

    # Setup worker script
    blob = f'''
        let workerBlobURL = URL.createObjectURL(new Blob([atob(`{base64.b64encode(worker_script.encode()).decode()}`)], {{ type: 'application/javascript' }}));
    '''
    main_script = main_script.replace('const workerBlobURL = "WORKER_BLOB_URL_PLACEHOLDER";', blob.strip())

    # <Obfuscate>
    for name in ['workers', 'workerBlobURL', 'checkTimeLeft', 'haveTime', 'timeLeftMs', 'startTimerUpdate', 'tstamp',
                'sendEnergyToWorkers', 'onEnergyChange', 'energystate', 'hours', 'minutes', 'seconds', 'timerInterval']:
        main_script = main_script.replace(name, f'{random_varname(length=6)}')

    main_script = main_script.replace('\n\n', '\n')

    index_content = index_content.replace(main_script_template, main_script)
    return index_content

if __name__ == "__main__":
    script = generate_script()
    with open('test_output.html', 'w+', encoding='utf-8') as f:
        f.write(script)
