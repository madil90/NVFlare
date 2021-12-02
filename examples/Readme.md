# Hello NVFlare setup

This document describes the basic setup required to run hello apps in NVFlare.

## (Optional) 1. Set up a virtual environment
```
python3 -m pip install --user --upgrade pip
python3 -m pip install --user virtualenv
```
(If needed) make all shell scripts executable using
```
find . -name ".sh" -exec chmod +x {} \;
```
initialize virtual environment.
```
source ./virtualenv/set_env.sh
```
install required packages for training
```
pip install --upgrade pip
pip install -r ./virtualenv/min-requirements.txt
```
(optional) if you would like to plot the TensorBoard event files as shown below, please also install
```
pip install -r ./virtualenv/plot-requirements.txt
```
For details of installing NVFlare, please see [Installation](https://nvidia.github.io/NVFlare/installation.html).

## 2. Create your FL workspace 

### 2.1 POC ("proof of concept") workspace
To run FL experiments in POC mode, create your local FL workspace the below command. 
In the following experiments, we will be using 8 clients. Press y and enter when prompted. 
```
cd setup
./create_poc_workpace.sh 8
```

### 2.2 (Optional) Secure FL workspace

The project file for creating the secure workspace used in this example is shown at 
[./workspaces/secure_project.yml](setup/workspaces/secure_project.yml).

To create the secure workspace, please use the following to build a package and copy it 
to `secure_workspace` for later experimentation.
```
cd ./setup/workspaces
provision -p ./secure_project.yml
cp -r ./workspace/secure_project/prod_00 ./secure_workspace
mkdir -p admin@nvidia.com/admin/transfer
cp -rf ../../../examples/* admin@nvidia.com/admin/transfer
cd ..
```
For more information about secure provisioning see the [documentation](https://nvidia.github.io/NVFlare/user_guide/provisioning_tool.html).

For more information about secure provisioning see the [documentation](https://nvidia.github.io/NVFlare/user_guide/provisioning_tool.html).

> **_NOTE:_** **POC** stands for "proof of concept" and is used for quick experimentation 
> with different amounts of clients.
> It doesn't need any advanced configurations while provisioning the startup kits for the server and clients. 
>
> The **secure** workspace on the other hand is needed to run experiments that require encryption keys such as the 
> homomorphic encryption (HE) one shown below. These startup kits allow secure deployment of FL in real-world scenarios 
> using SSL certificated communication channels.

### Running server and clients

With both the client and server ready, you can now run everything and see federated learning in action. FL systems usually have a server and multiple clients. We therefore have to start the server first:

```
./poc/server/startup/start.sh
```

Once the server is running you can start the clients in different terminals. Open a new terminal and start the first client:

```
./poc/site-1/startup/start.sh
```

Perform the step above for all the other clients. In the last terminal start the admin:

```
./poc/admin/startup/fl_admin.sh localhost
```

This will launch a command prompt, where you can input commands to control and monitor many aspects of the FL process. Log in by entering admin for both the username and password.

### Running the FL System

Enter the commands below in order. Pay close attention to what happens in each of four terminals. You can see how the admin controls the server and clients with each command. 

```
upload_app <example_name>
```

Uploads the application from the admin client to the  server's staging area.

```
set_run_number 1
```

Creates a run directory in the workspace for the run_number on the server and all clients. The run directory allows for the isolation of different runs so the information in one particular run does not interfere with other runs.

```
deploy_app <example_name> all
```

This will make the hello-pt application the active one in the run_number workspace. After the above two commands, the server and all the clients know the hello-pt application will reside in the run_1 workspace.

```
start_app all
```

This start_app command instructs the NVIDIA FLARE server and clients to start training with the hello-pt application in that run_1 workspace. 

From time to time, you can issue check_status server in the admin client to check the entire training progress.

You should now see how the training does in the very first terminal (the one that started the server).

Once the fl run is complete and the server has successfully aggregated the clients’ results after all the rounds, run the following commands in the fl_admin to shutdown the system (while inputting admin when prompted with user name):

```
shutdown client
shutdown server
bye
```

In order to stop all processes, run ./stop_fl.sh.

All artifacts from the FL run can be found in the server run folder you created with set_run_number. In the above example, the folder used is run_1.