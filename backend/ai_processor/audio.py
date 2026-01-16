import paramiko


def trigger_remote_audio():
    try:
        # Configuration for your Pi
        pi_ip = "192.168.1.123"
        pi_user = "nori"
        pi_password = "norielite"  # Or use a key file

        # Create SSH client
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(pi_ip, username=pi_user, password=pi_password, timeout=2)

        # Run the audio command in the background (&) so the GCS doesn't hang
        # 'mpg123 -q' runs it in quiet mode
        command = 'mpg123 -q "/home/nori/Music/Fetty Wap - Again [BASS BOOSTED].mp3" > /dev/null 2>&1 &'
        ssh.exec_command(command)

        print("GCS: Triggered audio alert on Raspberry Pi.")
        ssh.close()
    except Exception as e:
        print(f"GCS: Failed to trigger Pi audio: {e}")


def stop_remote_audio(self):
    try:
        # Same connection details as before
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect("192.168.1.123", username="pi", password="your_password")

        # pkill looks for the process by name and terminates it
        command = "pkill mpg123"
        ssh.exec_command(command)

        print("GCS: Sent STOP command to Raspberry Pi audio.")
        ssh.close()
    except Exception as e:
        print(f"GCS: Failed to stop Pi audio: {e}")


if __name__ == "__main__":
    trigger_remote_audio()
