# SSH, GitHub, and Power BI Setup Guide

## Obtaining the dashboard
Unfortunately, the only way to access the Power BI dashboard would be for me to provide you with access through Google Drive. 
If you would like to take a look around for yourself, please send me an email on: elliot.kerr@bath.edu.

## SSH

1. Run `ssh-keygen` in Command Prompt.
2. Choose the directory and key name where you want to store your SSH key.
3. Choose a password for your SSH key.
4. Find the SSH files:

   * `cd` into your chosen directory.
   * Run:

     ```cmd
     type ssh_key_name.pub
     ```
   * Copy the entire text displayed.

## GitHub

1. Go to your GitHub account settings.
2. Click **SSH and GPG Keys**.
3. Click **New SSH Key**.
4. Paste your SSH public key.
5. Give the key a name so you can identify it among your different SSH keys.

## Clone the Repository

Clone the repository onto your own device.

Once cloned, `cd` into the repository and run:

```powershell
& "C:\Program Files\Git\bin\bash.exe" ./data_extraction_workflow/start.sh
```

## Create SQLite ODBC Connections for the Gold Database

For information on connecting Power BI to SQLite:

[Can Power BI Connect to a SQLite Database?](https://www.thebricks.com/resources/guide-can-power-bi-connect-to-sqlite-database)

Once you've created the connection:

1. Open **Power BI**.
2. Click **Transform Data**.
3. Click **Data source settings**.
4. Select the current data source and click **Change Source**.
5. Open the dropdown and select your database.
6. Close the pop-up and click **Refresh Preview**.
7. Click **Close and Apply**.

You should now have a locally working Power BI report.

## Running the Python Script

1. Find the Python installation configured in Power BI:

   1. Go to **File**.
   2. Select **Options and settings**.
   3. Select **Options**.
   4. Select **Python scripting**.

2. Note the **Python home directory** shown there, or switch to a Python installation that already has `matplotlib` and `pandas` installed.

3. Open Command Prompt and install any missing packages using that exact Python installation:

   ```cmd
   "C:\path\to\python.exe" -m pip install matplotlib pandas
   ```

4. Restart Power BI.
