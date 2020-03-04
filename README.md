# Pinocchio Deployment Steps
```
git clone https://github.com/awhdesmond/fyp-newsbot
git clone https://github.com/awhdesmond/fyp-api
git clone https://github.com/awhdesmond/fyp-web
git clone https://github.com/awhdesmond/fyp-nlp

cd fyp-api
docker build -t pinocchio-api .
cd fyp-web
docker build -t pinocchio-web .
cd fyp-nlp
docker build -t pinocchio-nlp .

docker network create pinocchio-network

docker run -d --name elasticsearch -p 5601:5601 -p 9200:9200 --network pinocchio-network nshou/elasticsearch-kibana:kibana6

docker run -d --name pinocchio-web -p 3000:3000 --network pinocchio-network pinocchio-web 

docker run -d --name pinocchio-api -p 9000:9000 --network pinocchio-network pinocchio-api

docker run -d --name pinocchio-nlp -p 8080:8080 --network pinocchio-network -v path/to/DATA_FOLDER:/pinocchio-nlp/DATA_FOLDER pinocchio-nlp
```

## Getting `DATA_FOLDER`
The `DATA_FOLDER` contains the models files and data files needed to build and run the NLP model.

```
rsync -avzh --progress root@206.189.42.104/:/root/fyp-nlp/DATA_FOLDER /path/to/local/DATA_FOLDER
```
Note that when you run rsync it will prompt you for a password.