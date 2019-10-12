# Instagram Scraper
Uses instagram-private-api to download posts of the users that a user follows. Reliant on a few .txt files that you must write yourself:

## Required

usersnames.txt: the usersname(s) of users you will log into to access the API. Separate each username with a new line.

passwords.txt: the password(s) accompanying the username(s) in usersnames.txt. 

program_last_ran.txt: This will download all the available posts. When the program is ran again, it will download the posts that have been uploaded since the program was last ran. Put the output of the following code block into your post if you want to download all posts since yesterday - time.time() will output the number of seconds since the epoch (December 31st, 1969).
```python
>>> import time
>>> print(time.time() - (1 * 24 * 60 * 60)) # 1 day ago * 24 hours per day * 60 minutes per hour * 60 seconds per minute
1570829823.5312817
```


## Optional

paths.txt: the full path to where you want images and videos to be downloaded, using front slashes instead of backslashes. Separate the path to images and videos with a new line. Otherwise, downloads to wherever the project is located. Example: 

C:/User/Pictures

C:/User/Videos

## Created by the program
users_to_not_download.txt: This file is created by the program. If the program errors out, then you can resume and it will not download the stories of the users inside this .txt file.


## Demonstration of use:

![](https://i.imgur.com/bSH3GfI.gif)


## Afterwards:

![](https://i.imgur.com/fj1vJLR.png)



Due to rate limit errors, if one sends too many requests to the API, an account will be rate limited (and locked out of the API). To try to combat this, the program sleeps a random amount between 50 and 60 seconds in between each users posts that it accesses. If one has multiple accounts to download with and inputs them into usernames.txt and passwords.txt, the program will attempt to log into each of them sequentially.

## Possible improvements

  * multithreading with each client.
  * GUI 
  * Better use of environment variables



## To come

  * PyTorch image classifier using these photos and various other ML related applications to social media (seeing effects of tags and captions on exposure).



## Known bugs 

If the program crashes (or errors out), on next run, it resumes downloading everyone - except those you told it not too. If it crashes often, users_to_not_download.txt grows exponentially in size. Admittedly, for this to be a problem, it'd take about 40+ tries. It also resets on succesful completion of the program.
