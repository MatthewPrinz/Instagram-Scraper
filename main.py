import instagram_private_api
import datetime
import time as t
import requests
import shutil
import random as r
import os
from instagramclasses import User
from typing import List, Dict


def read_time() -> str:
    """
    :return: returns the time the program started
    """
    with open("program_last_ran.txt", 'r') as text:
        time = text.readline()
        return time


def write_time(time_in: str):
    with open("program_last_ran.txt", 'w') as text:
        text.write(time_in)


def check_users(login_information: Dict[str, str]) -> Dict[str, str]:
    """
    The instagram API is fickle. Users are blocked due to downloading too much data (sentry error) or suspicious logins
    (checkpoint challenge). This will only return users which can download data.
    :param login_information: dictionary. keys: usernames. values: passwords.
    :return: dictionary of working logins
    """
    working_logins = {}
    for username, password in login_information.items():
        try:
            api = instagram_private_api.Client(username, password)
            api.login()
            api.logout()
            working_logins[username] = password
        except instagram_private_api.errors:
            pass
    return working_logins


def get_stories(api: instagram_private_api.Client, user: User, image_path='', video_path='', **kwargs):
    """
    :param api: Instagram API client that is given
    :param user: User type
    :param user: username
    :param image_path: path to where you want to download images to.
    :param video_path: path to where you want to download videos to.
    :return: return is in local folder.
    """
    past = 0
    for k, v in kwargs.items():
        if k == "past":
            past = v

    story_of_user_id = api.reels_media([user.user_id])  # story of the given user_id. You could input
    # an entire list of user_ids, but I just do them one at a time due to how the driver function works.

    for random_id, story_info in story_of_user_id['reels'].items():
        for item in story_info['items']:
            # item is an "element" in the story. A story is composed of different elements which one
            # could tap through, essentially, and an item is just one of those elements.
            if item['taken_at'] > past:
                if item['media_type'] == 1:
                    image_url = item['image_versions2']['candidates'][0]['url']
                    download_media(image_url, user, 1, False, image_path=image_path)
                if item['media_type'] == 2:
                    # Turns out, video stories have an image representation. I save that along with the .mp4 itself.
                    image_url = item['image_versions2']['candidates'][0]['url']
                    download_media(image_url, user, 1, True, image_path=image_path)

                    video_url = item['video_versions'][0]['url']
                    download_media(video_url, user, 2, False, video_path=video_path)


def get_timeline(api: instagram_private_api.Client, user: User, last_ran: float, image_path='', video_path='') -> None:
    """
    Downloads the timeline of a user.
    :param api: Instagram API client that is given
    :param user: person to download, given as type User
    :param last_ran: time the program was last ran at.
    :param image_path: path to where you want to download images to.
    :param video_path: path to where you want to download videos to.
    :return: returns None
    """
    a_feed = api.user_feed(user.user_id)
    pictures_to_download = []
    videos_to_download = []

    # We iterate through the posts on someone's timeline.
    for post in a_feed['items']:

        # Only download if the media was posted later than the time the program was last ran.
        if post['taken_at'] > last_ran:

            # Indicates that the media is a video.
            if post['media_type'] == 2:
                potential_videos = {}

                # Iterates through the different versions of the videos, adds them to potential_videos
                for video in post['video_versions']:
                    if type(video) == dict:
                        if 'width' in video.keys() and 'height' in video.keys() and 'url' in video.keys():
                            potential_videos[video['url']] = video['width'] * video['height']

                # Appends the url of the highest resolution video to the download_list.
                videos_to_download.append(max(potential_videos, key=lambda key: potential_videos[key]))

            # If the post has an image version, add it to downloads.
            if 'image_versions2' in list(post.keys()):
                # Dictionary which stores the two photos. The two photos will be different in quality - one will be
                # higher, one will be lower.
                potential_photos = {}

                # Iterates through the two different quality images
                for i, ele in enumerate(post['image_versions2']['candidates']):

                    # Images are given as ['image_versions2'] and carousels are given as ['carousel_media']
                    if 'width' in ele.keys() and 'height' in ele.keys() and 'url' in ele.keys():

                        # We create a dictionary to store the 2 candidate photos: their url & their size in pixels
                        potential_photos[ele['url']] = ele['width'] * ele['height']

                # Adds the picture with the highest resolution
                pictures_to_download.append(max(potential_photos, key=lambda key: potential_photos[key]))

            # This deals with carousels - i.e. ONE post which you can flip through and see various media types.
            elif 'carousel_media' in list(post.keys()):
                potential_photos = {}

                # Carousel media is a list which contains the various media objects.
                for ele in post['carousel_media']:
                    carousel_photos = []

                    # The if statements ensure we only add JSON photo objects.
                    for photo in ele['image_versions2']['candidates']:
                        if type(photo) == dict:
                            if 'width' in photo.keys() and 'height' in photo.keys() and 'url' in photo.keys():
                                carousel_photos.append(photo)

                    # We add the two photos into potential_photos.
                    for photo in carousel_photos:
                        potential_photos[photo['url']] = photo['width'] * photo['height']

                    # We only want the highest quality photo (i.e. the photo with the higher pixelation)
                    pictures_to_download.append(max(potential_photos, key=lambda key: potential_photos[key]))
                    potential_photos.clear()

    # We're done using the api for now, so might as well.
    api.logout()

    for url in videos_to_download:
        download_media(url, user, 2, False, video_path=video_path)

    # Feeds the collected urls one at a time into download_media.
    for url in pictures_to_download:
        download_media(url, user, 1, False, image_path=image_path)


def download_media(url: str, user: User, media_type: int, image_of_video_story: bool, image_path='', video_path='')\
        -> None:
    """
    :param url: url of content to download
    :param user: User type
    :param media_type: 1: image. 2: video.
    :param image_of_video_story: boolean, True if image of a video story, False otherwise
    :param image_path: path to where you want to download images to.
    :param video_path: path to where you want to download videos to.
    :return: downloaded image or video
    """
    uniquely_identifiable_code = str(int(t.time() * 1000))
    video_name_no_extension = user.user_name + uniquely_identifiable_code
    if image_of_video_story:
        image_name_no_extension = user.user_name + "IMAGE_OF_VIDEO_STORY" + uniquely_identifiable_code
    else:
        image_name_no_extension = user.user_name + uniquely_identifiable_code

    image_name = image_path + image_name_no_extension + '.jpg'
    video_name = video_path + video_name_no_extension + '.mp4'
    full_image_name = os.path.join(image_path, image_name)
    full_video_name = os.path.join(video_path, video_name)
    if media_type == 1:
        # get file-like object from request
        response = requests.get(url, stream=True)
        if response.status_code == 200:
            with open(full_image_name, 'wb') as out_file:
                response.raw.decode_content = True
                shutil.copyfileobj(response.raw, out_file)
        else:
            print(f'Photo downloading: Response.status code != 200. It is: {response.status_code}')
    if media_type == 2:
        video_data = requests.get(url, stream=True)
        if video_data.status_code == 200:
            with open(full_video_name, 'wb') as out_file:
                video_data.raw.decode_content = True
                shutil.copyfileobj(video_data.raw, out_file)
        else:
            print(f'MP4 dowloading: Response.status code != 200. It is: {video_data.status_code}')
        del video_data


def dict_to_user_list(dict_for_now: dict, do_not_download_list: List[str], default_status=False) -> List[User]:
    """
    :param default_status: set all stories to not download (False), set all stories to download (True)
    :param dict_for_now: input: dict where keys are usernames and values are user_ids
    :param do_not_download_list: users to not download
    :return: list of User class
    """
    result = []
    for k, v in dict_for_now.items():
        if k in do_not_download_list:
            person = User(default_status, k, v)
        else:
            person = User(default_status, k, v)
        result.append(person)

    return result


def user_list_to_dict(user_list: List[User]) -> Dict[str, int]:
    """
    :param user_list: list of class User
    :return: dictionary with keys = username, values = user_ids.
    """
    result = {}
    for user in user_list:
        result[user.user_name] = user.user_id
    return result


def first_run(api: instagram_private_api.Client) -> Dict[str, int]:
    """
    Finds all users that you are following, and puts them into a dictionary.
    :param api: Instagram API that is logged into
    :return: dictionary. key: instagram username. value: instagram user_id
    """
    # Initialize result dictionary
    dict_of_users_following = {}

    # Iterate through client's user_following. uses user_id and uuid, returns a dictionary we go through
    for user in api.user_following(api.authenticated_user_id, api.generate_uuid())['users']:
        # every use is a dictionary. 'pk' is user_id. username is username.
        dict_of_users_following[user['username']] = user['pk']
    # Return result
    return dict_of_users_following


def login(username: str, password: str):
    """
    Logs into instagram-api using username and password
    :param username:
    :param password:
    :return: api or failed username
    """
    error = True
    while error:
        try:
            api = instagram_private_api.Client(username, password)
            api.login()
            return api
        except instagram_private_api.errors.ClientCheckpointRequiredError:
            print(f" Checkpoint challenge required, user {username} failed, returning..")
            return username
        except instagram_private_api.errors.ClientSentryBlockError:
            print(f"Sentry block error, user {username} failed, returning...")
            return username
        except instagram_private_api.errors.ClientError as clienterror:
            print(f'{clienterror.msg}')
            return username


def set_usernames_passwords() -> int:
    """
    Reads in usernames and passwords from usernames.txt and passwords.txt respectively. Assumes that the first line of
    usernames.txt is a username with password that corresponds to the first line of the passwords.txt file, same for
    the second and third line.
    :return: Returns number of environment variables set (representing number of accounts to create)
    """
    # Reads in usernames from usernames.txt and passwords from passwords.txt
    with open("usernames.txt", 'r') as usernames, open("passwords.txt", 'r') as passwords:
        count = 0
        # This is the key behind assuming that the first line username corresponds with the first password.
        for username, password in zip(usernames, passwords):
            name_of_env_var = 'API_User' + str(count)
            # Splicing out \n that is added from the for loop
            if '\n' in username:
                username = username.replace('\n', '')
            # Setting environment variable API_UserI to username from line I in usernames.txt
            os.environ[name_of_env_var] = username
            key_of_env_var = 'Password' + str(count)
            if '\n' in password:
                password = password.replace('\n', '')
            # Setting environment variable PasswordI to password from line I in password.txt
            os.environ[key_of_env_var] = password
            count += 1
    return count


def create_login_dictionary(num_accounts: int) -> Dict[str, str]:
    """
    Creates the login dictionary.
    :param num_accounts: number of accounts to create (based on set_usernames_passwords())
    :return: dictionary with keys as usernames and values as passwords, to log into the API with
    """
    login_dictionary = {}
    for i in range(num_accounts):
        login_dictionary[os.environ['API_User' + str(i)]] = os.environ['Password' + str(i)]
    return login_dictionary


def main():
    # 1) Stores the time the program was started at.
    # 2) Finds and prints the time the program was last run at.
    # 3) Sets up login_information, a dictionary with keys as usernames and values as passwords to log into the api with
    # 4) Attempts to log in using login_information
    # ================================================================================================================ #
    last_ran = float(read_time())
    print(f'Program last ran at: {t.ctime(float(last_ran))}.')
    print(f'It has been {str(datetime.timedelta(seconds=t.time() - last_ran))}.')
    program_start = t.time()
    login_information = create_login_dictionary(set_usernames_passwords())
    username = list(login_information.keys())[0]
    password = list(login_information.values())[0]
    api = login(username, password)
    new_username = username
    error_on_login = False
    if type(api) == str:
        # This is because login returns the username of the failed user - thus, if logging in does not work, api will be
        # a string representing the username that could not log in.
        error_on_login = True
    try:
        while error_on_login:
            del login_information[api]
            new_username = r.choice(list(login_information.keys()))
            api = login(new_username, login_information[new_username])
            if type(api) != str:
                error_on_login = False
    except IndexError:
        print(f'No more usernames to choose from. Exiting.')
        quit()
    print(f"Using account: {new_username}.")
    # ================================================================================================================ #
    # Used to keep track of progress
    # ================================================================================================================ #
    idx = 0
    # ================================================================================================================ #
    # Dictionary of users to download.
    # ================================================================================================================ #
    dict_for_now = first_run(api)
    # ================================================================================================================ #
    # Format: users_to_not_download.txt should have all usernames that one does not want to download inside, each split
    # by \n
    #
    # If users_to_not_download.txt exists, read from it and do not download all users inside.
    # users_to_not_download.txt will be deleted at the end of the program. If the program crashes - no worries you don't have to re-make users_to_not_download.txt
    # ================================================================================================================ #
    names_entered_by_user = []

    # For the following while loop
    run_input_loop = True
    program_crashed = False

    # Only exists if created in the past iteration due to the program erroring/crashing out
    if os.path.exists("users_to_not_download.txt"):
        with open("users_to_not_download.txt", 'r') as text:
            names_entered_by_user.append(text.read())
        names_entered_by_user = names_entered_by_user[0].split('\n')
        program_crashed = True
    # ================================================================================================================ #
    # Sometimes you don't want to download some users stories.
    # ================================================================================================================ #
    inverse_dict_to_user_flag = True
    while run_input_loop and not program_crashed:
        user_input = input("Input the username of a user whose story you do want to download. Enter a c "
                           "followed by a comma separated list, \nenter an x if you want to download all except the "
                           "users you have written, or\nenter an n if you want to begin downloading.\n")
        if user_input == "n":
            run_input_loop = False
        elif user_input == "c":
            comma_separated_list = input("Enter the comma separated list: ")
            names_entered_by_user = comma_separated_list.split(", ")
            run_input_loop = False
        elif user_input == "x":
            inverse_dict_to_user_flag = False
        else:
            names_entered_by_user.append(user_input.strip())
    if inverse_dict_to_user_flag:
        print(f'Users stories being downloaded: {names_entered_by_user}')
    else:
        print(f'Users stories not being downloaded: {names_entered_by_user}')
    if not os.path.exists("users_to_not_download.txt"):
        f = open("users_to_not_download.txt", "w+")
        f.close()
    for user in names_entered_by_user:
        with open("users_to_not_download.txt", 'a') as text:
            text.write(user + '\n')
    correct_cond = input("Is this correct? Press any key but n if it is. Type clear to wipe the old list and exit the "
                         "program\n")
    if correct_cond == "n":
        quit()
    if correct_cond == "clear":
        os.remove("users_to_not_download.txt")
        quit()
    if inverse_dict_to_user_flag:
        users_followed = dict_to_user_list(dict_for_now, names_entered_by_user, False)
    else:
        users_followed = dict_to_user_list(dict_for_now, names_entered_by_user, True)
    # ================================================================================================================ #
    # Does the actual downloading.
    # ================================================================================================================ #
    try:
        with open('paths.txt', 'r') as paths:
            image_path = paths.readline().replace('\n', '')
            video_path = paths.readline()
    except FileNotFoundError:
        image_path = str(os.getcwd()).replace('\\', '/') + '/'
        video_path = str(os.getcwd()).replace('\\', '/') + '/'
    for person in users_followed:
        try:
            time_to_sleep = r.randint(50, 60)
            api.login()
            print(f'Starting to download user: {person}')
            get_timeline(api, person, last_ran, image_path, video_path)
            if person.download_story:
                get_stories(api, person, image_path, video_path, past=last_ran)
            print(f'Sleeping for: {time_to_sleep}s. This is done to prevent rate limit errors.')
            # Don't wait on the last user.
            if person != users_followed[len(users_followed)-1]:
                t.sleep(time_to_sleep)
        except instagram_private_api.errors.ClientCheckpointRequiredError:
            print(f" Checkpoint challenge required, user {new_username} failed. Removing {new_username} from pool of "
                  f"users to download with")
            del login_information[new_username]
            new_username = r.choice(list(login_information.keys()))
            api = ""
            while type(api) == str:
                if not login_information:
                    print(f"Trying username: {new_username}.")
                    api = login(new_username, login_information[new_username])
                    if type(api) != str:
                        api.login()
                    else:
                        del login_information[new_username]
                        new_username = r.choice(list(login_information.keys()))
                else:
                    print(f'Out of usernames to try. Exiting the program')
                    quit(-1)
            print(f'Using new username {new_username}')
            print(f'Adding {person} to end of the queue.')
            users_followed.append(person)
        except instagram_private_api.errors.ClientSentryBlockError:
            print(f"Sentry block error, user {new_username} failed. Removing {new_username} from pool of users "
                  f"to download with")
            del login_information[new_username]
            new_username = r.choice(list(login_information.keys()))
            # Unfortunately, the following duplicated code block is necessary to get the correct error message printed
            # out
            api = ""
            while type(api) == str:
                if not login_information:
                    print(f"Trying username: {new_username}.")
                    api = login(new_username, login_information[new_username])
                    if type(api) != str:
                        api.login()
                    else:
                        del login_information[new_username]
                        new_username = r.choice(list(login_information.keys()))
                else:
                    print(f'Out of usernames to try. Exiting the program')
                    quit(-1)
            print(f'Using new username {new_username}')
            print(f'Adding {person} to end of the queue.')
            users_followed.append(person)
        except instagram_private_api.errors.ClientError as clienterror:
            if str(clienterror) == 'Bad Request: rate_limit_error':
                print(f"Rate limit error, user {new_username} failed. Removing {new_username} from pool of "
                      f"users to download with")
                del login_information[new_username]
                new_username = r.choice(list(login_information.keys()))
                # Unfortunately, the following duplicated code block is necessary to get the correct error message
                # printed
                # out
                api = ""
                while type(api) == str:
                    if not login_information:
                        api = login(new_username, login_information[new_username])
                        if type(api) != str:
                            api.login()
                        else:
                            del login_information[new_username]
                            new_username = r.choice(list(login_information.keys()))
                    else:
                        print(f'Out of usernames to try. Exiting the program')
                        quit(-1)
                print(f'Adding {person} to end of the queue.')
                users_followed.append(person)
            else:
                print(f'ClientError downloading {person}. Error given: {clienterror} .')
        idx += 1
        print(f'Finished {person.user_name}, user {idx} of {len(users_followed)}')
    # ================================================================================================================ #
    # Logging out, rewriting the time the program started at, and removing duplicates from carousel downloading.
    # ================================================================================================================ #
    api.logout()
    print(f'Program started at {t.ctime(float(program_start))}. Total runtime: '
          f'{str(datetime.timedelta(seconds=t.time() - program_start))}')
    write_time(str(program_start))
    os.remove("users_to_not_download.txt")


def testing():
    pass

if __name__ == "__main__":
    main()
