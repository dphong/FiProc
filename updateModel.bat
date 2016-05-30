set APP_NAME=FiProcess

python manage.py makemigrations %APP_NAME%
python manage.py migrate
PAUSE