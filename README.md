# FTP Backup Tool

## Description
FTP Backup Tool is a utility for automating the process of backing up local data and uploading it to an FTP server. The program includes the following features:

- Local backup creation.
- Uploading backups to an FTP server.
- Cleaning up old local and remote backups.
- Logging all actions for monitoring and debugging.

---

## Key Features

### 1. Local Backup Creation
- Recursively copy the contents of a specified folder to a backup directory with the current date.

### 2. FTP Upload
- Upload backups to an FTP server with automatic remote folder creation.
- Validate FTP structure and create directories as needed.

### 3. Old Backup Cleanup
- Delete local backups older than a specified period.
- Remove outdated backups from the FTP server.

### 4. Logging
- Logs every step of the process: copying, uploading, deleting, and errors.
- Logs are saved in the `backup.log` file.

---

## Installation and Usage

### Requirements
- Python 3.8+
- Libraries:
  - `ftplib`
  - `pathlib`
  - `shutil`

### Installation
1. Clone the repository:
   ```bash
   git clone https://github.com/your-username/ftp-backup-tool.git
   ```
2. Navigate to the project folder:
   ```bash
   cd ftp-backup-tool
   ```

### Configuration
1. Update the settings in `main.py`:
   ```python
   local_folder = r"D:\\Work\\Obsidian"  # Path to the local folder for backups
   backup_folder = r"H:\\Obsidian\\DailyBackup"  # Path to the local backup folder
   ftp_credentials = {
       'host': 'ftp.example.com',
       'username': 'your_username',
       'password': 'your_password'
   }
   remote_folder = "/backups/obsidian"  # Remote folder on the FTP server
   ```

### Run the Script
Run the script using Python:
```bash
python main.py
```

---

## Project Structure

```plaintext
ftp-backup-tool/
├── main.py          # Main script
├── README.md        # Project description
├── backup.log       # Log file (automatically generated)
└── requirements.txt # List of dependencies (if needed)
```

---

## How It Works
1. **Backup Creation:**
   - Creates a local copy of the folder contents with the current date appended to the name.

2. **FTP Upload:**
   - Uploads the backup to a remote folder on the FTP server.
   - Automatically creates folders if they don't exist.

3. **Cleanup of Old Backups:**
   - Deletes local and remote backups older than 30 days.

4. **Logging:**
   - Logs all steps to a file for diagnostics.

---

## Example Log File
```plaintext
2024-12-28 10:00:00,000 - INFO - Starting backup process.
2024-12-28 10:01:00,000 - INFO - Finished copying content from D:\Work\Obsidian to H:\Obsidian\DailyBackup\2024-12-28.
2024-12-28 10:02:00,000 - INFO - Uploaded file to FTP: /backups/obsidian/2024-12-28/file.txt
2024-12-28 10:03:00,000 - INFO - Deleted old backup folder: H:\Obsidian\DailyBackup\2024-11-28.
2024-12-28 10:03:30,000 - INFO - Deleted old FTP backup folder: /backups/obsidian/2024-11-28
2024-12-28 10:04:00,000 - INFO - Backup and upload process completed successfully.
```

---

## Future Improvements
- Add SFTP support for secure uploads.
- Notifications via email or Telegram.
- GUI for configuration and execution.
- Integration with cloud storage (Google Drive, AWS S3).

---

## License
This project is licensed under the MIT License. See the `LICENSE` file for details.

---

<author>Foxhand</author>
<link>https://foxhands.pp.ua</link>

