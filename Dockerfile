# set base image (host OS)
FROM python:3.8-slim-buster

# set the working directory in the container
WORKDIR /app

# copy the dependencies file to the working directory
COPY requirements.txt requirements.txt

# install dependencies
RUN pip install -r requirements.txt

# copy the content of the local src directory to the working directory
COPY Cog.py Cog.py
COPY Persistence.py Persistence.py 
COPY SortingHat.py SortingHat.py

# command to run on container start
CMD [ "python", "./SortingHat.py" ]