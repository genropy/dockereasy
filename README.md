Dockereasy
=======

A Genropy UI for docker.
-
Release 0.1


![image](https://raw.githubusercontent.com/genropy/dockereasy/master/Dockereasy.png)
**Features**

  - Local images: list, inspect, remove, history, pull
  - Repository images : search & Info
  - Containers : Stop, Start, Remove, Inspect,Changes,Logs
  
  
**To do**

  - Create containers
  - Commit, Push
  - More....
 
Try dockereasy in a container
-
  

	sudo docker run -d -p 8990:8990 -v /var/run/docker.sock:/docker.sock genropy/dockereasy
	
Open your browser to http://*dockerost_ip*:8990

	
Browsers
-
Chrome

Safari 

Firefox

Github
-

https://github.com/genropy/dockereasy
 

**Dockereasy**: Copyright (c) 2014 Softwell.it

License
=======

The code is licensed under the LGPL license::
    
    This library is free software; you can redistribute it and/or
    modify it under the terms of the GNU Lesser General Public
    License as published by the Free Software Foundation; either
    version 2.1 of the License, or (at your option) any later version.
    
    This library is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
    GNU Lesser General Public License for more details.
    
    You should have received a copy of the GNU Lesser General Public
    License along with this library; if not, write to the Free Software
    Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA
