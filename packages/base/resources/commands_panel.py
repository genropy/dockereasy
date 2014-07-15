# -*- coding: UTF-8 -*-
#--------------------------------------------------------------------------
# Copyright (c) : 2004 - 2007 Softwell sas - Milano 
# Written by    : Giovanni Porcari, Michele Bertoldi
#                 Saverio Porcari, Francesco Porcari , Francesco Cavazzana
#--------------------------------------------------------------------------
#This library is free software; you can redistribute it and/or
#modify it under the terms of the GNU Lesser General Public
#License as published by the Free Software Foundation; either
#version 2.1 of the License, or (at your option) any later version.

#This library is distributed in the hope that it will be useful,
#but WITHOUT ANY WARRANTY; without even the implied warranty of
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
#Lesser General Public License for more details.

#You should have received a copy of the GNU Lesser General Public
#License along with this library; if not, write to the Free Software
#Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA

from gnr.web.gnrbaseclasses import BaseComponent
from gnr.core.gnrdecorator import public_method
from gnr.web.gnrwebstruct import struct_method

class CommandsPanel(BaseComponent):
    py_requires='gnrcomponents/framegrid:FrameGrid,gnrcomponents/formhandler:FormHandler'

    @struct_method
    def cm_storedCommandsPanel(self,pane):
        view = pane.frameGrid(frameCode='V_commands' ,struct=self.cm_struct_command,
                                    datapath='.view')
        view.top.slotToolbar('2,vtitle,*,delrow,addrow,5',vtitle='Commands')
        fstore = view.grid.fsStore(childname='store',
                                    folders='site:docker/commands',
                                    include='*.xml')
        view.dataController("fstore.store.loadData();",fstore=fstore,_onBuilt=True)
        form = view.grid.linkedForm(frameCode='F_commands',
                                 datapath='.form',loadEvent='onRowDblClick',
                                 dialog_height='600px',dialog_width='800px',
                                 dialog_title='Command',
                                 handlerType='dialog',
                                 childname='form',attachTo=pane,
                                 store='document')
        form.store.handler('save',rpcmethod=self.cm_saveCommand)
        form.top.slotToolbar('2,navigation,*,delete,add,save,semaphore,2')
        form.commandFormFields()

    @public_method
    def cm_saveCommand(self,data=None,path=None,**kwargs):
        fileid = data['fileid'] or self.getUuid()
        data['fileid'] = fileid
        if path=='*newrecord*':
            path = self.site.getStaticPath('site:docker','commands','%s.xml' %fileid,autocreate=-1)
        data.toXml(path)
        return dict(path=path)

    def cm_struct_command(self,struct):
        r = struct.view().rows()
        r.cell('dockerpath')
        r.cell('daemon')
        r.cell('open_port')

    @struct_method
    def cm_commandFormFields(self,form):
        form.dataController("""var f = new gnr.GnrBag();
                localImages.forEach(function(r){
                        var v = r.getValue()
                        f.setItem(r.label,null,{id:v.getItem('name'),caption:v.getItem('name')});
                    })
            SET #FORM.localImages = f;
            """,localImages='^#localImages.images')
        maintc = form.center.stackContainer(region='center',datapath='.record',margin='2px')
        form.top.slotToolbar('*,stackButtons,*')
        bc = maintc.borderContainer(title='Create')
        fb = bc.contentPane(region='center').div(margin_right='10px').formbuilder(cols=2,border_spacing='3px',colswidth='auto',
                                                        width='100%',fld_width='100%',lbl_margin_left='5px')
        fb.filteringSelect(value='^.image',lbl='Image',storepath='#FORM.localImages',
                            validate_notnull=True,colspan=2)
        
        fb.textbox(value='^.create.command',lbl='Command',colspan=2)
        fb.textbox(value='^.create.hostname',lbl='Hostname')
        fb.textbox(value='^.create.user',lbl='User')
        fb.checkbox(value='^.create.detach',label='Detach')
        fb.checkbox(value='^.create.stdin_open',label='OpenStdin')
        fb.checkbox(value='^.create.tty',label='Tty')
        fb.checkbox(value='^.create.network_disabled',label='Network disabled')
        fb.textbox(value='^.create.name',lbl='Name')
        fb.textbox(value='^.create.entrypoint',lbl='Entrypoint')
        fb.numberTextbox(value='^.create.cpu_shares',lbl='Cpu shares')
        fb.textbox(value='^.create.mem_limit',lbl='Mem. Limit')
        fb.textbox(value='^.create.domainname',lbl='Domain')
        fb.numberTextbox(value='^.create.memswap_limit',lbl='Memswap limit')
        fb.textbox(value='^.create.working_dir',lbl='WorkingDir',colspan=2)

        bottom = bc.framePane(region='bottom',height='150px')
        bottom.top.slotToolbar('*,stackButtons,*')
        tc = bottom.center.stackContainer()
        grid = tc.contentPane(title='Ports').quickGrid(value='^.create.ports',border='1px solid silver') #list
        grid.column('ip',name='IP',width='100%',edit=True)
        grid.column('hostPort',width='7em',name='HostPort',edit=True)
        grid.column('containerPort',width='7em',name='ContainerPort',edit=True)
        grid.tools('delrow,addrow',position='BL')
        grid = tc.contentPane(title='Volumes').quickGrid(value='^.common.volumes',border='1px solid silver') #list
        grid.column('volumePath',name='VolumePath',width='50%',edit=True)
        grid.column('hostPath',name='HostPath',width='50%',edit=True)
        grid.tools('delrow,addrow',position='BL')
        grid = tc.contentPane(title='Volumes from').quickGrid(value='^.common.volumes_from',border='1px solid silver') #list
        grid.column('container',name='Container',width='100%',edit=dict(tag='filteringSelect',storepath='#FORM.localImages'))
        grid.tools('delrow,addrow',position='BL')
        grid = tc.contentPane(title='Dns').quickGrid(value='^.common.dns',border='1px solid silver') #list
        grid.column('dns',name='DNS',width='100%',edit=True)
        grid.tools('delrow,addrow',position='BL')
        grid = tc.contentPane(title='Env').quickGrid(value='^.create.environment',border='1px solid silver') #dict
        grid.column('varname',name='Key',width='50%',edit=True)
        grid.column('value',name='Value',width='50%',edit=True)
        grid.tools('delrow,addrow',position='BL')

        #start
        bc = maintc.borderContainer(title='Start')

        fb = bc.contentPane(region='top').div(margin_right='10px').formbuilder(cols=3,border_spacing='3px',
                                                        lbl_min_width='30px',colswidth='auto',
                                                        width='100%',fld_width='100%')
        fb.textbox(value='^.start.network_mode',lbl='Network mode')
        fb.checkbox(value='^.start.publish_all_ports',label='All Ports',lbl=' ')
        fb.checkbox(value='^.start.privileged',label='Privileged',lbl=' ')
        fb.simpleTextArea(value='^.start.dns_search',lbl='Dns search',colspan=3)

        bottom = bc.framePane(region='center')
        bottom.top.slotToolbar('*,stackButtons,*')
        tc = bottom.center.stackContainer()

        tc.contentPane(title='Binds').simpleTextArea(value='^.start.binds')
        tc.contentPane(title='Port Bindings').simpleTextArea(value='^.start.port_bindings')
        tc.contentPane(title='Lxc conf').simpleTextArea(value='^.start.lxc_conf',lbl='Lxc conf')
        grid = tc.contentPane(title='Links').quickGrid(value='^.start.links',border='1px solid silver') #list
        grid.column('container',name='Container',width='20em',edit=dict(tag='filteringSelect',storepath='#FORM.localImages'))
        grid.column('alias',name='Alias',width='20em',edit=True)
        grid.tools('delrow,addrow',position='BL')




    @struct_method
    def cm_commandFormRunner(self,pane):
        dlg = pane.dialog(title='Create and Run')
        form = dlg.frameForm(frameCode='container_runner',
                            height='400px',width='500px',
                            datapath='main.create.runner',
                            store='memory')
        form.commandFormFields()
        bottom_bar = form.bottom.slotBar('2,cancel_btn,*,confirm,2',_class='slotbar_dialog_footer')
        bottom_bar.cancel_btn.button('Close', action= 'this.form.abort();')
        bottom_bar.confirm.button('Run', action= 'FIRE #FORM.runcontainer;')
        bottom_bar.dataRpc('dummy',self.cm_createAndRun,_fired='^#FORM.runcontainer',
                            data='=#FORM.record',
                            _onResult='this.form.abort();',_lockScreen=True)
        form.dataController('dlg.show()',formsubscribe_onLoaded=True,dlg=dlg.js_widget)
        form.dataController('dlg.hide()',formsubscribe_onDismissed=True,dlg=dlg.js_widget)
        return form

    @public_method
    def cm_createAndRun(self,data=None):
        ports = data['ports']
        if ports:
            ports = ports.split('\n')
        result = self.docker.create_container(data['image'], command=data['command'],
                        hostname=data['hostname'], user=data['user'],
                         detach = data['detach'] or False, 
                         stdin_open = data['stdin_open'] or False, 
                         tty = data['tty'] or False,
                         mem_limit=data['mem_limit'] or 0, 
                         ports=ports, 
                         environment=data['environment'], 
                         dns=data['dns'].split(',') if data['dns'] else None,
                         volumes=data['volumes'].split(',') if data['volumes'] else None, 
                         volumes_from=data['volumes_from'].split(',') if data['volumes_from'] else None,
                         network_disabled=data['network_disabled'] or False, 
                         name=data['name'], entrypoint=data['entrypoint'],
                         cpu_shares=data['cpu_shares'], working_dir=data['working_dir'], domainname=data['domainname'],
                         memswap_limit=data['memswap_limit'] or 0)        
        self.docker.start(result['Id'])


