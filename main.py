import os
import logging
from pathlib import Path
from datetime import datetime, timedelta
from ftplib import FTP, error_perm
import shutil

# Настройка логирования
logging.basicConfig(level=logging.INFO, filename="backup.log", filemode="a",
                    format="%(asctime)s - %(levelname)s - %(message)s")

def copy_folder_content(src_folder, dest_folder):
    """Копирует содержимое из src_folder в dest_folder."""
    logging.info(f"Starting to copy content from {src_folder} to {dest_folder}.")
    dest_path = Path(dest_folder)
    src_path = Path(src_folder)
    dest_path.mkdir(parents=True, exist_ok=True)

    for item in src_path.rglob("*"):
        relative_path = item.relative_to(src_path)
        target = dest_path / relative_path

        if item.is_dir():
            target.mkdir(parents=True, exist_ok=True)
        else:
            shutil.copy2(item, target)
            logging.info(f"File {item} copied to {target}.")
    logging.info(f"Finished copying content from {src_folder} to {dest_folder}.")

def delete_old_backups(backup_folder, days=30):
    """Удаляет резервные копии старше заданного количества дней."""
    logging.info(f"Checking for old backups in {backup_folder} older than {days} days.")
    cutoff_date = datetime.now() - timedelta(days=days)
    for folder in Path(backup_folder).iterdir():
        if folder.is_dir():
            try:
                folder_date = datetime.strptime(folder.name, '%Y-%m-%d')
                if folder_date < cutoff_date:
                    shutil.rmtree(folder)
                    logging.info(f"Deleted old backup folder: {folder}")
            except ValueError:
                logging.warning(f"Skipping folder {folder}, not a valid date format.")
                continue
    logging.info(f"Finished checking old backups in {backup_folder}.")

def ensure_remote_directory(ftp, remote_path):
    """Создает удаленные директории на FTP сервере рекурсивно."""
    logging.info(f"Ensuring remote directory exists: {remote_path}")
    dirs = remote_path.strip('/').split('/')
    current_path = ''
    for dir in dirs:
        current_path += f'/{dir}'
        try:
            ftp.cwd(current_path)
        except error_perm:
            ftp.mkd(current_path)
            ftp.cwd(current_path)
            logging.info(f"Created directory: {current_path}")

def delete_old_ftp_backups(ftp, remote_folder, days=30):
    """Удаляет старые резервные копии на FTP."""
    logging.info(f"Checking for old backups on FTP in {remote_folder} older than {days} days.")
    cutoff_date = datetime.now() - timedelta(days=days)
    try:
        ftp.cwd(remote_folder)
        for folder in ftp.nlst():
            if not folder.startswith("."):
                try:
                    folder_date = datetime.strptime(folder, '%Y-%m-%d')
                    if folder_date < cutoff_date:
                        delete_remote_directory(ftp, f"{remote_folder}/{folder}")
                        logging.info(f"Deleted old FTP backup folder: {folder}")
                except ValueError:
                    logging.warning(f"Skipping FTP folder {folder}, not a valid date format.")
                    continue
    except error_perm as e:
        logging.error(f"Error accessing remote folder {remote_folder}: {e}")

def delete_remote_directory(ftp, remote_dir):
    """Рекурсивное удаление директории на FTP."""
    try:
        ftp.cwd(remote_dir)
        for item in ftp.nlst():
            if not item.startswith("."):
                try:
                    ftp.delete(f"{remote_dir}/{item}")
                    logging.info(f"Deleted file {remote_dir}/{item}")
                except error_perm:
                    delete_remote_directory(ftp, f"{remote_dir}/{item}")
        ftp.cwd("..")
        ftp.rmd(remote_dir)
        logging.info(f"Deleted directory {remote_dir}")
    except error_perm as e:
        logging.error(f"Error deleting {remote_dir}: {e}")

def upload_to_ftp(local_folder, remote_folder, ftp_credentials):
    """Загрузка файлов на FTP сервер."""
    logging.info(f"Starting upload to FTP: {ftp_credentials['host']}, folder: {remote_folder}")
    with FTP(ftp_credentials['host']) as ftp:
        ftp.login(ftp_credentials['username'], ftp_credentials['password'])
        logging.info(f"Connected to FTP: {ftp_credentials['host']}")

        for local_file in Path(local_folder).rglob("*"):
            relative_path = local_file.relative_to(local_folder)
            remote_path = f"{remote_folder}/{relative_path}".replace("\\", "/")

            if local_file.is_dir():
                ensure_remote_directory(ftp, remote_path)
            else:
                try:
                    with open(local_file, 'rb') as file:
                        ftp.storbinary(f'STOR {remote_path}', file)
                        logging.info(f"Uploaded {local_file} to {remote_path}")
                except Exception as e:
                    logging.error(f"Failed to upload {local_file} to {remote_path}: {e}")
    logging.info(f"Finished upload to FTP: {ftp_credentials['host']}")

if __name__ == "__main__":
    # Настройки
    local_folder = r"D:\\Work\\Obsidian"
    backup_folder = r"H:\\Obsidian\\DailyBackup"
    ftp_credentials = {
        'host': 'ftp.example.com',
        'username': 'your_username',
        'password': 'your_password'
    }
    remote_folder = "/backups/obsidian"

    try:
        # Шаг 1: Создание локальной резервной копии
        logging.info("Starting backup process.")
        current_date = datetime.now().strftime('%Y-%m-%d')
        dated_backup_folder = Path(backup_folder) / current_date
        copy_folder_content(local_folder, dated_backup_folder)

        # Шаг 2: Загрузка резервной копии на FTP
        upload_to_ftp(local_folder, f"{remote_folder}/{current_date}", ftp_credentials)

        # Шаг 3: Очистка старых резервных копий локально
        delete_old_backups(backup_folder)

        # Шаг 4: Очистка старых резервных копий на FTP
        with FTP(ftp_credentials['host']) as ftp:
            ftp.login(ftp_credentials['username'], ftp_credentials['password'])
            delete_old_ftp_backups(ftp, remote_folder)

        logging.info("Backup and upload process completed successfully.")
    except Exception as e:
        logging.error(f"An error occurred: {e}")
