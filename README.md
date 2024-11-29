

### How to

- Install GDAL Globally if cannot install inside pipenv

- Install Depedencies `pipenv install`
- Start pipenv `pipenv shell`
- Exit pipenv `exit`
- Check if in pipenv `echo $PIPENV_ACTIVE`
- Install new depedency `pipenv install package_name`
- Check depedencies `pipenv graph`

### CheatSheet

- Must go inside PIPENV Shell
- Run project `python manage.py runserver`
- DB Migration `python manage.py migrate`
- Create module `python manage.py startapp module_name`
- Create superuser `python manage.py createsuperuser`
    - username : superuser
    - email : superuser@localhost.com
    - password : #Abcd1234

#### Run Migrations after create new model to create the table

- python manage.py makemigrations batas_wilayah
- python manage.py migrate

### Problems

- When install package using pipenv, the vscode won't find the import. Change the python source to pipenv. Or install the package using pip instead of pipenv 


### Other

- Test API `http://localhost:8000/api/worldborders/100/?format=json`


### Connect PostGIS to GeoServer

- Login
- Click `Stores`
- Add new Store -> PostGIS
- host use `docker-name`, save
- Click `Layers`
- Add new layer, from PostGIS
- Choose the table

Filter Using CQL 
http://localhost:5050/geoserver/ne/wms?service=WMS&version=1.1.0&request=GetMap&layers=ne%3Atb_batas_wilayah&bbox=-180.0%2C-90.0%2C180.0%2C83.62359619140625&width=768&height=370&srs=EPSG%3A4326&styles=&format=application/openlayers&CQL_FILTER=file_metadata_id=%27d75961f9-8eec-4a7e-8bff-b2272b7dd3d6%27