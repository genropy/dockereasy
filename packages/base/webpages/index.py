#!/usr/bin/env pythonw
# -*- coding: UTF-8 -*-
#
#  untitled
#
#  Created by Giovanni Porcari on 2007-03-24.
#  Copyright (c) 2007 Softwell. All rights reserved.
#


from gnr.core.gnrdecorator import public_method
from gnr.core.gnrbag import Bag
from docker.client import Client
import sh
import urllib
from bs4 import BeautifulSoup
from gnr.core.gnrstring import fromJson
from time import sleep
try:
    DOCKER_HOST = 'tcp://%s:2375' %sh.boot2docker('ip')
except sh.CommandNotFound,e:
    DOCKER_HOST = 'unix://docker.sock'

class GnrCustomWebPage(object):
    css_requires='public'
    py_requires='gnrcomponents/framegrid:FrameGrid,gnrcomponents/formhandler:FormHandler'
    google_fonts = 'Oxygen:400,700,300'
    
    def isDeveloper(self):
        return True
        
    def main(self, root, **kwargs):
        bc = root.borderContainer(background_color='#fefefe', font_family="'Oxygen', sans-serif")
        self.pageHeader(bc.contentPane(region='top'))
        self.pageFooter(bc.contentPane(region='bottom'))
        tc = bc.tabContainer(region='center',splitter=True,margin='2px',datapath='main')
        self.imagesPanel(tc.stackContainer(title='Images',datapath='.images'))
        self.containersPanel(tc.borderContainer(title='Containers',datapath='.containers'))
        self.commandsPanel(tc.contentPane(title='Commands',datapath='.commands'))
        self.infoPanel(tc.contentPane(title='Info',datapath='.info'))

    def pageHeader(self,pane):
        sb = pane.div(padding_bottom='2px')
        sb.div('Dockereasy',font_size='40px',color='#FEE14E',font_weight='bold',line_height='40px',display='inline-block',margin_right='4px',margin_left='10px')
        sb.div('a Genropy Docker UI',font_size='12px',color='#2A7ACC',line_height='40px',display='inline-block')
    
    def pageFooter(self,pane):
        pane.attributes.update(dict(overflow='hidden',background='silver'))
        sb = pane.slotToolbar('3,genrologo,*',_class='slotbar_toolbar framefooter',height='20px',
                        gradient_from='gray',gradient_to='silver',gradient_deg=90)
        sb.genrologo.img(src='/_rsrc/common/images/made_with_genropy.png',height='20px')
        
    def infoPanel(self,pane):
        info = Bag()
        info.fromJson(self.docker.info())
        version = Bag()
        version.fromJson(self.docker.version())
        pane.data('.info',info)
        pane.data('.version',version)
        box = pane.div(margin='10px')
        box.div('Info',color='#2A7ACC',font_weight='bold',line_height='40px',padding='5px',font_size='18px')
        box.div('==_v.getFormattedValue({nested:true})',_v='^.info')
        box = pane.div(margin='10px')
        box.div('Version',color='#2A7ACC',font_weight='bold',line_height='40px',padding='5px',font_size='18px')
        box.div('==_v.getFormattedValue({nested:true})',_v='^.version')

    @public_method
    def searchImages(self,imageToSearch=None):
        result = Bag()
        currentImages = [img['RepoTags'][0].split(':')[0] for img in self.docker.images() if img['RepoTags'][0]]
        images = self.docker.search(imageToSearch)
        for img in images:
            b = Bag(img)
            if b['name'] in currentImages:
                command = 'Update Image'
            else:
                command = 'Pull image'
            b['status'] = """<a style="cursor:pointer; text-align:center;" href="javascript:genro.publish('pull_image',{image:'%s'})">%s</a> """ %(b['name'],command)
            result.setItem(img['name'],b)
        return result

    def imagesPanel(self,sc):
        bc = sc.borderContainer(title='!!Local',datapath='.local',nodeId='localImages')
        self.searchImagePanel(sc.borderContainer(title='!!Remote',datapath='.remote'))
        frame = bc.frameGrid(frameCode='dockerImages',
                        grid_selected_Id='.selected_Id',
                      struct=self.struct_images,region='top',height='50%',splitter=True,
                      border_bottom='1px solid silver')
        
        frame.top.slotToolbar('2,parentStackButtons,*,delrow,searchOn,4')
        frame.grid.bagStore(storeType='ValuesBagRows',
                                sortedBy='=.grid.sorted',

                                deleteRows="""function(pkeys,protectPkeys){
                                                    var that = this;
                                                    genro.serverCall('deleteImages',{imagesNames:pkeys},
                                                                    function(){
                                                                        that.storeNode.fireEvent('.reload');
                                                                    });
                                                }""",
                                data='^.images',selfUpdate=True,
                                _identifier='Id')
        frame.dataRpc('.images',self.getLocalImages,_onStart=True,_lockScreen=True,
                     _fired ='^.reload')
        center = bc.tabContainer(region='center',margin='2px')
        center.contentPane(title='Inspect').div('==_inspect?_inspect.getFormattedValue({nested:true}):"";',
                                          _inspect='^.detail.inspect',margin='2px',font_size='12px')
        center.contentPane(title='History').quickGrid(value='^.detail.history')

        center.dataRpc('.detail',self.getImageDetails,image='^.grid.selected_Id',
                        _if='image',_else='null')

    @public_method
    def getImageDetails(self,image=None):
        inspect = Bag()
        history = Bag()
        inspect.fromJson(self.docker.inspect_image(image))
        history.fromJson(self.docker.history(image))
        return Bag(dict(inspect=inspect,history=history))

    @public_method
    def deleteImages(self,imagesNames=None):
        docker = self.docker
        for imgname in imagesNames:
            docker.remove_image(imgname,force=True)

    def struct_images(self,struct):
        r = struct.view().rows()
        r.cell('RepoTags',width='15em',name='RepoTags')
        r.cell('Created', width='12em', name='Created',format='epoch')
        r.cell('Id', width='20em', name='Id')
        r.cell('ParentId', width='20em', name='ParentId')
        r.cell('Size',width='10em',name='Size',format='bytes')
        r.cell('VirtualSize',width='10em',name='VirtualSize',format='bytes')
        
    def searchImagePanel(self,bc):
        frame = bc.framePane(frameCode='searchGrid',region='top',height='50%',
                           border_bottom='1px solid silver',splitter=True)
        bar = frame.top.slotToolbar('2,parentStackButtons,20,remoteSearch,*,10,searchOn,4')
        bar.dataRpc('.data',self.searchImages,imageToSearch='^.imageToSearch',_lockScreen=True)
        fb = bar.remoteSearch.formbuilder(cols=1,border_spacing='0',margin_top='2px')
        fb.textbox(value='^.imageToSearch',lbl='Search string',lbl_margin_right='2px',onEnter=True)
        #bar.pull_image.slotButton('Pull images',action='FIRE .pull_selected')
        frame.data('.format',self.searchImage_format())
        grid=frame.quickGrid(value='^.data',format='^.format',multiSelect=False,
                            subscribe_update_image_pull="""
                            var b = this.widget.storebag();
                            var r = b.getItem($1.image);
                            if(!r){
                                return;
                            }
                            r.setItem('status',$1.status);
                            """,
                            selected_name='.selected_image_name')
        grid.dataRpc('dummy',self.pullImage,subscribe_pull_image=True,
                    _onCalling='genro.publish("update_image_pull",{image:image,status:"Prepare pull..."})',
                    _onResult='FIRE #localImages.reload;',
                    timeout=0)
        center = bc.contentPane(region='center')
        center.dataRpc('.image_info',self.getRemoteImageInfo, image_name='^.selected_image_name',
                                _if='image_name',_else='')
                                
        center.contentPane(overflow='hidden').iFrameDiv(value='^.image_info',height='100%',width='100%',zoom='.8')
       
    @public_method
    def getRemoteImageInfo(self,image_name=None):
        urlobj = urllib.urlopen('http://registry.hub.docker.com/u/%s' % image_name)
        bs=BeautifulSoup(urlobj.read())
        r=bs.find_all(class_='repo-info-tab-body')
        if r:
            return r[0]
                
    def searchImage_format(self):
        format = Bag()
        format.setItem('name',None,width='10em',name='Name')
        format.setItem('description',None,width='40em',name='Description')
        format.setItem('is_official',None,dtype='B',name='Official')
        format.setItem('is_trusted',None,dtype='B',name='Trusted')
        format.setItem('star_count',None,width='7em',name='Stars')
        format.setItem('status',None,width='100%',name='Status')
        return format
        
    @public_method
    def pullImage(self,image=None):
        for prog in self.docker.pull(image,stream=True):
            prog = fromJson(prog)
            status = prog.get('status')
            if not status:
                continue
            if ' from ' in status:
                status,f = status.split(' from ')
            status = """ %s: %s """ %(status,prog['id'])
            progressDetail = prog.get('progressDetail',None)
            if progressDetail:
                progressDetail['status'] = status
                progress = prog.get('progress','')
                if progress:
                    progressDetail['desc'] = progress.split(']')[1].strip()
                else:
                    progressDetail['desc'] = ''
                status = r""" %(status)s <progress style='width:12em' max='%(total)s' value='%(current)s'></progress> %(desc)s """ %progressDetail
            print 'status',status
            self.clientPublish('update_image_pull',status=status,image=image)
    
        
    def containersPanel(self,bc):
        self.containersPane_top(bc.contentPane(region='top',height='50%',border_bottom='1px solid silver',splitter=True))
        self.containersPane_center(bc.tabContainer(region='center',margin='2px'))
        
    def containersPane_top(self,top):
        frame=top.frameGrid(frameCode='containers',struct=self.struct_containers,grid_selected_Id='.selected_Id')
        bar = frame.top.slotToolbar('2,sbuttons,*,stop_remove_btn,start_btn,searchOn,4')
        bar.start_btn.slotButton('Start',hidden='^.currentStorename?=#v=="active"',action='FIRE .start_selected')
        bar.stop_remove_btn.slotButton('Stop',hidden='^.currentStorename?=#v=="inactive"',action='FIRE .stop_selected')
        bar.stop_remove_btn.slotButton('Remove',hidden='^.currentStorename?=#v=="active"',action='FIRE .remove_selected')
        bar.sbuttons.multiButton(value='^.currentStorename',values='active:Active containers,inactive:Inactive containers')
        rpckw = dict(_grid=frame.grid.js_widget,
                    _onCalling='kwargs["pkeys"]=_grid.getSelectedPkeys()',
                    _onResult='FIRE .forced_reload;')
        bar.dataRpc('dummy',self.startSelectedContainers,_fired='^.start_selected',**rpckw)
        bar.dataRpc('dummy',self.stopSelectedContainers,_fired='^.stop_selected',_ask='You are stopping some containers. Confirm?',**rpckw)
        bar.dataRpc('dummy',self.removeSelectedContainers,_fired='^.remove_selected',_ask='You are removing some containers. Confirm?',**rpckw)

        frame.grid.bagStore(storeType='ValuesBagRows',
                                sortedBy='=.grid.sorted',
                                data='^.currentStoreData',selfUpdate=True,
                                _identifier='Id')
        bar.dataController("""
                            var currentStoreData = data.getItem(currentStorename);
                            SET .currentStoreData = currentStoreData?currentStoreData.deepCopy():new gnr.GnrBag();""",
                            data='^.containerData',currentStorename='^.currentStorename',_delay=100)
        frame.dataRpc('.containerData',self.getContainers,_onStart=True,_fired='^.forced_reload',_lockScreen=True)
  
    def containersPane_center(self,center):
        center.contentPane(title='Inspect').div('==_inspect?_inspect.getFormattedValue({nested:true}):"";',
                                          _inspect='^.detail.inspect',margin='2px',font_size='12px')
        
        center.contentPane(title='Changes').quickGrid(value='^.detail.changes')
        #center.contentPane(title='Process').quickGrid(value='^.detail.process')
        center.contentPane(title='Logs').pre(value='^.detail.logs')
        center.dataRpc('.detail',self.getContainerDetails, container='^.grid.selected_Id',
                        _if='container',_else='null')

    @public_method
    def getContainerDetails(self,container=None):
        inspect = Bag()
        changes = Bag()
        inspect.fromJson(self.docker.inspect_container(container))
        changes.fromJson(self.docker.diff(container))
        return Bag(dict(inspect=inspect,changes=changes,logs=self.docker.logs(container)))
        
        
    @public_method
    def startSelectedContainers(self,pkeys=None):
        for contId in pkeys:
            self.docker.start(contId,publish_all_ports=True)

    @public_method
    def stopSelectedContainers(self,pkeys=None):
        for contId in pkeys:
            self.docker.stop(contId)

    @public_method
    def removeSelectedContainers(self,pkeys=None):
        for contId in pkeys:
            self.docker.remove_container(contId)

    def struct_containers(self,struct):
        r = struct.view().rows()
        r.cell('Command',width='12em',name='Command')
        r.cell('Created',width='12em',name='Created',format='epoch')
        r.cell('Id',width='20em',name='Id')
        r.cell('Image',width='20em',name='Image')
        r.cell('Names',width='20em',name='Names')
        r.cell('Ports',width='20em',name='Ports')
        r.cell('Status',width='12em',name='Status')

    def commandsPanel(self,pane):
        view = pane.frameGrid(frameCode='V_commands' ,struct=self.struct_command,
                                    datapath='.view')
        view.top.slotToolbar('2,vtitle,*,delrow,addrow,5',vtitle='Commands')
        fstore = view.grid.fsStore(childname='store',
                                    folders='site:docker/commands',
                                    include='*.xml')
        view.dataController("fstore.store.loadData();",fstore=fstore,_onBuilt=True)
        form = view.grid.linkedForm(frameCode='F_commands',
                                 datapath='.form',loadEvent='onRowDblClick',
                                 dialog_height='450px',dialog_width='620px',
                                 modal=True,
                                 dialog_title='Command',
                                 handlerType='dialog',
                                 childname='form',attachTo=pane,
                                 store='document')
        form.store.handler('save',rpcmethod=self.saveCommand)

        fb = form.record.formbuilder(cols=2,border_spacing='3px')
        form.top.slotToolbar('2,navigation,*,delete,add,save,semaphore,2')
        form.dataController("""var f = new gnr.GnrBag();
                localImages.forEach(function(r){
                    console.log('r',r);
                        var v = r.getValue()
                        f.setItem(r.label,null,{id:v.getItem('Id'),caption:v.getItem('RepoTags')});
                    })
            SET #FORM.localImages = f;
            """,localImages='^#localImages.images')
        fb.filteringSelect(value='^.image',lbl='Image',storepath='#FORM.localImages')
        fb.textbox(value='^.command',lbl='Command')
        fb.textbox(value='^.hostname',lbl='Hostname')
        fb.textbox(value='^.user',lbl='User')
        fb.checkbox(value='^.detach',lbl='Detach')
        fb.checkbox(value='^.stdin_open',lbl='OpenStdin')
        fb.checkbox(value='^.tty',lbl='Tty')
        fb.simpleTextArea(value='^.ports',lbl='Ports') #list
        fb.textbox(value='^.environment',lbl='Env') #dict
        fb.simpleTextArea(value='^.dns',lbl='Dns') #list
        fb.simpleTextArea(value='^.volumes',lbl='Volumes') #list
        fb.simpleTextArea(value='^.volumes_from',lbl='Volumes from') #list
        fb.checkbox(value='^.network_disabled',lbl='Network disabled')
        fb.textbox(value='^.name',lbl='Name')
        fb.textbox(value='^.entrypoint',lbl='Entrypoint')
        fb.checkbox(value='^.cpu_shares',lbl='Cpu shares')
        fb.textbox(value='^.working_dir',lbl='WorkingDir')
        fb.textbox(value='^.domainname',lbl='Domain')
        fb.numberTextbox(value='^.memswap_limit',lbl='Memswap limit')


    #def create_container(self, image, command=None, hostname=None, user=None,
    #        detach=False, stdin_open=False, tty=False,
    #        mem_limit=0, ports=None, environment=None, dns=None,
    #        volumes=None, volumes_from=None,
    #        network_disabled=False, name=None, entrypoint=None,
    #        cpu_shares=None, working_dir=None, domainname=None,
    #        memswap_limit=0):
    

#def _container_config(self, image, command, hostname=None, user=None,
            #detach=False, stdin_open=False, tty=False,
            #mem_limit=0, ports=None, environment=None, dns=None,
            #volumes=None, volumes_from=None,
            #network_disabled=False, entrypoint=None,
            #cpu_shares=None, working_dir=None, domainname=None,
            #memswap_limit=0):   

#{
#"Hostname":"",
#"User":"",
#"Memory":0,
#"MemorySwap":0,
#"AttachStdin":false,
#"AttachStdout":true,
#"AttachStderr":true,
#"PortSpecs":null,
#"Tty":false,
#"OpenStdin":false,
#"StdinOnce":false,
#"Env":null,
#"Cmd":[
#"date"
#],
#"Image":"base",
#"Volumes":{
#"/tmp": {}
#},
#"WorkingDir":"",
#"DisableNetwork": false,
#"ExposedPorts":{
#"22/tcp": {}
#}
#}

#HTTP/1.1 201 OK
#Content-Type: application/json
#
#{
#"Id":"e90e34656806"
#"Warnings":[]
#}
#







    @public_method
    def saveCommand(self,data=None,path=None,**kwargs):
        fileid = data['fileid'] or self.getUuid()
        data['fileid'] = fileid
        if path=='*newrecord*':
            path = self.site.getStaticPath('site:docker','commands','%s.xml' %fileid,autocreate=-1)
        data.toXml(path)
        return dict(path=path)

    def struct_command(self,struct):
        r = struct.view().rows()
        r.cell('dockerpath')
        r.cell('daemon')
        r.cell('open_port')

    @public_method
    def getLocalImages(self):
        result = Bag()
        images = self.docker.images()
        if images:
            result.fromJson(images,listJoiner=',')
        return result

    @public_method
    def getContainers(self):
        result = Bag()
        for i,cnt in enumerate(self.docker.containers(all=True)):
            #0.0.0.0:49153->8080/tcp
            r = Bag(cnt)
            r['Names'] = ','.join(r['Names'])
            r['Ports'] = ','.join(['%(IP)s:%(PublicPort)s->%(PrivatePort)s/%(Type)s' %kw for kw in r['Ports']])
            if 'Exited' in r['Status']:
                prefix = 'inactive'
            else:
                prefix = 'active'
            result.setItem('%s.r_%i' %(prefix,i),r)
        return result

    @property
    def docker(self):
        if not getattr(self,'_docker',None):
            self._docker = Client(DOCKER_HOST)
        return self._docker





