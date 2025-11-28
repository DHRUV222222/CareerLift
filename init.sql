-- Create the database if it doesn't exist
CREATE DATABASE IF NOT EXISTS careerlift;

-- Create the user if it doesn't exist and grant all privileges
GRANT ALL PRIVILEGES ON careerlift.* TO 'careerlift_user'@'%' IDENTIFIED BY 'your_secure_password';

-- Apply the changes
FLUSH PRIVILEGES;
