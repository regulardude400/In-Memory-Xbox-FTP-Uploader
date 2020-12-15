"""This module was created to help you transfer your 7z compressed Xbox games to
your Xbox without having to worry about disk space. It's main feature is that it
extracts files in RAM and uploads them to your Xbox. You will need at least 7GB
or more of free memory to support any titles that use Dual Layer DVD like
Ninja Gaiden (~6.2GB) or The Guy Game (~6.5GB)."""

import py7zr  # Module used for 7z extraction.
import os  # Necessary module to find files in directory.
import shutil  # Used for empty recursive folder deleting.
import ftplib  # Used for ftp connections.
import traceback  # Used to catch the errors.
import getpass  # Used to display blank or asterisks while you type your password if not using idle or Jupyter
from functools import partial  # Necessary to pass more than one arg to pool.map.
from multiprocessing.dummy import Pool as ThreadPool  # Used to upload more than one file at a time.

pool = ThreadPool(2)  # We only want a max of x connections to our Xbox. 2 is default and safe.

ftp_server_ip = ''  # Global placeholder for the server ip.
ftp_server_username = ''  # Global placeholder for the server username.
ftp_server_password = ''  # Global placeholder for the server password.


def upload(item, game_folder):
    try:
        ftp = ftplib.FTP(ftp_server_ip)
        ftp.login(ftp_server_username, ftp_server_password)  # Your xbox ftp credentials. Default is xbox, xbox
        full_file_path = item[0]
        bio = item[1]  # This is the byteIO object which is the file data
        split_file_paths = str(full_file_path).split("/")  # Split the path by /
        file_name = split_file_paths[-1]  # Get the last element which is file_name
        sub_dir = "/".join(split_file_paths[1:-1])  # Get all the subdirectories
        file_path = game_folder + sub_dir  # Combine the game folder and sub dir
        remote_game_dir_without_file_name = "/".join(split_file_paths[0:-1])
        ftp.cwd(file_path)  # Change the current remote directory
        cmd_file = "STOR " + file_name  # The command to upload a file + file to upload
        ftp.storbinary(cmd_file, bio, 102400)  # Upload the file in 100kb block size.
        path_to_delete = './' + split_file_paths[0]  # Let's specify the directory to remove.
        if os.path.exists(path_to_delete):
            shutil.rmtree(path_to_delete)  # Remove the specified directory.
        print(str(file_name), " has been uploaded successfully on your Xbox in dir: ",
              remote_game_dir_without_file_name)
        ftp.quit()  # Close and quit the session else we get connection refused errors on Xbox
    except Exception:
        print(traceback.format_exc())  # Print the error in it's entirety.
        try:
            print("There was an error uploading the file: ", str(file_name))
        except Exception:
            print("There was an error uploading the current file and when trying to get the local filename.")

        try:
            print("Please try to manually upload the file to: ", str(file_path))
        except Exception:
            print("Please try to manually upload the file to the correct remote folder. The local folder path could "
                  "not be obtained for this particular file: ", str(file_name))


def decompress_game_in_memory():
    for root, dirs, files in os.walk(".", topdown=False):  # For the directories and files in the root folder.
        for file in files:  # For file in files.
            if ".7z" in file:
                try:
                    if not os.path.exists("Copy_Games_to_Original_Xbox_progress.txt"):
                        with open("Copy_Games_to_Original_Xbox_progress.txt", "w") as new_file:
                            new_file.write("")  # Write a blank file if the file doesn't exist yet.
                    with open("Copy_Games_to_Original_Xbox_progress.txt") as progress_file:
                        completed_files_dict = {}
                        for game in progress_file:
                            completed_files_dict[game.strip("\n")] = True  # Game has already been uploaded.

                        if str(file) not in completed_files_dict:
                            archive = py7zr.SevenZipFile(file, mode='r')  # Open the file in read mode.
                            game_folder = '/F/Games/' + str(file)[:-7] + "/"  # Set the remote dir
                            print("Reading the archive's file list and file data for: ", str(file), "\nPlease wait...")

                            if archive:
                                data = list(archive.readall().items())  # Read all file and their data in archive
                                pool.map(partial(upload, game_folder=game_folder), data,
                                         chunksize=1)  # Pool the uploads.
                                archive.close()  # Close the file
                                with open("Copy_Games_to_Original_Xbox_progress.txt", "a") as new_progress_file:
                                    new_progress_file.write(str(file) + "\n")  # If game was uploaded, add name to EOF.
                        else:
                            print(str(file), " has been uploaded already.")
                            print("To upload it again, remove the individual line or delete the entire "
                                  "Copy_Games_to_Original_Xbox_progress.txt file")
                except Exception:
                    print(traceback.format_exc())
                    print("There was an issue reading the file: ", str(file))
                    print("Skipping to the next file.")
    pool.close()  # Stop the pool.
    pool.join()  # Let all remaining connections gracefully terminate.
    print("All done!")


def show_ftp_settings():
    info_list = []  # List to hold the settings.
    if not os.path.exists("Copy_Games_to_Original_Xbox.ini"):
        print("File doesn't exist")
        with open("Copy_Games_to_Original_Xbox.ini", "w") as ini_file:
            ini_file.write("192.168.1.80\nxbox\nxbox")  # If the ini file doesn't exist, create it and give it settings.
    with open("Copy_Games_to_Original_Xbox.ini", "r") as ini_file:
        for line in ini_file:
            info_list.append(str(line).strip("\n"))  # Read each line and strip the newline to read the settings cleanly

    if info_list:
        global ftp_server_ip  # We want to declare that we are using the global object instead of local object.
        global ftp_server_username
        global ftp_server_password
        ftp_server_ip = info_list[0]
        ftp_server_username = info_list[1]
        ftp_server_password = info_list[2]

    print("Server IP Address: ", ftp_server_ip)
    print("Server Username: ", ftp_server_username)
    print("Server Password: ", "*Intentionally hidden. Please check Copy_Games_to_Original_Xbox.ini*")


def check_if_ip_is_valid(ip_input):
    octet_list = ip_input.split('.')  # Split the input by the period.
    if len(octet_list) == 4:  # Check if 4 octets (in binary) exists.
        for octet in octet_list:
            if 0 <= int(octet) <= 255:  # We want the number to be >= 0 and <= 255
                valid = True
            else:
                return False
    else:
        return False
    return valid


def change_ftp_settings(user_input=''):
    info_list = []
    while user_input not in ('1', '2', '3', '4'):
        user_input = input("Please select which action you wish to do."
                           "\n1: Change Server IP Address\n2: Change Server Username\n3: Change Server Password"
                           "\n4: Return to main menu.\n")

        if user_input == '1':
            ip_input = input("Please type in the ip address in this format: xxx.xxx.xxx.xxx\n")
            try:
                if check_if_ip_is_valid(ip_input):
                    info_list.append(ip_input + "\n")
                    with open("Copy_Games_to_Original_Xbox.ini", "r") as ini_file:
                        for line in list(ini_file)[1:]:
                            info_list.append(str(line))
                    with open("Copy_Games_to_Original_Xbox.ini", "w") as ini_file:
                        for line in info_list:
                            ini_file.write(line)
                    print("Updated the ini file with the new IP: ", str(ip_input))
                else:
                    print("An error occurred while trying to verify your IPv4 Address Please enter it in this format "
                          "all numeric: xxx.xxx.xxx.xxx")
                    user_prompt()
            except Exception:
                print("You have entered non numeric characters or as the ip address. Please try again.\n")
                user_prompt()

        elif user_input == '2':
            username_input = input("Please enter the username that you wish to use.\n")
            try:
                save_to_file_input = str.lower(input("Do you wish to save this username to file?(y/n)\n"))
                while save_to_file_input in ('y', 'n'):
                    if save_to_file_input == 'y':
                        with open("Copy_Games_to_Original_Xbox.ini", "r") as ini_file:
                            for line, value in enumerate(list(ini_file)):
                                if line == 1:
                                    info_list.append(str(username_input))
                                else:
                                    info_list.append(str(value).strip("\n"))

                        with open("Copy_Games_to_Original_Xbox.ini", "w") as ini_file:
                            for line in info_list:
                                print(line)
                                ini_file.write(line + "\n")

                        with open("Copy_Games_to_Original_Xbox.ini", "r") as ini_file:
                            for line, value in enumerate(list(ini_file)):
                                print(value)

                        print("Updated the ini file with the new username: ", str(username_input))
                    elif save_to_file_input == 'n':
                        global ftp_server_username
                        ftp_server_username = str(username_input)
                    else:
                        print("An error occurred while trying to update the username. Please try again.\n")
                    user_prompt()

            except Exception:
                print("An error has occurred. Please report this to the developer on github.\n")
                user_prompt()

        elif user_input == '3':
            password_input = (getpass.getpass("Please enter the password that you wish to use.\n"))
            try:
                save_to_file_input = str.lower(input("Do you wish to save this username to file?(y/n)\n"))
                while save_to_file_input in ('y', 'n'):
                    if save_to_file_input == 'y':
                        with open("Copy_Games_to_Original_Xbox.ini", "r") as ini_file:
                            for line, value in enumerate(list(ini_file)):
                                if line == 2:
                                    info_list.append(str(password_input))
                                else:
                                    info_list.append(str(value).strip("\n"))

                        with open("Copy_Games_to_Original_Xbox.ini", "w") as ini_file:
                            for line in info_list:
                                ini_file.write(line + "\n")
                        print("Updated the ini file with the new password: ")
                    elif save_to_file_input == 'n':
                        global ftp_server_password
                        ftp_server_password = str(password_input)
                    else:
                        print("An error occurred while trying to update the username. Please try again.\n")
                    user_prompt()

            except Exception:
                print("An error has occurred. Please report this to the developer on github.\n")
                user_prompt()

        elif user_input == '4':
            print("Returning to main menu.")
        else:
            print("Invalid selection. Returning to main menu.")
        user_prompt()


def user_prompt(user_input=''):
    while user_input not in ('1', '2'):
        user_input = input("Please select which action you wish to do.\n1: Change FTP settings"
                           "\n2: Upload all .7z games to your Xbox.\nOr press any other key to quit the program\n")

        if user_input == '1':
            show_ftp_settings()
            change_ftp_settings()
        elif user_input == '2':
            show_ftp_settings()
            decompress_game_in_memory()
        else:
            os._exit(0)


def main():
    user_prompt()


if __name__ == '__main__':
    main()
