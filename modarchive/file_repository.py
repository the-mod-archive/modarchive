import os
import tempfile
import zipfile
import shutil

from django.conf import settings
from django.core.files.uploadedfile import UploadedFile

class UploadProcessor:
    def __init__(self, songfile: UploadedFile):
        self.songfile = songfile
        self.unique_temp_dir_path = tempfile.mkdtemp(dir=settings.TEMP_UPLOAD_DIR)
        self.temp_file_path = os.path.join(self.unique_temp_dir_path, songfile.name)

        # Save the uploaded file to the temporary directory
        with open(self.temp_file_path, 'wb') as f:
            for chunk in songfile.chunks():
                f.write(chunk)

    def get_files(self):
        if zipfile.is_zipfile(self.temp_file_path):
            with zipfile.ZipFile(self.temp_file_path, 'r') as zip_ref:
                zip_ref.extractall(self.unique_temp_dir_path)

            os.remove(self.temp_file_path)
            extracted_files = []
            for file_name in os.listdir(self.unique_temp_dir_path):
                file_path = os.path.join(self.unique_temp_dir_path, file_name)
                if os.path.isfile(file_path):
                    extracted_files.append(file_path)
            return extracted_files
        else:
            return [self.temp_file_path]

    def move_into_new_songs(self, file):
        """
        Accepts a file and zips and moves the file from the processing directory to the new files directory
        """

        # Create a zip file with the same name as the original file
        zip_filename = os.path.join(settings.TEMP_UPLOAD_DIR, f"{os.path.basename(file)}.zip")
        with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            zip_file.write(file, arcname=os.path.basename(file))

        # Move the zip file to the new files directory
        final_file_path = os.path.join(settings.NEW_FILE_DIR, f"{os.path.basename(file)}.zip")
        shutil.move(zip_filename, final_file_path)

    def remove_processing_directory(self):
        if os.path.exists(self.unique_temp_dir_path):
            self.delete_files_in_directory(self.unique_temp_dir_path)
            os.rmdir(self.unique_temp_dir_path)

    def delete_files_in_directory(self, directory_path):
        for filename in os.listdir(directory_path):
            file_path = os.path.join(directory_path, filename)
            try:
                if os.path.isfile(file_path) or os.path.islink(file_path):
                    os.unlink(file_path)
                elif os.path.isdir(file_path):
                    os.rmdir(file_path)
            except Exception as e:
                print(f"Failed to delete {file_path}. Reason: {e}")
