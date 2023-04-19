# pull latest image
sudo docker pull whoicd/icd-api

# container port 80 (expected by who api), expose port 8000 to the outside world
sudo docker run -p 8000:80 -e acceptLicense=true -e saveAnalytics=true whoicd/icd-api:latest

# troubleshooting

# what's running on port 80?
sudo ss -pt state listening 'sport = :80'

# remove all existing images
sudo docker rm -fv $(sudo docker ps -aq)

# permissions issue caused docker pull to fail
sudo chmod 666 /var/run/docker.sock;

# open a terminal on a running container:
sudo docker exec -it dazzling_mestorf sh
