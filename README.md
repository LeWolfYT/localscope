# My Weather Station

Do you like the Wii Forecast Channel? Maybe The Weather Channel's older WeatherStar units? Maybe you just want a fun way of checking the weather? Look no further! (#TODO: Remind me to add some more info here.)

## Setup

While setting up the app, you'll need to create a `vars.py` file in the same folder as the main program. An example is demonstrated below.
```python
daytheme = "/path/to/music.mp3"
nighttheme = "/my/other/music.mp3"
```
Right now, you can also set the `weatheraddr` variable, which can be used to modify the location of the [wttr.in](https://wttr.in) API call. This value defaults to https://wttr.in?format=j2, which will do its best to approximate your location. You can set this to something like https://wttr.in/Myrtle_Beach?format=j2 to give it a better idea of your location.

## Contributing

This project is in **very active** development and any and all contributions are welcome! I'll be making it a goal to label some of my spaghetti code to make contributing easier.
