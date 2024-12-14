* Instructions are valid for Ubuntu 22.04 (other versions may be slightly different, contact support if you have problems)

1. Enter the following console command on your server: sudo apt update && sudo apt-get install xauth xorg openbox xrdp -y
2. After the installation is complete, open Remote Desktop Connection in Windows and specify the IP of your server to connect.
3. Enter your Linux account credentials:
user: root
password: *required when renting a server*.
4. Open a terminal (PCM -> Open terminal here).
5. Install Google Chrome using the following commands:
cd ~
wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
sudo dpkg -i --force-depends google-chrome-stable_current_amd64.deb
sudo apt-get install -f
rm google-chrome-stable_current_amd64.deb
6. Launch Google Chrome with the command: google-chrome --no-sandbox
7. Open another terminal window (or a new tab); do not close the current one, as this will cause the browser to close.
8. Use the Termius application on Windows to connect to your machine, and move the installed archive in the SFTP tab to your desktop (Desktop folder)
9. Before the first launch, you need to set up content overwriting of the original application:
    9.1. Open MemHash in the web version of Telegram and navigate to the console with the keyboard shortcut Ctrl + Shift + I (Windows) or Shift + CMD + I (Mac)
    9.2. Go to the Sources tab and find the Overrides subsection, select the Desktop/override folder
    9.3 Check the box next to "Enable local overrides".

    * For future launches, just opening the browser console will be sufficient.

10. Start the worker using the following commands (you cannot close the console with the worker):
cd ~/Desktop/worker/linux
chmod +x ./memhash_worker (this command is entered only once, subsequent runs are optional)
./memhash_worker
11. click "Start mining" - the Worker should immediately start its work, displaying information about the active subscription in the console.

* Performance on Linux is noticeably higher than on Windows (a lighter system), so it is preferable to put just on it.
* Moreover, the performance of the miner directly depends on the configuration of the PC when used with this script, so renting a server is also preferable to a home PC.
* If you have problems with the installation - contact support.

---

* Инструкция действительна для Ubuntu 22.04 (для других версий может немного отличаться, обратитесь в поддержку при возникновении проблем)

1. Введите следующую консольную команду на вашем сервере: sudo apt update && sudo apt install xauth xorg openbox xrdp xfce4 xfce4-goodies xfonts-base -y
2. После завершения установки, откройте Remote Desktop Connection в Windows и укажите IP вашего сервера для подключения.
3. Введите данные от вашей учетной записи Linux:
user: root
password: *сообщается при аренде сервера*
4. Откройте терминал (ПКМ -> Open terminal here).
5. Установите Google Chrome посредством следующих команд:
cd ~
wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
sudo dpkg -i --force-depends google-chrome-stable_current_amd64.deb
sudo apt-get install -f
rm google-chrome-stable_current_amd64.deb
6. Запустите Google Chrome командой: google-chrome --no-sandbox
7. Откройте другое окно терминала (или новую вкладку); закрывать текущую нельзя, так как это вызовет закрытие браузера
8. Используйте приложение Termius на Windows, чтобы подключиться к вашей машине, и переместите установленный архив во вкладке SFTP на рабочий стол (папка Desktop)
9. Перед первым запуском необходимо настроить перезапись контента оригинального приложения:
    9.1. Откройте MemHash в веб-версии Telegram и перейдите в консоль сочетанием клавиш Ctrl + Shift + I (Windows) или Shift + CMD + I (Mac)
    9.2. Перейдите во вкладку Sources и найдите подраздел Overrides, выберите папку Desktop/override
    9.3. Поставьте галочку напротив пункта "Enable local overrides"

    * Для последующих запусков будет достаточно только открытия консоли браузера.

10. Запустите воркер, используя следующие команды (закрывать консоль с воркером нельзя):
cd ~/Desktop/worker/linux
chmod +x ./memhash_worker (эта команда вводится только один раз, последующие запуски необязательна)
./memhash_worker
11. Нажмите "Начать майнинг" - воркер тут же должен будет начать свою работу, выведя информацию об активной подписке в консоль.

* Производительность на Linux заметно выше, чем на Windows (более легковесная система), поэтому предпочтительнее ставить как раз на него.
* Более того, производительность майнера напрямую зависит от конфигурации ПК при использовании с этим скриптом, поэтому аренда сервера также предпочтительнее домашнего ПК.
* При возникновении проблем с установкой - обратитесь в поддержку.
