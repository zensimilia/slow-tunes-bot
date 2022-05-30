from pydub import AudioSegment, utils
from pydub.exceptions import PydubException


async def slow_down(file_path: str, speed: float = 1) -> str:
    """This function slow down audio file."""

    slowed_file = file_path[:-4] + '_slowed_down.mp3'
    try:
        media_info = utils.mediainfo(file_path)
        sound = AudioSegment.from_file(file_path)

        slowed = speed_change(sound, speed)
        slowed.export(
            slowed_file,
            format='mp3',
            bitrate=media_info['bit_rate'],
        )
    except PydubException as error:
        print(error)  # TODO: logger
        slowed_file = ""

    return slowed_file


def speed_change(sound, speed: float = 1.5):
    """Change speed of AudioSegment."""

    # Manually override the frame_rate. This tells the computer how many
    # samples to play per second
    sound_with_altered_frame_rate = (
        sound._spawn(  # pylint: disable=protected-access
            sound.raw_data,
            overrides={"frame_rate": int(sound.frame_rate * speed)},
        )
    )
    # convert the sound with altered frame rate to a standard frame rate
    # so that regular playback programs will work right. They often only
    # know how to play audio at standard frame rate (like 44.1k)
    return sound_with_altered_frame_rate.set_frame_rate(sound.frame_rate)
