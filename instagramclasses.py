"""
Created on: 6/29/2019 at 6:07 PM
@author: Matthew Prinz

WHAT PROGRAM DOES: Provides User and Post class for main.py
    
"""


class Post:
    def __init__(self, url, media_type, user):
        """
        :param url: url of the post
        :param media_type: 1: image. 2: video. 8: carousel. For my purposes, carousels might as well be images (they're
        downloaded the same way)
        """
        self._url = url
        if user is type(int):
            self._user = "__" + user + "__"  # Signifies using a user_id as a user_name, not technically proper, but
            # shouldn't be necessary
        self._user = user

        if media_type == 8:
            self._media_type = 1
        else:
            self._media_type = media_type

    @property
    def media_type(self):
        return self._media_type

    @property
    def url(self):
        return self._url

    @property
    def user(self):
        return self._user

    def __str__(self):
        return self.user

    def __repr__(self):
        return str(self.user)


class User:
    def __init__(self, download_story, user_name, user_id):
        """

        :param download_story: boolean, true or false, should the program download their story yes or no
        :param user_id: given
        :param user_name: given
        """
        self._download_story = download_story
        self._user_id = user_id
        self._user_name = user_name

    @property
    def download_story(self):
        return self._download_story

    @download_story.setter
    def download_story(self, value):
        self._download_story = value

    @property
    def user_id(self):
        return self._user_id

    @user_id.setter
    def user_id(self, val):
        self._user_id = val

    @property
    def user_name(self):
        return self._user_name

    @user_name.setter
    def user_name(self, name):
        self._user_name = name

    def __str__(self):
        return self.user_name

    def __repr__(self):
        result = f'{self.user_name} with ID {self.user_id}.'
        return result
