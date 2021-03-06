import os
import pickle
import requests

# Karaoke Mugen repository to scrape from
kara_list_url = "https://kara.moe/api/karas/"
media_download_url = "https://kara.moe/downloads/medias/{mediafile}"
kara_bundle_url = "https://kara.moe/api/karas/{kid}/raw"

# Language to scrape
language = "jpn"
# Sub filetype to scrape for
sub_file = ".ass"

# Audio bitrate & sample rate
bitrate = 24000
rate = 12000

# Location to save
save_location = "./data/ass/"

# ffmpeg command
ffmpeg = "ffmpeg -i {input} -ac 1 -ab {bitrate} -ar {rate} -y -vn {output}.mp3"


# Open the karaoke list
kara_list = requests.get(kara_list_url)
# We only care about the content, so ignore everything else
kara_list = kara_list.json()['content']

# Filter to only the language
kara_list = filter(lambda kara: len(kara['langs']) == 1 and kara['langs'][0]['name'] == language, kara_list)

# Filter to the filetype
kara_list = list(filter(lambda kara: str(kara['subfile']).endswith(sub_file), kara_list))

# Get the mediafile and the kid
mediafiles = list(map(lambda kara: kara['mediafile'], kara_list))
kids = list(map(lambda kara: kara['kid'], kara_list))

# For progress
size = len(mediafiles)
i = 1

# to download in reverse
# mediafiles.reverse()
# kids.reverse()
# otherwise zip
everything = zip(mediafiles, kids)

# Save the processed list
with open(save_location + "../ass.pickle", 'wb') as f:
    # store the data as binary data stream
    pickle.dump(everything, f)

# Start processing everything
for (mediafile, kid) in everything:
    if os.path.exists(save_location + kid + ".mp3"):
        # Skip if the file is already downloaded
        i = i + 1
        continue
    print("Downloading", i, "of", size, "...", mediafile)
    # Get metadata for lyrics
    metadata = requests.get(kara_bundle_url.format(kid=kid))
    # Get the lyrics
    lyrics = metadata.json()['lyrics']['data']

    # Save the lyrics to the appropriate file
    with open(save_location + kid + sub_file, 'wb') as f:
        f.write(bytes(lyrics, 'utf-8'))

    # Save the video
    video_name = requests.utils.quote(mediafile, safe='~()*!.\'')
    video = requests.get(media_download_url.format(mediafile=video_name))
    with open(save_location + video_name, 'wb') as f:
        f.write(video.content)

    # re-encode
    os.system(ffmpeg.format(input=save_location+video_name, output=save_location+kid, rate=rate, bitrate=bitrate))
    os.remove(save_location+video_name)

    # update progress
    i = i + 1

print("done!")
