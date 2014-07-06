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
        self.imagesPanel(tc.stackContainer(title='Images'))
        self.commandsPanel(tc.contentPane(title='Commands',datapath='.commands'))
        self.containerPanel(tc.contentPane(title='Container'))
        self.infoPanel(tc.contentPane(title='Info',datapath='.info'))

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

    def pageHeader(self,pane):
        sb = pane.div()
        sb.div('Dockereasy',font_size='40px',color='#FEE14E',font_weight='bold',line_height='40px',display='inline-block',margin_right='4px',margin_left='10px')
        sb.div('a Genropy Docker UI',font_size='12px',color='#2A7ACC',line_height='40px',display='inline-block')
    
    def pageFooter(self,pane):
        pane.attributes.update(dict(overflow='hidden',background='silver'))
        sb = pane.slotToolbar('3,genrologo,*',_class='slotbar_toolbar framefooter',height='20px',
                        gradient_from='gray',gradient_to='silver',gradient_deg=90)
        sb.genrologo.img(src='/_rsrc/common/images/made_with_genropy.png',height='20px')
    
    def searchImagePanel(self,bc):
        frame = bc.framePane(frameCode='searchGrid',region='top',height='50%',splitter=True)
        bar = frame.top.slotToolbar('2,parentStackButtons,*,remoteSearch,2,searchStarter,5')
        fb = bar.remoteSearch.formbuilder(cols=1,border_spacing='0',margin_top='2px')
        fb.textbox(value='^.imageToSearch',lbl='Search')
        bar.searchStarter.button('Start',fire='.start_search')
        bar.dataRpc('.founded_images',self.searchImages,imageToSearch='=.imageToSearch',
                    _fired='^.start_search')
        f = Bag()
        f.setItem('name',None,width='10em',field='name',name='Name')
        f.setItem('description',None,width='40em',field='description',name='Description')
        f.setItem('is_official',None,dtype='B',field='is_official',name='Official')
        f.setItem('is_trusted',None,dtype='B',field='is_trusted',name='Trusted')
        f.setItem('start_count',None,width='7em',field='start_count',name='S.Count')
        frame.data('.format',f)
        frame.quickGrid(value='^.founded_images',
                        format='^.format')

    @public_method
    def searchImages(self,imageToSearch=None):
        result = Bag()
        result.fromJson(self.docker.search(imageToSearch))
        return result

    def imagesPanel(self,sc):
        bc = sc.borderContainer(title='!!Local')
        frame = bc.frameGrid(frameCode='dockerImages',datapath='.images',
                        grid_selected_Id='.selected_Id',
                      struct=self.struct_images,region='top',height='50%',splitter=True)
        self.searchImagePanel(sc.borderContainer(title='!!Remote'))
        frame.top.slotToolbar('2,parentStackButtons,*,delrow,searchOn,4')
        frame.grid.bagStore(storeType='ValuesBagRows',
                                sortedBy='=.grid.sorted',
                                deleteRows="""function(pkeys,protectPkeys){
                                                    var that = this;
                                                    genro.serverCall('deleteImages',{imagesNames:pkeys},
                                                                    function(){
                                                                        that.loadData();
                                                                    });
                                                }""",
                                data='^.currentImages',selfUpdate=True,
                                _identifier='Id')
        frame.dataRpc('.currentImages',self.getCurrentImages,_onStart=True,_timing=5)
        center = bc.tabContainer(region='center',datapath='.images',margin='2px')
        center.contentPane(title='Inspect').div('==_inspect?_inspect.getFormattedValue({nested:true}):"";',_inspect='^.inspect',margin='2px',font_size='14px')
        center.contentPane(title='History').quickGrid(value='^.history')

        center.dataRpc('dummy',self.getImageDetails,image='^.grid.selected_Id',
                        _onResult="""SET .history=result.pop("history");
                                    SET .inspect=result.pop("inspect");
                                            """)

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
        r.cell('Created', width='6em', name='Created')
        r.cell('Id', width='20em', name='Id')
        r.cell('ParentId', width='20em', name='ParentId')
        r.cell('Size',width='10em',name='Size')
        r.cell('VirtualSize',width='10em',name='VirtualSize')

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

    def containerPanel(self,pane):
        frame = pane.frameGrid(frameCode='containers',datapath='.containers',struct=self.struct_containers)
        bar = frame.top.slotToolbar('2,sbuttons,*,stop_remove_btn,start_btn,searchOn,4')
        bar.start_btn.slotButton('Start',hidden='^.currentStorename?=#v=="active"',action='FIRE .start_selected')
        bar.stop_remove_btn.slotButton('Stop',hidden='^.currentStorename?=#v=="exited"',action='FIRE .stop_selected')
        bar.stop_remove_btn.slotButton('Remove',hidden='^.currentStorename?=#v=="active"',action='FIRE .remove_selected')
        bar.sbuttons.multiButton(value='^.currentStorename',values='active:Active containers,exited:Exited containers')
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
        frame.dataRpc('.containerData',self.getContainers,_onStart=True,_timing=5,_fired='^.forced_reload')

    def struct_containers(self,struct):
        r = struct.view().rows()
        r.cell('Command',width='12em',name='Command')
        r.cell('Created',width='12em',name='Created')
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

        fb.textbox(value='^.dockerpath',lbl='Docker image')
        fb.checkbox(value='^.daemon',lbl='Daemon')
        fb.checkbox(value='^.open_port',lbl='Open ports')

    @public_method
    def saveCommand(self,data=None,**kwargs):
        p = self.site.getStaticPath('site:docker','containers','%s.xml' %data['dockerpath'].replace('/','_'),autocreate=-1)
        data.toXml(p)

    def struct_command(self,struct):
        r = struct.view().rows()
        r.cell('dockerpath')
        r.cell('daemon')
        r.cell('open_port')

    @public_method
    def getCurrentImages(self):
        result = Bag()
        result.fromJson(self.docker.images(),listJoiner=',')
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
                prefix = 'exited'
            else:
                prefix = 'active'
            result.setItem('%s.r_%i' %(prefix,i),r)
        return result

    @property
    def docker(self):
        if not getattr(self,'_docker',None):
            self._docker = Client(DOCKER_HOST)
        return self._docker





