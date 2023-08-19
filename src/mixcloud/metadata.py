import music_tag

def metadata(filePath, title, artist, genre, epNr, date):
    meta = music_tag.load_file(filePath)
    meta['title'] = title
    meta['artist'] = artist
    meta['genre'] = genre
    meta['tracknumber'] = str(epNr)
    meta['date'] = str(date)
    meta.save() 