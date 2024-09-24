

### How to

- Install GDAL Globally if cannot install inside pipenv

- Install Depedencies `pipenv install`
- Start pipenv `pipenv shell`
- Exit pipenv `exit`
- Check if in pipenv `echo $PIPENV_ACTIVE`
- Install new depedency `pipenv install package_name`
- Check depedencies `pipenv graph`

### CheatSheet

- Run project `python manage.py runserver`
- DB Migration `python manage.py migrate`
- Create module `python manage.py startapp module_name`
- Create superuser `python manage.py createsuperuser`
    - username : superuser
    - email : superuser@localhost.com
    - password : #Abcd1234

### Problems

- When install package using pipenv, the vscode won't find the import. Change the python source to pipenv. Or install the package using pip instead of pipenv 


### Other

- Test API `http://localhost:8000/api/worldborders/100/?format=json`
