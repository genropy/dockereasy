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
                                 dialog_height='450px',dialog_width='620px',
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
                        f.setItem(r.label,null,{id:v.getItem('Id'),caption:v.getItem('RepoTags')});
                    })
            SET #FORM.localImages = f;
            """,localImages='^#localImages.images')
        bc = form.center.borderContainer()
        pane = bc.contentPane(region='center',datapath='.record')
        fb = pane.div(margin='10px').formbuilder(cols=2,border_spacing='3px')
        fb.filteringSelect(value='^.image',lbl='Image',storepath='#FORM.localImages',validate_notnull=True)
        
        fb.textbox(value='^.create.command',lbl='Command')
        fb.textbox(value='^.create.hostname',lbl='Hostname')
        fb.textbox(value='^.create.user',lbl='User')
        fb.checkbox(value='^.create.detach',label='Detach')
        fb.checkbox(value='^.create.stdin_open',label='OpenStdin')
        fb.checkbox(value='^.create.tty',label='Tty')
        fb.checkbox(value='^.create.network_disabled',label='Network disabled')
        fb.textbox(value='^.create.name',lbl='Name')
        fb.textbox(value='^.create.entrypoint',lbl='Entrypoint')
        fb.checkbox(value='^.create.cpu_shares',label='Cpu shares')
        fb.textbox(value='^.create.working_dir',lbl='WorkingDir')
        fb.textbox(value='^.create.domainname',lbl='Domain')
        fb.numberTextbox(value='^.create.memswap_limit',lbl='Memswap limit')
        fb.simpleTextArea(value='^.create.environment',lbl='Env') #dict
        fb.simpleTextArea(value='^.create.ports',lbl='Ports') #list
        fb.simpleTextArea(value='^.common.dns',lbl='Dns') #list
        fb.simpleTextArea(value='^.common.volumes',lbl='Volumes') #list
        fb.simpleTextArea(value='^.common.volumes_from',lbl='Volumes from') #list
        
        #start
        fb.simpleTextArea(value='^.start.binds',lbl='Binds')
        fb.simpleTextArea(value='^.start.port_bindings',lbl='Port Bindings')
        fb.simpleTextArea(value='^.start.lxc_conf',lbl='Lxc conf')
        fb.checkbox(value='^.start.publish_all_ports',label='All Ports')
        fb.simpleTextArea(value='^.start.links',lbl='Links')
        fb.simpleTextArea(value='^.start.dns_search',lbl='Dns search')
        fb.checkbox(value='^.start.privileged',label='Privileged')
        fb.textbox(value='^.start.network_mode',lbl='Network mode')


    @struct_method
    def cm_commandFormRunner(self,pane):
        dlg = pane.dialog(title='Create and Run')
        form = dlg.frameForm(frameCode='container_runner',
                            height='450px',width='620px',
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


