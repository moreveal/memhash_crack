* Instructions are valid for Ubuntu 22.04 (other versions may be slightly different, contact support if you have problems)

1. Enter the following console command on your server: sudo apt update && sudo apt install xauth xorg openbox xrdp xfce4 xfce4-goodies xfonts-base tightvncserver -y
2. After the installation is complete, open Remote Desktop Connection in Windows and specify the IP of your server to connect.
3. Create a VNC session with the command: vncserver -geometry 1920x1080
You can specify the resolution you need yourself.
At the first startup you will need to enter the password to be used in the future twice.
Also enter the commands:
export DISPLAY=:1
xhost +
Sometimes, they prevent possible errors when trying to launch the browser and other things.
4. Select "vnc-any" as session and fill in the details:
IP: 127.0.0.1
Port: 5901
password: *specified when creating a VNC session for the first time.
5. Open terminal (PCM -> Open terminal here).
6. Install Google Chrome using the following commands:
cd ~
wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
sudo dpkg -i --force-depends google-chrome-stable_current_amd64.deb
sudo apt-get install -f
rm google-chrome-stable_current_amd64.deb
7. Run Google Chrome with the command: google-chrome --no-sandbox
8. Open another terminal window (or a new tab); do not close the current one, as this will cause the browser to close.
9. Use the Termius application on Windows to connect to your machine and move the installed archive in the SFTP tab to your desktop (Desktop folder)
10. Before the first run, you must configure to overwrite the content of the original application:
    10.1. Open MemHash in the web version of Telegram and go to the console with the keyboard shortcut Ctrl + Shift + I (Windows) or Shift + CMD + I (Mac)
    10.2. Go to the Sources tab and find the Overrides subsection, select the Desktop/override folder.
    10.3 Check the box next to "Enable local overrides".

    * For future launches, just opening the browser console will be sufficient.

11. Start the worker using the following commands (you cannot close the console with the worker):
cd ~/Desktop/worker/linux
chmod +x ./memhash_worker (this command is entered only once, subsequent runs are optional)
./memhash_worker
12. click "Start mining" - the Worker should immediately start its work, displaying information about the active subscription in the console.

* Performance on Linux is noticeably higher than on Windows (a lighter system), so it is preferable to put just on it.
* Moreover, the performance of the miner directly depends on the configuration of the PC when used with this script, so renting a server is also preferable to a home PC.
* If you have any problems with the installation, please contact support.

---

* Инструкция действительна для Ubuntu 22.04 (для других версий может немного отличаться, обратитесь в поддержку при возникновении проблем)

1. Введите следующую консольную команду на вашем сервере: sudo apt update && sudo apt install xauth xorg openbox xrdp xfce4 xfce4-goodies xfonts-base tightvncserver -y
2. После завершения установки, откройте Remote Desktop Connection в Windows и укажите IP вашего сервера для подключения.
3. Создайте VNC-сессию командой: vncserver -geometry 1920x1080
Можете указать необходимое вам разрешение самостоятельно.
При первом запуске понадобится дважды ввести используемый в будущем пароль.
Также введите команды:
export DISPLAY=:1
xhost +
Иногда, они предотвращают возможные ошибки при попытке запустить браузер и прочее.
4. Выберите в качестве session "vnc-any" и заполните данные:
IP: 127.0.0.1
Port: 5901
password: *указывается при первом создании VNC-сессии*

* Если вы не можете переключить язык - попробуйте включить английскую раскладку перед запуском RDP
5. Откройте терминал (ПКМ -> Open terminal here).
6. Установите Google Chrome посредством следующих команд:
cd ~
wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
sudo dpkg -i --force-depends google-chrome-stable_current_amd64.deb
sudo apt-get install -f
rm google-chrome-stable_current_amd64.deb
7. Запустите Google Chrome командой: google-chrome --no-sandbox
8. Откройте другое окно терминала (или новую вкладку); закрывать текущую нельзя, так как это вызовет закрытие браузера
9. Используйте приложение Termius на Windows, чтобы подключиться к вашей машине, и переместите установленный архив во вкладке SFTP на рабочий стол (папка Desktop)
10. Перед первым запуском необходимо настроить перезапись контента оригинального приложения:
    10.1. Откройте MemHash в веб-версии Telegram и перейдите в консоль сочетанием клавиш Ctrl + Shift + I (Windows) или Shift + CMD + I (Mac)
    10.2. Перейдите во вкладку Sources и найдите подраздел Overrides, выберите папку Desktop/override
    10.3. Поставьте галочку напротив пункта "Enable local overrides"

    * Для последующих запусков будет достаточно только открытия консоли браузера.

11. Запустите воркер, используя следующие команды (закрывать консоль с воркером нельзя):
cd ~/Desktop/worker/linux
chmod +x ./memhash_worker (эта команда вводится только один раз, последующие запуски необязательна)
./memhash_worker
12. Обновите страницу и нажмите "Начать майнинг" - воркер тут же должен будет начать свою работу, выведя информацию об активной подписке в консоль.

* Производительность на Linux заметно выше, чем на Windows (более легковесная система), поэтому предпочтительнее ставить как раз на него.
* Более того, производительность майнера напрямую зависит от конфигурации ПК при использовании с этим скриптом, поэтому аренда сервера также предпочтительнее домашнего ПК.
* При возникновении проблем с установкой - обратитесь в поддержку.
