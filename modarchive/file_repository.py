import os
import shutil
import tempfile

from django.conf import settings
from django.core.files.uploadedfile import UploadedFile

# 
def put_into_upload_processing(songfile: UploadedFile):
    """
    Accepts an uploaded file and inserts it into a temporary directory.
    Returns the path of the uploaded file in its new location
    """
    unique_temp_dir_path = tempfile.mkdtemp(dir=settings.TEMP_UPLOAD_DIR)
    temp_file_path = os.path.join(unique_temp_dir_path, songfile.name)

    # Save the uploaded file to the temporary directory
    with open(temp_file_path, 'wb') as f:
        for chunk in songfile.chunks():
            f.write(chunk)

    return temp_file_path

def move_into_new_songs(filename, temp_file_path):
    """
    Accepts a filename and temporary file path
    Moves the temporary file into the new files directory, and then cleans up the
    temporary file path by removing it from the directory tree
    """
    final_file_path = os.path.join(settings.NEW_FILE_DIR, filename)
    os.rename(temp_file_path, final_file_path)
    shutil.rmtree(os.path.dirname(temp_file_path))