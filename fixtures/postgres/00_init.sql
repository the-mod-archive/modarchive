-- Create application user
CREATE USER mod_archive WITH PASSWORD 'mod_archive';

-- Allow application user to create databases for tests/migrations
ALTER USER mod_archive CREATEDB;

-- Create application database
CREATE DATABASE mod_archive OWNER mod_archive;
