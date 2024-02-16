import eyed3

def add_metadata_to_mp3(file_path, show_name, dj_name, ep_nr, genre, year):
    # Load the MP3 file
    audiofile = eyed3.load(file_path)
    
    # Set metadata
    audiofile.tag.artist = dj_name
    audiofile.tag.title = show_name
    audiofile.tag.album = show_name
    audiofile.tag.release_date = year
    audiofile.tag.track_num = (ep_nr, None)  # (track_number, total_tracks)
    audiofile.tag.genre = genre
    
    # Save changes
    audiofile.tag.save()