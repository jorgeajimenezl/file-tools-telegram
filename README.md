# Telegram bot for manage your files

## Deploy

## Deploy (Debian)
Clone repository to the VM  
[WARNING]: Edit configuration in `src/config/config.yml`

### Install dependencies
```shell
~> sudo apt update
~> sudo apt install -y curl build-essential tcl libssl-dev libffi-dev python3-setuptools
~> sudo apt install -y python3.9 python3.9-dev python3.9-pip virtualenv
~> sudo apt install -y redis
```

### Create and activate virtual enviroment
```shell
~> virtualenv --python=python3 env
~> source ./env/bin/activate
```

### Install app dependencies
```shell
(env) ~> pip3 install -r requirements.txt
```

### Start *file-toolsbot*
```shell
(env) ~> python3 app.py
```