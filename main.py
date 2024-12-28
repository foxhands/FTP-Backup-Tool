import os
import logging
from pathlib import Path
from datetime import datetime, timedelta
from ftplib import FTP, error_perm
import shutil

# Logging configuration
logging.basicConfig(level=logging.INFO, filename="backup.log", filemode="a",
                    format="%(asctime)s - %(levelname)s - %(message)s")

def copy_folder_content(src_folder, dest_folder):
    """Copies the content from src_folder to dest_folder.

    If files with the same names already exist in the destination folder, they will be overwritten.
    If the destination folder does not exist, it will be created.
    Directories are created recursively as needed.
    """
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
    """Deletes backups older than the specified number of days.

    This function iterates through the contents of the specified backup folder and checks for directories
    with names that match a date format (YYYY-MM-DD). If a folder's date is older than the cutoff date,
    it is deleted. Non-backup folders (those without date-based names) are skipped.
    """
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
    """Recursively creates remote directories on the FTP server.

    Errors such as permission issues or invalid paths are logged, and the process continues
    for other directories. If a directory cannot be created due to lack of permissions,
    a warning is logged, and the function skips that specific directory.
    """
    logging.info(f"Ensuring remote directory exists: {remote_path}")
    dirs = remote_path.strip('/').split('/')
    current_path = ''
    for dir in dirs:
        current_path += f'/{dir}'
        try:
            ftp.cwd(current_path)
        except error_perm:
            try:
                ftp.mkd(current_path)
                ftp.cwd(current_path)
                logging.info(f"Created directory: {current_path}")
            except error_perm as e:
                logging.warning(f"Permission error while creating directory {current_path}: {e}")

def delete_old_ftp_backups(ftp, remote_folder, days=30):
    """Deletes old backups on the FTP server.

    This function checks for directories in the specified remote folder with names that match
    a date format (YYYY-MM-DD). If a directory's date is older than the cutoff date, it is deleted.
    Directories that cannot be parsed as valid dates are skipped, and a warning is logged for each.
    Skipped folders do not affect the processing of other valid directories.
    """
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
    """Recursively deletes a directory on the FTP server."""
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
    """Uploads files to the FTP server.

    Errors during the upload process are logged. If a file fails to upload,
    the process continues with the remaining files. The details of each error,
    such as connection issues or file access problems, are included in the log.
    """
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
    # Configuration
    local_folder = r"D:\\Work\\Obsidian"
    backup_folder = r"H:\\Obsidian\\DailyBackup"
    ftp_credentials = {
        'host': 'ftp.example.com',
        'username': 'your_username',
        'password': 'your_password'
    }
    remote_folder = "/backups/obsidian"

    try:
        # Step 1: Create a local backup
        logging.info("Starting backup process.")
        current_date = datetime.now().strftime('%Y-%m-%d')
        dated_backup_folder = Path(backup_folder) / current_date
        copy_folder_content(local_folder, dated_backup_folder)

        # Step 2: Upload the backup to FTP
        upload_to_ftp(local_folder, f"{remote_folder}/{current_date}", ftp_credentials)

        # Step 3: Clean up old local backups
        delete_old_backups(backup_folder)

        # Step 4: Clean up old backups on FTP
        with FTP(ftp_credentials['host']) as ftp:
            ftp.login(ftp_credentials['username'], ftp_credentials['password'])
            delete_old_ftp_backups(ftp, remote_folder)

        logging.info("Backup and upload process completed successfully.")
    except Exception as e:
        logging.error(f"An error occurred: {e}")
