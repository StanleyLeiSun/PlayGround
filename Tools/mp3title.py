import file_ext as fe
import os
import mutagen


from mutagen.easyid3 import EasyID3
 
def modify_mp3_info(file_path, title, artist, album):
    audio = EasyID3(file_path)
    audio['title'] = title
    ##audio['artist'] = artist
    ##audio['album'] = album
    audio.save()
    print("Update", file_path, title)

if __name__ == '__main__':
    img_path = "/Users/stansun/Downloads/mp3/"
    files = fe.get_file_list(img_path)
    print("Found %d files totally."%len(files))

    for file_path in files:
        base_name = os.path.basename(file_path)
        end_pos = len(base_name)-8
        modify_mp3_info(file_path, base_name[5:end_pos], "", "")

    

